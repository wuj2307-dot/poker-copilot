import streamlit as st
import re
import requests
import json
import pandas as pd

# --- 1. 頁面設定 (開啟寬螢幕模式) ---
st.set_page_config(page_title="Poker Copilot Pro", page_icon="♠️", layout="wide")

# 自定義 CSS：讓介面更有質感，卡片化設計
st.markdown("""
<style>
    /* 調整一下字體與間距 */
    .block-container { padding-top: 2rem; }
    
    /* 數據卡片的樣式 */
    div[data-testid="stMetric"] {
        background-color: #262730;
        border: 1px solid #464b5c;
        padding: 15px;
        border-radius: 10px;
        color: white;
    }
    
    /* 讓 Emoji 牌大一點 */
    .poker-card { font-size: 1.5rem; }
</style>
""", unsafe_allow_html=True)

st.title("♠️ Poker Copilot Pro")
st.caption("Version 9.0 | 儀表板進化版 (秒開統計 + 視覺化)")

# --- 2. 側邊欄：設定與模型 ---
with st.sidebar:
    st.header("⚙️ 控制台")
    api_key = st.text_input("Gemini API Key", type="password")
    
    # 自動偵測模型 (沿用之前的邏輯)
    selected_model = "gemini-1.5-flash"
    if api_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                models = [m['name'].replace('models/', '') for m in data.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
                # 簡單排序：Flash 優先
                models.sort(key=lambda x: 'flash' not in x)
                if models:
                    selected_model = st.selectbox("AI 引擎", models, index=0)
                    st.success("✅ 引擎就緒")
        except: pass
            
    st.divider()
    st.markdown("### 📝 使用說明")
    st.info("1. 上傳紀錄檔\n2. 系統自動計算 VPIP\n3. 點擊單手牌進行 AI 復盤")

# --- 3. 核心功能：讀檔與解析 ---
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
    # 切割手牌
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
    hid = hid.group(1) if hid else "Unknown"
    
    # 抓 Hero 牌
    hero_cards = re.search(r"Dealt to Hero \[(.*?)\]", h)
    cards = hero_cards.group(1) if hero_cards else None
    
    # 簡單計算 VPIP/PFR (基本關鍵字偵測)
    is_vpip = False
    if "Hero: raises" in h or "Hero: calls" in h or "Hero: bets" in h:
        is_vpip = True
    
    is_pfr = False
    if "Hero: raises" in h or "Hero: bets" in h:
        is_pfr = True
        
    # 抓輸贏結果
    res = "😐"
    if "Hero showed" in h and "lost" in h: res = "❌"
    elif "Hero collected" in h or "Hero won" in h: res = "💰"
    elif "Hero folded" in h: res = "🛡️"
    
    if cards: # 只保留 Hero 有拿到底牌的手牌
        parsed_list.append({
            "id": hid, "cards": cards, "result": res, 
            "is_vpip": is_vpip, "is_pfr": is_pfr, "raw": h
        })

# 🂡 視覺化魔法：把文字變成 Emoji 牌
def cards_to_emoji(card_str):
    if not card_str: return ""
    # 定義撲克符號
    suits_map = {'s': '♠️', 'h': '♥️', 'd': '♦️', 'c': '♣️'}
    formatted = []
    
    # 處理像 "Ah Ks" 這樣的字串
    for card in card_str.split():
        if len(card) >= 2:
            rank = card[:-1] # 處理 10, J, Q, K, A
            suit = card[-1]  # 處理 s, h, d, c
            # 組合
            display = f"{rank}{suits_map.get(suit, suit)}"
            formatted.append(display)
            
    return " ".join(formatted)

# --- 4. AI 分析函數 (單點觸發) ---
def analyze_hand_ai(hand_text, api_key, model):
    if not api_key: return "⚠️ 請先在側邊欄輸入 API Key"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    prompt = f"""
    你是一個德州撲克教練。請用繁體中文分析這手牌。
    風格：直接、犀利、數據導向。
    
    【輸出格式】
    ### 🎯 核心評價
    (一句話總結，例如：標準跑馬 / 這裡太鬆了 / 打得很好)
    
    ### 🧠 關鍵決策點
    * **翻牌前 (Pre-flop):** ...
    * **翻牌後 (Post-flop):** ...
    
    ### 💡 教練建議
    (如果有錯，下次該怎麼打？)
    
    手牌紀錄：
    {hand_text}
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {'Content-Type': 'application/json'}
    
    try:
        resp = requests.post(url, headers=headers, data=json.dumps(payload))
        if resp.status_code == 200:
            return resp.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"❌ 請求失敗: {resp.text}"
    except Exception as e: return f"連線錯誤: {str(e)}"

# --- 5. 主介面邏輯 ---
uploaded_file = st.file_uploader("📂 請上傳手牌紀錄 (.txt)", type=["txt"])

if uploaded_file:
    content = load_content(uploaded_file)
    if content:
        hands = parse_hands(content)
        if hands:
            # 轉換成 Pandas DataFrame 方便算數據
            df = pd.DataFrame(hands)
            total_hands = len(df)
            
            # 計算數據
            vpip_count = df['is_vpip'].sum()
            pfr_count = df['is_pfr'].sum()
            
            vpip = (vpip_count / total_hands) * 100
            pfr = (pfr_count / total_hands) * 100
            
            # --- 儀表板區域 ---
            st.markdown("### 📊 賽局數據儀表板")
            c1, c2, c3, c4 = st.columns(4)
            
            c1.metric("總手牌", total_hands)
            
            # 用顏色標示是否健康 (VPIP 20-30 為健康)
            vpip_delta = "健康" if 20 <= vpip <= 30 else "偏離"
            vpip_color = "normal" if 20 <= vpip <= 30 else "inverse"
            c2.metric("入池率 (VPIP)", f"{vpip:.1f}%", delta=vpip_delta, delta_color=vpip_color)
            
            c3.metric("加注率 (PFR)", f"{pfr:.1f}%", f"Gap: {vpip-pfr:.1f}%")
            
            # 簡單勝率 (如果有贏到底池的)
            win_count = len(df[df['result'] == '💰'])
            c4.metric("獲勝手牌數", win_count)
            
            st.divider()
            
            # --- 左右分欄操作區 ---
            col_list, col_analysis = st.columns([1, 2])
            
            with col_list:
                st.subheader("📜 手牌歷程")
                # 製作選單： 💰 A♠️ K♥️ (#1234)
                # 使用 DataFrame 的 apply 快速處理
                display_options = df.apply(
                    lambda x: f"{x['result']} {cards_to_emoji(x['cards'])} (#{str(x['id'])[-4:]})", 
                    axis=1
                ).tolist()
                
                # 選單
                selected_idx = st.radio(
                    "點擊檢視詳細復盤：", 
                    range(len(hands)), 
                    format_func=lambda x: display_options[x],
                    label_visibility="collapsed"
                )
                
            with col_analysis:
                hand = hands[selected_idx]
                
                # 標題區：顯示大大的牌
                st.markdown(f"## {hand['result']} 手牌 #{hand['id']}")
                st.markdown(f"<div class='poker-card'>{cards_to_emoji(hand['cards'])}</div>", unsafe_allow_html=True)
                
                # AI 分析區
                st.markdown("---")
                
                # 這裡設計成：先顯示按鈕，點了才跑 AI，避免卡頓
                if st.button("🔥 呼叫 AI 教練分析這手牌", type="primary", use_container_width=True):
                    with st.spinner("AI 教練正在看牌..."):
                        analysis = analyze_hand_ai(hand['raw'], api_key, selected_model)
                        st.markdown(analysis)
                
                with st.expander("查看原始文字紀錄 (Raw Data)"):
                    st.code(hand['raw'])

    else:
        st.error("❌ 檔案無法讀取，請確認格式。")
