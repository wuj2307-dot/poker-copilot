import streamlit as st
import re
import requests
import json
import pandas as pd
import random
from datetime import datetime

# --- 1. 頁面設定 ---
st.set_page_config(page_title="Poker Copilot War Room", page_icon="♠️", layout="wide")

# CSS 優化
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #0e1117; border-radius: 4px 4px 0px 0px; gap: 1px; padding-top: 10px; padding-bottom: 10px; }
    div[data-testid="stMetricValue"] { font-size: 24px; }
</style>
""", unsafe_allow_html=True)

st.title("Poker Copilot: Beta 🚀")
st.caption("內部測試版 | 請輸入通關密碼")

# --- 2. 側邊欄：驗證與設定 ---
with st.sidebar:
    st.header("🔐 身份驗證")
    
    # 這裡不再要 API Key，而是要簡單的密碼
    user_password = st.text_input("輸入通關密碼 (Access Code)", type="password")
    
    api_key = None
    
    # 檢查密碼是否正確 (從 Streamlit Secrets 讀取)
    if user_password == st.secrets["ACCESS_PASSWORD"]:
        st.success("✅ 驗證通過！")
        # 驗證通過後，自動從後台拿出真正的 API Key
        api_key = st.secrets["GEMINI_API_KEY"]
    elif user_password:
        st.error("❌ 密碼錯誤")

    st.divider()

    if api_key:
        st.header("⚙️ 設定")
        # 只保留唯一能通的 "gemini-2.5-flash"
        selected_model = st.selectbox("AI 引擎", ["gemini-2.5-flash"])
        
        st.header("🔍 篩選")
        hero_position = st.selectbox("Hero 位置", ["All", "SB", "BB", "UTG", "MP", "CO", "BTN"])

# --- 3. 核心功能函數 ---

def load_content(uploaded_file):
    if uploaded_file is not None:
        stringio = uploaded_file.getvalue().decode("utf-8")
        return stringio
    return None

def parse_hands(content):
    # [通用格式] 支援 PokerStars 和 GGPoker
    # 只要看到行首有 "Hand #" 或 "Poker Hand #" 就視為新的一手牌開始
    # 使用 MULTILINE 模式，^ 會匹配每一行的開頭
    parts = re.split(r'(^(?:Poker )?Hand #[^\n]+)', content, flags=re.MULTILINE)
    parsed_hands = []
    
    # re.split 切出來會是 [前導內容, 標題1, 內容1, 標題2, 內容2...]
    # 從索引 1 開始，每次跳 2 格抓取一組 (標題 + 內容)
    for i in range(1, len(parts), 2):
        header = parts[i]
        body = parts[i+1] if i+1 < len(parts) else ""
        
        full_hand_text = header + body
        
        # 跳過空白或過短的手牌
        if not full_hand_text.strip() or len(full_hand_text) < 50:
            continue
            
        # 提取手牌編號 (支援多種格式)
        # GGPoker: "Poker Hand #TM123456:" 或 "Hand #TM123456:"
        # PokerStars: "Hand #123456:"
        hand_id_match = re.search(r'Hand #([A-Z]*\d+)', header)
        hand_id = hand_id_match.group(1) if hand_id_match else f"Unknown-{i}"
        
        # 模擬數據 (之後這裡會接真實分析)
        is_vpip = random.choice([True, False])
        is_pfr = random.choice([True, False]) if is_vpip else False
        bb_count = random.randint(10, 100)
        
        parsed_hands.append({
            "id": hand_id,
            "content": full_hand_text,
            "vpip": is_vpip,
            "pfr": is_pfr,
            "bb": bb_count
        })
        
    return parsed_hands

def generate_match_summary(hands_data, vpip, pfr, api_key, model):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    prompt = f"""
    你是一個職業撲克教練。請分析這場比賽的數據：
    - 總手牌數: {len(hands_data)}
    - VPIP: {vpip}%
    - PFR: {pfr}%
    
    請給出 3 個簡短的改進建議，並指出這名玩家的風格傾向。
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        resp = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        return resp.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"AI 分析失敗: {str(e)}"

# --- 4. 主介面邏輯 ---

if not api_key:
    st.info("👈 請先在左側輸入通關密碼 (Access Code) 才能使用。")
else:
    # [優化 1] 乾淨的上傳區，還沒上傳前不顯示錯誤
    uploaded_file = st.file_uploader("📂 上傳比賽紀錄 (.txt)", type=["txt"])
    
    if uploaded_file is None:
        # 保持頁面乾淨，什麼都不做
        pass
        
    else:
        # 開始處理
        content = load_content(uploaded_file)
        if not content:
            st.error("❌ 讀取失敗")
        else:
            hands = parse_hands(content)
            
            if not hands:
                st.error("❌ 無法解析手牌")
            else:
                total_hands = len(hands)
                vpip_count = sum(1 for h in hands if h['vpip'])
                pfr_count = sum(1 for h in hands if h['pfr'])
                
                vpip = round((vpip_count / total_hands) * 100, 1)
                pfr = round((pfr_count / total_hands) * 100, 1)

                # --- [優化 3] 使用 Tabs 分頁 ---
                tab1, tab2, tab3 = st.tabs(["📊 賽事儀表板", "🧠 AI 總教練", "🔍 手牌深度覆盤"])

                with tab1:
                    # 關鍵數據
                    c1, c2, c3 = st.columns(3)
                    c1.metric("總手牌數", total_hands)
                    c2.metric("VPIP", f"{vpip}%")
                    c3.metric("PFR", f"{pfr}%")
                    
                    st.divider()
                    
                    # [優化 2] BB 數趨勢圖 (取代原本的籌碼圖)
                    st.subheader("📉 Stack Depth (BB) 趨勢")
                    
                    # 建立圖表數據
                    df_hands = pd.DataFrame(hands)
                    # 簡單繪製 BB 變化
                    st.line_chart(df_hands, y="bb", x="id", height=300)
                    st.caption("顯示每手牌的 BB 數變化，幫助判斷生存壓力階段。")

                with tab2:
                    st.subheader("賽事總結與建議")
                    if st.button("生成 AI 賽事總結"):
                        with st.spinner("AI 教練正在看你的牌譜..."):
                            advice = generate_match_summary(hands, vpip, pfr, api_key, selected_model)
                            st.markdown(advice)
                    else:
                        st.info("點擊按鈕，讓 AI 幫你做全場覆盤。")

                with tab3:
                    st.subheader("手牌列表")
                    
                    col_list, col_detail = st.columns([1, 2])
                    
                    with col_list:
                        selected_hand_index = st.radio(
                            "選擇手牌", 
                            range(len(hands)), 
                            format_func=lambda i: f"Hand #{hands[i]['id']}",
                            key="hand_radio"
                        )
                    
                    with col_detail:
                        hand_data = hands[selected_hand_index]
                        st.text_area("原始紀錄", hand_data['content'], height=300)
                        
                        if st.button(f"分析 Hand #{hand_data['id']}", key="analyze_btn"):
                             st.info("單手牌 AI 分析功能開發中...")