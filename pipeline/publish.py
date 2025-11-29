"""CLI helper to purge fake data and publish new events to Supabase."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv  # type: ignore[import-not-found]

from pipeline.orchestrator import ingest_event_directory
from pipeline.supabase_client import SupabaseClient, SupabaseConfig


def _iter_event_dirs(base_dir: str) -> List[Path]:
    base = Path(base_dir)
    return [p for p in base.iterdir() if p.is_dir()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Publica eventos a Supabase (limpia datos falsos si se pide).")
    parser.add_argument("base_dir", help="Carpeta que contiene subcarpetas de eventos (fotos/videos).")
    parser.add_argument("--output-dir", default="output", help="Carpeta para artefactos temporales.")
    parser.add_argument("--table", default="kv_store_c4bb2206_rows", help="Tabla Supabase a poblar.")
    parser.add_argument("--bucket", default="events", help="Bucket de Storage para media.")
    parser.add_argument("--purge", action="store_true", help="Borra todos los registros existentes antes de insertar.")
    parser.add_argument("--gemini-model", default="gemini-2.0-flash", help="Modelo Gemini Vision.")
    parser.add_argument("--text-provider", default="openai", help="Proveedor de texto: openai|gemini.")
    args = parser.parse_args()

    load_dotenv()
    config = SupabaseConfig.from_env()
    client = SupabaseClient(config)

    if args.purge:
        print(f"Purging table {args.table}...")
        client.delete_all(args.table)

    event_dirs = _iter_event_dirs(args.base_dir)
    if not event_dirs:
        print("No se encontraron carpetas de eventos.")
        return

    print(f"Procesando {len(event_dirs)} eventos...")
    for event_dir in sorted(event_dirs):
        prefix = event_dir.name
        out_dir = os.path.join(args.output_dir, prefix)
        print(f"- {prefix}: ingest + upload")
        result = ingest_event_directory(
            str(event_dir),
            out_dir,
            gemini_model=args.gemini_model,
            text_provider=args.text_provider,
            supabase_client=client,
            upload_to_supabase=True,
            supabase_bucket=args.bucket,
            supabase_table=args.table,
            supabase_prefix=prefix,
        )
        print(f"  -> slug: {result.payload.get('slug')} | supabase id: {result.supabase_response}")


if __name__ == "__main__":
    main()
