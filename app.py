import streamlit as st
import re
import requests
import json
from datetime import datetime

# --- 1. 頁面設定 ---
st.set_page_config(page_title="Poker Copilot War Room", page_icon="♠️", layout="wide")

# CSS 優化 (數據卡片樣式)
st.markdown("""
<style>
    /* Tab 樣式 */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; 
        white-space: pre-wrap; 
        background-color: #0e1117; 
        border-radius: 4px 4px 0px 0px; 
        padding: 10px; 
    }
    
    /* Metric 數據卡片樣式 */
    div[data-testid="stMetricValue"] { 
        font-size: 36px; 
        font-weight: 700;
        color: #00FF88;
        text-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
    }
    
    div[data-testid="stMetricLabel"] { 
        font-size: 14px; 
        font-weight: 600;
        color: #AAAAAA;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Metric 容器卡片效果 */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #1a1a2e, #16213e);
        border: 1px solid #2a2a4a;
        border-radius: 12px;
        padding: 20px 16px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    
    /* Metric delta (變化值) 樣式 */
    div[data-testid="stMetricDelta"] {
        font-size: 12px;
    }
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
    """
    專為 GGPoker 格式設計的手牌解析器
    參考檔案: GGtest.txt
    """
    # 切割手牌：以 "Poker Hand #" 為分隔符
    raw_hands = re.split(r"(?=Poker Hand #)", content)
    parsed_hands = []
    detected_hero = None

    for raw_hand in raw_hands:
        if not raw_hand.strip() or len(raw_hand) < 100:
            continue
        
        full_hand_text = raw_hand.strip()
        
        # 1. 抓取手牌 ID (格式: "Poker Hand #TM5492660659:")
        hand_id_match = re.search(r"Poker Hand #(TM\d+):", full_hand_text)
        hand_id = hand_id_match.group(1) if hand_id_match else "Unknown"
        
        # 2. 抓取 Big Blind 大小 (格式: "Level19(1,750/3,500)")
        bb_size_match = re.search(r"Level\d+\([\d,]+/([\d,]+)\)", full_hand_text)
        bb_size = int(bb_size_match.group(1).replace(",", "")) if bb_size_match else 1
        
        # 3. 抓取 Hero 名字
        # GGPoker 格式：只有 Hero 會有 "Dealt to <Name> [牌]"，其他玩家是 "Dealt to <Name>" (無牌或空)
        # 關鍵：找有實際手牌的那行 (中括號內有內容)
        hero_match = re.search(r"Dealt to (\S+) \[[A-Za-z0-9]{2} [A-Za-z0-9]{2}\]", full_hand_text)
        current_hero = hero_match.group(1) if hero_match else None
        
        if current_hero and detected_hero is None:
            detected_hero = current_hero
        
        # 如果找不到 Hero，跳過此手牌
        if not current_hero:
            continue
        
        # 4. 抓取 Hero 的起始籌碼 (格式: "Seat 6: Hero (35,803 in chips)")
        stack_pattern = rf"Seat \d+: {re.escape(current_hero)} \(([\d,]+) in chips\)"
        stack_match = re.search(stack_pattern, full_hand_text)
        hero_chips = int(stack_match.group(1).replace(",", "")) if stack_match else 0
        bb_count = round(hero_chips / bb_size, 1) if bb_size > 0 else 0
        
        # 5. 計算 VPIP/PFR (嚴格只看 Hero 的主動動作)
        # 排除盲注投入：posts small blind / posts big blind / posts the ante
        is_vpip = False
        is_pfr = False
        
        hero_escaped = re.escape(current_hero)
        
        # VPIP: Hero 有 raises / calls / bets (排除 posts)
        # 格式: "Hero: raises 31,803" 或 "Hero: calls 1,600"
        vpip_pattern = rf"^{hero_escaped}: (raises|calls|bets)"
        if re.search(vpip_pattern, full_hand_text, re.MULTILINE):
            is_vpip = True
        
        # PFR: Hero 有 raises
        pfr_pattern = rf"^{hero_escaped}: raises"
        if re.search(pfr_pattern, full_hand_text, re.MULTILINE):
            is_pfr = True
        
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
                    st.markdown("### 📊 關鍵數據")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("總手牌數", total_hands)
                    c2.metric("VPIP", f"{vpip}%")
                    c3.metric("PFR", f"{pfr}%")
                    c4.metric("Hero ID", hero_name if hero_name else "Unknown")

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