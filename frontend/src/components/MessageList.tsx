import { useEffect, useRef } from "react";
import { Chat, ChatFile, ChatMessage, SkillSummary } from "../api/client";
import { Markdown } from "./Markdown";

type Props = {
  chat: Chat;
  skills: SkillSummary[];
  pendingAssistant: boolean;
};

export function MessageList({ chat, skills, pendingAssistant }: Props) {
  const endRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [chat.messages.length, pendingAssistant]);

  if (chat.messages.length === 0 && !pendingAssistant) {
    return (
      <div className="message-list">
        <EmptyState skills={skills} />
      </div>
    );
  }

  const fileById = new Map(chat.files.map((f) => [f.id, f] as const));

  return (
    <div className="message-list">
      <div className="message-list-inner">
        {chat.messages.map((m) => (
          <MessageRow key={m.id} message={m} fileById={fileById} />
        ))}
        {pendingAssistant ? <ThinkingRow /> : null}
        <div ref={endRef} />
      </div>
    </div>
  );
}

function MessageRow({
  message,
  fileById,
}: {
  message: ChatMessage;
  fileById: Map<string, ChatFile>;
}) {
  const attached = (message.file_ids || [])
    .map((fid) => fileById.get(fid))
    .filter((f): f is ChatFile => Boolean(f));
  return (
    <div className={`message ${message.role}`}>
      <div className="avatar" aria-hidden>
        {message.role === "user" ? "You" : "TA"}
      </div>
      <div className="body">
        <div className="role">{message.role === "user" ? "You" : "Teaching Assistant"}</div>
        <Markdown text={message.content} />
        {attached.length > 0 ? (
          <div className="files">
            {attached.map((f) => (
              <span key={f.id} className="file-pill" title={f.filename}>
                📎 {f.label}
              </span>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}

function ThinkingRow() {
  return (
    <div className="message assistant">
      <div className="avatar" aria-hidden>TA</div>
      <div className="body">
        <div className="role">Teaching Assistant</div>
        <span className="content" style={{ color: "#6b7280", fontStyle: "italic" }}>
          thinking…
        </span>
      </div>
    </div>
  );
}

function EmptyState({ skills }: { skills: SkillSummary[] }) {
  return (
    <div className="empty-state">
      <h2>How can I help you study?</h2>
      <p>
        Send a message and I'll figure out which Socratic teaching approach fits best.
        I'll always confirm before activating one.
      </p>
      {skills.length > 0 ? (
        <div className="skills-grid">
          {skills.map((s) => (
            <div key={s.id} className="skill-card">
              <div className="name">{s.name}</div>
              <div className="desc">{s.description.slice(0, 120)}{s.description.length > 120 ? "…" : ""}</div>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
