import { useChatStore, useHealthStore } from "@/context";
import { Banner } from "@/components/common/Banner";
import { Button } from "@/components/common/Button";
import { MessageList } from "./MessageList";
import { PromptInput } from "./PromptInput";

export function ChatWindow() {
  const { messages, isSending, error, sendMessage, clearHistory, dismissError } = useChatStore();
  const apiStatus = useHealthStore((s) => s.status);

  const offline = apiStatus === "offline";

  return (
    <div className="chat-window">
      <header className="chat-header">
        <h1>Local RAG</h1>
        <Button variant="ghost" onClick={clearHistory} disabled={messages.length === 0}>
          Clear chat
        </Button>
      </header>

      {offline && (
        <Banner tone="error">
          Can't reach the API backend. Make sure the FastAPI server is running and reachable.
        </Banner>
      )}
      {!offline && error && (
        <Banner tone="error" onDismiss={dismissError}>
          {error}
        </Banner>
      )}

      <MessageList messages={messages} isSending={isSending} />

      <div className="chat-footer">
        <PromptInput onSubmit={sendMessage} disabled={isSending || offline} />
        <p className="chat-disclaimer">Answers are grounded only in your indexed documents.</p>
      </div>
    </div>
  );
}
