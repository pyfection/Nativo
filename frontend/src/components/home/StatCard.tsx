import { ReactNode, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';

interface StatCardProps {
  value: number | null;
  label: string;
  /** If set, the card becomes a Link. */
  href?: string;
  /** Render a CTA element below the value when value === 0. */
  zeroCta?: ReactNode;
  loading?: boolean;
}

// Animates a number from 0 → target on mount and whenever target changes.
function useCountUp(target: number, durationMs = 900): number {
  const [value, setValue] = useState(0);
  const rafRef = useRef<number | null>(null);
  useEffect(() => {
    if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    if (target === 0) {
      setValue(0);
      return;
    }
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / durationMs);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - t, 3);
      setValue(Math.round(target * eased));
      if (t < 1) rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    };
  }, [target, durationMs]);
  return value;
}

export default function StatCard({ value, label, href, zeroCta, loading }: StatCardProps) {
  const animated = useCountUp(value ?? 0);
  const display = loading ? '…' : animated;
  const showCta = !loading && value === 0 && zeroCta;

  const body = (
    <>
      <div className="stat-number">{display}</div>
      <div className="stat-label">{label}</div>
      {showCta && <div className="stat-cta">{zeroCta}</div>}
    </>
  );

  if (href && !showCta) {
    return (
      <Link className="stat-card stat-card-link" to={href}>
        {body}
      </Link>
    );
  }
  return <div className="stat-card">{body}</div>;
}
