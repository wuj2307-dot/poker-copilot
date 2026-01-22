import streamlit as st
import re
import requests
import json

# --- 1. 頁面設定 ---
st.set_page_config(page_title="AI Poker Copilot", page_icon="♠️", layout="wide")
st.title("♠️ AI Poker Copilot")
st.caption("Version 8.0 | 解鎖審查版 (Safety Settings OFF)")

# --- 2. 側邊欄 ---
with st.sidebar:
    st.header("⚙️ 設定")
    api_key = st.text_input("輸入 Gemini API Key", type="password")
    
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
                    if 'generateContent' in m.get('supportedGenerationMethods', []):
                        name = m['name'].replace('models/', '')
                        available_models.append(name)
                available_models.sort(reverse=True)
                if available_models:
                    st.success(f"✅ 連線成功！({len(available_models)} Models)")
                    # 預設選一個比較新的 Flash
                    default_idx = 0
                    for i, m in enumerate(available_models):
                        if "flash" in m and "002" in m: default_idx = i
                    selected_model = st.selectbox("選擇模型", available_models, index=default_idx)
        except:
            pass
            
    st.markdown("[👉 獲取 Key](https://aistudio.google.com/app/apikey)")
    st.divider()

# --- 3. 讀檔功能 ---
def load_content(uploaded_file):
    bytes_data = uploaded_file.getvalue()
    encodings = ["utf-8", "utf-16-le", "utf-16", "utf-8-sig", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            decoded = bytes_data.decode(enc)
            if "Hand" in decoded or "Tournament" in decoded or "Poker" in decoded or "Dealt" in decoded:
                return decoded
        except UnicodeDecodeError:
            continue
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

# --- 4. AI 分析 (關閉安全審查) ---
def analyze_with_direct_api(hand_text, api_key, model_name):
    if not api_key: return "⚠️ 請先輸入 API Key"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    prompt_text = f"""
    You are a professional poker coach. Analyze this hand history.
    Point out Hero's mistakes. Answer in Traditional Chinese.
    \n{hand_text}
    """
    
    # 🔥 關鍵：加上 safetySettings 告訴 Google 不要擋我
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        if response.status_code == 200:
            result = response.json()
            # 嘗試抓取內容
            try:
                return result['candidates'][0]['content']['parts'][0]['text']
            except KeyError:
                # 如果內容是空的，很有可能是被擋掉了，或是 Google 回傳了 Finish Reason
                finish_reason = result.get('candidates', [{}])[0].get('finishReason', 'Unknown')
                return f"⚠️ AI 拒絕回答 (原因: {finish_reason}) \n\n完整回傳 debug: {result}"
        else:
            return f"❌ 請求失敗 ({response.status_code}): {response.text}"
            
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
                    with st.spinner(f"正在連線 {selected_model}..."):
                        st.markdown(analyze_with_direct_api(sel_hand['raw'], api_key, selected_model))
                if options:
                    with st.expander("原始紀錄"):
                        st.code(sel_hand['raw'])
    else:
        st.error("❌ 檔案讀取失敗")
