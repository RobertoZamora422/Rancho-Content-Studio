from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def normalize_optional_path(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def resolve_tool_path(configured_path: str | None, executable_name: str) -> tuple[str | None, str | None]:
    normalized_path = normalize_optional_path(configured_path)
    if normalized_path:
        path = Path(normalized_path).expanduser()
        if path.is_file():
            return str(path.resolve()), None
        return None, f"No se encontro el ejecutable configurado: {normalized_path}"

    discovered = shutil.which(executable_name)
    if discovered:
        return discovered, None
    return None, f"No se encontro {executable_name} en PATH ni en la configuracion local."


def read_tool_version(command: str, args: list[str], timeout_seconds: int = 5) -> tuple[str | None, str | None]:
    try:
        completed = subprocess.run(
            [command, *args],
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout_seconds,
        )
    except OSError as error:
        return None, str(error)
    except subprocess.TimeoutExpired:
        return None, "La validacion excedio el tiempo de espera."

    output = (completed.stdout or completed.stderr).strip()
    if completed.returncode != 0:
        return None, output or f"El comando finalizo con codigo {completed.returncode}."

    first_line = output.splitlines()[0] if output else None
    return first_line, None
