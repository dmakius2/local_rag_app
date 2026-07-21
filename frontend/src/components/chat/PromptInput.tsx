import { useRef, useState, type KeyboardEvent } from "react";
import { Button } from "@/components/common/Button";

interface PromptInputProps {
  onSubmit: (question: string) => void;
  disabled: boolean;
}

export function PromptInput({ onSubmit, disabled }: PromptInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSubmit(trimmed);
    setValue("");
    textareaRef.current?.focus();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="prompt-input">
      <textarea
        ref={textareaRef}
        className="prompt-textarea"
        placeholder="Ask a question about your documents…"
        rows={1}
        value={value}
        disabled={disabled}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
      />
      <Button
        variant="primary"
        className="prompt-send"
        onClick={handleSubmit}
        disabled={disabled || !value.trim()}
      >
        Send
      </Button>
    </div>
  );
}
