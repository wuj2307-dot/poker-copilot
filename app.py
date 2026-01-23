import streamlit as st
import re
import requests
import json
import pandas as pd # 引入 Pandas 做數據統計

# --- 1. 頁面設定 (Dark Mode & Wide Layout) ---
st.set_page_config(page_title="Poker Copilot Pro", page_icon="♠️", layout="wide")

# 自定義 CSS 讓介面更像 App
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #fafafa; }
    .card-text { font-size: 1.2rem; font-weight: bold; font-family: monospace; }
    .stat-box { border: 1px solid #333; padding: 10px; border-radius: 5px; text-align: center; }
    .highlight-red { color: #ff4b4b; font-weight: bold; }
    .highlight-green { color: #00cc00; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("♠️ Poker Copilot Pro")
st.caption("Version 9.0 | 儀表板進化版 (秒開統計 + 視覺化)")

# --- 2. 側邊欄 ---
with st.sidebar:
    st.header("⚙️ 控制台")
    api_key = st.text_input("Gemini API Key", type="password")
    
    # 自動抓取模型
    selected_model = "gemini-1.5-flash" 
    if api_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                available_models = []
                for m in data.get('models', []):
                    name = m['name'].replace('models/', '')
                    if 'generateContent' in m.get('supportedGenerationMethods', []):
                        available_models.append(name)
                # 優先找 flash
                available_models.sort(key=lambda x: 'flash' not in x)
                if available_models:
                    selected_model = st.selectbox("AI 模型", available_models, index=0)
        except:
            pass
            
    st.divider()
    st.info("💡 提示：上傳後會自動計算 VPIP 等數據，點擊單手牌可進行 AI 深度復盤。")

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
    
    # 抓 VPIP 關鍵字 (是否有主動下注/跟注)
    is_vpip = False
    if "Hero: raises" in h or "Hero: calls" in h or "Hero: bets" in h:
        is_vpip = True
    
    # 抓 PFR 關鍵字 (是否有加注)
    is_pfr = False
    if "Hero: raises" in h or "Hero: bets" in h: # 簡化邏輯
        is_pfr = True
        
    # 抓輸贏
    res = "😐"
    if "Hero showed" in h and "lost" in h: res = "❌ 輸"
    elif "Hero collected" in h or "Hero won" in h: res = "💰 贏"
    elif "Hero folded" in h: res = "🛡️ 棄"
    
    if cards: # 只保留有玩的手牌
        parsed_list.append({
            "id": hid, "cards": cards, "result": res, 
            "is_vpip": is_vpip, "is_pfr": is_pfr, "raw": h
        })

# 🂡 視覺化小工具：把文字牌轉 Emoji
def cards_to_emoji(card_str):
    if not card_str: return ""
    suits = {'s': '♠️', 'h': '♥️', 'd': '♦️', 'c': '♣️'}
    # 簡單轉換，例如 As -> A♠️
    formatted = []
    for card in card_str.split():
        if len(card) == 2:
            rank = card[0]
            suit = card[1]
            color = "red" if suit in ['h', 'd'] else "black" # Streamlit markdown 支援有限，先用 Emoji
            formatted.append(f"{rank}{suits.get(suit, suit)}")
        else:
            formatted.append(card)
    return " ".join(formatted)

# --- 4. AI 分析 ---
def analyze_hand_ai(hand_text, api_key, model):
    if not api_key: return "⚠️ 請輸入 API Key"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    prompt = f"""
    你是一個德州撲克教練。請用繁體中文分析這手牌。
    
    【格式要求】
    1. 🎯 **核心評價**：一句話講評 (例如：標準的 Cooler / 這裡打太鬆了)。
    2. 🧠 **決策分析**：指出 Hero 在 翻牌前/翻牌後 的關鍵決策是否正確。
    3. 💡 **改進建議**：如果不對，該怎麼打？
    
    手牌紀錄：
    {hand_text}
    """
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        resp = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        if resp.status_code == 200:
            return resp.json()['candidates'][0]['content']['parts'][0]['text']
        return f"Error: {resp.text}"
    except Exception as e: return str(e)

# --- 5. 主介面邏輯 ---
uploaded_file = st.file_uploader("📂 上傳比賽紀錄 (.txt)", type=["txt"])

if uploaded_file:
    content = load_content(uploaded_file)
    if content:
        hands = parse_hands(content)
        if hands:
            # 📊 Step 1: 瞬間顯示全局統計 (Dashboard)
            df = pd.DataFrame(hands)
            total_hands = len(df)
            vpip = df['is_vpip'].sum() / total_hands * 100
            pfr = df['is_pfr'].sum() / total_hands * 100
            
            st.markdown("### 📊 比賽數據總覽")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("總手牌數", total_hands)
            c1.metric("入池率 (VPIP)", f"{vpip:.1f}%", delta="標準 20-25%" if 20<=vpip<=25 else "偏離")
            c2.metric("加注率 (PFR)", f"{pfr:.1f}%")
            c3.metric("激進指數", "計算中...") # 預留
            
            st.divider()
            
            # 🖐️ Step 2: 左右分欄介面
            col_list, col_analysis = st.columns([1, 2])
            
            with col_list:
                st.subheader("📜 手牌歷程")
                # 製作漂亮的選單字串
                options = [f"{h['result']} {cards_to_emoji(h['cards'])} (#{h['id'][-4:]})" for h in hands]
                selected_idx = st.radio("選擇手牌", range(len(hands)), format_func=lambda x: options[x])
                
            with col_analysis:
                hand = hands[selected_idx]
                st.subheader(f"🕵️ 手牌分析 {cards_to_emoji(hand['cards'])}")
                
                # 顯示牌局預覽
                with st.expander("查看原始紀錄", expanded=False):
                    st.code(hand['raw'])
                
                # AI 分析按鈕 (按需呼叫，解決速度問題)
                if st.button("🔥 AI 教練，幫我復盤這手牌！", type="primary"):
                    with st.spinner("AI 正在思考中..."):
                        analysis = analyze_hand_ai(hand['raw'], api_key, selected_model)
                        st.markdown(analysis)
                else:
                    st.info("👈 點擊左側列表選擇一手牌，然後按上方按鈕開始分析。")

    else:
        st.error("無法讀取檔案")
