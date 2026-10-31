// 홈 상단부 배경 장식: 해 + 남산타워가 있는 서울 스카이라인 실루엣. 장식이라 스크린리더에서 숨긴다.
// 상단부 아래쪽에 깔리고(absolute), 색은 brand 토큰을 옅게 쓴다.
export function SeoulSkyline({ className = "" }: { className?: string }) {
  return (
    <svg
      aria-hidden
      viewBox="0 0 1200 220"
      preserveAspectRatio="xMidYMax slice"
      className={`pointer-events-none absolute inset-x-0 bottom-0 h-full w-full ${className}`}
    >
      <circle cx="930" cy="120" r="120" className="fill-brand-soft" opacity="0.9" />
      <circle cx="930" cy="120" r="78" className="fill-brand" opacity="0.18" />
      <g className="fill-brand" opacity="0.16">
        {/* 왼쪽 빌딩들 */}
        <rect x="0" y="150" width="40" height="70" />
        <rect x="46" y="128" width="28" height="92" />
        <rect x="80" y="160" width="52" height="60" />
        <rect x="138" y="138" width="24" height="82" />
        <rect x="168" y="170" width="44" height="50" />
        {/* 오른쪽 빌딩들 */}
        <rect x="640" y="160" width="46" height="60" />
        <rect x="692" y="132" width="30" height="88" />
        <rect x="728" y="150" width="56" height="70" />
        <rect x="790" y="118" width="26" height="102" />
        <rect x="822" y="146" width="40" height="74" />
        <rect x="868" y="166" width="60" height="54" />
        <rect x="934" y="126" width="34" height="94" />
        <rect x="974" y="154" width="50" height="66" />
        <rect x="1030" y="138" width="28" height="82" />
        <rect x="1064" y="160" width="58" height="60" />
        <rect x="1128" y="144" width="72" height="76" />
        {/* 남산 + 남산타워 */}
        <path d="M980 220 Q1040 168 1100 220 Z" />
        <rect x="1036" y="92" width="8" height="90" />
        <rect x="1028" y="104" width="24" height="10" rx="3" />
        <rect x="1039" y="64" width="2" height="30" />
      </g>
    </svg>
  );
}
