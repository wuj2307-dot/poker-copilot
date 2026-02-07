import streamlit as st
import re
import requests
import json
import random
from datetime import datetime

from demo_data import DEMO_HANDS_TEXT

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

# 單手分析時的隨機等待文案
LOADING_TEXTS = [
    "正在計算死錢賠率...",
    "正在分析對手範圍...",
    "正在回顧 GTO 策略...",
    "AI 教練正在思考最佳打法...",
]


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
    st.markdown("---")
    st.link_button("💬 許願 / 回報 Bug", "https://docs.google.com/forms/d/e/1FAIpQLSeiQT3WgoxLXqfn6eMrvQkS5lBTewgl9iS9AkxQuMyGTySESA/viewform", use_container_width=True)

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
        
        # 1. 抓取手牌 ID (格式: "Poker Hand #TM5492660659:" 或 "Poker Hand #DEMO_TRAP:")
        hand_id_match = re.search(r"Poker Hand #(TM\d+|[A-Za-z0-9_]+):", full_hand_text)
        hand_id = hand_id_match.group(1) if hand_id_match else "Unknown"
        
        # 2. 抓取 Big Blind 大小 (GGPoker: "Level19(1,750/3,500)" / Demo: "posts big blind 400")
        bb_size_match = re.search(r"Level\d+\([\d,]+/([\d,]+)\)", full_hand_text)
        if bb_size_match:
            bb_size = int(bb_size_match.group(1).replace(",", ""))
        else:
            bb_fallback = re.search(r"posts big blind ([\d,]+)", full_hand_text)
            bb_size = int(bb_fallback.group(1).replace(",", "")) if bb_fallback else 400
        
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
        
        # 4. 抓取 Hero 的起始籌碼 (GGPoker: "in chips" / Demo: "Seat 1: Hero (40000)")
        stack_pattern = rf"Seat \d+: {re.escape(current_hero)} \(([\d,]+)(?: in chips)?\)"
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
        
        # 6. 手牌花色與牌型（同花判定 + 牌型標籤）
        is_suited = False
        hand_type = None
        is_pair = False
        is_ax = False
        is_broadway = False
        if hero_cards:
            cards = hero_cards.split()
            if len(cards) >= 2:
                suit1 = cards[0][-1].lower()
                suit2 = cards[1][-1].lower()
                is_suited = (suit1 == suit2)
                rank_order = "AKQJT98765432"
                broadway_ranks = "AKQJT"
                r1, r2 = cards[0][:-1].upper(), cards[1][:-1].upper()
                is_pair = (r1 == r2)
                is_ax = (r1 == "A" or r2 == "A")
                is_broadway = (r1 in broadway_ranks and r2 in broadway_ranks)
                if r1 not in rank_order or r2 not in rank_order:
                    hand_type = f"{r1}{r2}{'s' if is_suited else 'o'}"
                else:
                    high, low = (r1, r2) if rank_order.index(r1) < rank_order.index(r2) else (r2, r1)
                    hand_type = f"{high}{low}{'s' if is_suited else 'o'}"
        
        # 7. 抓取底池大小 (GGPoker: "Total pot 1,250" / Demo: "collected 12000 from pot" or "won (40000)")
        pot_match = re.search(r"Total pot ([\d,]+)", full_hand_text)
        if pot_match:
            pot_size = int(pot_match.group(1).replace(",", ""))
        else:
            collected = re.search(r"collected ([\d,]+) from pot", full_hand_text)
            won = re.search(r"won \(([\d,]+)\)", full_hand_text)
            pot_size = int((collected or won).group(1).replace(",", "")) if (collected or won) else 0
        
        # 8. 精準抓取座位並用數學計算位置（完全移除 AI 對位置的解釋權）
        btn_match = re.search(r"The button is in seat #(\d+)", full_hand_text) or re.search(r"Seat #(\d+) is the button", full_hand_text)
        button_seat = int(btn_match.group(1)) if btn_match else None
        hero_seat_match = re.search(rf"Seat (\d+): {re.escape(current_hero)}\s", full_hand_text)
        hero_seat = int(hero_seat_match.group(1)) if hero_seat_match else None
        # GGPoker: "in chips" / Demo: "Seat 1: Hero (40000)"
        active_seats = list(set(int(m.group(1)) for m in re.finditer(r"Seat (\d+): .+\([\d,]+\)", full_hand_text)))
        if not active_seats:
            active_seats = list(set(int(m.group(1)) for m in re.finditer(r"Seat (\d+):", full_hand_text)))
        hero_position_str = calculate_position(hero_seat, button_seat, active_seats)
        hero_dist = distance_to_button(hero_seat, button_seat, active_seats)
        dist_to_name = {0: "BTN", 1: "SB", 2: "BB", 3: "UTG", 4: "UTG+1", 5: "MP", 6: "MP+1", 7: "CO"}
        position_name = dist_to_name.get(hero_dist, "Early") if hero_dist is not None else "Early"
        
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
        
        # 10. 輸贏結果偵測（Hero collected / won / matches → win；有 VPIP 未贏 → loss；未入池 → fold）
        hero_win_pattern = rf"{re.escape(current_hero)}\s+(collected|won|wins|matches)"
        if re.search(hero_win_pattern, full_hand_text, re.IGNORECASE):
            result = "win"
        elif is_vpip:
            result = "loss"
        else:
            result = "fold"
        
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
            "result": result,
            "bb_size": bb_size,
            "is_pair": is_pair,
            "is_ax": is_ax,
            "is_broadway": is_broadway,
            "position_name": position_name,
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
    
    prompt = f"""你是 Hero 的專屬撲克教練 "Poker Copilot"。
你的風格是：**先同理心 (Empathy)，再講邏輯 (Logic)，最後給建議 (Action)**。
你要像一個在牌桌旁看了 20 年牌的老手，說話犀利但有溫度，不要像機器人一樣背誦公式。

【時間線裁決 (CRITICAL TIMELINE RULE)】
你正在覆盤 Hero 的「當下決策」。
1. **嚴禁偷看未來**：當 Hero 行動時，排在 Hero 後面的玩家尚未行動。即使 Log 顯示他們後來 Call 了，你在分析當下必須假定他們動作未知。
2. **位置檢核**：嚴格確認 Hero 相對位置，不要混淆順序。

【一致性協議 (Consistency Protocol)】
你的分析必須具備「重現性」。對於同一手牌數據，必須給出相同的建議。
- 當遇到「邊緣決策 (Close Call)」時，請優先選擇 **GTO 頻率最高** 的選項，而不是隨機挑選「混合策略 (Mixed Strategy)」中的小頻率選項。
- 除非有明確的剝削理由（例如對手數據異常），否則一律以**標準 GTO 線路**為準。

【陷阱牌過濾機制 (Trap Hand Filter)】
5. **非同花人頭牌 (Offsuit Broadways)**（如 JTo, QJo, KJo, ATo）：
   - 在面對 UTG/EP 加注時，這些牌通常是被壓制 (Dominated) 的。
   - 即使底池賠率 (Pot Odds) 很好，也要考慮 **反向隱含賠率 (Reverse Implied Odds)**。
   - **預設動作**：除非是在 BTN/BB 且對手極弱，否則面對早位加注，優先建議 **棄牌 (Fold)**。
   - 不要因為「便宜」就建議跟注。便宜的代價往往是翻後輸掉更大的底池。

【語氣範例 (Few-Shot Examples) - 請模仿這種說話方式】

範例 1 (Hero 正確棄掉陷阱牌):
"一句話狠評：別被賠率騙了，這手牌是典型的捕鼠籠。
===SPLIT===
### 🧐 局勢解讀
我知道你在 BTN 拿到 JTo，前面有三個人入池，底池賠率看起來香得不得了，只要付一點點就能看翻牌。
但兄弟，這就是標準的『反向隱含賠率』陷阱！
UTG 的開牌範圍裡全是 AJ, KJ, QJ, AT，你的牌天生被壓制。如果你中了 J 或 T，你很難贏大底池，但很容易輸掉整疊籌碼。

### 💡 教練建議
GTO 在這裡是非常明確的：面對早位強勢加注，JTo 這種雜色牌就是直接棄掉 (Fold)。
省下的這 2BB，就是你未來的利潤。好棄牌！"

範例 2 (Hero 在錯誤的時機詐唬):
"一句話狠評：時機不對，泡沫期不要用邊緣牌對抗深籌碼。
===SPLIT===
### 🧐 局勢解讀
我很欣賞你這裡想要操作的心態，在泡沫期想用 A5s 偷雞，這個 aggressive 的想法是好的。
可惜這個對手是全場 Chip Leader，他跟注的範圍太寬了。根據死錢計算，你這裡的棄牌率 (Fold Equity) 不足以支持這次詐唬。

### 💡 教練建議
這不是你的錯，是時機不對。如果是決賽桌，這手牌就是神操作，但現在我們需要的是生存。下次這種邊緣牌，面對深籌碼還是穩一點好。"

範例 3 (Hero 打得好):
"一句話狠評：漂亮！精準利用了對手範圍過寬的弱點。
===SPLIT===
### 🧐 局勢解讀
這就是我要看到的打法！雖然 KJs 在這裡不是最強的牌，但你精準地判斷出 BB 位防守範圍過寬。
這個 Check-Raise 直接打斷了對手的節奏，完美的利用了位置優勢。

### 💡 教練建議
這手牌沒什麼好挑剔的，邏輯清晰，執行果斷。保持這種狀態，決賽桌就在前面了。"

---

【真實手牌數據】
{fact_sheet}

【手牌紀錄】
{hand_content}

---

【輸出格式】
0. **撲克牌**：提到撲克牌時一律使用 Emoji（如 A♥️, T♠️, K♣️），嚴禁純文字代碼。
1. **一句話狠評**：(模仿上面的語氣，直接點出關鍵)
2. ===SPLIT===
3. **Markdown 分析**：(包含「🧐 局勢解讀」與「💡 教練建議」兩個區塊，請用口語化解釋 EV 與範圍，不要機械式背誦定律)
"""
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1}
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
    # session_state：一鍵試用 Demo 模式
    if "use_demo" not in st.session_state:
        st.session_state.use_demo = False

    uploaded_file = st.file_uploader("📂 上傳比賽紀錄 (.txt)", type=["txt"])

    if uploaded_file:
        content = load_content(uploaded_file)
        st.session_state.use_demo = False
    elif st.session_state.use_demo:
        content = DEMO_HANDS_TEXT
        st.sidebar.warning("🦁 目前正在展示 Demo 牌譜 (共36手)")
    else:
        content = None
    
    # 主畫面大按鈕 (當沒有內容時顯示)
    if content is None:
        st.markdown("---")
        st.markdown("### 👋 歡迎來到 Poker Copilot")
        st.markdown("這是一個使用 AI 幫你覆盤撲克比賽的工具。你可以上傳 GG Poker 的手牌紀錄，或是...")
        
        col_demo_btn, _ = st.columns([1, 2])
        with col_demo_btn:
            if st.button("🎲 我沒檔案，先載入範例試玩看看", type="primary", key="main_demo_btn"):
                st.session_state.use_demo = True
                st.rerun()

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
                    # 進階篩選區：多重條件取交集
                    with st.expander("🔍 進階手牌篩選 (點擊展開)", expanded=True):
                        filter_option = st.selectbox(
                            "主要篩選",
                            ["全部", "💥 VPIP", "🏆 獲勝", "💸 落敗", "🔥 大底池 (>20BB)"],
                            index=0,
                            key="hand_filter"
                        )
                        if filter_option == "全部":
                            base_hands = hands
                        elif filter_option == "💥 VPIP":
                            base_hands = [h for h in hands if h.get("vpip")]
                        elif filter_option == "🏆 獲勝":
                            base_hands = [h for h in hands if h.get("result") == "win"]
                        elif filter_option == "💸 落敗":
                            base_hands = [h for h in hands if h.get("result") == "loss"]
                        else:
                            bb_size_default = 1
                            base_hands = [h for h in hands if (h.get("bb_size") or bb_size_default) and (h.get("pot_size", 0) > 20 * (h.get("bb_size") or bb_size_default))]
                        
                        card_type_options = ["對子 (Pair)", "Ax 牌型", "人頭大牌 (Broadway)"]
                        selected_card_types = st.multiselect("牌型篩選", card_type_options, default=[], key="card_type_filter")
                        position_options = ["BTN", "SB", "BB", "UTG", "MP", "CO"]
                        selected_positions = st.multiselect("位置篩選", position_options, default=[], key="position_filter")
                        
                        filtered_hands = base_hands
                        if selected_card_types:
                            def match_card_type(h):
                                if "對子 (Pair)" in selected_card_types and h.get("is_pair"):
                                    return True
                                if "Ax 牌型" in selected_card_types and h.get("is_ax"):
                                    return True
                                if "人頭大牌 (Broadway)" in selected_card_types and h.get("is_broadway"):
                                    return True
                                return False
                            filtered_hands = [h for h in filtered_hands if match_card_type(h)]
                        if selected_positions:
                            filtered_hands = [h for h in filtered_hands if h.get("position_name") in selected_positions]
                    
                    if not filtered_hands:
                        st.info("此分類無手牌")
                        hand_data = hands[0] if hands else {}
                    else:
                        def format_filtered_label(i):
                            hand = filtered_hands[i]
                            hand_num = hand.get("display_index", i + 1)
                            cards_display = cards_to_emoji(hand.get("hero_cards"))
                            return f"Hand #{hand_num}: {cards_display}"
                        
                        selected_index = st.radio(
                            "選擇手牌",
                            range(len(filtered_hands)),
                            format_func=format_filtered_label,
                            key="hand_radio"
                        )
                        hand_data = filtered_hands[selected_index]
                
                with col_detail:
                    # --- AI 分析區塊 (置頂) ---
                    st.markdown("### 🤖 AI 教練分析")
                    analyze_clicked = st.button(f"立即分析這手牌", key="analyze_btn", use_container_width=True)
                    
                    # --- 系統資訊 ---
                    sys_position = hand_data.get("position", "Other")
                    sys_cards = hand_data.get("hero_cards_emoji") or cards_to_emoji(hand_data.get("hero_cards"))
                    st.caption(f"📍 **系統判定**：位置 {sys_position} | 手牌 {sys_cards}")

                    # --- 執行分析 ---
                    if analyze_clicked:
                        with st.spinner(random.choice(LOADING_TEXTS)):
                            analysis = analyze_specific_hand(hand_data, api_key, selected_model)
                            st.markdown("### 💡 AI 分析結果")
                            parts = analysis.split("===SPLIT===")
                            summary_text = parts[0].strip() if parts else ""
                            detail_text = parts[1].strip() if len(parts) > 1 else ""
                            if summary_text and detail_text:
                                st.info(summary_text, icon="🦁")
                                st.markdown(detail_text)
                            else:
                                st.markdown(analysis)
                    else:
                        st.info("👆 點擊上方按鈕，查看教練建議")

                    # --- 手牌原始紀錄 (移到底部) ---
                    st.divider()
                    with st.expander("查看原始手牌紀錄"):
                        st.text(hand_data.get("content", ""))