import { ReactNode } from 'react';
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

export default function StatCard({ value, label, href, zeroCta, loading }: StatCardProps) {
  const display = loading ? '…' : value ?? 0;
  const showCta = !loading && value === 0 && zeroCta;

  const body = (
    <>
      <div className="stat-number">{display}</div>
      <div className="stat-label">{label}</div>
      {showCta && <div className="stat-cta">{zeroCta}</div>}
    </>
  );

  if (href && !showCta) {
    // Clickable, no CTA — wrap whole card in Link
    return (
      <Link className="stat-card stat-card-link" to={href}>
        {body}
      </Link>
    );
  }
  return <div className="stat-card">{body}</div>;
}
