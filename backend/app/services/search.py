"""F1 물가 검색: 영어/한국어 검색어를 price_stats 품목에 매칭한다.

수집 데이터(서울 생필품 가격)는 품목명이 한글뿐이고(name_en = name_ko, aliases 비어 있음)
"쌀(오대쌀) 10kg 1포"처럼 기본 품목명 + (세부 종류) + 규격 형태다.
그래서 기본 품목명(쌀)에 영어 이름과 동의어를 붙이는 사전을 코드에 둔다.
DB를 건드리지 않으므로 재수집해도 그대로 동작한다.
"""
import difflib
import re

# 기본 품목명(한글) → (영어 표시 이름, 검색 동의어들). 동의어는 소문자로 쓴다.
ITEM_DICT: dict[str, tuple[str, list[str]]] = {
    "간장": ("Soy sauce", ["soy sauce", "soysauce", "ganjang"]),
    "갈치": ("Hairtail fish", ["hairtail", "cutlassfish", "galchi", "fish"]),
    "감자": ("Potato", ["potato", "potatoes", "gamja"]),
    "계란": ("Eggs", ["egg", "eggs", "달걀", "gyeran"]),
    "고구마": ("Sweet potato", ["sweet potato", "sweet potatoes", "goguma"]),
    "고등어": ("Mackerel", ["mackerel", "godeungeo", "fish"]),
    "고추장": ("Gochujang (red pepper paste)", ["gochujang", "red pepper paste", "chili paste"]),
    "고춧가루": ("Gochugaru (red pepper powder)", ["gochugaru", "red pepper powder", "chili powder", "chili flakes"]),
    "골드키위": ("Gold kiwi", ["kiwi", "gold kiwi", "키위"]),
    "국수": ("Noodles (somyeon)", ["noodle", "noodles", "somyeon", "guksu"]),
    "굵은소금": ("Sea salt", ["salt", "sea salt", "소금"]),
    "귤": ("Tangerine", ["tangerine", "tangerines", "mandarin", "mandarins", "gyul"]),
    "김치": ("Kimchi", ["kimchi", "gimchi"]),
    "깐마늘": ("Peeled garlic", ["garlic", "마늘"]),
    "깻잎": ("Perilla leaves", ["perilla", "perilla leaves", "sesame leaves", "kkaennip"]),
    "꽈리고추": ("Shishito pepper", ["shishito", "shishito pepper", "pepper", "고추"]),
    "단감": ("Sweet persimmon", ["persimmon", "persimmons", "감"]),
    "닭고기": ("Chicken", ["chicken", "닭", "meat"]),
    "당근": ("Carrot", ["carrot", "carrots"]),
    "대파": ("Green onion", ["green onion", "scallion", "spring onion", "leek", "파"]),
    "돼지고기": ("Pork", ["pork", "돼지", "meat", "samgyeopsal", "삼겹살"]),
    "된장": ("Doenjang (soybean paste)", ["doenjang", "soybean paste", "miso"]),
    "두부": ("Tofu", ["tofu", "bean curd", "dubu"]),
    "라면": ("Ramyeon (instant noodles)", ["ramen", "ramyeon", "ramyun", "instant noodles", "noodles"]),
    "마른멸치": ("Dried anchovies", ["anchovy", "anchovies", "멸치"]),
    "마요네즈": ("Mayonnaise", ["mayo", "mayonnaise"]),
    "만두": ("Frozen dumplings", ["dumpling", "dumplings", "mandu"]),
    "맛김": ("Seasoned seaweed", ["seaweed", "laver", "gim", "kim", "김"]),
    "맥주": ("Beer", ["beer", "maekju"]),
    "명태": ("Pollock", ["pollock", "fish"]),
    "무": ("Korean radish", ["radish", "daikon", "mu"]),
    "밀가루": ("Flour", ["flour", "wheat flour"]),
    "바나나": ("Banana", ["banana", "bananas"]),
    "바디워시": ("Body wash", ["body wash", "bodywash", "shower gel"]),
    "방울토마토": ("Cherry tomatoes", ["cherry tomato", "cherry tomatoes", "tomato"]),
    "배": ("Korean pear", ["pear", "pears", "asian pear"]),
    "배추": ("Napa cabbage", ["napa cabbage", "kimchi cabbage", "chinese cabbage", "cabbage"]),
    "버섯": ("Mushroom", ["mushroom", "mushrooms"]),
    "복숭아": ("Peach", ["peach", "peaches"]),
    "부침가루": ("Korean pancake mix", ["pancake mix", "buchim"]),
    "붉은고추": ("Red chili pepper", ["red pepper", "chili", "chili pepper", "pepper", "고추"]),
    "브로콜리": ("Broccoli", ["broccoli"]),
    "비누": ("Soap", ["soap"]),
    "빵": ("Bread", ["bread", "bun", "buns"]),
    "사과": ("Apple", ["apple", "apples"]),
    "사이다": ("Lemon-lime soda (cider)", ["cider", "sprite", "soda", "lemon lime soda"]),
    "상추": ("Lettuce", ["lettuce", "sangchu"]),
    "새우": ("Shrimp", ["shrimp", "prawn", "prawns"]),
    "생수": ("Bottled water", ["water", "bottled water", "물"]),
    "샴푸": ("Shampoo", ["shampoo"]),
    "설탕": ("Sugar", ["sugar"]),
    "세제": ("Laundry detergent", ["detergent", "laundry detergent"]),
    "소고기": ("Beef", ["beef", "쇠고기", "meat", "hanwoo", "한우"]),
    "소시지": ("Sausage", ["sausage", "sausages"]),
    "소주": ("Soju", ["soju"]),
    "수박": ("Watermelon", ["watermelon"]),
    "시금치": ("Spinach", ["spinach"]),
    "식용유": ("Cooking oil", ["cooking oil", "oil", "vegetable oil"]),
    "식초": ("Vinegar", ["vinegar"]),
    "쌀": ("Rice", ["rice", "ssal"]),
    "애호박": ("Korean zucchini", ["zucchini", "squash", "호박"]),
    "양배추": ("Cabbage", ["cabbage"]),
    "양파": ("Onion", ["onion", "onions"]),
    "어묵": ("Fish cake", ["fish cake", "fishcake", "eomuk", "odeng", "오뎅"]),
    "오렌지": ("Orange", ["orange", "oranges"]),
    "오이": ("Cucumber", ["cucumber", "cucumbers"]),
    "오징어": ("Squid", ["squid", "ojingeo"]),
    "우유": ("Milk", ["milk"]),
    "조개": ("Clams", ["clam", "clams"]),
    "조기": ("Yellow croaker", ["croaker", "yellow croaker", "fish"]),
    "즉석밥": ("Instant rice", ["instant rice", "cooked rice", "hetbahn", "햇반", "rice"]),
    "참기름": ("Sesame oil", ["sesame oil", "oil"]),
    "참외": ("Korean melon", ["korean melon", "melon", "chamoe"]),
    "청양고추": ("Cheongyang hot pepper", ["cheongyang", "hot pepper", "pepper", "고추"]),
    "치약": ("Toothpaste", ["toothpaste"]),
    "치즈": ("Sliced cheese", ["cheese"]),
    "칫솔": ("Toothbrush", ["toothbrush", "toothbrushes"]),
    "컵라면": ("Cup noodles", ["cup noodles", "cup ramen", "cup ramyeon", "ramen", "noodles"]),
    "케찹": ("Ketchup", ["ketchup", "케첩"]),
    "콜라": ("Cola", ["cola", "coke", "coca cola"]),
    "콩": ("Soybeans", ["soybean", "soybeans", "beans"]),
    "콩나물": ("Bean sprouts", ["bean sprouts", "sprouts", "kongnamul"]),
    "토마토": ("Tomato", ["tomato", "tomatoes"]),
    "통조림": ("Canned", ["canned", "can", "tuna", "canned tuna", "참치"]),
    "파프리카": ("Bell pepper", ["paprika", "bell pepper", "pepper"]),
    "팥": ("Red beans", ["red bean", "red beans", "adzuki", "azuki", "beans"]),
    "포도": ("Grapes", ["grape", "grapes"]),
    "햄": ("Ham", ["ham", "spam", "스팸"]),
}

# 괄호 안 세부 종류 → 영어. 사전에 없으면 한글 그대로 둔다.
VARIANT_DICT: dict[str, str] = {
    "국산": "Korean", "수입": "imported", "수입산": "imported", "제주산": "Jeju",
    "냉동": "frozen", "생물": "fresh", "신선냉장": "chilled", "염장": "salted",
    "대": "large", "중": "medium", "소": "small",
    "가을": "fall", "봄": "spring", "여름": "summer",
    "부사": "Fuji", "홍로": "Hongro", "홍옥": "Hongok", "신고": "Singo",
    "밤고구마": "chestnut", "호박고구마": "pumpkin", "백도": "white", "황도": "yellow",
    "샤인머스켓": "Shine Muscat", "캠벨": "Campbell", "적상추": "red", "청상추": "green",
    "대하": "king prawn", "바지락": "Manila", "부세조기": "large", "참조기": "true",
    "새송이버섯": "king oyster", "다다기": "Dadagi", "천일염": "sun-dried", "참치": "tuna",
    "이천쌀": "Icheon", "오대쌀": "Odae", "붉은팥": "red", "1병": "",
}

# 외국인이 많이 찾지만 아직 데이터가 없는 외식 메뉴. 결과가 없을 때 "외식비는 아직 없음"을 안내한다.
RESTAURANT_TERMS = {
    "bibimbap", "비빔밥", "kimchi stew", "kimchi jjigae", "김치찌개", "naengmyeon", "냉면",
    "jajangmyeon", "jjajangmyeon", "짜장면", "자장면", "samgyetang", "삼계탕", "kalguksu", "칼국수",
    "kimbap", "gimbap", "김밥", "tteokbokki", "떡볶이", "fried chicken", "치킨", "bulgogi", "불고기",
    "americano", "아메리카노", "coffee", "커피", "latte", "라떼", "korean bbq", "bbq", "고기집",
    "subway", "지하철", "taxi", "택시", "bus", "버스", "t-money", "tmoney", "티머니",
}

_PAREN = re.compile(r"\(([^)]*)\)")
HANGUL = re.compile(r"[가-힣]")


def normalize(text: str) -> str:
    """소문자, 공백 하나로. 하이픈/언더스코어는 공백으로."""
    return re.sub(r"\s+", " ", re.sub(r"[-_]", " ", (text or "").lower())).strip()


def compact(text: str) -> str:
    """공백을 모두 뺀다. 띄어쓰기가 달라도 같은 말로 비교할 때 쓴다 ("김치 찌개" = "김치찌개").
    메뉴 수천 행마다 부르는 함수라 정규식 대신 split을 쓴다 (2배 이상 빠르다)."""
    return "".join(text.split())


def free_korean_term(query: str) -> str | None:
    """사전에 없을 때 이름에서 그대로 찾아볼 한글 검색어 (두 글자 이상). 없으면 None."""
    term = compact(normalize(query))
    return term if HANGUL.search(term) and len(term) >= 2 else None


def split_name(name_ko: str) -> tuple[str, list[str]]:
    """'오징어(국산, 냉동) 1마리' → ('오징어', ['국산', '냉동']). 규격은 버린다(unit에 따로 있음)."""
    variants = [v.strip() for m in _PAREN.findall(name_ko) for v in m.split(",") if v.strip()]
    base = re.split(r"[\s(]", name_ko.strip(), maxsplit=1)[0]
    return base, variants


def english_name(name_ko: str) -> str | None:
    base, variants = split_name(name_ko)
    entry = ITEM_DICT.get(base)
    if entry is None:
        return None
    parts = [VARIANT_DICT.get(v, v) for v in variants]
    parts = [p for p in parts if p]
    return f"{entry[0]} ({', '.join(parts)})" if parts else entry[0]


def _search_keys(item: dict) -> tuple[set[str], set[str]]:
    """(정확히 일치하면 높은 점수를 줄 키, 부분 일치에만 쓸 키). 모두 normalize 됨."""
    base, variants = split_name(item["name_ko"])
    # 한 글자 세부 종류(대/중/소)는 너무 흔해서 키로 쓰지 않는다
    exact = {normalize(base), *(normalize(v) for v in variants if len(v) >= 2)}
    entry = ITEM_DICT.get(base)
    if entry:
        exact.add(normalize(entry[0]))
        exact.update(normalize(a) for a in entry[1])
    exact.update(normalize(a) for a in item.get("aliases") or [])
    if item.get("name_en") and item["name_en"] != item["name_ko"]:
        exact.add(normalize(item["name_en"]))
    partial = {normalize(item["name_ko"]), *exact}
    return {k for k in exact if k}, {k for k in partial if k}


def score_item(query: str, item: dict) -> int:
    """0이면 매칭 안 됨. 높을수록 앞에 보여준다."""
    q = normalize(query)
    if not q:
        return 0
    qc = compact(q)
    base, _ = split_name(item["name_ko"])
    exact, partial = _search_keys(item)
    compact_exact = {compact(k) for k in exact}

    # 기본 품목명 자체와 일치 ("rice" → 쌀) 가 동의어 일치("rice" → 즉석밥)보다 앞에 오게 한다
    entry = ITEM_DICT.get(base)
    primary = {normalize(base)} | ({normalize(entry[0]), normalize(entry[1][0])} if entry else set())
    if q in primary or qc in {compact(p) for p in primary}:
        return 100
    if q in exact or qc in compact_exact:
        return 90
    if any(k.startswith(q) or compact(k).startswith(qc) for k in partial) and len(qc) >= 2:
        return 70
    if len(qc) >= 2 and any(qc in compact(k) for k in partial):
        return 50
    # "소주 한 병", "price of soju" 처럼 검색어 안에 품목명이 들어 있는 경우
    tokens = set(q.split())
    if any((k in tokens) or (len(compact(k)) >= 2 and compact(k) in qc and not k.isascii()) for k in exact):
        return 40
    return 0


def search_items(query: str, items: list[dict], limit: int = 20) -> list[dict]:
    scored = [(score_item(query, it), it) for it in items]
    hits = [(s, it) for s, it in scored if s > 0]
    hits.sort(key=lambda x: (-x[0], x[1]["name_ko"]))
    return [it for _, it in hits[:limit]]


def _jamo(text: str) -> str:
    """한글 음절을 초성·중성·종성 번호로 풀어서 오타 비교를 글자 단위보다 촘촘하게 한다 (맥쥬 ≈ 맥주)."""
    out = []
    for ch in text:
        code = ord(ch) - 0xAC00
        if 0 <= code < 11172:
            out.append(chr(0x1100 + code // 588) + chr(0x1161 + code % 588 // 28) + (chr(0x11A7 + code % 28) if code % 28 else ""))
        else:
            out.append(ch)
    return "".join(out)


def suggest(query: str, items: list[dict], n: int = 5) -> list[str]:
    """결과가 없을 때 오타 교정 후보 ("bananna" → "banana"). 품목마다 하나씩, 바로 검색할 수 있는 대표 검색어."""
    q = normalize(query)
    if not q:
        return []
    key_to_base: dict[str, str] = {}
    for it in items:
        base, _ = split_name(it["name_ko"])
        key_to_base.setdefault(normalize(base), base)
        entry = ITEM_DICT.get(base)
        if entry:
            for a in [entry[0], *entry[1]]:
                key_to_base.setdefault(normalize(a), base)
    by_jamo = {_jamo(k): k for k in key_to_base}
    out: list[str] = []
    for m in difflib.get_close_matches(_jamo(q), list(by_jamo), n=n * 3, cutoff=0.7):
        base = key_to_base[by_jamo[m]]
        entry = ITEM_DICT.get(base)
        label = entry[1][0] if entry and q.isascii() else base  # 영어로 찾았으면 영어로 제안
        if label not in out:
            out.append(label)
    return out[:n]


def is_restaurant_query(query: str) -> bool:
    q = normalize(query)
    qc = compact(q)
    return any(t == q or compact(t) == qc or (not t.isascii() and compact(t) in qc) for t in RESTAURANT_TERMS)
