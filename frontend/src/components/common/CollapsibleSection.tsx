import { useState, type ReactNode } from "react";

interface CollapsibleSectionProps {
  title: string;
  icon?: ReactNode;
  defaultOpen?: boolean;
  children: ReactNode;
}

export function CollapsibleSection({ title, icon, defaultOpen = true, children }: CollapsibleSectionProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <section className="sidebar-section">
      <button
        className="sidebar-section-header"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <span className="sidebar-section-title">
          {icon}
          {title}
        </span>
        <span className={`chevron ${open ? "chevron-open" : ""}`} aria-hidden="true">
          ▾
        </span>
      </button>
      {open && <div className="sidebar-section-body">{children}</div>}
    </section>
  );
}
