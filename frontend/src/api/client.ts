export type SkillSummary = {
  id: string;
  name: string;
  tags: string[];
  description: string;
};

export type ChatSummary = {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  active_skill: string | null;
  pending_skill: string | null;
  message_count: number;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  file_ids: string[];
  created_at: string;
};

export type ChatFile = {
  id: string;
  label: string;
  filename: string;
  size: number;
  has_text: boolean;
};

export type Chat = {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  active_skill: string | null;
  pending_skill: string | null;
  messages: ChatMessage[];
  files: ChatFile[];
  folder_pins: string[];
};

export type FolderFile = ChatFile;

export type SendMessageResponse = {
  user_message: ChatMessage;
  assistant_message: ChatMessage;
  chat: {
    id: string;
    title: string;
    active_skill: string | null;
    pending_skill: string | null;
  };
  state_change: Record<string, unknown>;
};

async function jsonFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.json();
}

export const api = {
  listSkills: () =>
    jsonFetch<{ skills: SkillSummary[] }>("/api/skills"),

  listChats: () =>
    jsonFetch<{ chats: ChatSummary[] }>("/api/chats"),

  getChat: (chatId: string) =>
    jsonFetch<Chat>(`/api/chats/${chatId}`),

  createChat: (title?: string) =>
    jsonFetch<Chat>("/api/chats", {
      method: "POST",
      body: JSON.stringify({ title: title || "New chat" }),
    }),

  deleteChat: (chatId: string) =>
    jsonFetch<{ ok: boolean }>(`/api/chats/${chatId}`, { method: "DELETE" }),

  patchChat: (chatId: string, patch: Partial<Pick<Chat, "title" | "folder_pins" | "active_skill">>) =>
    jsonFetch<Chat>(`/api/chats/${chatId}`, {
      method: "PATCH",
      body: JSON.stringify(patch),
    }),

  sendMessage: (chatId: string, content: string, fileIds: string[] = []) =>
    jsonFetch<SendMessageResponse>(`/api/chats/${chatId}/messages`, {
      method: "POST",
      body: JSON.stringify({ content, file_ids: fileIds }),
    }),

  uploadChatFile: async (chatId: string, file: File, label: string): Promise<ChatFile> => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("label", label);
    const res = await fetch(`/api/chats/${chatId}/files`, { method: "POST", body: fd });
    if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
    return res.json();
  },

  deleteChatFile: (chatId: string, fileId: string) =>
    jsonFetch<{ ok: boolean }>(`/api/chats/${chatId}/files/${fileId}`, { method: "DELETE" }),

  listFolder: () =>
    jsonFetch<{ files: FolderFile[] }>("/api/folder"),

  uploadFolderFile: async (file: File, label: string): Promise<FolderFile> => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("label", label);
    const res = await fetch("/api/folder", { method: "POST", body: fd });
    if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
    return res.json();
  },

  patchFolderFile: (fileId: string, patch: { label?: string }) =>
    jsonFetch<FolderFile>(`/api/folder/${fileId}`, {
      method: "PATCH",
      body: JSON.stringify(patch),
    }),

  deleteFolderFile: (fileId: string) =>
    jsonFetch<{ ok: boolean }>(`/api/folder/${fileId}`, { method: "DELETE" }),
};
