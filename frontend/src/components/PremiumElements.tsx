import type { ReactNode } from "react";

interface CrownIconProps {
  className?: string;
}

export function CrownIcon({ className }: CrownIconProps) {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className={className}>
      <path
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.7"
        d="M4.5 17.4h15l-1-7.2-4.6 3.2L12 7l-1.9 6.4-4.6-3.2z"
      />
      <path
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.7"
        d="M7 19.5h10"
      />
    </svg>
  );
}

interface PremiumBadgeProps {
  compact?: boolean;
}

export function PremiumBadge({ compact = false }: PremiumBadgeProps) {
  return (
    <span className={`badge badge--premium${compact ? " badge--premium-compact" : ""}`}>
      <CrownIcon className="badge__icon" />
      Premium
    </span>
  );
}

interface PremiumLockProps {
  locked: boolean;
  message: string;
  cta: string;
  children: ReactNode;
}

export function PremiumLock({ locked, message, cta, children }: PremiumLockProps) {
  return (
    <div className={`premium-lock${locked ? " premium-lock--active" : ""}`}>
      <div className="premium-lock__content">{children}</div>
      {locked ? (
        <div className="premium-lock__overlay">
          <div className="premium-lock__panel">
            <PremiumBadge compact />
            <p>{message}</p>
            <span className="premium-lock__cta">{cta}</span>
          </div>
        </div>
      ) : null}
    </div>
  );
}
