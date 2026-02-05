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

def cards_to_emoji(cards_str):
    """
    將撲克牌字串轉換為 Emoji 格式
    例如: "Ah Ks" -> "A♥️ K♠️"
    """
    if not cards_str:
        return "Unknown"
    
    suit_map = {
        'h': '♥️',  # Hearts 紅心
        'd': '♦️',  # Diamonds 方塊
        'c': '♣️',  # Clubs 梅花
        's': '♠️'   # Spades 黑桃
    }
    
    cards = cards_str.split()
    emoji_cards = []
    
    for card in cards:
        if len(card) >= 2:
            rank = card[:-1]  # 牌面 (A, K, Q, J, T, 9, 8...)
            suit = card[-1].lower()  # 花色 (h, d, c, s)
            emoji_cards.append(f"{rank}{suit_map.get(suit, suit)}")
    
    return " ".join(emoji_cards)

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
        
        # 3. 抓取 Hero 名字與手牌
        # GGPoker 格式：只有 Hero 會有 "Dealt to <Name> [牌]"，其他玩家是 "Dealt to <Name>" (無牌或空)
        # 關鍵：找有實際手牌的那行 (中括號內有內容)
        hero_match = re.search(r"Dealt to (\S+) \[([A-Za-z0-9]{2} [A-Za-z0-9]{2})\]", full_hand_text)
        current_hero = hero_match.group(1) if hero_match else None
        hero_cards = hero_match.group(2) if hero_match else None
        
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
        
        # 5. 計算 VPIP/PFR（僅翻牌前 Pre-flop）
        # 以 "*** FLOP ***" 切割，只對第一部分做匹配，避免翻後動作誤算
        preflop_text = full_hand_text.split("*** FLOP ***")[0] if "*** FLOP ***" in full_hand_text else full_hand_text
        
        is_vpip = False
        is_pfr = False
        hero_escaped = re.escape(current_hero)
        
        # VPIP: 翻牌前 Hero 有 raises / calls / bets（排除 posts）
        vpip_pattern = rf"^{hero_escaped}: (raises|calls|bets)"
        if re.search(vpip_pattern, preflop_text, re.MULTILINE):
            is_vpip = True
        
        # PFR: 翻牌前 Hero 有 raises
        pfr_pattern = rf"^{hero_escaped}: raises"
        if re.search(pfr_pattern, preflop_text, re.MULTILINE):
            is_pfr = True
        
        # 6. 手牌花色與牌型（同花判定：兩張牌最後一字元相同則 is_suited=True）
        is_suited = False
        hand_type = None
        if hero_cards:
            cards = hero_cards.split()
            if len(cards) >= 2:
                suit1 = cards[0][-1].lower()
                suit2 = cards[1][-1].lower()
                is_suited = (suit1 == suit2)
                rank_order = "AKQJT98765432"
                r1, r2 = cards[0][:-1].upper(), cards[1][:-1].upper()
                if r1 not in rank_order or r2 not in rank_order:
                    hand_type = f"{r1}{r2}{'s' if is_suited else 'o'}"
                else:
                    high, low = (r1, r2) if rank_order.index(r1) < rank_order.index(r2) else (r2, r1)
                    hand_type = f"{high}{low}{'s' if is_suited else 'o'}"
        
        # 7. 抓取底池大小 (GGPoker 格式: "Total pot 1,250 | Rake 0")
        pot_match = re.search(r"Total pot ([\d,]+)", full_hand_text)
        pot_size = int(pot_match.group(1).replace(",", "")) if pot_match else 0
        
        # 8. 精準抓取位置與座位 (Button / SB / BB / Other)
        button_match = re.search(r"Seat #(\d+) is the button", full_hand_text)
        button_seat = button_match.group(1) if button_match else None
        hero_seat_match = re.search(rf"Seat (\d+): {re.escape(current_hero)}\s", full_hand_text)
        hero_seat = hero_seat_match.group(1) if hero_seat_match else None
        
        position = "Other"
        if hero_seat and button_seat and hero_seat == button_seat:
            position = "BTN"
        elif re.search(rf"^{re.escape(current_hero)}: posts small blind", preflop_text, re.MULTILINE):
            position = "SB"
        elif re.search(rf"^{re.escape(current_hero)}: posts big blind", preflop_text, re.MULTILINE):
            position = "BB"
        
        parsed_hands.append({
            "id": hand_id,
            "content": full_hand_text,
            "vpip": is_vpip,
            "pfr": is_pfr,
            "bb": bb_count,
            "hero": current_hero,
            "hero_cards": hero_cards,
            "is_suited": is_suited,
            "hand_type": hand_type,
            "pot_size": pot_size,
            "position": position
        })
    
    return parsed_hands, detected_hero

def generate_match_summary(hands_data, vpip, pfr, api_key, model):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    # 關鍵手牌篩選：vpip == True，依 pot_size（底池大小）由大到小排序，取前 5 手最大底池
    key_hands_raw = [h for h in hands_data if h.get("vpip")]
    key_hands_raw.sort(key=lambda h: h.get("pot_size", 0), reverse=True)
    key_hands = key_hands_raw[:5]
    
    # 組關鍵手牌描述：一律使用 Hand #<display_index>（與 UI 列表一致），不顯示 TM... 原始 ID
    key_hands_lines = []
    for i, h in enumerate(key_hands, 1):
        display_idx = h.get("display_index", i)
        hero_cards = h.get("hero_cards") or "??"
        suited_label = "(Suited)" if h.get("is_suited") else "(Offsuit)"
        ht = h.get("hand_type") or "??"
        pot_size = h.get("pot_size", 0)
        key_hands_lines.append(
            f"【Hand #{display_idx}】\n"
            f"- Hero 底牌: {hero_cards} {suited_label} (牌型: {ht})\n"
            f"- 底池: {pot_size}\n"
            f"- 完整紀錄:\n{h.get('content', '')}"
        )
    
    key_hands_text = "\n\n---\n\n".join(key_hands_lines) if key_hands_lines else "（無 VPIP 手牌）"
    
    prompt = f"""你是一位專業且資深的撲克導師。語氣要求：專業、冷靜、客觀，帶有建設性。請勿使用「兄弟」、「喔！」、「秀肌肉」等過於輕浮或江湖味的詞彙。

---

【整體數據】
- 總手牌數: {len(hands_data)}
- VPIP: {vpip}%
- PFR: {pfr}%

【關鍵手牌（共 5 手，依底池大小選出）】
以下手牌編號為 Hand #數字，與使用者介面列表完全對應。請依此編號引用，勿使用 TM 等原始 ID。手牌已標註 (Suited) 或 (Offsuit)，請依此解讀花色。

{key_hands_text}

---

【輸出格式】請務必依以下三個區塊、用 Markdown 撰寫：

## 🎯 賽事回顧
請寫一段約 150～200 字的完整段落，像賽後新聞稿一樣，專業地總結選手的風格（鬆/緊、被動/激進）以及本場比賽的主要漏洞。不要只寫一句話。

## 🔥 關鍵戰役覆盤
針對上述 5 手大底池手牌，分析 Hero 在大底池處理上的優缺點。每當提到某一手時，必須標註「Hand #數字」（例如 Hand #3、Hand #12），與介面列表一致。

## 💡 下場比賽調整
給出 1～2 個具體可執行的建議。"""
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        resp = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        return resp.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "AI 連線失敗，請檢查 API Key 或稍後再試。"

def analyze_specific_hand(hand_data, api_key, model):
    """
    傳入完整 hand_data 字典，以事實注入 (Fact Sheet) 抗幻覺。
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    # 事實區塊：用程式算好的數據，防止 AI 看錯花色或位置
    hero_cards_emoji = cards_to_emoji(hand_data.get("hero_cards"))
    position = hand_data.get("position", "Other")
    bb_count = hand_data.get("bb", 0)
    
    fact_sheet = f"""【🔍 牌局事實 (Fact Sheet)】以下為程式解析結果，請以之為準。
- Hero 手牌：{hero_cards_emoji}
- 位置：{position}
- 籌碼量：{bb_count} BB

請基於上述事實進行分析。若原始手牌紀錄內容與上述事實衝突，以本事實區塊為準。"""
    
    hand_content = hand_data.get("content", "")
    
    prompt = f"""你是撲克教練。請分析這手牌，指出 Hero（主角）的決策是否正確。

{fact_sheet}

---

【原始手牌紀錄】
{hand_content}"""
    
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

            # 反轉為時間正序（最舊→最新），並為每手牌加上 display_index（與 UI 一致）
            hands.reverse()
            for idx, h in enumerate(hands, start=1):
                h["display_index"] = idx
            
            if not hands:
                st.error("❌ 無法解析手牌，請確認格式。")
            else:
                total_hands = len(hands)
                vpip_count = sum(1 for h in hands if h['vpip'])
                pfr_count = sum(1 for h in hands if h['pfr'])
                
                vpip = round((vpip_count / total_hands) * 100, 1) if total_hands > 0 else 0
                pfr = round((pfr_count / total_hands) * 100, 1) if total_hands > 0 else 0

                # --- 分頁顯示 (合併為 2 個分頁) ---
                tab1, tab2 = st.tabs(["📊 賽事儀表板", "🔍 手牌深度覆盤"])

                with tab1:
                    # 數據卡片區塊
                    st.markdown("### 📊 關鍵數據")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("總手牌數", total_hands)
                    c2.metric("VPIP", f"{vpip}%")
                    c3.metric("PFR", f"{pfr}%")
                    c4.metric("Hero ID", hero_name if hero_name else "Unknown")
                    
                    # 分隔線
                    st.divider()
                    
                    # AI 賽事總結區塊 (原 Tab 2 內容)
                    st.markdown("### 🧠 AI 賽事總結")
                    if st.button("生成 AI 賽事總結", key="summary_btn"):
                        with st.spinner("AI 思考中..."):
                            advice = generate_match_summary(hands, vpip, pfr, api_key, selected_model)
                            st.markdown(advice)

                with tab2:
                    # 手牌覆盤區塊 (優化版)
                    st.markdown("### 🔍 手牌覆盤")
                    col_list, col_detail = st.columns([1, 2])
                    
                    with col_list:
                        # 優化手牌列表顯示：Hand #<display_index>: A♥️ K♠️（與 AI 報告編號一致）
                        def format_hand_label(i):
                            hand = hands[i]
                            hand_num = hand.get("display_index", i + 1)
                            cards_display = cards_to_emoji(hand.get('hero_cards'))
                            return f"Hand #{hand_num}: {cards_display}"
                        
                        selected_index = st.radio(
                            "選擇手牌", 
                            range(len(hands)), 
                            format_func=format_hand_label,
                            key="hand_radio"
                        )
                    
                    with col_detail:
                        hand_data = hands[selected_index]
                        
                        # AI 分析按鈕（傳入完整 hand_data，含事實注入抗幻覺）
                        if st.button(f"🤖 AI 分析這手牌", key="analyze_btn", use_container_width=True):
                            with st.spinner("AI 正在分析這手牌..."):
                                analysis = analyze_specific_hand(hand_data, api_key, selected_model)
                                st.markdown("### 💡 AI 分析結果")
                                st.markdown(analysis)
                        else:
                            # 未點擊按鈕時顯示提示
                            st.info("👆 點擊上方按鈕，讓 AI 分析這手牌的決策。")