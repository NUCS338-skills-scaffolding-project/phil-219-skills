import { ChatSummary } from "../api/client";

type Props = {
  chats: ChatSummary[];
  activeChatId: string | null;
  folderActive: boolean;
  onNewChat: () => void;
  onSelectChat: (chatId: string) => void;
  onDeleteChat: (chatId: string) => void;
  onOpenFolder: () => void;
};

export function Sidebar({
  chats,
  activeChatId,
  folderActive,
  onNewChat,
  onSelectChat,
  onDeleteChat,
  onOpenFolder,
}: Props) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-title">PHIL-219 TA</div>
        <button className="new-chat-btn" onClick={onNewChat}>
          <span aria-hidden>+</span>
          <span>New chat</span>
        </button>
      </div>
      <div className="chat-list">
        {chats.length === 0 ? (
          <div style={{ color: "#9b9b9b", padding: "8px 12px", fontSize: 13 }}>
            No chats yet.
          </div>
        ) : null}
        {chats.map((c) => (
          <button
            key={c.id}
            className={`chat-item${c.id === activeChatId ? " active" : ""}`}
            onClick={() => onSelectChat(c.id)}
            title={c.title}
          >
            <span className="title">{c.title || "New chat"}</span>
            <span
              className="delete"
              role="button"
              aria-label="Delete chat"
              onClick={(e) => {
                e.stopPropagation();
                if (confirm(`Delete "${c.title}"?`)) onDeleteChat(c.id);
              }}
            >
              ×
            </span>
          </button>
        ))}
      </div>
      <div className="sidebar-footer">
        <button
          className={`folder-link${folderActive ? " active" : ""}`}
          onClick={onOpenFolder}
          title="Shared knowledge base"
        >
          <span aria-hidden>📁</span>
          <span>Shared Folder</span>
        </button>
      </div>
    </aside>
  );
}
