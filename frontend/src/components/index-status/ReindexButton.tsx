import { useIndexStore } from "@/context";
import { Button } from "@/components/common/Button";
import { Spinner } from "@/components/common/Spinner";

export function ReindexButton() {
  const { phase, triggerReindex } = useIndexStore();
  const isIndexing = phase === "indexing";

  return (
    <Button variant="secondary" onClick={triggerReindex} disabled={isIndexing} className="reindex-btn">
      {isIndexing ? (
        <>
          <Spinner size="sm" /> Reindexing…
        </>
      ) : (
        "Reindex documents"
      )}
    </Button>
  );
}
