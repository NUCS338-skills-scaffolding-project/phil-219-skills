import { useCallback, useEffect, useState } from "react";
import { Sidebar } from "./components/Sidebar";
import { ChatView } from "./components/ChatView";
import { FolderPanel } from "./components/FolderPanel";
import { api, Chat, ChatSummary, FolderFile, SkillSummary } from "./api/client";

type View = { kind: "chat" } | { kind: "folder" };

export default function App() {
  const [chats, setChats] = useState<ChatSummary[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [activeChat, setActiveChat] = useState<Chat | null>(null);
  const [folder, setFolder] = useState<FolderFile[]>([]);
  const [skills, setSkills] = useState<SkillSummary[]>([]);
  const [view, setView] = useState<View>({ kind: "chat" });
  const [error, setError] = useState<string | null>(null);

  const refreshChats = useCallback(async () => {
    try {
      const { chats } = await api.listChats();
      setChats(chats);
      return chats;
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load chats");
      return [];
    }
  }, []);

  const refreshFolder = useCallback(async () => {
    try {
      const { files } = await api.listFolder();
      setFolder(files);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load folder");
    }
  }, []);

  const refreshSkills = useCallback(async () => {
    try {
      const { skills } = await api.listSkills();
      setSkills(skills);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load skills");
    }
  }, []);

  const loadChat = useCallback(async (chatId: string) => {
    try {
      const chat = await api.getChat(chatId);
      setActiveChat(chat);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load chat");
    }
  }, []);

  useEffect(() => {
    (async () => {
      await Promise.all([refreshSkills(), refreshFolder()]);
      const list = await refreshChats();
      if (list.length > 0) {
        setActiveChatId(list[0].id);
      } else {
        const fresh = await api.createChat("New chat");
        setActiveChat(fresh);
        setActiveChatId(fresh.id);
        await refreshChats();
      }
    })().catch((e) => setError(String(e)));
  }, [refreshSkills, refreshFolder, refreshChats]);

  useEffect(() => {
    if (activeChatId) loadChat(activeChatId);
  }, [activeChatId, loadChat]);

  const handleNewChat = useCallback(async () => {
    try {
      const fresh = await api.createChat("New chat");
      setActiveChat(fresh);
      setActiveChatId(fresh.id);
      setView({ kind: "chat" });
      await refreshChats();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to create chat");
    }
  }, [refreshChats]);

  const handleSelectChat = useCallback((chatId: string) => {
    setActiveChatId(chatId);
    setView({ kind: "chat" });
  }, []);

  const handleDeleteChat = useCallback(
    async (chatId: string) => {
      try {
        await api.deleteChat(chatId);
        const list = await refreshChats();
        if (activeChatId === chatId) {
          if (list.length > 0) {
            setActiveChatId(list[0].id);
          } else {
            const fresh = await api.createChat("New chat");
            setActiveChat(fresh);
            setActiveChatId(fresh.id);
            await refreshChats();
          }
        }
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to delete chat");
      }
    },
    [activeChatId, refreshChats]
  );

  const handleChatChanged = useCallback(
    (chat: Chat) => {
      setActiveChat(chat);
      refreshChats();
    },
    [refreshChats]
  );

  const handleFolderChanged = useCallback(() => {
    refreshFolder();
  }, [refreshFolder]);

  const handleOpenFolder = useCallback(() => setView({ kind: "folder" }), []);

  return (
    <div className="app-shell">
      <Sidebar
        chats={chats}
        activeChatId={view.kind === "chat" ? activeChatId : null}
        folderActive={view.kind === "folder"}
        onNewChat={handleNewChat}
        onSelectChat={handleSelectChat}
        onDeleteChat={handleDeleteChat}
        onOpenFolder={handleOpenFolder}
      />
      <main className="main-pane">
        {error ? <div className="error-banner">{error}</div> : null}
        {view.kind === "folder" ? (
          <FolderPanel
            files={folder}
            chat={activeChat}
            onChanged={handleFolderChanged}
            onChatChanged={handleChatChanged}
          />
        ) : activeChat ? (
          <ChatView
            chat={activeChat}
            skills={skills}
            folder={folder}
            onChatChanged={handleChatChanged}
          />
        ) : (
          <div className="empty-state">
            <h2>Loading…</h2>
          </div>
        )}
      </main>
    </div>
  );
}
