import { useDocuments } from "@/hooks";
import { Banner } from "@/components/common/Banner";
import { Spinner } from "@/components/common/Spinner";
import { useDocumentsStore } from "@/context";
import { DocumentDropzone } from "./DocumentDropzone";
import { DocumentListItem } from "./DocumentListItem";

export function DocumentList() {
  const { documents, isLoading, error } = useDocuments();
  const deleteError = useDocumentsStore((s) => s.deleteError);
  const dismissDeleteError = useDocumentsStore((s) => s.dismissDeleteError);

  return (
    <>
      <DocumentDropzone />
      {deleteError && (
        <Banner tone="error" onDismiss={dismissDeleteError}>
          {deleteError}
        </Banner>
      )}
      {isLoading && documents.length === 0 ? (
        <div className="sidebar-loading">
          <Spinner size="sm" /> Loading documents…
        </div>
      ) : error ? (
        <p className="sidebar-error">{error}</p>
      ) : documents.length === 0 ? (
        <p className="sidebar-empty">No documents indexed yet. Drop files above and reindex.</p>
      ) : (
        <ul className="document-list">
          {documents.map((doc) => (
            <DocumentListItem key={doc.filename} document={doc} />
          ))}
        </ul>
      )}
    </>
  );
}
