# PHIL-219 Teaching Assistant

A ChatGPT-style web app that wraps the five Socratic teaching skills defined
in [`skills/`](skills/) (Passage Identification, Key Idea Extraction,
Evidence Interpretation, Assumption Surfacing, Counterview Consideration)
inside a multi-chat UI with per-chat file uploads and a global shared PDF
folder.

## Architecture at a glance

```
phil-219-skills/
├── backend/              FastAPI app
│   ├── app.py            entry (uvicorn target)
│   ├── routers/          chats, messages, uploads, skills
│   └── services/
│       ├── skill_registry.py   auto-loads every skills/<id>/{skills.md,logic.py}
│       ├── skill_detector.py   keyword + LLM-fallback skill detection
│       ├── chat_engine.py      detect → confirm → run() orchestration
│       ├── pdf_extract.py      pypdf-based text extraction
│       └── storage.py          JSON-on-disk persistence
├── frontend/             React + Vite + TypeScript SPA
│   └── src/components    Sidebar, ChatView, MessageList, MessageInput,
│                         SkillConfirmBanner, FolderPanel, UploadModal
├── skills/               unchanged — each subfolder is a self-contained skill
└── requirements.txt
```

The backend serves `/api/*`. The frontend dev server (Vite) proxies `/api`
to `http://127.0.0.1:8000`.

## Setup

```bash
# 1. Backend deps
pip install -r requirements.txt

# 2. Frontend deps
cd frontend && npm install && cd ..

# 3. OpenAI key
cp .env.example .env       # if you haven't already
# put your key into .env: OPENAI_API_KEY=sk-...
```

## Run (two terminals)

```bash
# terminal 1 — backend
uvicorn backend.app:app --reload --port 8000

# terminal 2 — frontend
cd frontend && npm run dev
```

Then open [http://localhost:5173](http://localhost:5173).

## How the skill router works

When you send a message, the assistant:

1. Runs a **keyword detector** over the message (per-skill phrase + word
   bags in `backend/services/skill_detector.py`).
2. If no keyword wins clearly, falls back to a tiny **LLM classifier**
   (`gpt-4o`) that picks the best-fitting skill from the registry.
3. **Confirms with you** before activating: *"It sounds like you may need
   help with **Passage Identification**. Is that correct?"* Yes/No buttons
   appear directly under the message.
4. On *yes*, the chat is locked into that skill — every subsequent
   message is routed through `skills/<id>/logic.py:run()`.

## Documents

- **Per-chat upload** — paperclip in the composer. You give each upload a
  custom label that the assistant uses when referencing it.
- **Shared Folder** — bottom of the sidebar. Drop PDFs that should be
  reusable across all chats. From any chat, open the folder and click
  *Pin to chat* to make a PDF part of that chat's reading context.

Uploaded PDFs are text-extracted on upload (`pypdf`) and the extracted
text is cached alongside the raw file in `backend/data/files/`. PDFs and
chats persist across restarts via `backend/data/{chats.json,folder.json}`.

## Adding a sixth skill

1. Create `skills/<new-skill>/skills.md` with YAML frontmatter and a body
   that serves as the system prompt.
2. Create `skills/<new-skill>/logic.py` exposing
   `run(input: dict) -> str` (mirror any of the existing skills).
3. Optionally add an entry to `SKILL_KEYWORDS` in
   `backend/services/skill_detector.py` to bias keyword detection. Even
   without it, the LLM-classifier fallback will route to the new skill
   based on its name and description.

No changes to routers or the frontend are required — the registry
auto-discovers new folders on backend startup.
