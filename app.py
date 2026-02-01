import streamlit as st
import re
import requests
import json
import pandas as pd
from datetime import datetime

# --- 1. 頁面設定 ---
st.set_page_config(page_title="Poker Copilot War Room", page_icon="♠️", layout="wide")

# CSS 優化 (保留好看的介面)
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
    user_password = st.text_input("輸入通關密碼 (Access Code)", type="password")
    api_key = None
    
    if user_password == st.secrets["ACCESS_PASSWORD"]:
        st.success("✅ 驗證通過！")
        api_key = st.secrets["GEMINI_API_KEY"]
    elif user_password:
        st.error("❌ 密碼錯誤")

    st.divider()

    if api_key:
        st.header("⚙️ 設定")
        selected_model = st.selectbox("AI 引擎", ["gemini-2.5-flash"])

# --- 3. 核心功能函數 (修復版) ---

def load_content(uploaded_file):
    if uploaded_file is not None:
        return uploaded_file.getvalue().decode("utf-8")
    return None

def parse_hands(content):
    # [邏輯回滾] 使用最穩定的切割方式 (相容 GG/Stars)
    # 不再依賴複雜 Regex，直接切 "Poker Hand" 或 "PokerStars Hand"
    raw_hands = re.split(r"(?:PokerStars Hand #|Poker Hand #)", content)
    parsed_hands = []
    
    # 用來檢查是否抓到 Hero (除錯用)
    detected_hero = None 

    for raw_hand in raw_hands:
        if not raw_hand.strip():
            continue
            
        full_hand_text = "Hand #" + raw_hand # 補回被切掉的頭
        
        # 1. 抓 ID
        hand_id_match = re.search(r"(\d+):", raw_hand)
        hand_id = hand_id_match.group(1) if hand_id_match else "Unknown"

        # 2. 抓 Hero 名字 (關鍵修復：解決 VPIP 0 或 76 的問題)
        # 邏輯：找 "Dealt to [名字]" 這一行
        hero_match = re.search(r"Dealt to (.+?) \[", full_hand_text)
        if not hero_match:
             hero_match = re.search(r"Dealt to (.+?)(?:\n|$)", full_hand_text) # 針對沒括號的情況
        
        current_hero = hero_match.group(1) if hero_match else None
        
        if current_hero and detected_hero is None:
            detected_hero = current_hero # 紀錄抓到的第一個人名

        # 3. 算 VPIP/PFR (只看 Hero 的動作)
        is_vpip = False
        is_pfr = False
        bb_count = 0

        if current_hero:
            # 簡化判斷：只要名字後面接動作關鍵字就算
            # 這種寫法比 Regex 穩，因為不會被冒號格式影響
            lines = full_hand_text.split('\n')
            hero_acted = False
            
            for line in lines:
                if current_hero in line:
                    if "raises" in line:
                        is_vpip = True
                        is_pfr = True
                    elif "bets" in line or "calls" in line:
                        is_vpip = True
            
            # 4. 抓 BB 數 (嘗試抓取 Hero 的籌碼)
            # 找 "Hero: 1000" 或 "Hero ($50)" 格式
            stack_match = re.search(re.escape(current_hero) + r".*?(\d+(\.\d+)?)", full_hand_text)
            if stack_match:
                try:
                    # 這裡簡化處理，暫時抓不到準確 BB 沒關係，先讓程式不報錯
                    bb_count = float(stack_match.group(1)) 
                except:
                    bb_count = 0

        parsed_hands.append({
            "id": hand_id,
            "content": full_hand_text,
            "vpip": is_vpip,
            "pfr": is_pfr,
            "bb": bb_count,
            "hero": current_hero
        })
        
    return parsed_hands, detected_hero

def generate_match_summary(hands_data, vpip, pfr, api_key, model):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    prompt = f"你是一個撲克教練。請簡短分析數據：VPIP {vpip}%, PFR {pfr}%, 手牌數 {len(hands_data)}。給出3點建議。"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        resp = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        return resp.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "AI 連線失敗，請檢查 API Key 或稍後再試。"

def analyze_specific_hand(hand_content, api_key, model):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    prompt = f"你是撲克教練。請分析這手牌，指出 Hero (主角) 的決策是否正確：\n\n{hand_content}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        resp = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        return resp.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"分析失敗: {str(e)}"

# --- 4. 主介面邏輯 ---

if not api_key:
    st.info("👈 請先在左側輸入通關密碼才能使用。")
else:
    uploaded_file = st.file_uploader("📂 上傳比賽紀錄 (.txt)", type=["txt"])
    
    if uploaded_file:
        content = load_content(uploaded_file)
        if content:
            # 呼叫解析函數
            hands, hero_name = parse_hands(content)
            
            if not hands:
                st.error("❌ 無法解析手牌，請確認格式。")
            else:
                total_hands = len(hands)
                vpip_count = sum(1 for h in hands if h['vpip'])
                pfr_count = sum(1 for h in hands if h['pfr'])
                
                vpip = round((vpip_count / total_hands) * 100, 1) if total_hands > 0 else 0
                pfr = round((pfr_count / total_hands) * 100, 1) if total_hands > 0 else 0

                # --- 分頁顯示 ---
                tab1, tab2, tab3 = st.tabs(["📊 賽事儀表板", "🧠 AI 總教練", "🔍 手牌深度覆盤"])

                with tab1:
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("總手牌數", total_hands)
                    c2.metric("VPIP", f"{vpip}%")
                    c3.metric("PFR", f"{pfr}%")
                    c4.metric("偵測 ID", hero_name if hero_name else "Unknown") # 這裡讓你確認有沒有抓對人
                    
                    st.divider()
                    st.subheader("📉 籌碼變化趨勢 (模擬)")
                    df_hands = pd.DataFrame(hands)
                    st.line_chart(df_hands, y="bb", x="id", height=300)

                with tab2:
                    st.subheader("賽事總結與建議")
                    if st.button("生成 AI 賽事總結"):
                        with st.spinner("AI 思考中..."):
                            advice = generate_match_summary(hands, vpip, pfr, api_key, selected_model)
                            st.markdown(advice)

                with tab3:
                    st.subheader("手牌覆盤")
                    col_list, col_detail = st.columns([1, 2])
                    
                    with col_list:
                        selected_index = st.radio(
                            "選擇手牌", 
                            range(len(hands)), 
                            format_func=lambda i: f"Hand #{hands[i]['id']}",
                            key="hand_radio"
                        )
                    
                    with col_detail:
                        hand_data = hands[selected_index]
                        st.text_area("原始紀錄", hand_data['content'], height=300)
                        
                        # [修復] 單手分析按鈕接回來了
                        if st.button(f"🤖 AI 分析 Hand #{hand_data['id']}", key="analyze_btn"):
                             with st.spinner("AI 正在分析這手牌..."):
                                analysis = analyze_specific_hand(hand_data['content'], api_key, selected_model)
                                st.markdown("### 💡 AI 分析結果")
                                st.markdown(analysis)