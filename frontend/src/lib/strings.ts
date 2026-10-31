// UI strings kept in one place so the English version (roadmap step 1) is a drop-in.
export const strings = {
  ko: {
    appName: "WonSense",
    tagline: "서울 물가 감각",
    searchPlaceholder: "음식이나 물건을 검색해 보세요 (예: bibimbap, 소주)",
    quizTitle: "물가 퀴즈",
    heatmapTitle: "Heat map",
    reviewTitle: "Review",
    comingSoon: "준비 중",
    quizLoading: "문제를 불러오는 중…",
    quizRight: "정답! 🎯",
    quizWrong: "오답 ❌",
    quizYourGuess: "내 답",
    quizAnswer: "평균 가격",
    quizSource: "출처",
    quizNext: "다음 문제",
    quizNeedNumber: "숫자를 입력하세요",
    quizError: "퀴즈를 불러오지 못했어요. 백엔드가 켜져 있는지 확인하세요.",
    heatmapSource: "출처: 한국소비자원 등 공공 통계",
    reviewEmpty: "아직 리뷰가 없어요",
  },
} as const;

export type Locale = keyof typeof strings;
export const t = strings.ko;
