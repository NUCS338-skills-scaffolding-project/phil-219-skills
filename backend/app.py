"""FastAPI entry point for the Teaching Assistant chat app."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.services.storage import init_storage
from backend.services.skill_registry import load_skills
from backend.routers import chats, messages, uploads, skills


def create_app() -> FastAPI:
    init_storage()
    load_skills()

    app = FastAPI(title="PHIL-219 Teaching Assistant", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(chats.router)
    app.include_router(messages.router)
    app.include_router(uploads.router)
    app.include_router(skills.router)

    @app.get("/api/health")
    def health() -> dict:
        return {"ok": True}

    return app


app = create_app()
