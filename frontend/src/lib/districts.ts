// 서울 25개 자치구 (가나다순). `districts` 테이블과 같은 값이다.
// code = 행정표준 시군구 코드 (price_stats.region), name = stores.district에 저장되는 한글 이름.
export const DISTRICTS = [
  { code: "11680", name: "강남구", nameEn: "Gangnam-gu" },
  { code: "11740", name: "강동구", nameEn: "Gangdong-gu" },
  { code: "11305", name: "강북구", nameEn: "Gangbuk-gu" },
  { code: "11500", name: "강서구", nameEn: "Gangseo-gu" },
  { code: "11620", name: "관악구", nameEn: "Gwanak-gu" },
  { code: "11215", name: "광진구", nameEn: "Gwangjin-gu" },
  { code: "11530", name: "구로구", nameEn: "Guro-gu" },
  { code: "11545", name: "금천구", nameEn: "Geumcheon-gu" },
  { code: "11350", name: "노원구", nameEn: "Nowon-gu" },
  { code: "11320", name: "도봉구", nameEn: "Dobong-gu" },
  { code: "11230", name: "동대문구", nameEn: "Dongdaemun-gu" },
  { code: "11590", name: "동작구", nameEn: "Dongjak-gu" },
  { code: "11440", name: "마포구", nameEn: "Mapo-gu" },
  { code: "11410", name: "서대문구", nameEn: "Seodaemun-gu" },
  { code: "11650", name: "서초구", nameEn: "Seocho-gu" },
  { code: "11200", name: "성동구", nameEn: "Seongdong-gu" },
  { code: "11290", name: "성북구", nameEn: "Seongbuk-gu" },
  { code: "11710", name: "송파구", nameEn: "Songpa-gu" },
  { code: "11470", name: "양천구", nameEn: "Yangcheon-gu" },
  { code: "11560", name: "영등포구", nameEn: "Yeongdeungpo-gu" },
  { code: "11170", name: "용산구", nameEn: "Yongsan-gu" },
  { code: "11380", name: "은평구", nameEn: "Eunpyeong-gu" },
  { code: "11110", name: "종로구", nameEn: "Jongno-gu" },
  { code: "11140", name: "중구", nameEn: "Jung-gu" },
  { code: "11260", name: "중랑구", nameEn: "Jungnang-gu" },
];

export const DISTRICT_NAMES = DISTRICTS.map((d) => d.name);

/** "11680" → "강남구" */
export const DISTRICT_NAME_BY_CODE: Record<string, string> = Object.fromEntries(DISTRICTS.map((d) => [d.code, d.name]));

/** "강남구" → "Gangnam-gu" */
export const DISTRICT_NAME_EN: Record<string, string> = Object.fromEntries(DISTRICTS.map((d) => [d.name, d.nameEn]));
