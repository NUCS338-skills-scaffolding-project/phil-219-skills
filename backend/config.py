"""Backend paths and configuration constants."""
import os

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BACKEND_DIR)
SKILLS_DIR = os.path.join(ROOT_DIR, "skills")

DATA_DIR = os.path.join(BACKEND_DIR, "data")
FILES_DIR = os.path.join(DATA_DIR, "files")
CHATS_PATH = os.path.join(DATA_DIR, "chats.json")
FOLDER_PATH = os.path.join(DATA_DIR, "folder.json")

MAX_PASSAGE_CHARS = 30_000

SKIP_SKILL_FOLDERS = {"shared", "example-skill", "__pycache__"}


def ensure_data_dirs() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(FILES_DIR, exist_ok=True)
