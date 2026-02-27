"""Category classification"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

RULES_PATH = Path(__file__).resolve().parent / "category_rules.json"
DEFAULT_CATEGORY = "other"


@lru_cache(maxsize=1)
def load_rules() -> dict[str, dict[str, list[str]]]:
    """
    카테고리 룰을 불러와서 사용가능 형태로 변경

    JSON shapes:
    - {"food": ["apple", "bread"]}  # legacy
    - {"food": {"word_keywords": [...], "meaning_keywords": [...]}}
    """
    raw = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    normalized: dict[str, dict[str, list[str]]] = {}

    for category, config in raw.items():
        if isinstance(config, list):
            normalized[category] = {
                "word_keywords": [str(item) for item in config],
                "meaning_keywords": [],
            }
        elif isinstance(config, dict):
            normalized[category] = {
                "word_keywords": [str(item) for item in config.get("word_keywords", [])],
                "meaning_keywords": [str(item) for item in config.get("meaning_keywords", [])],
            }

    return normalized


def get_rule_category_names() -> list[str]:
    """사전 정의된 카테고리 이름 불러오기"""
    return list(load_rules().keys())


def _normalize_text(text: str | None) -> str:
    """텍스트 정제"""
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\uac00-\ud7a3\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _keywords(config: dict[str, list[str]], key: str) -> list[str]:
    """탐색가능한 키워드 형태"""
    return [kw for kw in (_normalize_text(item) for item in config.get(key, [])) if kw]


def _score_by_keywords(text: str, keywords: list[str], weight: int = 1) -> int:
    """유사도 매칭"""
    if not text or not keywords:
        return 0

    score = 0
    for keyword in keywords:
        if keyword and keyword in text:
            score += max(len(keyword), 1) * weight
    return score


def classify_word(word_text: str, meaning_text: str | None) -> str:
    """
    1) 한국어 의미
    2) 키워드 매칭
    3) "other" fallback
    """
    rules = load_rules()
    normalized_word = _normalize_text(word_text)
    normalized_meaning = _normalize_text(meaning_text)

    best_category: str | None = None
    best_score = 0

    for category, config in rules.items():
        meaning_keywords = _keywords(config, "meaning_keywords")
        word_keywords = _keywords(config, "word_keywords")

        meaning_score = _score_by_keywords(normalized_meaning, meaning_keywords, weight=3)
        word_score = _score_by_keywords(normalized_word, word_keywords, weight=1)

        if normalized_word in word_keywords:
            word_score += 30

        total_score = meaning_score + word_score
        if total_score > best_score:
            best_score = total_score
            best_category = category

    return best_category if best_score > 0 else DEFAULT_CATEGORY
