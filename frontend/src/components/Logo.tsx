// 손글씨 로고 "비싼감?". 원본은 흰색 PNG(public/logo_hand_white.png)라 CSS mask로 모양만 따고 brand 색을 칠한다.
// 높이는 className으로 정한다 (예: h-14). 가로는 원본 비율(886×320)로 맞춘다.
export function Logo({ label, className = "" }: { label: string; className?: string }) {
  return (
    <span
      role="img"
      aria-label={label}
      className={`block aspect-[886/320] bg-brand ${className}`}
      style={{
        maskImage: "url(/logo_hand_white.png)",
        WebkitMaskImage: "url(/logo_hand_white.png)",
        maskSize: "contain",
        WebkitMaskSize: "contain",
        maskRepeat: "no-repeat",
        WebkitMaskRepeat: "no-repeat",
      }}
    />
  );
}
