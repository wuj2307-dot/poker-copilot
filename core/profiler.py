"""
[側寫師] (v2.3) 負責分析用戶習慣、讀寫 user_profiles.json。
"""
import json
from pathlib import Path

PROFILES_PATH = Path(__file__).resolve().parent.parent / "data" / "user_profiles.json"


def get_user_profile(user_id: str) -> dict:
    """讀取用戶畫像；若無則回傳空 dict。"""
    if not PROFILES_PATH.exists():
        return {}
    try:
        data = json.loads(PROFILES_PATH.read_text(encoding="utf-8"))
        return data.get(user_id, {})
    except Exception:
        return {}


def update_user_profile(user_id: str, updates: dict) -> None:
    """更新用戶畫像並寫入 data/user_profiles.json。"""
    data = {}
    if PROFILES_PATH.exists():
        try:
            data = json.loads(PROFILES_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    data[user_id] = {**data.get(user_id, {}), **updates}
    PROFILES_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROFILES_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
