import { useRef, useState } from "react";
import { api, Chat, FolderFile } from "../api/client";
import { UploadModal } from "./UploadModal";

type Props = {
  files: FolderFile[];
  chat: Chat | null;
  onChanged: () => void;
  onChatChanged: (chat: Chat) => void;
};

export function FolderPanel({ files, chat, onChanged, onChatChanged }: Props) {
  const [pendingUpload, setPendingUpload] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement | null>(null);

  function pickFile() {
    inputRef.current?.click();
  }

  function onInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (f) setPendingUpload(f);
    e.target.value = "";
  }

  function onDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files?.[0];
    if (f) setPendingUpload(f);
  }

  async function upload(label: string) {
    if (!pendingUpload) return;
    setUploading(true);
    try {
      await api.uploadFolderFile(pendingUpload, label);
      setPendingUpload(null);
      onChanged();
    } catch (e) {
      alert(`Upload failed: ${e instanceof Error ? e.message : e}`);
    } finally {
      setUploading(false);
    }
  }

  async function rename(file: FolderFile) {
    const next = prompt("New label:", file.label);
    if (!next || next === file.label) return;
    try {
      await api.patchFolderFile(file.id, { label: next.trim() });
      onChanged();
    } catch (e) {
      alert(`Rename failed: ${e instanceof Error ? e.message : e}`);
    }
  }

  async function remove(file: FolderFile) {
    if (!confirm(`Delete "${file.label}" from the shared folder?`)) return;
    try {
      await api.deleteFolderFile(file.id);
      onChanged();
    } catch (e) {
      alert(`Delete failed: ${e instanceof Error ? e.message : e}`);
    }
  }

  async function togglePin(file: FolderFile) {
    if (!chat) return;
    const isPinned = chat.folder_pins.includes(file.id);
    const next = isPinned
      ? chat.folder_pins.filter((id) => id !== file.id)
      : [...chat.folder_pins, file.id];
    try {
      const updated = await api.patchChat(chat.id, { folder_pins: next });
      onChatChanged(updated);
    } catch (e) {
      alert(`Pin update failed: ${e instanceof Error ? e.message : e}`);
    }
  }

  return (
    <div className="folder-panel">
      <h1>Shared Folder</h1>
      <p className="subtitle">
        PDFs in this folder are available across all chats. Pin one into the active chat to make
        the assistant treat it as required reading for that conversation.
      </p>

      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.txt,.md,.markdown"
        style={{ display: "none" }}
        onChange={onInputChange}
      />

      <div
        className={`dropzone${dragging ? " dragging" : ""}`}
        onClick={pickFile}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        <strong>Drop a PDF here</strong>
        <div style={{ marginTop: 6, fontSize: 13 }}>or click to choose a file</div>
      </div>

      {chat ? (
        <div style={{ fontSize: 13, color: "#6b7280", marginBottom: 12 }}>
          Pinning into chat: <strong style={{ color: "#111" }}>{chat.title}</strong>
        </div>
      ) : null}

      <div className="section-divider">{files.length} document{files.length === 1 ? "" : "s"}</div>

      <div className="folder-files">
        {files.length === 0 ? (
          <div style={{ color: "#6b7280", fontSize: 14 }}>
            No PDFs uploaded yet — drop one above to start your shared knowledge base.
          </div>
        ) : null}
        {files.map((f) => {
          const isPinned = chat ? chat.folder_pins.includes(f.id) : false;
          return (
            <div key={f.id} className="folder-file">
              <span className="icon">PDF</span>
              <div className="label">
                {f.label}
                <div className="filename">
                  {f.filename} · {(f.size / 1024).toFixed(1)} KB
                  {!f.has_text ? " · text not extracted" : ""}
                </div>
              </div>
              <div className="actions">
                {chat ? (
                  <button
                    className={isPinned ? "pinned" : ""}
                    onClick={() => togglePin(f)}
                    title={isPinned ? "Unpin from chat" : "Pin to chat"}
                  >
                    {isPinned ? "📌 Pinned" : "Pin to chat"}
                  </button>
                ) : null}
                <button onClick={() => rename(f)}>Rename</button>
                <a
                  className="btn"
                  href={`/api/folder/${f.id}/download`}
                  target="_blank"
                  rel="noreferrer"
                  style={{ padding: "5px 10px", fontSize: 12, textDecoration: "none", color: "inherit", border: "1px solid var(--border-strong)", borderRadius: 5 }}
                >
                  Open
                </a>
                <button className="danger" onClick={() => remove(f)}>Delete</button>
              </div>
            </div>
          );
        })}
      </div>

      {pendingUpload ? (
        <UploadModal
          file={pendingUpload}
          busy={uploading}
          onCancel={() => setPendingUpload(null)}
          onSubmit={upload}
        />
      ) : null}
    </div>
  );
}
