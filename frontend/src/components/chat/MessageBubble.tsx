import type { ChatMessage } from "@/types";
import { MarkdownRenderer } from "./MarkdownRenderer";
import { SourceList } from "./SourceList";

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={`message-row ${isUser ? "message-row-user" : "message-row-assistant"}`}>
      {!isUser && <div className="avatar avatar-assistant">AI</div>}
      <div className="message-column">
        <div
          className={`bubble ${isUser ? "bubble-user" : "bubble-assistant"} ${
            message.isError ? "bubble-error" : ""
          }`}
        >
          {isUser ? <p>{message.content}</p> : <MarkdownRenderer content={message.content} />}
        </div>
        {!isUser && message.sources && <SourceList sources={message.sources} />}
      </div>
      {isUser && <div className="avatar avatar-user">You</div>}
    </div>
  );
}
