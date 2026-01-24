import streamlit as st
import re
import requests
import json

# --- 1. 頁面設定 ---
st.set_page_config(page_title="Poker Copilot War Room", page_icon="♠️", layout="wide")

# CSS 優化：深色戰情室風格
st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    div[data-testid="stMetric"] {
        background-color: #1e212b;
        border: 1px solid #333;
        padding: 10px;
        border-radius: 8px;
    }
    .poker-card { font-size: 1.8rem; font-weight: bold; }
    .big-summary { background-color: #2b2d3e; padding: 20px; border-radius: 10px; border-left: 5px solid #ff4b4b; }
</style>
""", unsafe_allow_html=True)

st.title("♠️ Poker Copilot: War Room")
st.caption("Version 10.0 | 戰情室版 (總結報告 + 資金曲線 + 篩選器)")

# --- 2. 側邊欄：設定與篩選 ---
with st.sidebar:
    st.header("⚙️ 設定")
    api_key = st.text_input("Gemini API Key", type="password")
    
    # 自動偵測模型
    selected_model = "gemini-1.5-flash"
    if api_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                models = [m['name'].replace('models/', '') for m in data.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
                models.sort(key=lambda x: 'flash' not in x)
                if models: selected_model = st.selectbox("AI 引擎", models, index=0)
        except: pass
    
    st.divider()
    
    st.header("🔍 列表篩選")
    filter_vpip = st.checkbox("只顯示有玩的手牌 (VPIP)", value=False)
    filter_lost = st.checkbox("只顯示輸錢的手牌", value=False)
    filter_showdown = st.checkbox("只顯示攤牌 (Showdown)", value=False)

# --- 3. 核心解析邏輯 ---
def load_content(uploaded_file):
    bytes_data = uploaded_file.getvalue()
    encodings = ["utf-8", "utf-16-le", "utf-16", "utf-8-sig", "latin-1"]
    for enc in encodings:
        try:
            decoded = bytes_data.decode(enc)
            if "Hand" in decoded or "Poker" in decoded: return decoded
        except: continue
    return None

def parse_hands(content):
    if not content: return []
    raw_hands = re.split(r"(Poker Hand #|Hand #)", content)
    parsed = []
    current_hand = ""
    for part in raw_hands:
        if "Hand #" in part:
            if current_hand: process_single_hand(current_hand, parsed)
            current_hand = part
        else: current_hand += part
    if current_hand: process_single_hand(current_hand, parsed)
    return parsed

def process_single_hand(h, parsed_list):
    if len(h) < 50: return
    # 抓 ID
    hid = re.search(r"TM(\d+):", h) or re.search(r"#(\d+):", h)
    hid_str = hid.group(1) if hid else "Unknown"
    
    # 抓 Hero 牌
    hero_cards = re.search(r"Dealt to Hero \[(.*?)\]", h)
    cards = hero_cards.group(1) if hero_cards else None
    
    # 抓籌碼量 (這是畫圖的關鍵) - 嘗試抓取 Hero (...) 裡面的數字
    # GGPoker: Seat 1: Hero (1500)
    # PokerStars: Seat 1: Hero ($1500 in chips)
    chip_match = re.search(r"Hero \(\$?([\d,]+).*\)", h)
    chips = int(chip_match.group(1).replace(",", "")) if chip_match else 0
    
    # VPIP/PFR 判定
    is_vpip = "Hero: raises" in h or "Hero: calls" in h or "Hero: bets" in h
    is_pfr = "Hero: raises" in h or "Hero: bets" in h
    
    # 輸贏判定
    res = "😐"
    if "Hero showed" in h and "lost" in h: res = "❌"
    elif "Hero collected" in h or "Hero won" in h: res = "💰"
    elif "Hero folded" in h: res = "🛡️"
    
    # 是否攤牌
    is_showdown = "Hero showed" in h or "Hero mucks" in h
    
    if cards or chips > 0: # 只要有籌碼紀錄或有牌就抓
        parsed_list.append({
            "id": hid_str, "cards": cards, "result": res, 
            "is_vpip": is_vpip, "is_pfr": is_pfr, "chips": chips,
            "is_showdown": is_showdown, "raw": h,
            "result_text": "輸" if res == "❌" else "贏" if res == "💰" else "平/棄"
        })

def cards_to_emoji(card_str):
    if not card_str: return ""
    suits_map = {'s': '♠️', 'h': '♥️', 'd': '♦️', 'c': '♣️'}
    formatted = []
    for card in card_str.split():
        if len(card) >= 2:
            formatted.append(f"{card[:-1]}{suits_map.get(card[-1], card[-1])}")
    return " ".join(formatted)

# --- 4. AI 功能模組 ---

# 功能 A: 單手牌分析
def analyze_hand_ai(hand_text, api_key, model):
    if not api_key: return "⚠️ 請輸入 Key"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    prompt = f"你是一個德州撲克教練。請用繁體中文，犀利地點評這手牌 Hero 的決策：\n{hand_text}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        resp = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        return resp.json()['candidates'][0]['content']['parts'][0]['text'] if resp.status_code == 200 else f"Error: {resp.text}"
    except Exception as e: return str(e)

# 功能 B: 全局賽事總結 (New!)
def generate_match_summary(hands_data, vpip, pfr, api_key, model):
    if not api_key: return "⚠️ 請輸入 Key"
    
    # 為了節省 Token，我們只傳送「關鍵手牌」給 AI 進行總結
    # 篩選出 Hero 有玩的大底池或輸贏牌
    key_hands = [h['raw'] for h in hands_data if h['is_vpip']][:20] # 取前20手關鍵牌作為樣本
    key_hands_text = "\n\n".join(key_hands)
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    prompt = f"""
    你是一個職業撲克戰隊的總教練。這是學員剛剛打完的一場比賽數據與部分關鍵手牌。
    
    【學員數據】
    * 總手牌數: {len(hands_data)}
    * VPIP: {vpip:.1f}% (標準: 20-25%)
    * PFR: {pfr:.1f}% (標準: 17-22%)
    
    【關鍵手牌紀錄 (樣本)】
    {key_hands_text}
    
    請給我一份【賽事深度診斷報告】(繁體中文)：
    1. **風格畫像**：根據 VPIP/PFR，評價他的風格 (太鬆/太緊/剛好？)。
    2. **關鍵漏洞**：從手牌紀錄中，找出他的一個最大缺點 (例如：不該跟注時跟注、過於被動等)。
    3. **運氣成分**：這場輸掉是因為運氣 (Cooler) 還是打得爛？
    4. **總結建議**：一句話告訴他明天該練什麼。
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        resp = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        return resp.json()['candidates'][0]['content']['parts'][0]['text'] if resp.status_code == 200 else f"Error: {resp.text}"
    except Exception as e: return str(e)

# --- 5. 主介面 ---
uploaded_file = st.file_uploader("📂 上傳比賽紀錄 (.txt)", type=["txt"])

if uploaded_file:
    content = load_content(uploaded_file)
    if content:
        hands = parse_hands(content)
        if hands:
            # 統計數據
            total = len(hands)
            vpip_c = sum(1 for h in hands if h['is_vpip'])
            pfr_c = sum(1 for h in hands if h['is_pfr'])
            vpip = (vpip_c / total * 100) if total else 0
            pfr = (pfr_c / total * 100) if total else 0
            
            # --- Section 1: 戰情儀表板 ---
            st.markdown("### 📊 戰情儀表板")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("手牌數", total)
            c2.metric("VPIP", f"{vpip:.1f}%", "偏高" if vpip > 30 else "偏低" if vpip < 18 else "健康")
            c3.metric("PFR", f"{pfr:.1f}%", f"Gap {vpip-pfr:.1f}%")
            
            # 籌碼曲線數據
            chip_data = [h['chips'] for h in hands if h['chips'] > 0]
            start_chip = chip_data[0] if chip_data else 0
            end_chip = chip_data[-1] if chip_data else 0
            delta = end_chip - start_chip
            c4.metric("籌碼變化", f"{end_chip}", f"{delta:+}", delta_color="normal")
            
            # --- Section 2: 資金曲線 & 全局總結 ---
            g_col1, g_col2 = st.columns([2, 1])
            
            with g_col1:
                st.markdown("#### 📉 籌碼走勢圖 (Chip Graph)")
                if chip_data:
                    st.line_chart(chip_data, height=250)
                else:
                    st.info("無法從檔案中讀取籌碼數據，僅顯示手牌分析。")
            
            with g_col2:
                st.markdown("#### 🧠 AI 總教練報告")
                if st.button("📝 生成整場賽事總結", type="primary", use_container_width=True):
                    with st.spinner("教練正在閱讀整場比賽... (約需 10 秒)"):
                        summary = generate_match_summary(hands, vpip, pfr, api_key, selected_model)
                        st.markdown(f"<div class='big-summary'>{summary}</div>", unsafe_allow_html=True)
                else:
                    st.info("點擊按鈕，讓 AI 幫你復盤整場比賽的表現與風格。")

            st.divider()

            # --- Section 3: 手牌列表與詳細分析 ---
            col_list, col_analysis = st.columns([1, 2])
            
            with col_list:
                st.subheader("📜 手牌過濾器")
                
                # 應用篩選器
                filtered_hands = hands
                if filter_vpip: filtered_hands = [h for h in filtered_hands if h['is_vpip']]
                if filter_lost: filtered_hands = [h for h in filtered_hands if h['result'] == '❌']
                if filter_showdown: filtered_hands = [h for h in filtered_hands if h['is_showdown']]
                
                st.caption(f"顯示 {len(filtered_hands)} / {total} 手牌")
                
                # 列表
                options = [f"{h['result']} {cards_to_emoji(h['cards'])} (Chips: {h['chips']})" for h in filtered_hands]
                if not options:
                    st.warning("沒有符合篩選條件的手牌")
                    selected_hand = None
                else:
                    sel_idx = st.radio("選擇手牌", range(len(options)), format_func=lambda x: options[x], label_visibility="collapsed")
                    selected_hand = filtered_hands[sel_idx]
                
            with col_analysis:
                if selected_hand:
                    st.markdown(f"## {selected_hand['result']} 手牌 #{selected_hand['id']}")
                    st.markdown(f"<div class='poker-card'>{cards_to_emoji(selected_hand['cards'])}</div>", unsafe_allow_html=True)
                    st.caption(f"當下籌碼: {selected_hand['chips']}")
                    
                    st.markdown("---")
                    if st.button("🔥 分析這手牌", key="analyze_btn"):
                        with st.spinner("分析中..."):
                            res = analyze_hand_ai(selected_hand['raw'], api_key, selected_model)
                            st.markdown(res)
                    
                    with st.expander("原始紀錄"):
                        st.code(selected_hand['raw'])
    else:
        st.error("❌ 檔案無法讀取")
