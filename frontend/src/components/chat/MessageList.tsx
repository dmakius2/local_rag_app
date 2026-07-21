import type { ChatMessage } from "@/types";
import { useAutoScroll } from "@/hooks";
import { MessageBubble } from "./MessageBubble";
import { TypingIndicator } from "./TypingIndicator";
import { EmptyState } from "./EmptyState";

interface MessageListProps {
  messages: ChatMessage[];
  isSending: boolean;
}

export function MessageList({ messages, isSending }: MessageListProps) {
  const scrollRef = useAutoScroll<HTMLDivElement>(messages.length + (isSending ? 1 : 0));

  if (messages.length === 0 && !isSending) {
    return (
      <div className="message-list" ref={scrollRef}>
        <EmptyState />
      </div>
    );
  }

  return (
    <div className="message-list" ref={scrollRef}>
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}
      {isSending && <TypingIndicator />}
    </div>
  );
}
