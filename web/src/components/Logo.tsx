const LOGO_URL = "https://vignan.ac.in/images/LOGO_change.jpg";

export function Logo({ size = 40, rounded = "rounded-xl" }: { size?: number; rounded?: string }) {
  return (
    <span
      className={`flex shrink-0 items-center justify-center overflow-hidden bg-white p-1 shadow-sm ${rounded}`}
      style={{ width: size, height: size }}
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={LOGO_URL} alt="Vignan's Foundation for Science, Technology & Research" className="h-full w-full object-contain" />
    </span>
  );
}
