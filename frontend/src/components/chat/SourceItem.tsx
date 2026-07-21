import { useState } from "react";
import type { Source } from "@/types";

export function SourceItem({ source }: { source: Source }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <li className="source-item">
      <button
        className="source-item-header"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
      >
        <span className="source-icon" aria-hidden="true">
          📄
        </span>
        <span className="source-name">{source.document}</span>
        <span className="source-page">p. {source.page}</span>
        <span className={`chevron ${expanded ? "chevron-open" : ""}`} aria-hidden="true">
          ▾
        </span>
      </button>
      {expanded && <p className="source-chunk-text">{source.chunkText}</p>}
    </li>
  );
}
