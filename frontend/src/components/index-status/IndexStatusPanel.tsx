import { useIndexStore } from "@/context";
import { Banner } from "@/components/common/Banner";
import { ReindexButton } from "./ReindexButton";

export function IndexStatusPanel() {
  const { phase, lastResult, error, dismiss } = useIndexStore();

  return (
    <div className="index-status-panel">
      <ReindexButton />

      {phase === "indexing" && (
        <p className="sidebar-hint">
          Re-embedding every document from scratch — this can take a few minutes for large document sets.
        </p>
      )}

      {phase === "success" && lastResult && (
        <Banner tone="success" onDismiss={dismiss}>
          Indexed {lastResult.documentsProcessed} document
          {lastResult.documentsProcessed === 1 ? "" : "s"} ({lastResult.chunksCreated} chunks) in{" "}
          {lastResult.elapsedSeconds.toFixed(1)}s.
        </Banner>
      )}

      {phase === "error" && error && (
        <Banner tone="error" onDismiss={dismiss}>
          {error}
        </Banner>
      )}
    </div>
  );
}
