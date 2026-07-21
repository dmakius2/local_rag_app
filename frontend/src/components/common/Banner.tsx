import type { ReactNode } from "react";

type Tone = "error" | "warning" | "info" | "success";

interface BannerProps {
  tone: Tone;
  children: ReactNode;
  onDismiss?: () => void;
}

export function Banner({ tone, children, onDismiss }: BannerProps) {
  return (
    <div className={`banner banner-${tone}`} role={tone === "error" ? "alert" : "status"}>
      <span className="banner-message">{children}</span>
      {onDismiss && (
        <button className="banner-dismiss" onClick={onDismiss} aria-label="Dismiss">
          ×
        </button>
      )}
    </div>
  );
}
