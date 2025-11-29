"""Supabase helper for uploads and event POST."""

from __future__ import annotations

import json
import mimetypes
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


@dataclass
class SupabaseConfig:
    url: str
    key: str
    bucket: str = "events"

    @classmethod
    def from_env(cls) -> "SupabaseConfig":
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE") or os.environ.get("SUPABASE_ANON_KEY")
        if not url or not key:
            raise RuntimeError("Faltan variables de entorno SUPABASE_URL o SUPABASE_SERVICE_ROLE/ANON_KEY")
        return cls(url=url, key=key)


class SupabaseClient:
    def __init__(self, config: SupabaseConfig, session: Optional[requests.Session] = None):
        self.config = config
        self.session = session or requests.Session()

    def ensure_bucket(self, name: str, public: bool = True) -> None:
        url = f"{self.config.url}/storage/v1/bucket"
        resp = self.session.post(
            url,
            json={"name": name, "public": public},
            headers={
                "Authorization": f"Bearer {self.config.key}",
                "apikey": self.config.key,
                "Content-Type": "application/json",
            },
        )
        if resp.status_code in (200, 409):  # created or already exists
            return
        # Algunos proyectos devuelven 400 con mensaje Duplicate o Unauthorized (RLS)
        if resp.status_code == 400 and ("Duplicate" in resp.text or "Unauthorized" in resp.text):
            return
        # Si el rol (anon) no puede crear bucket pero ya existe, ignorar
        if resp.status_code == 403:
            return
        try:
            resp.raise_for_status()
        except Exception as exc:  # pragma: no cover - network path
            raise RuntimeError(f"Supabase ensure_bucket failed: {resp.status_code} {resp.text}") from exc

    # -------------------
    # Storage
    # -------------------
    def upload_file(self, local_path: str, dest_path: str, bucket: Optional[str] = None, content_type: Optional[str] = None) -> str:
        bucket_name = bucket or self.config.bucket
        url = f"{self.config.url}/storage/v1/object/{bucket_name}/{dest_path}"
        ctype = content_type or mimetypes.guess_type(local_path)[0] or "application/octet-stream"

        with open(local_path, "rb") as f:
            resp = self.session.put(
                url,
                data=f,
                headers={
                    "Authorization": f"Bearer {self.config.key}",
                    "apikey": self.config.key,
                    "Content-Type": ctype,
                    "x-upsert": "true",
                },
            )
        try:
            resp.raise_for_status()
        except Exception as exc:  # pragma: no cover - network path
            raise RuntimeError(f"Supabase upload failed: {resp.status_code} {resp.text}") from exc
        # Public bucket convention
        return f"{self.config.url}/storage/v1/object/public/{bucket_name}/{dest_path}"

    def upload_media_paths(self, media: Dict[str, Any], prefix: str, bucket: Optional[str] = None) -> Dict[str, Any]:
        bucket_name = bucket or self.config.bucket
        self.ensure_bucket(bucket_name, public=True)
        cover_url = ""
        logo_url = ""
        gallery_urls: List[str] = []

        if media.get("cover") and os.path.isfile(media["cover"]):
            cover_ext = Path(media["cover"]).suffix or ".webp"
            cover_dest = f"{prefix}/cover{cover_ext}"
            cover_url = self.upload_file(media["cover"], cover_dest, bucket=bucket_name)

        if media.get("logo") and os.path.isfile(media["logo"]):
            logo_ext = Path(media["logo"]).suffix or ".png"
            logo_dest = f"{prefix}/logo{logo_ext}"
            logo_url = self.upload_file(media["logo"], logo_dest, bucket=bucket_name)

        for idx, item in enumerate(media.get("gallery", []) or []):
            if item and os.path.isfile(item):
                dest = f"{prefix}/gallery_{idx:02d}{Path(item).suffix or '.webp'}"
                gallery_urls.append(self.upload_file(item, dest, bucket=bucket_name))

        return {"cover": cover_url, "logo": logo_url, "gallery": gallery_urls}

    # -------------------
    # REST API
    # -------------------
    def post_event(self, payload: Dict[str, Any], table: str = "events") -> Dict[str, Any]:
        url = f"{self.config.url}/rest/v1/{table}"
        resp = self.session.post(
            url,
            headers={
                "Authorization": f"Bearer {self.config.key}",
                "apikey": self.config.key,
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            },
            data=json.dumps(payload),
        )
        try:
            resp.raise_for_status()
        except Exception as exc:  # pragma: no cover - network path
            raise RuntimeError(f"Supabase post_event failed: {resp.status_code} {resp.text}") from exc
        try:
            return resp.json()
        except Exception:
            return {"status_code": resp.status_code, "text": resp.text}

    def delete_all(self, table: str = "events") -> int:
        """Delete all rows from a table. Returns affected row count."""
        url = f"{self.config.url}/rest/v1/{table}"
        resp = self.session.delete(
            url,
            headers={
                "Authorization": f"Bearer {self.config.key}",
                "apikey": self.config.key,
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            params={"id": "not.is.null"},
        )
        resp.raise_for_status()
        # PostgREST returns no content with Prefer=minimal; rely on status code
        return resp.status_code


__all__ = ["SupabaseClient", "SupabaseConfig"]
