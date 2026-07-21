import { useSettingsStore } from "@/context";
import { SourceItem } from "./SourceItem";
import type { Source } from "@/types";

export function SourceList({ sources }: { sources: Source[] }) {
  const topK = useSettingsStore((s) => s.topK);

  if (sources.length === 0) return null;

  const visible = sources.slice(0, topK);

  return (
    <div className="source-list">
      <div className="source-list-heading">Sources</div>
      <ul>
        {visible.map((source, i) => (
          <SourceItem key={`${source.document}-${source.page}-${i}`} source={source} />
        ))}
      </ul>
    </div>
  );
}
