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
    
    /* 優化引用區塊 (Blockquote) 樣式 - 用於顯示教練狠評 */
    blockquote {
        background-color: #1e2130;
        border-left: 5px solid #ff4b4b;
        padding: 15px;
        border-radius: 5px;
        color: #e0e0e0;
        font-size: 16px;
        margin: 20px 0;
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

# 花色對應（與 cards_to_emoji 一致，供 parse_hands 產出 hero_cards_emoji）
SUIT_EMOJI = {'c': '♣️', 's': '♠️', 'h': '♥️', 'd': '♦️'}

def calculate_position(hero_seat, button_seat, total_seats):
    """
    數學定義位置：依順時針距離 Button 計算。
    輸入：hero_seat (int), button_seat (int), total_seats (list[int]，已排序之所有玩家座號)。
    距離公式：(hero_idx - btn_idx) % count
    定義：0=BTN, 1=SB, 2=BB, 3=UTG, 4=UTG+1(6人+), 倒數第1=CO, 倒數第2=HJ, 其他=MP
    """
    if not total_seats or hero_seat is None or button_seat is None:
        return "Other"
    try:
        hero_seat = int(hero_seat)
        button_seat = int(button_seat)
        total_seats = sorted([int(s) for s in total_seats])
    except (TypeError, ValueError):
        return "Other"
    
    if hero_seat not in total_seats or button_seat not in total_seats:
        return "Other"
    
    n = len(total_seats)
    btn_idx = total_seats.index(button_seat)
    hero_idx = total_seats.index(hero_seat)
    distance = (hero_idx - btn_idx) % n
    
    if distance == 0:
        return "BTN"
    if distance == 1:
        return "SB"
    if distance == 2:
        return "BB"
    if distance == 3:
        return "UTG"
    if distance == 4 and n >= 6:
        return "UTG+1"
    if distance == n - 1:
        return "CO"
    if distance == n - 2:
        return "HJ"
    if 5 <= distance <= n - 3:
        return "MP"
    return "Other"

def distance_to_button(seat, button_seat, total_seats):
    """
    順時針距離 Button 的步數（0=BTN, 1=SB, 2=BB, 3=UTG, ...）。
    翻後行動順序為 SB→BB→UTG→...→BTN，故數字越大代表動作越晚 → In Position。
    """
    if not total_seats or seat is None or button_seat is None or seat not in total_seats or button_seat not in total_seats:
        return None
    sorted_seats = sorted([int(s) for s in total_seats])
    n = len(sorted_seats)
    btn_idx = sorted_seats.index(int(button_seat))
    seat_idx = sorted_seats.index(int(seat))
    return (seat_idx - btn_idx) % n

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
        
        # 8. 精準抓取座位並用數學計算位置（完全移除 AI 對位置的解釋權）
        btn_match = re.search(r"The button is in seat #(\d+)", full_hand_text) or re.search(r"Seat #(\d+) is the button", full_hand_text)
        button_seat = int(btn_match.group(1)) if btn_match else None
        hero_seat_match = re.search(rf"Seat (\d+): {re.escape(current_hero)}\s", full_hand_text)
        hero_seat = int(hero_seat_match.group(1)) if hero_seat_match else None
        active_seats = list(set(int(m.group(1)) for m in re.finditer(r"Seat (\d+): .+ in chips", full_hand_text)))
        hero_position_str = calculate_position(hero_seat, button_seat, active_seats)
        
        # 8b. 主要對手 (Main Villain) 與相對位置 (IP/OOP)
        villain_seat = None
        relative_pos_str = "N/A"
        m_raise = re.search(r"(\S+): raises", preflop_text)
        m_bet = re.search(r"(\S+): bets", preflop_text)
        villain_name = None
        if m_raise and m_bet:
            villain_name = m_raise.group(1) if m_raise.start() < m_bet.start() else m_bet.group(1)
        elif m_raise:
            villain_name = m_raise.group(1)
        elif m_bet:
            villain_name = m_bet.group(1)
        if villain_name:
            if villain_name == current_hero:
                relative_pos_str = "Hero 為翻前加注者 (無單一主要對手)"
            else:
                villain_seat_m = re.search(rf"Seat (\d+): {re.escape(villain_name)}\s", full_hand_text)
                if villain_seat_m and active_seats:
                    villain_seat = int(villain_seat_m.group(1))
                    if villain_seat in active_seats:
                        hero_dist = distance_to_button(hero_seat, button_seat, active_seats)
                        villain_dist = distance_to_button(villain_seat, button_seat, active_seats)
                        if hero_dist is not None and villain_dist is not None:
                            if hero_dist == 0:
                                relative_pos_str = "In Position (IP)"  # Hero 是 Button
                            elif villain_dist == 0:
                                relative_pos_str = "Out of Position (OOP)"  # 對手是 Button
                            elif hero_dist > villain_dist:
                                relative_pos_str = "In Position (IP)"  # Hero 距離更大 = 動作更晚
                            else:
                                relative_pos_str = "Out of Position (OOP)"
                    else:
                        relative_pos_str = "N/A (無法判定主要對手座位)"
                else:
                    relative_pos_str = "N/A (無法判定主要對手座位)"
        else:
            relative_pos_str = "多路底池 (無人加注)"
        
        # 9. 花色轉換：c=♣️, s=♠️, h=♥️, d=♦️，直接產出 hero_cards_emoji 存入字典
        hero_cards_emoji = "Unknown"
        if hero_cards:
            parts = hero_cards.split()
            emoji_parts = [f"{c[:-1]}{SUIT_EMOJI.get(c[-1].lower(), c[-1])}" for c in parts if len(c) >= 2]
            hero_cards_emoji = " ".join(emoji_parts) if emoji_parts else "Unknown"
        
        parsed_hands.append({
            "id": hand_id,
            "content": full_hand_text,
            "vpip": is_vpip,
            "pfr": is_pfr,
            "bb": bb_count,
            "hero": current_hero,
            "hero_cards": hero_cards,
            "hero_cards_emoji": hero_cards_emoji,
            "is_suited": is_suited,
            "hand_type": hand_type,
            "pot_size": pot_size,
            "position": hero_position_str,
            "villain_seat": villain_seat,
            "relative_pos_str": relative_pos_str,
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
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1}
    }
    try:
        resp = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        return resp.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "AI 連線失敗，請檢查 API Key 或稍後再試。"

def analyze_specific_hand(hand_data, api_key, model):
    """
    傳入完整 hand_data；花色與位置由系統事實強制注入，AI 無解釋權。
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    hero_cards_emoji = hand_data.get("hero_cards_emoji") or cards_to_emoji(hand_data.get("hero_cards"))
    hero_position = hand_data.get("position", "Other")
    bb_count = hand_data.get("bb", 0)
    display_index = hand_data.get("display_index", "?")
    relative_pos_str = hand_data.get("relative_pos_str", "N/A")
    
    fact_sheet = f"""【系統判定事實 - 分析基準，請嚴格遵守】
- Hero 手牌: {hero_cards_emoji}
- Hero 位置: {hero_position}
- 籌碼量: {bb_count} BB
- 相對位置優劣: {relative_pos_str} (針對主要對手)
若原始文本與上述衝突，以上述為準。輸出時請勿重複列出此清單，直接進入分析。

**相對位置思考限制**：你必須基於上述的「相對位置優劣」進行分析，嚴禁自行推斷 Hero 是 IP 還是 OOP。若 Hero 處於 **In Position (IP)**，請傾向於建議更寬的跟注 (Call) 或浮打 (Float) 範圍；若 **Out of Position (OOP)**，則建議更緊的防守。勿出現「CO vs UTG+1 是不利位置」等與系統事實矛盾的結論。**"""

    hand_content = hand_data.get("content", "")
    
    prompt = f"""你是 Hero 的專屬教練，也是一位說話直率的戰友。語氣要專業、銳利，但帶有溫度。禁止使用機器人口吻（如「根據數據顯示…」「總結如下…」），改用自然的教練口吻（如「兄弟，這裡你的範圍太強了…」「這手牌打得有點貪心…」）。

【核心分析邏輯 - 判斷優先級 (Decision Hierarchy)】
請**嚴格依照以下順序**判斷，先滿足者優先適用，後續條款不得覆蓋前一條款的結論。

**第一優先級：強勢擠壓判定 (The Power Shove Check)**
- **觸發條件**：Hero 持有 **88～QQ** 或 **AK / AQs**，且籌碼介於 **20BB～40BB**，面對 **Open Raise** 選擇全下 (Shove)。
- **判定結論**：此為最優策略 (+EV)。必須定義為「**標準擠壓 (Standard Squeeze)**」或「**剝削性全下**」。
- **指令**：**強制忽略**任何關於「尷尬籌碼量」的警告。請用「**展現宰制力**」、「**死錢效益 (Dead Money)**」、「敢於在翻前結束戰鬥」來稱讚此決策。勿使用負面或過度謹慎詞彙（如「風險不小」「運氣好」）。  
- **重要**：一旦符合本條，**不得**再套用第二優先級的尷尬籌碼警告。（例：31BB 的 99 全下 → 僅觸發本條讚賞。）

**第二優先級：尷尬籌碼量警告 (The Awkward Zone)**
- **觸發條件**：**僅在不符合第一優先級時**，若 Hero 籌碼介於 **30BB～50BB**。
- **判定結論**：對中等/邊緣牌型（如 22～66、ATo、KJo 等），全下風險過高。
- **指令**：此時應建議**保留跟注 (Flat Call)** 或**棄牌**，避免過度激進。可提及「尷尬籌碼區間」的結構性問題。

**第三優先級：價值下注原則 (Value Betting)**
- **觸發條件**：Hero 持有強牌（Set、兩對、順子以上），且對手範圍能支付時。
- **指令**：支持**薄價值下注**。不要因單張驚悚牌 (Scare Card)（如 River 出一張 A）而過度保守；除非牌面極度兇險（如完成 4 張同花或 4 張順子），否則應支持價值下注。若對手範圍內有足夠多差牌 (Worse Hands) 會跟注，下注即為 +EV。

**通用原則（貫穿各優先級）**
- **範圍對抗 (Range vs Range)**：推測對手在該位置的範圍與 Hero 的感知範圍；分析各街牌面對誰更有利。
- **EV 思維**：針對關鍵決策點，說明長期期望值 (EV) 是正或負。
- **20BB 以下**：對於 20BB 以下的 all-in/fold，參照 Nash 圖表；若為邊緣牌型 (Mixed Strategy)，可指出「高波動邊緣決策」。

**衝突裁決 (CRITICAL)**：
判斷必須嚴格遵守層級 (Hierarchy)。若手牌符合「第二優先級：尷尬籌碼警告」，你**必須**給出保守建議（棄牌或平跟）。**嚴禁**使用後面的「通用原則」（如 EV、底池賠率、賞金因素）來推翻「尷尬籌碼」的結論。在 30-50BB 區間，除非是頂級強牌 (JJ+, AK)，否則風險控制永遠優先於邊緣 EV。

{fact_sheet}

---

【原始手牌紀錄】
{hand_content}

---

【輸出格式 - 嚴格遵守】
0. **【最高優先級】撲克牌 Emoji 化**：在輸出的所有文字中，提到撲克牌時必須使用 Emoji 格式。例如：'Ts' 寫成 T♠️，'7d' 寫成 7♦️，'Ah' 寫成 A♥️，'Kc' 寫成 K♣️。嚴禁直接輸出純文字卡片代碼（如 Ts、Ah）。
1. **第一行起**：只寫教練的總結評價（狠評），一句話即可。不要加任何標題、不要加 Markdown 符號（如 ## 或 >）。
2. **狠評結束後**：強制換行，然後單獨一行寫入分隔符號：===SPLIT===
3. **分隔符號之後**：才是 Markdown 詳細分析，包含以下章節，區塊之間用 --- 分隔：
   - **🧐 關鍵局勢解讀**：Pre-flop 可玩性；Flop/Turn/River 有動作的街，重點在「為什麼」。**Range**、**EV**、**GTO**、**C-bet** 等用粗體。盡量列點。
   - **💡 漏洞與建議**：思維漏洞 + 1～2 個具體建議。

範例結構：
兄弟，這手牌在轉牌這裡打得有點貪心，EV 上你是在送錢。
===SPLIT===
## 🧐 關鍵局勢解讀
...
---
## 💡 漏洞與建議
..."""
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.0}
    }
    try:
        resp = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        raw_text = resp.json()['candidates'][0]['content']['parts'][0]['text']
        # 回傳原始文字，由呼叫端依 ===SPLIT=== 切分顯示
        return raw_text
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
                        
                        # 系統判定摘要（選牌時即顯示，讓使用者確認）
                        sys_position = hand_data.get("position", "Other")
                        sys_cards = hand_data.get("hero_cards_emoji") or cards_to_emoji(hand_data.get("hero_cards"))
                        st.caption(f"📍 **系統判定**：位置 {sys_position} | 手牌 {sys_cards}")
                        
                        # AI 分析按鈕（傳入完整 hand_data；結果依 ===SPLIT=== 分離狠評與詳情）
                        if st.button(f"🤖 AI 分析這手牌", key="analyze_btn", use_container_width=True):
                            with st.spinner("AI 正在分析這手牌..."):
                                analysis = analyze_specific_hand(hand_data, api_key, selected_model)
                                st.markdown("### 💡 AI 分析結果")
                                st.caption(f"📍 **系統鎖定**：位置 {sys_position} | 手牌 {sys_cards}")
                                parts = analysis.split("===SPLIT===")
                                summary_text = parts[0].strip() if parts else ""
                                detail_text = parts[1].strip() if len(parts) > 1 else ""
                                if summary_text and detail_text:
                                    st.info(summary_text, icon="🦁")
                                    st.markdown(detail_text)
                                else:
                                    st.markdown(analysis)
                        else:
                            st.info("👆 點擊上方按鈕，讓 AI 分析這手牌的決策。")