import type { DocumentSummary } from "@/types";

export function DocumentListItem({ document }: { document: DocumentSummary }) {
  return (
    <li className="document-item">
      <span className="document-icon" aria-hidden="true">
        📄
      </span>
      <div className="document-meta">
        <span className="document-name" title={document.filename}>
          {document.filename}
        </span>
        <span className="document-stats">
          {document.pages} {document.pages === 1 ? "page" : "pages"} · {document.chunks}{" "}
          {document.chunks === 1 ? "chunk" : "chunks"}
        </span>
      </div>
    </li>
  );
}
