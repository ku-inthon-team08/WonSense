"""F1 물가 검색의 마트·편의점 공산품 부분: 검색어를 product_prices의 상품명에 매칭한다.

상품명은 "참이슬 후레쉬(360ml)", "농심 신라면 큰사발면(114g)"처럼 브랜드 + 규격 형태의 한글이다.
외국인은 "soju", "beer", "toothpaste"처럼 종류로 찾으므로, 종류마다 영어·한국어 검색어와
상품명 패턴(정규식)을 둔다. 사전에 없는 한글 검색어는 상품명에 그대로 들어 있으면 보여준다 (예: 신라면).
"""
import re

from app.services.search import normalize

# (영어 표시 이름, 영어 검색어, 한국어 검색어, 상품명에 맞으면 포함할 패턴, 맞으면 뺄 패턴)
CONCEPTS: list[tuple[str, list[str], list[str], list[str], list[str]]] = [
    ("Soju", ["soju", "chamisul", "jinro", "chum churum"], ["소주", "참이슬", "처음처럼"], [r"^참이슬", r"^처음처럼", r"^진로", r"소주"], []),
    ("Beer", ["beer", "cass", "terra", "hite", "lager", "ale"], ["맥주"], [r"^카스 ", r"^테라\(", r"^하이트", r"에일\(", r"맥주"], []),
    ("Makgeolli (rice wine)", ["makgeolli", "rice wine"], ["막걸리"], [r"막걸리", r"우국생"], []),
    ("Bottled water", ["water", "bottled water", "samdasoo", "mineral water"], ["물", "생수"], [r"^삼다수", r"^아이시스", r"생수"], []),
    ("Sparkling water", ["sparkling water", "soda water", "carbonated water"], ["탄산수"], [r"탄산수"], []),
    ("Cola", ["cola", "coke", "coca cola", "pepsi"], ["콜라"], [r"콜라"], []),
    ("Lemon-lime soda (cider)", ["cider", "sprite", "lemon lime soda", "chilsung"], ["사이다"], [r"사이다", r"^스프라이트"], []),
    ("Sports drink", ["sports drink", "pocari", "pocari sweat", "gatorade", "powerade", "ion drink"], ["이온음료"], [r"포카리", r"게토레이", r"파워에이드"], []),
    ("Energy drink", ["energy drink", "red bull", "monster"], ["에너지음료"], [r"레드불", r"몬스터 에너지", r"핫식스"], []),
    ("Vitamin drink", ["vitamin drink", "vita500", "oronamin"], ["비타민음료"], [r"^비타500\(", r"오로나민", r"비타파워"], []),
    ("Hangover drink", ["hangover", "hangover drink", "condition"], ["숙취해소"], [r"컨디션", r"^여명", r"깨수깡"], []),
    ("Juice", ["juice", "orange juice"], ["주스"], [r"^델몬트 오렌지", r"^미닛메이드"], []),
    ("Coffee", ["coffee", "coffee mix", "instant coffee", "kanu", "maxim", "americano", "latte", "cold brew"], ["커피", "아메리카노", "라떼"], [r"커피", r"^맥심", r"^카누", r"아메리카노", r"라떼", r"콜드브루", r"^맥스웰", r"^스타벅스"], []),
    ("Tea", ["tea", "green tea"], ["차", "녹차"], [r"녹차", r"17차"], []),
    ("Milk", ["milk"], ["우유"], [r"우유"], [r"식빵", r"버터", r"치즈"]),
    ("Soy milk", ["soy milk", "soymilk"], ["두유"], [r"두유", r"베지밀"], []),
    ("Yogurt", ["yogurt", "yoghurt"], ["요거트", "요구르트"], [r"요거트", r"요플레", r"불가리스", r"^이오\("], []),
    ("Eggs", ["egg", "eggs"], ["계란", "달걀"], [r"계란", r"달걀", r"유정란", r"목초란"], []),
    ("Tofu", ["tofu", "bean curd"], ["두부"], [r"두부"], [r"진밥"]),
    ("Kimchi", ["kimchi"], ["김치"], [r"김치\("], []),
    ("Instant noodles (ramyeon)", ["ramen", "ramyeon", "ramyun", "instant noodles", "shin ramyun", "cup noodles", "cup ramen"], ["라면", "컵라면"], [r"라면", r"^너구리", r"^안성탕면", r"왕뚜껑", r"큰사발"], []),
    ("Instant rice", ["instant rice", "hetbahn", "cooked rice", "microwave rice"], ["햇반", "즉석밥"], [r"^햇반\(", r"^오뚜기밥"], []),
    ("Rice", ["rice"], ["쌀"], [r"쌀(\(| 특등급)", r"진상미", r"진미 특등급", r"^현미\("], []),
    ("Cup rice / ready meal", ["ready meal", "cup rice", "cupbap"], ["컵밥", "즉석식품"], [r"컵반", r"컵밥", r"볶음밥"], []),
    ("Porridge (juk)", ["porridge", "juk", "rice porridge"], ["죽"], [r"죽\("], []),
    ("Instant soup", ["soup", "instant soup"], ["국", "탕", "스프"], [r"곰탕", r"육개장", r"미역국", r"스프\(", r"콩나물국"], []),
    ("Curry (instant)", ["curry"], ["카레"], [r"카레"], []),
    ("Black bean sauce (jjajang)", ["jjajang", "black bean sauce"], ["짜장"], [r"짜장"], []),
    ("Dumplings (mandu)", ["dumpling", "dumplings", "mandu", "gyoza"], ["만두"], [r"만두", r"교자"], []),
    ("Tteokbokki kit", ["tteokbokki", "rice cake"], ["떡볶이"], [r"떡볶이"], []),
    ("Cold noodles kit", ["naengmyeon", "cold noodles"], ["냉면"], [r"냉면"], []),
    ("Udon", ["udon"], ["우동"], [r"우동"], []),
    ("Pasta / spaghetti", ["pasta", "spaghetti"], ["파스타", "스파게티"], [r"파스타", r"스파게티\("], []),
    ("Spam", ["spam", "luncheon meat"], ["스팸"], [r"^스팸"], []),
    ("Canned tuna", ["tuna", "canned tuna"], ["참치"], [r"참치"], []),
    ("Ham / sausage / bacon", ["ham", "sausage", "sausages", "bacon", "hot dog", "frankfurter"], ["햄", "소시지", "베이컨", "핫도그"], [r"햄", r"소시지", r"비엔나", r"후랑크", r"베이컨", r"핫도그"], [r"김밥용"]),
    ("Pork belly", ["pork belly", "samgyeopsal"], ["삼겹살"], [r"삼겹살"], []),
    ("Pork", ["pork"], ["돼지고기"], [r"돼지고기"], []),
    ("Beef", ["beef", "hanwoo"], ["소고기", "쇠고기", "한우"], [r"^쇠고기 (등심|불고기)"], []),
    ("Chicken", ["chicken", "nuggets", "chicken nuggets"], ["닭", "치킨"], [r"닭백숙", r"너겟", r"용가리"], []),
    ("Smoked duck", ["duck", "smoked duck"], ["오리"], [r"훈제오리"], []),
    ("Salmon", ["salmon"], ["연어"], [r"연어"], []),
    ("Pork cutlet (tonkatsu)", ["tonkatsu", "pork cutlet", "donkatsu"], ["돈까스", "돈가스"], [r"돈까스", r"돈카츠"], []),
    ("Seaweed snack (gim)", ["seaweed", "gim", "laver", "seasoned seaweed"], ["김"], [r"도시락김", r"올리브김"], []),
    ("Dried seaweed (miyeok)", ["miyeok", "dried seaweed", "wakame"], ["미역"], [r"미역\(", r"자른미역"], []),
    ("Gochujang", ["gochujang", "red pepper paste", "chili paste"], ["고추장"], [r"고추장"], []),
    ("Doenjang", ["doenjang", "soybean paste"], ["된장"], [r"된장", r"토장"], []),
    ("Ssamjang", ["ssamjang"], ["쌈장"], [r"쌈장"], []),
    ("Soy sauce", ["soy sauce"], ["간장"], [r"간장"], []),
    ("Sesame oil", ["sesame oil"], ["참기름"], [r"참기름"], []),
    ("Cooking oil", ["cooking oil", "oil", "canola oil", "vegetable oil"], ["식용유"], [r"카놀라유", r"식용유", r"콩기름", r"포도씨유"], []),
    ("Sugar", ["sugar"], ["설탕"], [r"설탕"], []),
    ("Salt", ["salt"], ["소금"], [r"소금"], []),
    ("Flour", ["flour"], ["밀가루"], [r"밀가루"], []),
    ("Ketchup", ["ketchup"], ["케첩", "케찹"], [r"케찹"], []),
    ("Mayonnaise", ["mayo", "mayonnaise"], ["마요네즈"], [r"마요네즈"], []),
    ("Honey", ["honey"], ["꿀"], [r"벌꿀"], []),
    ("Jam", ["jam"], ["잼"], [r"잼\("], []),
    ("Bread", ["bread"], ["빵"], [r"식빵", r"모닝롤", r"버터롤", r"단팥빵", r"크림빵", r"보름달"], []),
    ("Butter", ["butter"], ["버터"], [r"버터"], [r"롤", r"아몬드"]),
    ("Cheese", ["cheese"], ["치즈"], [r"치즈"], []),
    ("Cereal", ["cereal", "corn flakes"], ["시리얼"], [r"콘푸", r"스페셜K"], []),
    ("Snacks / chips", ["snack", "snacks", "chips", "crackers"], ["과자"], [r"새우깡", r"포카칩", r"포테토칩", r"참크래커", r"^아이비", r"초코파이", r"오예스", r"몽쉘"], []),
    ("Chocolate", ["chocolate"], ["초콜릿"], [r"가나", r"드림카카오", r"ABC 초코", r"자유시간", r"핫브레이크"], []),
    ("Ice cream", ["ice cream"], ["아이스크림"], [r"메로나", r"월드콘", r"부라보콘", r"투게더", r"돼지바", r"바밤바", r"싸만코"], []),
    ("Gum / candy / jelly", ["gum", "candy", "jelly", "haribo", "gummy"], ["껌", "사탕", "젤리"], [r"자일리톨", r"후라보노", r"캔디", r"젤리", r"하리보", r"마이구미", r"꿈틀이"], []),
    ("Toothpaste", ["toothpaste"], ["치약"], [r"치약", r"^2080 파워쉴드", r"^페리오 토탈7 오리지널"], []),
    ("Toothbrush", ["toothbrush"], ["칫솔"], [r"칫솔", r"미세모\(", r"크로스액션"], []),
    ("Mouthwash", ["mouthwash"], ["가글", "구강청결제"], [r"가그린", r"리스테린"], []),
    ("Shampoo", ["shampoo"], ["샴푸"], [r"샴푸"], []),
    ("Conditioner / treatment", ["conditioner", "hair treatment"], ["린스", "트리트먼트"], [r"트리트먼트"], []),
    ("Body wash", ["body wash", "shower gel"], ["바디워시"], [r"바디워시"], []),
    ("Soap", ["soap", "hand soap"], ["비누"], [r"비누", r"뷰티바", r"핸드워시", r"항균폼"], []),
    ("Toilet paper", ["toilet paper", "toilet tissue", "toilet roll"], ["화장지", "휴지"], [r"3겹"], []),
    ("Tissues", ["tissue", "tissues", "facial tissue"], ["티슈"], [r"미용티슈"], []),
    ("Wet wipes", ["wet wipes", "wipes"], ["물티슈"], [r"물티슈", r"손소독티슈"], []),
    ("Sunscreen", ["sunscreen", "sun cream", "sunblock"], ["선크림", "자외선차단제"], [r"(^| )선( |크림|\()"], []),
    ("Lip balm", ["lip balm", "chapstick"], ["립밤"], [r"립( |밤|테라피|\()"], []),
    ("Lotion", ["lotion", "moisturizer"], ["로션"], [r"로션", r"바디밀크"], []),
    ("Razor blades", ["razor", "razor blade", "razor blades"], ["면도기", "면도날"], [r"면도날"], []),
    ("Batteries", ["battery", "batteries"], ["건전지"], [r"건전지", r"에너자이저"], []),
    ("Face mask", ["mask", "face mask", "kf94"], ["마스크"], [r"마스크"], []),
    ("Bandages", ["bandage", "band aid", "plaster"], ["밴드", "반창고"], [r"밴드"], []),
    ("Laundry detergent", ["detergent", "laundry detergent"], ["세제", "세탁세제"], [r"분말세제", r"액체세제", r"파워젤", r"실내건조"], []),
    ("Dish soap", ["dish soap", "dishwashing liquid"], ["주방세제"], [r"주방세제", r"자연퐁", r"항균 트리오", r"베이킹소다 퓨어"], []),
    ("Fabric softener", ["fabric softener"], ["섬유유연제"], [r"섬유유연제"], []),
    ("Bleach", ["bleach"], ["락스"], [r"락스"], []),
    ("Insect spray", ["bug spray", "insect spray", "mosquito spray"], ["살충제", "모기약"], [r"에프킬라", r"컴배트", r"홈키파"], []),
    ("Diapers", ["diaper", "diapers", "nappies"], ["기저귀"], [r"하기스"], []),
    ("Sanitary pads", ["sanitary pad", "sanitary pads", "period pads"], ["생리대"], [r"^쏘피", r"^좋은느낌", r"^화이트 수퍼흡수"], []),
    ("Kitchen supplies", ["foil", "plastic wrap", "zipper bag", "rubber gloves", "kitchen towel"], ["호일", "랩", "지퍼백", "고무장갑", "키친타월"], [r"호일", r"크린랩\(", r"지퍼백", r"고무장갑", r"키친타월", r"크린백", r"롤백"], []),
    ("Butane gas", ["butane", "gas canister", "camping gas"], ["부탄가스"], [r"부탄가스"], []),
]

_HANGUL = re.compile(r"[가-힣]")
_COMPILED = [
    (en, {normalize(t) for t in terms}, set(ko), [re.compile(p) for p in inc], [re.compile(p) for p in exc])
    for en, terms, ko, inc, exc in CONCEPTS
]


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _matches(name: str, inc: list[re.Pattern], exc: list[re.Pattern]) -> bool:
    return any(p.search(name) for p in inc) and not any(p.search(name) for p in exc)


def match_concepts(query: str) -> list[int]:
    """검색어에 해당하는 종류(CONCEPTS의 번호)들."""
    q = normalize(query)
    qc = _compact(q)
    if not qc:
        return []
    hits = []
    for i, (en, terms, ko, _, _) in enumerate(_COMPILED):
        if q in terms or qc in {_compact(t) for t in terms} or normalize(en) == q:
            hits.append(i)
        elif _HANGUL.search(qc) and qc in ko:
            hits.append(i)
    return hits


def search_products(query: str, products: list[dict], limit: int = 12) -> list[dict]:
    """검색어에 맞는 상품들. 조사한 판매점이 많은(=흔한) 상품부터."""
    found: dict[str, dict] = {}
    for i in match_concepts(query):
        en, _, _, inc, exc = _COMPILED[i]
        for p in products:
            if p["product_name"] not in found and _matches(p["product_name"], inc, exc):
                found[p["product_name"]] = {**p, "category_en": en}

    # 사전에 없는 한글 검색어(브랜드명 등): 상품명에 그대로 들어 있으면 보여준다 (예: 신라면, 햇반)
    qc = _compact(normalize(query))
    if not found and _HANGUL.search(qc) and len(qc) >= 2:
        for p in products:
            if qc in _compact(p["product_name"]):
                found[p["product_name"]] = {**p, "category_en": None}

    out = sorted(found.values(), key=lambda p: (-p["store_count"], p["product_name"]))
    return out[:limit]
