import streamlit as st
import re
import requests
import json

# --- 1. 頁面設定 ---
st.set_page_config(page_title="AI Poker Copilot", page_icon="♠️", layout="wide")
st.title("♠️ AI Poker Copilot")
st.caption("Version 5.0 | 特種部隊版 (Direct API)")

# --- 2. 側邊欄 ---
with st.sidebar:
    st.header("⚙️ 設定")
    api_key = st.text_input("輸入 Gemini API Key", type="password")
    
    # 這裡我們直接對接 Google 的網址，不透過中間人
    model_option = st.selectbox(
        "選擇模型", 
        ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"],
        index=0
    )
    
    st.markdown("[👉 點此獲取免費 Key](https://aistudio.google.com/app/apikey)")
    st.divider()
    st.info(f"當前連線模型：{model_option}")

# --- 3. 核心功能：讀檔器 ---
def load_content(uploaded_file):
    bytes_data = uploaded_file.getvalue()
    # 窮舉解碼法
    encodings = ["utf-8", "utf-16-le", "utf-16", "utf-8-sig", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            decoded = bytes_data.decode(enc)
            # 只要解出來像英文或撲克紀錄就回傳
            if "Hand" in decoded or "Tournament" in decoded or "Poker" in decoded or "Dealt" in decoded:
                return decoded
        except UnicodeDecodeError:
            continue
    return None

def parse_hands(content):
    if not content: return []
    # 寬容切割
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

# --- 4. AI 分析模組 (直接呼叫 REST API) ---
def analyze_with_direct_api(hand_text, api_key, model_name):
    if not api_key: return "⚠️ 請先輸入 API Key"
    
    # 這是 Google Gemini 的官方 API 網址
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    # 設定給 AI 的提示詞
    prompt_text = f"""
    你是一個德州撲克教練。請繁體中文分析這手牌，指出 Hero 錯誤：
    \n{hand_text}
    """
    
    # 建構請求封包 (JSON)
    payload = {
        "contents": [{
            "parts": [{"text": prompt_text}]
        }]
    }
    
    headers = {'Content-Type': 'application/json'}
    
    try:
        # 直接發射！不經過任何 Python 套件
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        # 檢查結果
        if response.status_code == 200:
            result = response.json()
            # 解析 Google 回傳的複雜 JSON
            try:
                return result['candidates'][0]['content']['parts'][0]['text']
            except (KeyError, IndexError):
                return f"⚠️ AI 回傳了無法理解的格式: {result}"
        else:
            return f"❌ API 請求失敗 (Code {response.status_code}): {response.text}"
            
    except Exception as e:
        return f"❌ 連線錯誤: {str(e)}"

# --- 5. 主介面 ---
uploaded_file = st.file_uploader("📂 請上傳手牌紀錄 (.txt)", type=["txt"])

if uploaded_file is not None:
    content = load_content(uploaded_file)
    if content:
        hands_data = parse_hands(content)
        if hands_data:
            st.success(f"✅ 讀取成功！共 {len(hands_data)} 手牌。")
            col1, col2 = st.columns([1, 2])
            with col1:
                options = [f"#{h['id']} | {h['cards']} | {h['result']}" for h in hands_data]
                if options:
                    sel = st.radio("手牌列表", options)
                    sel_hand = hands_data[options.index(sel)]
            with col2:
                if options and st.button("🔥 AI 分析"):
                    with st.spinner(f"正在連線 Google {model_option}..."):
                        # 改用新的 direct api 函數
                        st.markdown(analyze_with_direct_api(sel_hand['raw'], api_key, model_option))
                if options:
                    with st.expander("原始紀錄"):
                        st.code(sel_hand['raw'])
    else:
        st.error("❌ 檔案讀取失敗，編碼無法
