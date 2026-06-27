from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
DEFAULT_TESSERACT_CANDIDATES = (
    Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
    Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
)


def resolve_asset_path(name: str) -> str:
    return str((ASSETS_DIR / name).resolve())


def select_tesseract_cmd(env: dict[str, str] | None = None, candidates: tuple[Path, ...] = DEFAULT_TESSERACT_CANDIDATES) -> str | None:
    env = os.environ if env is None else env
    override = (env.get("TESSERACT_CMD") or "").strip()
    if override:
        return override
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return None


def configure_tesseract_cmd(pytesseract_module, env: dict[str, str] | None = None, candidates: tuple[Path, ...] = DEFAULT_TESSERACT_CANDIDATES) -> str | None:
    command = select_tesseract_cmd(env=env, candidates=candidates)
    if command:
        pytesseract_module.pytesseract.tesseract_cmd = command
    return command
