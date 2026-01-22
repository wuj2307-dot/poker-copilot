import streamlit as st
import re
import google.generativeai as genai

# --- 1. 頁面設定 ---
st.set_page_config(page_title="AI Poker Copilot", page_icon="♠️", layout="wide")
st.title("♠️ AI Poker Copilot")
st.caption("Version 2.0 | 強力解碼版")

# --- 2. 側邊欄 ---
with st.sidebar:
    st.header("⚙️ 設定")
    api_key = st.text_input("輸入 Gemini API Key", type="password")
    st.markdown("[👉 點此獲取免費 Key](https://aistudio.google.com/app/apikey)")
    st.divider()
    st.info("支援：GGPoker / PokerStars")

# --- 3. 核心功能：超級讀檔器 ---
def load_content(uploaded_file):
    # 嘗試多種編碼格式，直到讀懂為止
    bytes_data = uploaded_file.getvalue()
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "utf-16"]
    
    for enc in encodings:
        try:
            return bytes_data.decode(enc)
        except UnicodeDecodeError:
            continue
    return None

def parse_hands(content):
    if not content: return []
    
    # 針對 GG 可能的格式差異做正規化
    # 有些檔案是用 "Poker Hand #" 有些前面會有空白
    hands = re.split(r"Poker Hand #", content)
    
    parsed = []
    for h in hands:
        if not h.strip(): continue
        
        # 排除太短的雜訊
        if len(h) < 50: continue

        # 抓 ID
        hid_match = re.search(r"TM(\d+):", h) or re.search(r"#(\d+):", h)
        hid = hid_match.group(1) if hid_match else "Unknown"
        
        # 抓 Hero 牌
        hero_match = re.search(r"Dealt to Hero \[(.*?)\]", h)
        cards = hero_match.group(1) if hero_match else "N/A"
        
        # 抓結果
        res = "😐 平局/存活"
        if "Hero showed" in h and "lost" in h: res = "❌ 輸掉底池"
        elif "Hero collected" in h or "Hero won" in h: res = "💰 贏得底池"
        elif "Hero folded" in h: res = "🛡️ 棄牌"
        
        parsed.append({
            "id": hid, 
            "cards": cards, 
            "result": res, 
            "raw": "Poker Hand #" + h
        })
    return parsed

# --- 4. AI 分析模組 ---
def analyze_with_gemini(hand_text, api_key):
    if not api_key: return "⚠️ 請先輸入 API Key"
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"你是德州撲克教練。請繁體中文分析這手牌，指出 Hero 錯誤：\n{hand_text}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ 分析失敗: {str(e)}"

# --- 5. 主介面 ---
uploaded_file = st.file_uploader("📂 請上傳手牌紀錄 (.txt)", type=["txt"])

if uploaded_file is not None:
    content = load_content(uploaded_file)
    
    if content is None:
        st.error("❌ 檔案編碼無法識別，請嘗試將檔案另存為 UTF-8 格式。")
    else:
        hands_data = parse_hands(content)
        
        if len(hands_data) == 0:
            st.error("⚠️ 讀取失敗：檔案內找不到 'Poker Hand #' 關鍵字。")
            with st.expander("🐞 點此查看檔案前 500 字內容 (Debug)"):
                st.text(content[:500])
        else:
            st.success(f"✅ 成功讀取 {len(hands_data)} 手牌！")
            
            # 選單與分析
            col1, col2 = st.columns([1, 2])
            with col1:
                options = [f"#{h['id']} | {h['cards']} | {h['result']}" for h in hands_data]
                sel = st.radio("手牌列表", options)
                sel_hand = hands_data[options.index(sel)]
            
            with col2:
                if st.button("🔥 AI 分析"):
                    st.markdown(analyze_with_gemini(sel_hand['raw'], api_key))
                with st.expander("原始紀錄"):
                    st.code(sel_hand['raw'])
