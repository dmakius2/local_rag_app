export function EmptyState() {
  return (
    <div className="empty-state">
      <div className="empty-state-icon" aria-hidden="true">
        💬
      </div>
      <h2>Ask something about your documents</h2>
      <p>
        Questions are answered using only the content of the PDFs you've indexed. Every answer
        cites the document and page it came from.
      </p>
    </div>
  );
}
