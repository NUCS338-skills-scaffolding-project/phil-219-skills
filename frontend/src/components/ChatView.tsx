import { useState } from "react";
import { api, Chat, FolderFile, SkillSummary } from "../api/client";
import { MessageInput } from "./MessageInput";
import { MessageList } from "./MessageList";
import { SkillConfirmBanner } from "./SkillConfirmBanner";
import { UploadModal } from "./UploadModal";

type Props = {
  chat: Chat;
  skills: SkillSummary[];
  folder: FolderFile[];
  onChatChanged: (chat: Chat) => void;
};

export function ChatView({ chat, skills, folder, onChatChanged }: Props) {
  const [sending, setSending] = useState(false);
  const [pendingUpload, setPendingUpload] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const activeSkill = chat.active_skill
    ? skills.find((s) => s.id === chat.active_skill)
    : null;

  const pinnedFolderFiles = folder.filter((f) => chat.folder_pins.includes(f.id));

  async function send(text: string) {
    if (sending) return;
    setSending(true);
    try {
      await api.sendMessage(chat.id, text);
      const updated = await api.getChat(chat.id);
      onChatChanged(updated);
    } catch (e) {
      alert(`Send failed: ${e instanceof Error ? e.message : e}`);
    } finally {
      setSending(false);
    }
  }

  async function confirmSkill(yes: boolean) {
    await send(yes ? "yes" : "no");
  }

  async function uploadFile(label: string) {
    if (!pendingUpload) return;
    setUploading(true);
    try {
      await api.uploadChatFile(chat.id, pendingUpload, label);
      const updated = await api.getChat(chat.id);
      onChatChanged(updated);
      setPendingUpload(null);
    } catch (e) {
      alert(`Upload failed: ${e instanceof Error ? e.message : e}`);
    } finally {
      setUploading(false);
    }
  }

  async function deleteChatFile(fileId: string) {
    if (!confirm("Remove this document from the chat?")) return;
    try {
      await api.deleteChatFile(chat.id, fileId);
      const updated = await api.getChat(chat.id);
      onChatChanged(updated);
    } catch (e) {
      alert(`Delete failed: ${e instanceof Error ? e.message : e}`);
    }
  }

  async function unpinFolderFile(fileId: string) {
    const next = chat.folder_pins.filter((id) => id !== fileId);
    try {
      const updated = await api.patchChat(chat.id, { folder_pins: next });
      onChatChanged(updated);
    } catch (e) {
      alert(`Unpin failed: ${e instanceof Error ? e.message : e}`);
    }
  }

  return (
    <>
      <header className="chat-header">
        <div className="title">
          <span>{chat.title || "New chat"}</span>
          {activeSkill ? (
            <span className="skill-pill active" title={activeSkill.description}>
              ● {activeSkill.name}
            </span>
          ) : chat.pending_skill ? (
            <span className="skill-pill" title="Awaiting confirmation">
              ⏳ awaiting confirmation
            </span>
          ) : (
            <span className="skill-pill">No skill active</span>
          )}
        </div>
      </header>

      <MessageList chat={chat} skills={skills} pendingAssistant={sending} />

      {chat.pending_skill ? (
        <div style={{ padding: "0 24px 12px", maxWidth: 760, margin: "0 auto", width: "100%" }}>
          <SkillConfirmBanner
            pendingSkill={chat.pending_skill}
            skills={skills}
            disabled={sending}
            onConfirm={confirmSkill}
          />
        </div>
      ) : null}

      {(chat.files.length > 0 || pinnedFolderFiles.length > 0) ? (
        <div className="file-tray">
          {chat.files.length > 0 ? <span className="label">Chat files:</span> : null}
          {chat.files.map((f) => (
            <span key={f.id} className="file-pill" title={f.filename}>
              📎 {f.label}
              <button className="x" aria-label="Remove" onClick={() => deleteChatFile(f.id)}>
                ×
              </button>
            </span>
          ))}
          {pinnedFolderFiles.length > 0 ? <span className="label">Pinned:</span> : null}
          {pinnedFolderFiles.map((f) => (
            <span key={f.id} className="file-pill" title={f.filename}>
              📌 {f.label}
              <button className="x" aria-label="Unpin" onClick={() => unpinFolderFile(f.id)}>
                ×
              </button>
            </span>
          ))}
        </div>
      ) : null}

      <MessageInput
        disabled={sending}
        onSend={send}
        onPickFile={(f) => setPendingUpload(f)}
      />

      {pendingUpload ? (
        <UploadModal
          file={pendingUpload}
          busy={uploading}
          onCancel={() => setPendingUpload(null)}
          onSubmit={uploadFile}
        />
      ) : null}
    </>
  );
}
