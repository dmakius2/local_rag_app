import { useDocumentsStore } from "@/context";
import { Spinner } from "@/components/common/Spinner";
import type { DocumentSummary } from "@/types";

export function DocumentListItem({ document }: { document: DocumentSummary }) {
  const isDeleting = useDocumentsStore((s) => s.deletingFilenames.has(document.filename));
  const deleteDocument = useDocumentsStore((s) => s.deleteDocument);

  function handleDelete() {
    if (isDeleting) return;
    const confirmed = window.confirm(
      `Delete "${document.filename}"? This removes it from the index and deletes the file — this can't be undone.`
    );
    if (confirmed) {
      void deleteDocument(document.filename);
    }
  }

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
      <button
        type="button"
        className="document-delete-btn"
        onClick={handleDelete}
        disabled={isDeleting}
        aria-label={`Delete ${document.filename}`}
        title={`Delete ${document.filename}`}
      >
        {isDeleting ? <Spinner size="sm" /> : "🗑"}
      </button>
    </li>
  );
}
