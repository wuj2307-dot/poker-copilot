import streamlit as st
import re
import google.generativeai as genai

# --- 1. 頁面設定 ---
st.set_page_config(page_title="AI Poker Copilot (Gemini版)", page_icon="♠️", layout="wide")

st.title("♠️ AI Poker Copilot")
st.caption("Powered by Google Gemini | 你的專屬賽後復盤教練")

# --- 2. 側邊欄：設定與 API Key ---
with st.sidebar:
    st.header("⚙️ 啟動設定")
    
    # 讓用戶輸入 Gemini API Key
    api_key = st.text_input("輸入 Gemini API Key", type="password", help="我們不會儲存你的 Key")
    
    st.markdown("""
    ### 🚀 如何獲取免費 Key？
    1. 前往 [Google AI Studio](https://aistudio.google.com/app/apikey)
    2. 點擊 **Create API key**
    3. 複製並貼上
    """)
    
    st.divider()
    st.info("支援格式：\n- GGPoker (PokerCraft)\n- PokerStars (.txt)")

# --- 3. 核心功能：智慧解析器 ---
def parse_hands(content):
    # 切割手牌
    hands = content.split("Poker Hand #")
    parsed = []
    
    for h in hands:
        if not h.strip(): continue
        
        # 抓 ID
        hid_match = re.search(r"TM(\d+):", h) or re.search(r"#(\d+):", h)
        hid = hid_match.group(1) if hid_match else "Unknown"
        
        # 抓 Hero 手牌
        hero_match = re.search(r"Dealt to Hero \[(.*?)\]", h)
        cards = hero_match.group(1) if hero_match else "N/A"
        
        # 簡單判斷結果
        res = "😐 平局/存活"
        if "Hero showed" in h and "lost" in h: res = "❌ 輸掉底池"
        elif "Hero collected" in h or "Hero won" in h: res = "💰 贏得底池"
        elif "Hero folded" in h: res = "🛡️ 棄牌"
        
        # 儲存
        parsed.append({
            "id": hid, 
            "cards": cards, 
            "result": res, 
            "raw": "Poker Hand #" + h
        })
        
    return parsed

# --- 4. AI 分析模組 (Gemini) ---
def analyze_with_gemini(hand_text, api_key):
    if not api_key:
        return "⚠️ 請先在左側輸入 API Key"
    
    try:
        # 設定 Google Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        你是一個世界級的德州撲克教練。請針對以下這手牌進行深度復盤。
        重點指出 Hero (主角) 是否有犯錯？GTO 的角度會怎麼打？
        
        請用繁體中文回答，語氣要像真人教練一樣直接、犀利，不要講廢話。
        如果 Hero 打得好，請給予肯定；打得爛，請用力批評。
        
        手牌紀錄：
        {hand_text}
        """
        
        with st.spinner("🧠 Gemini 教練正在思考中..."):
            response = model.generate_content(prompt)
            return response.text
            
    except Exception as e:
        return f"❌ 分析失敗: {str(e)}"

# --- 5. 主介面邏輯 ---
uploaded_file = st.file_uploader("📂 請上傳手牌紀錄 (.txt)", type=["txt"])

if uploaded_file is not None:
    # 讀取檔案 (嘗試自動修正編碼)
    try:
        content = uploaded_file.getvalue().decode("utf-8")
    except:
        content = uploaded_file.getvalue().decode("latin-1")
        
    hands_data = parse_hands(content)
    
    if len(hands_data) == 0:
        st.error("⚠️ 讀取失敗：找不到手牌紀錄，請確認檔案格式。")
    else:
        st.success(f"✅ 成功讀取！本場比賽共 {len(hands_data)} 手牌。")
        
        st.divider()
        
        # 選擇手牌區域
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("📋 手牌列表")
            # 製作選單文字
            options = [f"#{h['id']} | {h['cards']} | {h['result']}" for h in hands_data]
            selected_option = st.radio("選擇要復盤的手牌：", options, index=0)
            
            # 找到對應的資料
            idx = options.index(selected_option)
            selected_hand = hands_data[idx]
        
        with col2:
            st.subheader("🤖 AI 教練診斷室")
            
            # 分析按鈕
            if st.button("🔥 呼叫 Gemini 分析這手牌", type="primary"):
                analysis = analyze_with_gemini(selected_hand['raw'], api_key)
                st.markdown(analysis)
            else:
                st.info("👈 點擊左側列表選擇手牌，然後按上方按鈕開始分析。")
            
            with st.expander("查看原始紀錄代碼 (Raw Data)"):
                st.code(selected_hand['raw'], language='text')
