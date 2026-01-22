import streamlit as st
import re
import google.generativeai as genai

# --- 1. 頁面設定 ---
st.set_page_config(page_title="AI Poker Copilot", page_icon="♠️", layout="wide")
st.title("♠️ AI Poker Copilot")
st.caption("Version 4.0 | 模型切換版")

# --- 2. 側邊欄 ---
with st.sidebar:
    st.header("⚙️ 設定")
    api_key = st.text_input("輸入 Gemini API Key", type="password")
    
    # 🔥 新增功能：讓你自己選手機型號！
    # 如果 Flash 報錯，就選 Pro，Pro 是最穩定的老大哥
    model_name = st.selectbox(
        "選擇 AI 模型", 
        ["gemini-1.5-flash", "gemini-1.5-pro-latest", "gemini-pro"],
        index=0,
        help="如果 Flash 報錯，請切換到 gemini-pro 試試看"
    )
    
    st.markdown("[👉 點此獲取免費 Key](https://aistudio.google.com/app/apikey)")
    st.divider()
    st.info(f"目前使用模型：{model_name}")

# --- 3. 核心功能：讀檔器 ---
def load_content(uploaded_file):
    bytes_data = uploaded_file.getvalue()
    encodings = ["utf-8", "utf-16-le", "utf-16", "utf-8-sig", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            decoded = bytes_data.decode(enc)
            if "Hand" in decoded or "Tournament" in decoded or "Poker" in decoded:
                return decoded
        except UnicodeDecodeError:
            continue
    return None

def parse_hands(content):
    if not content: return []
    # 寬容模式切割
    raw_hands = re.split(r"(Poker Hand #|Hand #)", content)
    parsed = []
    current_hand = ""
    for part in raw_hands:
        if "Hand #" in part:
            if current_hand: process_single_hand(current_hand, parsed)
            current_hand = part
        else:
            current_hand += part
    if current_hand: process_single_hand(current_hand, parsed)
    return parsed

def process_single_hand(h, parsed_list):
    if len(h) < 50: return
    hid_match = re.search(r"TM(\d+):", h) or re.search(r"#(\d+):", h)
    hid = hid_match.group(1) if hid_match else "Unknown"
    hero_match = re.search(r"Dealt to Hero \[(.*?)\]", h)
    cards = hero_match.group(1) if hero_match else "N/A"
    res = "😐 平局/存活"
    if "Hero showed" in h and "lost" in h: res = "❌ 輸掉底池"
    elif "Hero collected" in h or "Hero won" in h: res = "💰 贏得底池"
    elif "Hero folded" in h: res = "🛡️ 棄牌"
    parsed_list.append({"id": hid, "cards": cards, "result": res, "raw": h})

# --- 4. AI 分析模組 ---
def analyze_with_gemini(hand_text, api_key, model_name):
    if not api_key: return "⚠️ 請先輸入 API Key"
    try:
        genai.configure(api_key=api_key)
        # 這裡會使用你在側邊欄選的模型
        model = genai.GenerativeModel(model_name)
        
        prompt = f"""
        你是一個德州撲克教練。請繁體中文分析這手牌，指出 Hero 錯誤：
        (請注意：如果是 gemini-pro 模型，可能會比較簡短)
        \n{hand_text}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ 分析失敗 ({model_name}): {str(e)}"

# --- 5. 主介面 ---
uploaded_file = st.file_uploader("📂 請上傳手牌紀錄 (.txt)", type=["txt"])

if uploaded_file is not None:
    content = load_content(uploaded_file)
    if content:
        hands_data = parse_hands(content)
        if hands_data:
            st.success(f"✅ 成功讀取 {len(hands_data)} 手牌！")
            col1, col2 = st.columns([1, 2])
            with col1:
                options = [f"#{h['id']} | {h['cards']} | {h['result']}" for h in hands_data]
                if options:
                    sel = st.radio("手牌列表", options)
                    sel_hand = hands_data[options.index(sel)]
            with col2:
                # 把模型名稱傳進去
                if options and st.button("🔥 AI 分析"):
                    with st.spinner(f"正在使用 {model_name} 分析中..."):
                        st.markdown(analyze_with_gemini(sel_hand['raw'], api_key, model_name))
                if options:
                    with st.expander("原始紀錄"):
                        st.code(sel_hand['raw'])
    else:
        st.error("檔案讀取失敗")
