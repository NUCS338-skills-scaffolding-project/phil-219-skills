"""GET /api/skills — list discovered teaching skills for the UI."""
from __future__ import annotations

from fastapi import APIRouter

from backend.services.skill_registry import all_skills

router = APIRouter(prefix="/api", tags=["skills"])


@router.get("/skills")
def list_skills():
    return {"skills": [s.to_public() for s in all_skills()]}
