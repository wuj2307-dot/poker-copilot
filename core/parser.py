"""
[搬運工] 負責解析 PokerStars/GG 格式的手牌文字。
"""
import re
import html
import streamlit as st


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
        'h': '♥️', 'd': '♦️', 'c': '♣️', 's': '♠️'
    }
    cards = cards_str.split()
    emoji_cards = []
    for card in cards:
        if len(card) >= 2:
            rank = card[:-1]
            suit = card[-1].lower()
            emoji_cards.append(f"{rank}{suit_map.get(suit, suit)}")
    return " ".join(emoji_cards)


SUIT_EMOJI = {'c': '♣️', 's': '♠️', 'h': '♥️', 'd': '♦️'}


def _card_badge(card_str):
    """單張牌 → 帶顏色的 HTML badge。紅心/方塊紅，黑桃/梅花灰藍。"""
    card_str = card_str.strip()
    if len(card_str) < 2:
        return ""
    rank, suit = card_str[:-1], card_str[-1].lower()
    if suit in ("h", "d"):
        color, border = "#e74c3c", "#c0392b"
    else:
        color, border = "#3498db", "#2980b9"
    emoji = SUIT_EMOJI.get(suit, "")
    label = html.escape(f"{rank}{emoji}")
    return f'<span class="timeline-card" style="background:{color};border-color:{border}">{label}</span>'


def _card_badge_chat(card_str):
    """單張牌 → 聊天風格 HTML badge。"""
    card_str = card_str.strip()
    if len(card_str) < 2:
        return ""
    rank, suit = card_str[:-1], card_str[-1].lower()
    cls = "card-badge-chat red" if suit in ("h", "d") else "card-badge-chat black"
    emoji = SUIT_EMOJI.get(suit, "")
    label = html.escape(f"{rank}{emoji}")
    return f'<span class="{cls}">{label}</span>'


def calculate_position(hero_seat, button_seat, total_seats):
    """
    數學定義位置：依順時針距離 Button 計算。
    0=BTN, 1=SB, 2=BB, 3=UTG, ...
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
    """順時針距離 Button 的步數（0=BTN, 1=SB, ...）。"""
    if not total_seats or seat is None or button_seat is None or seat not in total_seats or button_seat not in total_seats:
        return None
    sorted_seats = sorted([int(s) for s in total_seats])
    n = len(sorted_seats)
    btn_idx = sorted_seats.index(int(button_seat))
    seat_idx = sorted_seats.index(int(seat))
    return (seat_idx - btn_idx) % n


def render_hand_history_timeline(hand_content, hero_name="Hero"):
    """
    將手牌 log 解析為「聊天介面」風格：只顯示重要下注與公牌。
    """
    if not hand_content or not hand_content.strip():
        st.caption("無手牌內容")
        return
    level_match = re.search(r"Level(\d+)\(([\d,]+)/([\d,]+)\)", hand_content)
    if level_match:
        level_num = level_match.group(1)
        sb_str = level_match.group(2).replace(",", "")
        bb_str = level_match.group(3).replace(",", "")
        bb_size = int(bb_str) if bb_str else 400
        header_text = f"🏆 Level: {level_num} | Blinds: {sb_str}/{bb_str}"
    else:
        bb_fallback = re.search(r"posts big blind ([\d,]+)", hand_content)
        bb_size = int(bb_fallback.group(1).replace(",", "")) if bb_fallback else 400
        header_text = f"🏆 Blinds: —/{bb_size}"
    btn_match = re.search(r"Seat #(\d+) is the button", hand_content)
    button_seat = int(btn_match.group(1)) if btn_match else None
    seats_dict = {}
    for m in re.finditer(r"Seat (\d+): (\S+)", hand_content):
        sn, pid = m.group(1), m.group(2)
        if sn not in seats_dict:
            seats_dict[sn] = pid
    total_seats = sorted([int(s) for s in seats_dict.keys()]) if seats_dict else []
    id_to_position = {}
    for sn in total_seats:
        pid = seats_dict[str(sn)]
        id_to_position[pid] = calculate_position(sn, button_seat, total_seats)
    id_to_position[hero_name] = "Hero"

    def to_bb(amount_str):
        try:
            return int(amount_str.replace(",", "")) / bb_size if bb_size else 0
        except (ValueError, AttributeError):
            return 0

    def format_action_bb(line):
        line = re.sub(
            r"raises ([\d,]+) to ([\d,]+)( and is all-in)?",
            lambda m: f"raises {to_bb(m.group(1)):.1f} to {to_bb(m.group(2)):.1f} BB" + (m.group(3) or ""),
            line,
        )
        line = re.sub(r"bets ([\d,]+)", lambda m: f"bets {to_bb(m.group(1)):.1f} BB", line)
        line = re.sub(
            r"calls ([\d,]+)( and is all-in)?",
            lambda m: f"calls {to_bb(m.group(1)):.1f} BB" + (m.group(2) or ""),
            line,
        )
        return line

    def replace_speaker_with_position(line):
        if ": " not in line:
            return line
        speaker, rest = line.split(": ", 1)
        speaker = speaker.strip()
        pos = id_to_position.get(speaker, speaker)
        return f"{pos}: {rest}"

    IGNORE_SUBSTRINGS = [
        "posts the ante", "in chips", "returned to", "collected", "summary",
        "table", "seat", "posts small blind", "posts big blind", "Dealt to",
        "Uncalled", "Total pot", "Board ", "Seat ", "shows ", "won (",
        "and lost", "and won", "folded before", "folded on",
    ]

    def should_ignore_line(line):
        low = line.lower()
        return any(sub.lower() in low for sub in IGNORE_SUBSTRINGS)

    def is_hero_line(line):
        return line.strip().startswith(hero_name + ":")

    def is_active_action(line):
        if "folds" in line:
            return is_hero_line(line)
        return any(verb in line for verb in ("bets", "calls", "raises", "checks", "all-in"))

    parts = re.split(r"\n\s*\*\*\* (HOLE CARDS|FLOP|TURN|RIVER|SHOWDOWN|SUMMARY) \*\*\*\s*\n?", hand_content)
    segments = []
    for i in range(1, len(parts) - 1, 2):
        if i + 1 < len(parts):
            street_name = parts[i].strip()
            body = (parts[i + 1] or "").strip()
            segments.append((street_name, body))

    out = ['<div class="hand-chat-container">']
    out.append(f'<div class="hand-chat-header">{html.escape(header_text)}</div>')
    for street_name, body in segments:
        if street_name in ("SHOWDOWN", "SUMMARY"):
            continue
        lines = [ln.strip() for ln in body.split("\n") if ln.strip()]
        first_line = lines[0] if lines else ""
        start_idx = 0
        if street_name in ("FLOP", "TURN", "RIVER"):
            board_cards = re.findall(r"\[([A-Za-z0-9\s]+)\]", first_line)
            if board_cards:
                out.append('<div class="hand-chat-street-badge">')
                out.append(f'<div class="street-label">*** {street_name} ***</div>')
                out.append('<div class="street-cards">')
                for bracket in board_cards:
                    for card in bracket.split():
                        if re.match(r"^[AKQJT2-9][hdcs]$", card, re.IGNORECASE):
                            out.append(_card_badge_chat(card))
                out.append("</div></div>")
                start_idx = 1
        for line in lines[start_idx:]:
            if should_ignore_line(line) or not is_active_action(line):
                continue
            line = replace_speaker_with_position(line)
            line = format_action_bb(line)
            line_safe = html.escape(line)
            is_hero = line.strip().startswith("Hero:")
            bubble_cls = "hand-chat-bubble chat-right" if is_hero else "hand-chat-bubble chat-left"
            out.append(f'<div class="{bubble_cls}">{line_safe}</div>')
    out.append("</div>")
    st.markdown("".join(out), unsafe_allow_html=True)


def parse_hands(content):
    """
    專為 GGPoker 格式設計的手牌解析器。
    """
    raw_hands = re.split(r"(?=Poker Hand #)", content)
    parsed_hands = []
    detected_hero = None
    for raw_hand in raw_hands:
        if not raw_hand.strip() or len(raw_hand) < 100:
            continue
        full_hand_text = raw_hand.strip()
        hand_id_match = re.search(r"Poker Hand #(TM\d+|[A-Za-z0-9_]+):", full_hand_text)
        hand_id = hand_id_match.group(1) if hand_id_match else "Unknown"
        bb_size_match = re.search(r"Level\d+\([\d,]+/([\d,]+)\)", full_hand_text)
        if bb_size_match:
            bb_size = int(bb_size_match.group(1).replace(",", ""))
        else:
            bb_fallback = re.search(r"posts big blind ([\d,]+)", full_hand_text)
            bb_size = int(bb_fallback.group(1).replace(",", "")) if bb_fallback else 400
        hero_match = re.search(r"Dealt to (\S+) \[([A-Za-z0-9]{2} [A-Za-z0-9]{2})\]", full_hand_text)
        current_hero = hero_match.group(1) if hero_match else None
        hero_cards = hero_match.group(2) if hero_match else None
        if current_hero and detected_hero is None:
            detected_hero = current_hero
        if not current_hero:
            continue
        stack_pattern = rf"Seat \d+: {re.escape(current_hero)} \(([\d,]+)(?: in chips)?\)"
        stack_match = re.search(stack_pattern, full_hand_text)
        hero_chips = int(stack_match.group(1).replace(",", "")) if stack_match else 0
        bb_count = round(hero_chips / bb_size, 1) if bb_size > 0 else 0
        preflop_text = full_hand_text.split("*** FLOP ***")[0] if "*** FLOP ***" in full_hand_text else full_hand_text
        is_vpip = False
        is_pfr = False
        hero_escaped = re.escape(current_hero)
        if re.search(rf"^{hero_escaped}: (raises|calls|bets)", preflop_text, re.MULTILINE):
            is_vpip = True
        if re.search(rf"^{hero_escaped}: raises", preflop_text, re.MULTILINE):
            is_pfr = True
        is_suited = False
        hand_type = None
        is_pair = False
        is_ax = False
        is_broadway = False
        if hero_cards:
            cards = hero_cards.split()
            if len(cards) >= 2:
                suit1, suit2 = cards[0][-1].lower(), cards[1][-1].lower()
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
        pot_match = re.search(r"Total pot ([\d,]+)", full_hand_text)
        if pot_match:
            pot_size = int(pot_match.group(1).replace(",", ""))
        else:
            collected = re.search(r"collected ([\d,]+) from pot", full_hand_text)
            won = re.search(r"won \(([\d,]+)\)", full_hand_text)
            pot_size = int((collected or won).group(1).replace(",", "")) if (collected or won) else 0
        btn_match = re.search(r"The button is in seat #(\d+)", full_hand_text) or re.search(r"Seat #(\d+) is the button", full_hand_text)
        button_seat = int(btn_match.group(1)) if btn_match else None
        hero_seat_match = re.search(rf"Seat (\d+): {re.escape(current_hero)}\s", full_hand_text)
        hero_seat = int(hero_seat_match.group(1)) if hero_seat_match else None
        active_seats = list(set(int(m.group(1)) for m in re.finditer(r"Seat (\d+):", full_hand_text)))
        hero_position_str = calculate_position(hero_seat, button_seat, active_seats)
        hero_dist = distance_to_button(hero_seat, button_seat, active_seats)
        dist_to_name = {0: "BTN", 1: "SB", 2: "BB", 3: "UTG", 4: "UTG+1", 5: "MP", 6: "MP+1", 7: "CO"}
        position_name = dist_to_name.get(hero_dist, "Early") if hero_dist is not None else "Early"
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
                                relative_pos_str = "In Position (IP)"
                            elif villain_dist == 0:
                                relative_pos_str = "Out of Position (OOP)"
                            elif hero_dist > villain_dist:
                                relative_pos_str = "In Position (IP)"
                            else:
                                relative_pos_str = "Out of Position (OOP)"
                    else:
                        relative_pos_str = "N/A (無法判定主要對手座位)"
                else:
                    relative_pos_str = "N/A (無法判定主要對手座位)"
        else:
            relative_pos_str = "多路底池 (無人加注)"
        hero_cards_emoji = "Unknown"
        if hero_cards:
            parts = hero_cards.split()
            emoji_parts = [f"{c[:-1]}{SUIT_EMOJI.get(c[-1].lower(), c[-1])}" for c in parts if len(c) >= 2]
            hero_cards_emoji = " ".join(emoji_parts) if emoji_parts else "Unknown"
        hero_win_pattern = rf"{re.escape(current_hero)}\s+(collected|won|wins|matches)"
        if re.search(hero_win_pattern, full_hand_text, re.IGNORECASE):
            result = "win"
        elif is_vpip:
            result = "loss"
        else:
            result = "fold"
        is_winner = (result == "win")
        total_pot = pot_size
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
            "is_winner": is_winner,
            "total_pot": total_pot,
            "bb_size": bb_size,
            "is_pair": is_pair,
            "is_ax": is_ax,
            "is_broadway": is_broadway,
            "position_name": position_name,
        })
    return parsed_hands, detected_hero
