"""File upload endpoints for per-chat documents and the global folder."""
from __future__ import annotations

import os
import uuid
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.config import FILES_DIR
from backend.services import storage
from backend.services.pdf_extract import extract_text, write_text_cache

router = APIRouter(prefix="/api", tags=["uploads"])


def _safe_extension(filename: str) -> str:
    ext = os.path.splitext(filename or "")[1].lower()
    if not ext or len(ext) > 10:
        return ""
    return ext


def _save_upload(file: UploadFile, prefix: str) -> tuple[str, str, str, int]:
    ext = _safe_extension(file.filename or "")
    file_id = f"{prefix}_{uuid.uuid4().hex[:10]}"
    disk_name = f"{file_id}{ext}"
    disk_path = os.path.join(FILES_DIR, disk_name)
    contents = file.file.read()
    with open(disk_path, "wb") as f:
        f.write(contents)
    return file_id, disk_name, disk_path, len(contents)


# ---------- Per-chat ----------

@router.post("/chats/{chat_id}/files")
def upload_chat_file(
    chat_id: str,
    file: UploadFile = File(...),
    label: str = Form(...),
):
    if not storage.get_chat(chat_id):
        raise HTTPException(status_code=404, detail="Chat not found")
    file_id, disk_name, disk_path, size = _save_upload(file, prefix="f")
    text = extract_text(disk_path)
    if text:
        write_text_cache(os.path.join(FILES_DIR, f"{file_id}.txt"), text)

    meta = {
        "id": file_id,
        "label": label or (file.filename or "Document"),
        "filename": file.filename or disk_name,
        "size": size,
        "disk_name": disk_name,
        "has_text": bool(text),
    }
    storage.add_chat_file(chat_id, meta)
    return meta


@router.delete("/chats/{chat_id}/files/{file_id}")
def delete_chat_file(chat_id: str, file_id: str):
    meta = storage.get_chat_file(chat_id, file_id)
    if not meta:
        raise HTTPException(status_code=404, detail="File not found")
    if not storage.remove_chat_file(chat_id, file_id):
        raise HTTPException(status_code=404, detail="File not found")
    _delete_disk_files(meta.get("disk_name"), file_id)
    return {"ok": True}


# ---------- Global folder ----------

class PatchFolderFileBody(BaseModel):
    label: Optional[str] = None


@router.get("/folder")
def list_folder():
    return {"files": storage.list_folder_files()}


@router.post("/folder")
def upload_folder_file(
    file: UploadFile = File(...),
    label: str = Form(...),
):
    file_id, disk_name, disk_path, size = _save_upload(file, prefix="gf")
    text = extract_text(disk_path)
    if text:
        write_text_cache(os.path.join(FILES_DIR, f"{file_id}.txt"), text)

    meta = {
        "id": file_id,
        "label": label or (file.filename or "Document"),
        "filename": file.filename or disk_name,
        "size": size,
        "disk_name": disk_name,
        "has_text": bool(text),
    }
    storage.add_folder_file(meta)
    return meta


@router.patch("/folder/{file_id}")
def patch_folder_file(file_id: str, body: PatchFolderFileBody):
    fields = {k: v for k, v in body.dict(exclude_unset=True).items() if v is not None}
    meta = storage.update_folder_file(file_id, **fields)
    if not meta:
        raise HTTPException(status_code=404, detail="File not found")
    return meta


@router.delete("/folder/{file_id}")
def delete_folder_file(file_id: str):
    meta = storage.get_folder_file(file_id)
    if not meta:
        raise HTTPException(status_code=404, detail="File not found")
    if not storage.remove_folder_file(file_id):
        raise HTTPException(status_code=404, detail="File not found")
    _delete_disk_files(meta.get("disk_name"), file_id)
    return {"ok": True}


@router.get("/folder/{file_id}/download")
def download_folder_file(file_id: str):
    meta = storage.get_folder_file(file_id)
    if not meta:
        raise HTTPException(status_code=404, detail="File not found")
    disk_path = os.path.join(FILES_DIR, meta.get("disk_name", ""))
    if not os.path.isfile(disk_path):
        raise HTTPException(status_code=404, detail="File missing on disk")
    return FileResponse(disk_path, filename=meta.get("filename") or "document.pdf")


def _delete_disk_files(disk_name: Optional[str], file_id: str) -> None:
    if disk_name:
        try:
            os.remove(os.path.join(FILES_DIR, disk_name))
        except OSError:
            pass
    txt_path = os.path.join(FILES_DIR, f"{file_id}.txt")
    try:
        os.remove(txt_path)
    except OSError:
        pass
