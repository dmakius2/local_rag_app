import type { ApiStatus } from "@/context";

const LABELS: Record<ApiStatus, string> = {
  checking: "Checking backend…",
  online: "Backend online",
  offline: "Backend unavailable",
};

export function StatusDot({ status }: { status: ApiStatus }) {
  return (
    <span className="status-dot-row" title={LABELS[status]}>
      <span className={`status-dot status-dot-${status}`} />
      <span className="status-dot-label">{LABELS[status]}</span>
    </span>
  );
}
