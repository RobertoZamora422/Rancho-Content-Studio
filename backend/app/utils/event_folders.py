from __future__ import annotations

import re
import unicodedata
from datetime import date
from pathlib import Path

WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}

EVENT_SUBDIRECTORIES = (
    "01_Originales",
    "02_Seleccionados",
    "03_Descartados_Logicos",
    "04_Mejorados",
    "05_Reels",
    "06_Carruseles",
    "07_Historias",
    "08_Copies",
    "09_Listo_Para_Publicar",
    "10_Publicado",
    "metadata",
)


def safe_windows_name(value: str, fallback: str = "Evento") -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_value = re.sub(r'[<>:"/\\|?*\x00-\x1F]', " ", ascii_value)
    ascii_value = re.sub(r"\s+", "_", ascii_value.strip())
    ascii_value = re.sub(r"_+", "_", ascii_value)
    ascii_value = ascii_value.strip(" ._")

    if not ascii_value:
        ascii_value = fallback

    if ascii_value.upper() in WINDOWS_RESERVED_NAMES:
        ascii_value = f"{ascii_value}_Evento"

    return ascii_value[:120]


def build_event_folder_name(event_date: date, name: str) -> str:
    return f"{event_date.isoformat()}_{safe_windows_name(name)}"


def unique_event_directory(root_path: Path, folder_name: str) -> Path:
    candidate = root_path / folder_name
    if not candidate.exists():
        return candidate

    for index in range(2, 1000):
        next_candidate = root_path / f"{folder_name}_{index:02d}"
        if not next_candidate.exists():
            return next_candidate

    raise RuntimeError("No se pudo generar una carpeta unica para el evento.")


def create_event_directory_tree(root_path: Path, folder_name: str) -> Path:
    event_path = unique_event_directory(root_path, folder_name)
    event_path.mkdir(parents=False, exist_ok=False)
    for subdirectory in EVENT_SUBDIRECTORIES:
        (event_path / subdirectory).mkdir()
    return event_path
