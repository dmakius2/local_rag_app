import { useEffect } from "react";
import { useDocumentsStore } from "@/context";

/** Loads the document list on first mount of whichever component uses it. */
export function useDocuments() {
  const { documents, isLoading, error, hasLoaded, loadDocuments } = useDocumentsStore();

  useEffect(() => {
    if (!hasLoaded) {
      loadDocuments();
    }
  }, [hasLoaded, loadDocuments]);

  return { documents, isLoading, error, reload: loadDocuments };
}
