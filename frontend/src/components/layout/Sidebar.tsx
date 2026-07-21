import { CollapsibleSection } from "@/components/common/CollapsibleSection";
import { StatusDot } from "@/components/common/StatusDot";
import { DocumentList } from "@/components/documents/DocumentList";
import { IndexStatusPanel } from "@/components/index-status/IndexStatusPanel";
import { SettingsPanel } from "@/components/settings/SettingsPanel";
import { useHealthStore } from "@/context";

export function Sidebar() {
  const apiStatus = useHealthStore((s) => s.status);

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <span className="sidebar-brand-icon" aria-hidden="true">
          🧠
        </span>
        <span className="sidebar-brand-name">Local RAG</span>
      </div>

      <StatusDot status={apiStatus} />

      <div className="sidebar-sections">
        <CollapsibleSection title="Documents" icon="📁">
          <DocumentList />
        </CollapsibleSection>

        <CollapsibleSection title="Index status" icon="⚙️">
          <IndexStatusPanel />
        </CollapsibleSection>

        <CollapsibleSection title="Settings" icon="🎛️" defaultOpen={false}>
          <SettingsPanel />
        </CollapsibleSection>
      </div>
    </aside>
  );
}
