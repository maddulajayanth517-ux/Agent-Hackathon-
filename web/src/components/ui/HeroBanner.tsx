export function HeroBanner({
  title,
  subtitle,
  tone = "brand",
  right,
}: {
  title: string;
  subtitle: string;
  tone?: "brand" | "warm";
  right?: React.ReactNode;
}) {
  const gradient =
    tone === "warm"
      ? "from-[var(--color-accent-pink)] via-[var(--color-brand-600)] to-[var(--color-accent-blue)]"
      : "from-[var(--color-brand-900)] via-[var(--color-brand-700)] to-[var(--color-brand-500)]";
  return (
    <div className={`relative overflow-hidden rounded-2xl bg-gradient-to-br ${gradient} px-6 py-6 text-white shadow-sm sm:px-8`}>
      <div className="absolute inset-0 opacity-20 [background-image:radial-gradient(circle_at_10%_10%,white,transparent_30%),radial-gradient(circle_at_90%_90%,white,transparent_28%)]" />
      <div className="relative flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold">{title}</h2>
          <p className="mt-1 text-sm text-white/80">{subtitle}</p>
        </div>
        {right}
      </div>
    </div>
  );
}
