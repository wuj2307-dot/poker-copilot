import streamlit as st
import re
import requests
import json
import pandas as pd
import random

# --- 1. 頁面設定 ---
st.set_page_config(page_title="Poker Copilot War Room", page_icon="♠️", layout="wide")

# CSS 優化

st.title("♠️ Poker Copilot: Alpha")
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
    
        # 只保留唯一能通的 "gemini-2.5-flash"，把其他會報錯的都刪掉
        selected_model = st.selectbox("AI 引擎", ["gemini-2.5-flash"])
        
        st.header("🔍 篩選")
        filter_vpip = st.checkbox("只顯示有玩 (VPIP)", value=False)
        filter_lost = st.checkbox("只顯示輸錢", value=False)
    else:
        st.warning("請先輸入正確密碼才能解鎖功能。")

# --- 3. 核心解析邏輯 ---
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
    hid = re.search(r"TM(\d+):", h) or re.search(r"#(\d+):", h)
    hid_str = hid.group(1) if hid else "Unknown"
    hero_cards = re.search(r"Dealt to Hero \[(.*?)\]", h)
    cards = hero_cards.group(1) if hero_cards else None
    chip_match = re.search(r"Hero \(\$?([\d,]+).*\)", h)
    chips = int(chip_match.group(1).replace(",", "")) if chip_match else 0
    is_vpip = "Hero: raises" in h or "Hero: calls" in h or "Hero: bets" in h
    is_pfr = "Hero: raises" in h or "Hero: bets" in h
    res = "😐"
    if "Hero showed" in h and "lost" in h: res = "❌"
    elif "Hero collected" in h or "Hero won" in h: res = "💰"
    elif "Hero folded" in h: res = "🛡️"
    is_showdown = "Hero showed" in h or "Hero mucks" in h
    if cards or chips > 0:
        parsed_list.append({
            "id": hid_str, "cards": cards, "result": res, 
            "is_vpip": is_vpip, "is_pfr": is_pfr, "chips": chips,
            "is_showdown": is_showdown, "raw": h
        })

def cards_to_emoji(card_str):
    if not card_str: return ""
    suits_map = {'s': '♠️', 'h': '♥️', 'd': '♦️', 'c': '♣️'}
    formatted = []
    for card in card_str.split():
        if len(card) >= 2:
            formatted.append(f"{card[:-1]}{suits_map.get(card[-1], card[-1])}")
    return " ".join(formatted)

# --- 4. AI 功能 (V12.0 精準提示優化版) ---
def analyze_hand_ai(hand_text, api_key, model):
    if not api_key: return "⚠️ 請先解鎖"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    # 🔥 V12.0 關鍵修改：植入「撲克規則庫」與「花色字典」
    prompt = f"""
    你是一個世界級的德州撲克教練。請分析這手牌。
    
    【⚠️ 嚴格資料解讀規則 - 必須遵守】
    1. **花色代碼對照**：
       - 'h' = ♥️ 紅心 (Hearts)
       - 's' = ♠️ 黑桃 (Spades)
       - 'd' = ♦️ 方塊 (Diamonds)
       - 'c' = ♣️ 梅花 (Clubs)
       - 請絕對不要看錯花色。
       
    2. **牌型定義 (Hand Rankings)**：
       - **Top Pair (頂對)**：你的底牌之一 **對到了** 牌面上最大的那張牌。(例如：手牌 T9，牌面 T-5-2)。
       - **Overcards (高張)**：你的底牌比牌面都大，但 **沒有對到**。(例如：手牌 AT，牌面 9-8-2)。這叫 "Ace High"，**不是** Top Pair。
       - **Draws (聽牌)**：
         - Flush Draw (同花聽牌)：你有 4 張同花色。
         - OESD (兩頭順)：差一張成順子。

    【分析任務】
    請一步步思考 (Chain of Thought)：
    1. 先在心中確認 Hero 的確切底牌與花色。
    2. 確認翻牌/轉牌的結構。
    3. 準確判斷 Hero 目前的牌力 (是成牌還是聽牌？)。
    4. 用繁體中文輸出犀利的決策分析。

    【輸出格式】
    ### 🃏 手牌與牌面
    Hero: [你的解讀] (例如：♥️A ♥️T)
    Board: [你的解讀]
    目前牌力：(例如：高牌 A-High + 堅果同花聽牌 + 兩頭順聽牌)

    ### 🎯 核心評價
    (一句話總結)

    ### 🧠 決策分析
    (針對翻牌前、翻牌後的操作進行點評)

    ### 💡 改進建議
    (如有錯誤，該怎麼打)

    手牌紀錄：
    {hand_text}
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {'Content-Type': 'application/json'}
    
    try:
        resp = requests.post(url, headers=headers, data=json.dumps(payload))
        if resp.status_code == 200:
            return resp.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Error: {resp.text}"
    except Exception as e: return str(e)

def generate_match_summary(hands_data, vpip, pfr, api_key, model):
    if not api_key: return "⚠️ 請先解鎖"
    key_hands = [h['raw'] for h in hands_data if h['is_vpip']][:20]
    key_hands_text = "\n\n".join(key_hands)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    prompt = f"""
    你是一個職業撲克戰隊總教練。
    【學員數據】手牌數: {len(hands_data)}, VPIP: {vpip:.1f}%, PFR: {pfr:.1f}%
    【關鍵手牌樣本】{key_hands_text}
    請給出一份【賽事深度診斷報告】(繁體中文)：1.風格畫像 2.關鍵漏洞 3.運氣成分 4.總結建議。
    """
    # 這裡加入了 safetySettings (安全通行證)，強制關閉敏感過濾
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    try:
        resp = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        return resp.json()['candidates'][0]['content']['parts'][0]['text'] if resp.status_code == 200 else f"Error: {resp.text}"
    except Exception as e: return str(e)

# --- 5. 主介面 ---
if not api_key:
    st.info("👈 請先在左側輸入通關密碼 (Access Code) 才能使用。")
else:
    uploaded_file = st.file_uploader("📂 上傳比賽紀錄 (.txt)", type=["txt"])
    # 修復預讀錯誤：未上傳檔案時不執行解析、不顯示錯誤，只顯示上傳框
    if uploaded_file is None:
        pass  # 保持頁面乾淨，只顯示上傳框
    else:
        content = load_content(uploaded_file)
        if not content:
            st.error("❌ 讀取失敗")
        else:
            hands = parse_hands(content)
            if not hands:
                st.error("❌ 無法解析手牌")
            else:
                total = len(hands)
                vpip_c = sum(1 for h in hands if h['is_vpip'])
                pfr_c = sum(1 for h in hands if h['is_pfr'])
                vpip = (vpip_c / total * 100) if total else 0
                pfr = (pfr_c / total * 100) if total else 0
                chip_data = [h['chips'] for h in hands if h['chips'] > 0]
                start_chip = chip_data[0] if chip_data else 0
                end_chip = chip_data[-1] if chip_data else 0

                # BB 數趨勢圖：若有籌碼數據則用 chips/BB 模擬 Stack Depth，否則用隨機數據示範
                BB = 100  # 假設大盲為 100，若未來有解析可改為真實 BB
                if chip_data:
                    stack_bb = [c / BB for c in chip_data]
                else:
                    stack_bb = [random.randint(15, 80) for _ in range(max(1, total))]
                df_bb = pd.DataFrame({"BB數": stack_bb})

                tab1, tab2, tab3 = st.tabs(["📊 賽事儀表板", "🧠 AI 總教練", "🔍 手牌深度覆盤"])

                with tab1:
                    st.markdown("### 📊 賽事儀表板")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("手牌數", total)
                    c2.metric("VPIP", f"{vpip:.1f}%", "偏高" if vpip > 30 else "偏低" if vpip < 18 else "健康")
                    c3.metric("PFR", f"{pfr:.1f}%", f"Gap {vpip-pfr:.1f}%")
                    c4.metric("籌碼變化", f"{end_chip}", f"{end_chip - start_chip:+}")
                    st.markdown("#### Stack Depth in BB（生存壓力趨勢）")
                    st.line_chart(df_bb, height=280)
                    st.caption("X 軸：手牌序號　｜　Y 軸：BB 數 (Stack Depth)")

                with tab2:
                    st.markdown("### 🧠 AI 總教練")
                    summary_key = f"match_summary_{uploaded_file.name}"
                    if st.button("📝 生成賽事總結", type="primary", use_container_width=True, key="summary_btn"):
                        with st.spinner("教練正在閱讀..."):
                            summary = generate_match_summary(hands, vpip, pfr, api_key, selected_model)
                            st.session_state[summary_key] = summary
                    if st.session_state.get(summary_key):
                        st.markdown(st.session_state[summary_key])

                with tab3:
                    st.markdown("### 🔍 手牌深度覆盤")
                    col_list, col_analysis = st.columns([1, 2])
                    with col_list:
                        st.subheader("📜 手牌")
                        filtered_hands = hands
                        if filter_vpip:
                            filtered_hands = [h for h in filtered_hands if h['is_vpip']]
                        if filter_lost:
                            filtered_hands = [h for h in filtered_hands if h['result'] == '❌']
                        options = [f"{h['result']} {cards_to_emoji(h['cards'])} (Chips: {h['chips']})" for h in filtered_hands]
                        if not options:
                            st.warning("無符合條件手牌")
                            selected_hand = None
                        else:
                            sel_idx = st.radio("選擇手牌", range(len(options)), format_func=lambda x: options[x], label_visibility="collapsed", key="hand_radio")
                            selected_hand = filtered_hands[sel_idx]
                    with col_analysis:
                        if selected_hand:
                            st.markdown(f"## {selected_hand['result']} #{selected_hand['id']}")
                            st.markdown(f"<div class='poker-card'>{cards_to_emoji(selected_hand['cards'])}</div>", unsafe_allow_html=True)
                            st.markdown("---")
                            if st.button("🔥 分析這手牌", key="analyze_btn"):
                                with st.spinner("分析中..."):
                                    res = analyze_hand_ai(selected_hand['raw'], api_key, selected_model)
                                    st.markdown(res)
                            with st.expander("原始紀錄"):
                                st.code(selected_hand['raw'])
