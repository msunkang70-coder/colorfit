"""
classifier.py — 하이브리드 카테고리 분류 (키워드 + Gemini Flash 폴백)

1단계: 키워드 매칭 (~70%, 0원, <1ms)
2단계: LLM 캐시 조회 (<1ms)
3단계: Gemini Flash 실시간 분류 (~300ms, 극소수)
"""

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "backend" / "data"
LLM_CACHE_PATH = DATA_DIR / "llm_cache.json"

# ── 31개 카테고리 키워드 딕셔너리 ────────────────────────────

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    # Top (상의)
    "니트": ["니트", "스웨터", "풀오버", "캐시미어", "저지"],
    "셔츠": ["셔츠", "드레스셔츠", "옥스포드셔츠"],
    "블라우스": ["블라우스", "프릴블라우스"],
    "티셔츠": ["티셔츠", "반팔티", "프린트티", "그래픽티"],
    "맨투맨": ["맨투맨", "스웨트셔츠", "크루넥"],
    "후드": ["후드티", "후드", "후디", "후드집업"],
    "크롭탑": ["크롭", "크롭탑", "크롭티"],
    "반팔": ["반팔", "반팔셔츠", "반소매"],
    "머슬핏": ["머슬핏", "머슬티", "슬리브리스"],
    "탱크탑": ["탱크탑", "나시", "슬리브리스탑"],
    # Bottom (하의)
    "슬랙스": ["슬랙스", "드레스팬츠", "정장바지", "테일러드팬츠"],
    "청바지": ["청바지", "데님", "진", "데님팬츠"],
    "스커트": ["스커트", "미니스커트", "롱스커트", "플리츠스커트", "미디스커트"],
    "와이드팬츠": ["와이드팬츠", "와이드", "와이드핏"],
    "레깅스": ["레깅스", "요가팬츠", "스포츠레깅스"],
    "숏팬츠": ["숏팬츠", "반바지", "숏츠", "쇼트팬츠"],
    "조거팬츠": ["조거팬츠", "조거", "트레이닝팬츠", "트레이닝바지"],
    "치노": ["치노", "치노팬츠", "면바지"],
    # Outer (아우터)
    "자켓": ["자켓", "재킷", "블레이저"],
    "코트": ["코트", "트렌치코트", "울코트", "롱코트", "핸드메이드코트"],
    "패딩": ["패딩", "다운자켓", "푸퍼", "패딩조끼"],
    "가디건": ["가디건", "카디건"],
    "점퍼": ["점퍼", "바람막이", "윈드브레이커", "아노락"],
    # Onepiece
    "원피스": ["원피스", "드레스", "롱원피스", "미니원피스", "셔츠원피스"],
    # Shoes (신발)
    "로퍼": ["로퍼", "페니로퍼", "드라이빙슈즈"],
    "스니커즈": ["스니커즈", "운동화", "캔버스화", "러닝화"],
    "힐": ["힐", "하이힐", "펌프스", "뮬", "킬힐"],
    "부츠": ["부츠", "앵클부츠", "첼시부츠", "워커", "롱부츠"],
    "샌들": ["샌들", "슬리퍼", "플립플롭", "뮬샌들"],
    # Bag (가방)
    "토트백": ["토트백", "토트", "쇼퍼백"],
    "크로스백": ["크로스백", "숄더백", "미니백", "클러치", "체인백", "백팩"],
}

# ── 실루엣 키워드 ───────────────────────────────────────────

SILHOUETTE_KEYWORDS: dict[str, list[str]] = {
    "oversized": ["오버사이즈", "오버핏", "루즈핏", "박시"],
    "slim": ["슬림", "슬림핏", "스키니", "타이트"],
    "fitted": ["피티드", "핏티드", "바디핏", "머슬핏"],
    "wide": ["와이드", "와이드핏", "세미와이드"],
    "regular": ["레귤러", "레귤러핏", "스탠다드핏"],
}

# ── 포멀도 매핑 ─────────────────────────────────────────────

FORMALITY_MAP: dict[str, int] = {
    # 1 = 스포츠/애슬레저
    "레깅스": 1, "숏팬츠": 1, "조거팬츠": 1, "크롭탑": 1,
    "머슬핏": 1, "탱크탑": 1,
    # 2 = 캐주얼
    "청바지": 2, "티셔츠": 2, "맨투맨": 2, "후드": 2,
    "스니커즈": 2, "반팔": 2, "점퍼": 2, "샌들": 2,
    # 3 = 스마트캐주얼
    "니트": 3, "치노": 3, "가디건": 3, "로퍼": 3,
    "와이드팬츠": 3, "토트백": 3, "크로스백": 3, "부츠": 3,
    # 4 = 비즈니스캐주얼
    "셔츠": 4, "블라우스": 4, "슬랙스": 4, "자켓": 4,
    "스커트": 4, "코트": 4,
    # 5 = 포멀
    "힐": 5, "원피스": 4, "패딩": 2,
}

# ── 성별 키워드 ─────────────────────────────────────────────

GENDER_FEMALE_KEYWORDS = [
    "여성", "우먼", "레이디", "걸", "미시", "여자",
    "블라우스", "스커트", "원피스", "힐", "크롭탑",
]
GENDER_MALE_KEYWORDS = [
    "남성", "맨즈", "남자", "보이",
]


# ── 키워드 기반 분류 (1단계) ────────────────────────────────

def classify_by_keyword(name: str, cat_hint: str = "") -> dict | None:
    """
    키워드 기반으로 분류한다. 매칭 실패 시 None 반환.

    Returns:
        {"category", "silhouette", "formality", "gender", "tpo"} or None
    """
    text = (name + " " + cat_hint).lower()

    # 카테고리
    category = None
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                category = cat
                break
        if category:
            break

    if category is None:
        return None

    # 실루엣
    silhouette = "regular"
    for sil, keywords in SILHOUETTE_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                silhouette = sil
                break

    # 포멀도
    formality = FORMALITY_MAP.get(category, 3)

    # 성별
    gender = "unisex"
    for kw in GENDER_FEMALE_KEYWORDS:
        if kw in text:
            gender = "female"
            break
    if gender == "unisex":
        for kw in GENDER_MALE_KEYWORDS:
            if kw in text:
                gender = "male"
                break

    # TPO (간이 매핑)
    tpo = _infer_tpo(category, formality, text)

    return {
        "category": category,
        "silhouette": silhouette,
        "formality": formality,
        "gender": gender,
        "tpo": tpo,
    }


def _infer_tpo(category: str, formality: int, text: str) -> list[str]:
    """카테고리와 포멀도 기반으로 TPO를 추론한다."""
    tpo = []
    if formality >= 4:
        tpo.extend(["commute", "interview"])
    if formality >= 3:
        tpo.append("date")
    if formality <= 2:
        tpo.extend(["weekend", "campus"])
    if formality == 1:
        tpo.append("workout")
    if "여행" in text or "트래블" in text:
        tpo.append("travel")
    if "행사" in text or "하객" in text or "웨딩" in text:
        tpo.append("event")
    return list(set(tpo)) or ["casual"]


# ── LLM 캐시 (2단계) ───────────────────────────────────────

_llm_cache: dict | None = None


def _load_llm_cache() -> dict:
    global _llm_cache
    if _llm_cache is not None:
        return _llm_cache
    if LLM_CACHE_PATH.exists():
        with open(LLM_CACHE_PATH, "r", encoding="utf-8") as f:
            _llm_cache = json.load(f)
    else:
        _llm_cache = {}
    return _llm_cache


def _save_llm_cache():
    if _llm_cache is not None:
        with open(LLM_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(_llm_cache, f, ensure_ascii=False, indent=2)


def lookup_cache(product_id: str) -> dict | None:
    """LLM 캐시에서 분류 결과를 조회한다."""
    cache = _load_llm_cache()
    return cache.get(product_id)


def store_cache(product_id: str, result: dict):
    """LLM 분류 결과를 캐시에 저장한다."""
    cache = _load_llm_cache()
    cache[product_id] = result
    _save_llm_cache()


# ── Gemini Flash 분류 (3단계) ───────────────────────────────

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

CLASSIFY_PROMPT = """다음 패션 상품을 분류해주세요.

상품명: {name}
카테고리 힌트: {cat_hint}

아래 JSON 형식으로만 응답해주세요:
{{
  "category": "31종 중 하나 (니트/셔츠/블라우스/티셔츠/맨투맨/후드/크롭탑/반팔/머슬핏/탱크탑/슬랙스/청바지/스커트/와이드팬츠/레깅스/숏팬츠/조거팬츠/치노/자켓/코트/패딩/가디건/점퍼/원피스/로퍼/스니커즈/힐/부츠/샌들/토트백/크로스백)",
  "silhouette": "oversized/slim/fitted/wide/regular 중 하나",
  "formality": 1~5 (1=스포츠, 2=캐주얼, 3=스마트캐주얼, 4=비즈니스캐주얼, 5=포멀),
  "gender": "female/male/unisex 중 하나",
  "tpo": ["해당 TPO 리스트 (commute/date/interview/weekend/campus/travel/event/workout)"]
}}"""


def classify_by_gemini(name: str, cat_hint: str = "") -> dict | None:
    """Gemini Flash API로 분류한다. API 키가 없으면 None 반환."""
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY 미설정. LLM 분류 건너뜀.")
        return None

    try:
        import google.generativeai as genai

        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")

        prompt = CLASSIFY_PROMPT.format(name=name, cat_hint=cat_hint)
        response = model.generate_content(prompt)

        text = response.text.strip()
        # JSON 블록 추출
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        return json.loads(text)
    except Exception as e:
        logger.error("Gemini 분류 실패: %s — %s", name, e)
        return None


# ── 하이브리드 분류 메인 ────────────────────────────────────

def classify_product(
    product_id: str,
    name: str,
    cat_hint: str = "",
    use_llm: bool = True,
) -> dict:
    """
    하이브리드 분류: 키워드 → 캐시 → Gemini 순으로 시도.

    Returns:
        {"category", "silhouette", "formality", "gender", "tpo", "_method"}
    """
    # 1단계: 키워드
    result = classify_by_keyword(name, cat_hint)
    if result:
        result["_method"] = "keyword"
        return result

    # 2단계: LLM 캐시
    cached = lookup_cache(product_id)
    if cached:
        cached["_method"] = "cache"
        return cached

    # 3단계: Gemini
    if use_llm:
        llm_result = classify_by_gemini(name, cat_hint)
        if llm_result:
            store_cache(product_id, llm_result)
            llm_result["_method"] = "gemini"
            return llm_result

    # 폴백: 미분류
    return {
        "category": "unknown",
        "silhouette": "regular",
        "formality": 3,
        "gender": "unisex",
        "tpo": ["casual"],
        "_method": "fallback",
    }
