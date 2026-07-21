export function TypingIndicator() {
  return (
    <div className="message-row message-row-assistant">
      <div className="avatar avatar-assistant">AI</div>
      <div className="bubble bubble-assistant typing-indicator" aria-label="Assistant is typing">
        <span className="typing-dot" />
        <span className="typing-dot" />
        <span className="typing-dot" />
      </div>
    </div>
  );
}
