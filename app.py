import streamlit as st
import re
import requests
import json

# --- 1. 頁面設定 ---
st.set_page_config(page_title="AI Poker Copilot", page_icon="♠️", layout="wide")
st.title("♠️ AI Poker Copilot")
st.caption("Version 7.0 | 自我診斷版 (Auto-Detect Models)")

# --- 2. 側邊欄 ---
with st.sidebar:
    st.header("⚙️ 設定")
    api_key = st.text_input("輸入 Gemini API Key", type="password")
    
    # 🔥 V7.0 核心升級：自動抓取可用模型
    selected_model = "gemini-1.5-flash" # 預設值
    
    if api_key:
        try:
            # 問 Google: 這把鑰匙能用什麼模型？
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                # 過濾出支援 "generateContent" (生成文字) 的模型
                available_models = []
                for m in data.get('models', []):
                    if 'generateContent' in m.get('supportedGenerationMethods', []):
                        # 只留名字，去掉 models/ 前綴
                        name = m['name'].replace('models/', '')
                        available_models.append(name)
                
                # 排序一下，把 flash 放前面
                available_models.sort(reverse=True)
                
                if available_models:
                    st.success(f"✅ 成功連線！找到 {len(available_models)} 個可用模型")
                    selected_model = st.selectbox("請選擇模型 (建議選 1.5-flash)", available_models, index=0)
                else:
                    st.warning("⚠️ 連線成功但沒找到支援的模型")
            else:
                st.error(f"❌ 無法獲取模型清單 (Code {response.status_code})")
        except Exception as e:
            st.error(f"連線錯誤: {e}")
    
    st.markdown("[👉 點此獲取免費 Key](https://aistudio.google.com/app/apikey)")
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

# --- 4. AI 分析 (使用動態選擇的模型) ---
def analyze_with_direct_api(hand_text, api_key, model_name):
    if not api_key: return "⚠️ 請先輸入 API Key"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    prompt_text = f"""
    你是一個德州撲克教練。請繁體中文分析這手牌，指出 Hero 錯誤：
    \n{hand_text}
    """
    
    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            result = response.json()
            try:
                return result['candidates'][0]['content']['parts'][0]['text']
            except:
                return f"⚠️ AI 回傳格式異常: {result}"
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
                    with st.spinner(f"正在連線 {selected_model}..."):
                        st.markdown(analyze_with_direct_api(sel_hand['raw'], api_key, selected_model))
                if options:
                    with st.expander("原始紀錄"):
                        st.code(sel_hand['raw'])
    else:
        st.error("❌ 檔案讀取失敗，編碼無法識別。")
