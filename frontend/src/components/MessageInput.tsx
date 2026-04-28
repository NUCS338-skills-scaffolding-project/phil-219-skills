import { useEffect, useRef, useState } from "react";

type Props = {
  disabled: boolean;
  onSend: (text: string) => void;
  onPickFile: (file: File) => void;
};

export function MessageInput({ disabled, onSend, onPickFile }: Props) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    autoresize();
  }, [value]);

  function autoresize() {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 240)}px`;
  }

  function send() {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
    requestAnimationFrame(autoresize);
  }

  function handleKey(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (f) onPickFile(f);
    e.target.value = "";
  }

  return (
    <>
      <div className="composer">
        <div className="composer-inner">
          <input
            ref={fileInputRef}
            type="file"
            style={{ display: "none" }}
            onChange={handleFileChange}
            accept=".pdf,.txt,.md,.markdown"
          />
          <button
            className="icon-btn"
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled}
            aria-label="Attach file"
            title="Attach a document to this chat"
          >
            📎
          </button>
          <textarea
            ref={textareaRef}
            placeholder="Message your TA…"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKey}
            rows={1}
            disabled={disabled}
          />
          <button
            className="icon-btn send-btn"
            type="button"
            onClick={send}
            disabled={disabled || !value.trim()}
            aria-label="Send"
            title="Send (Enter)"
          >
            ↑
          </button>
        </div>
      </div>
      <div className="composer-hint">
        Enter to send · Shift+Enter for newline · attach PDFs/Markdown for chat-specific reading
      </div>
    </>
  );
}
