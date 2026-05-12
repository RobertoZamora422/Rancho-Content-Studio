from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import SessionLocal, init_database
from app.services.reset_service import reset_operational_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Resetea datos operativos locales de prueba sin borrar archivos fisicos. "
            "Por defecto solo muestra lo que eliminaria."
        )
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Ejecuta el reset. Sin esta bandera el script corre en modo simulacion.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    init_database()
    with SessionLocal() as db:
        result = reset_operational_data(db, dry_run=not args.yes)

    mode = "SIMULACION" if result.dry_run else "RESET EJECUTADO"
    print(f"{mode}: datos operativos locales")
    for table_name, count in result.deleted_counts.items():
        print(f"- {table_name}: {count}")
    if result.dry_run:
        print("No se modifico la base. Ejecuta con --yes para aplicar.")
    else:
        print("Seed base restaurado. No se borraron carpetas ni archivos del usuario.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
