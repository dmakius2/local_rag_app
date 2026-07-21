import { useDocuments } from "@/hooks";
import { Spinner } from "@/components/common/Spinner";
import { DocumentListItem } from "./DocumentListItem";

export function DocumentList() {
  const { documents, isLoading, error } = useDocuments();

  if (isLoading && documents.length === 0) {
    return (
      <div className="sidebar-loading">
        <Spinner size="sm" /> Loading documents…
      </div>
    );
  }

  if (error) {
    return <p className="sidebar-error">{error}</p>;
  }

  if (documents.length === 0) {
    return <p className="sidebar-empty">No documents indexed yet. Add PDFs and reindex.</p>;
  }

  return (
    <ul className="document-list">
      {documents.map((doc) => (
        <DocumentListItem key={doc.filename} document={doc} />
      ))}
    </ul>
  );
}
