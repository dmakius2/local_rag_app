import { useRef, useState, type DragEvent } from "react";
import { useDocumentsStore } from "@/context";
import { Banner } from "@/components/common/Banner";
import { Spinner } from "@/components/common/Spinner";
import { ACCEPTED_UPLOAD_EXTENSIONS } from "@/types";

const ACCEPT_ATTR = ACCEPTED_UPLOAD_EXTENSIONS.join(",");

export function DocumentDropzone() {
  const { isUploading, uploadError, lastUpload, uploadFiles, dismissUploadResult } = useDocumentsStore();
  const [isDraggingOver, setIsDraggingOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleDragOver(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDraggingOver(true);
  }

  function handleDragLeave(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDraggingOver(false);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDraggingOver(false);
    const files = Array.from(event.dataTransfer.files);
    if (files.length > 0) {
      void uploadFiles(files);
    }
  }

  function handleFileInputChange(event: React.ChangeEvent<HTMLInputElement>) {
    const files = event.target.files ? Array.from(event.target.files) : [];
    if (files.length > 0) {
      void uploadFiles(files);
    }
    event.target.value = "";
  }

  const skippedDocFiles = (lastUpload ?? []).filter((d) => !d.extractable);

  return (
    <div className="document-dropzone-wrap">
      <div
        className={`document-dropzone ${isDraggingOver ? "document-dropzone-active" : ""}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        aria-label="Upload documents"
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
        }}
      >
        {isUploading ? (
          <>
            <Spinner size="sm" /> Uploading…
          </>
        ) : (
          <>
            <span className="document-dropzone-icon" aria-hidden="true">
              📤
            </span>
            <span>Drag & drop files, or click to browse</span>
            <span className="document-dropzone-hint">PDF, DOC, DOCX, TXT</span>
          </>
        )}
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ACCEPT_ATTR}
          className="document-dropzone-input"
          onChange={handleFileInputChange}
        />
      </div>

      {uploadError && (
        <Banner tone="error" onDismiss={dismissUploadResult}>
          {uploadError}
        </Banner>
      )}

      {lastUpload && lastUpload.length > 0 && (
        <Banner tone="success" onDismiss={dismissUploadResult}>
          Uploaded {lastUpload.length} file{lastUpload.length === 1 ? "" : "s"}. Reindex to make{" "}
          {lastUpload.length === 1 ? "it" : "them"} searchable.
          {skippedDocFiles.length > 0 && (
            <>
              {" "}
              Note: {skippedDocFiles.map((d) => d.filename).join(", ")} won't be searchable until converted to
              .docx or PDF.
            </>
          )}
        </Banner>
      )}
    </div>
  );
}
