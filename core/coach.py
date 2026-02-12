"""
[教練大腦] 負責跟 LLM 溝通、處理 Prompt。
"""
import json
import requests
from pathlib import Path

from .parser import cards_to_emoji

# 策略檔路徑：專案根目錄
_STRATEGY_FILE = Path(__file__).resolve().parent.parent / "poker_strategy_bible.txt"
if not _STRATEGY_FILE.exists():
    _STRATEGY_FILE = Path(__file__).resolve().parent.parent / "poker_strategy_bible"


def _load_strategy_logic():
    try:
        return _STRATEGY_FILE.read_text(encoding="utf-8")
    except Exception:
        return "（策略檔案未找到，使用預設邏輯）"


def generate_match_summary(hands_data, vpip, pfr, api_key, model):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    total_hands = len(hands_data)
    vpip_count = sum(1 for h in hands_data if h.get("vpip"))
    pfr_count = sum(1 for h in hands_data if h.get("pfr"))
    agg_freq = round((pfr_count / vpip_count) * 100, 1) if vpip_count > 0 else 0.0
    POS_GROUPS = {
        "BTN": ["BTN"], "SB": ["SB"], "BB": ["BB"],
        "EP": ["UTG", "UTG+1"], "MP": ["MP", "MP+1", "HJ"], "CO": ["CO"],
    }

    def calc_pos_stats(pos_keys):
        hands_in_pos = [h for h in hands_data if h.get("position") in pos_keys or h.get("position_name") in pos_keys]
        n = len(hands_in_pos)
        if n == 0:
            return "N/A", "N/A", 0
        v = sum(1 for h in hands_in_pos if h.get("vpip"))
        p = sum(1 for h in hands_in_pos if h.get("pfr"))
        vpip_pct = round((v / n) * 100, 1)
        pfr_pct = round((p / n) * 100, 1)
        return vpip_pct, pfr_pct, n

    vpip_btn, pfr_btn, _ = calc_pos_stats(POS_GROUPS["BTN"])
    vpip_sb, pfr_sb, _ = calc_pos_stats(POS_GROUPS["SB"])
    vpip_bb, pfr_bb, _ = calc_pos_stats(POS_GROUPS["BB"])
    vpip_ep, pfr_ep, _ = calc_pos_stats(POS_GROUPS["EP"])
    vpip_mp, pfr_mp, _ = calc_pos_stats(POS_GROUPS["MP"])
    vpip_co, pfr_co, _ = calc_pos_stats(POS_GROUPS["CO"])

    def fmt_pos(vpip_val, pfr_val):
        if vpip_val == "N/A" or pfr_val == "N/A":
            return "N/A"
        return f"VPIP {vpip_val}% / PFR {pfr_val}%"

    key_hands_raw = [h for h in hands_data if h.get("vpip")]
    key_hands_raw.sort(key=lambda h: h.get("pot_size", 0), reverse=True)
    key_hands = key_hands_raw[:5]
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
- 總手牌數: {total_hands}
- VPIP: {vpip:.1f}% | PFR: {pfr:.1f}% | Agg: {agg_freq:.1f}%

【位置別數據 (Positional Stats)】
- BTN: {fmt_pos(vpip_btn, pfr_btn)}
- SB:  {fmt_pos(vpip_sb, pfr_sb)}
- BB:  {fmt_pos(vpip_bb, pfr_bb)}
- EP:  {fmt_pos(vpip_ep, pfr_ep)}
- MP:  {fmt_pos(vpip_mp, pfr_mp)}
- CO:  {fmt_pos(vpip_co, pfr_co)}

【關鍵手牌（共 5 手，依底池大小選出）】
以下手牌編號為 Hand #數字，與使用者介面列表完全對應。請依此編號引用，勿使用 TM 等原始 ID。手牌已標註 (Suited) 或 (Offsuit)，請依此解讀花色。

{key_hands_text}

---

【輸出格式】請務必依以下三個區塊、用 Markdown 撰寫：

## 🎯 賽事回顧
請寫一段約 150～200 字的完整段落，像賽後新聞稿一樣，專業地總結選手的風格（鬆/緊、被動/激進）以及本場比賽的主要漏洞。**務必結合「位置別數據」指出特定位置的漏洞**（例如 BB 防守過緊、BTN 開池過少等）。不要只寫一句話。

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
    except Exception:
        return "AI 連線失敗，請檢查 API Key 或稍後再試。"


def analyze_specific_hand(hand_data, api_key, model):
    """
    傳入完整 hand_data；花色與位置由系統事實強制注入，AI 無解釋權。
    """
    strategy_logic = _load_strategy_logic()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    hero_cards_emoji = hand_data.get("hero_cards_emoji") or cards_to_emoji(hand_data.get("hero_cards"))
    hero_position = hand_data.get("position", "Other")
    bb_count = hand_data.get("bb", 0)
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

【深層戰術意識 (INTERNAL KNOWLEDGE)】
以下是你過去 20 年職業生涯累積的深層撲克知識。請將這些原則內化為你的直覺。
**⚠️ 風格嚴格限制 (STYLE RULES)：**
1. **嚴禁引用來源**：絕對不要說「根據戰術守則...」、「依照第一章...」或「講義上說...」。
2. **轉化為專家口吻**：你必須把理論轉化為你的個人見解。
   - ❌ 錯誤示範：「根據文件第 2 條，乾燥面應該下注 33%。」
   - ✅ 正確示範：「在這種乾燥牌面，對手很難擊中，我們輕輕打個 1/3 底池，既便宜又能給壓力，這才是標準打法。」
3. **權威感**：如果 Hero 犯錯，直接用你的觀點指出，例如「這裡平跟是大忌」，而不是「規則說不能平跟」。

[知識內容開始]
{strategy_logic}
[知識內容結束]

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
        return raw_text
    except Exception as e:
        return f"分析失敗: {str(e)}"
