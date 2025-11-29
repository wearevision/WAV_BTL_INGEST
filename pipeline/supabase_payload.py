"""Helpers to build Supabase-ready payloads for WAV events."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pipeline.text_generator import WavEvent


def _safe_str(value: Any) -> str:
    return "" if value is None else str(value)


def _safe_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return [item for item in value if item is not None]
    if isinstance(value, tuple):
        return [item for item in value if item is not None]
    return [value]


def build_supabase_event_payload(
    wav_event: WavEvent,
    media: Dict[str, Any],
    override_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Serializa WavEvent + media en el payload final para Supabase."""

    cover_url = _safe_str(media.get("cover")) if media else ""
    logo_url = _safe_str(media.get("logo")) if media else ""
    gallery_urls = _safe_list(media.get("gallery")) if media else []

    payload: Dict[str, Any] = {
        "id": override_id if override_id is not None else None,
        "brand": _safe_str(wav_event.brand),
        "title": _safe_str(wav_event.title),
        "slug": _safe_str(wav_event.slug),
        "category": _safe_str(wav_event.category),
        "year": getattr(wav_event, "year", None),
        "summary": _safe_str(wav_event.summary),
        "description": _safe_str(wav_event.description),
        "highlights": _safe_list(getattr(wav_event, "highlights", [])),
        "keywords": _safe_list(getattr(wav_event, "keywords", [])),
        "hashtags": _safe_list(getattr(wav_event, "hashtags", [])),
        "instagram_hook": _safe_str(wav_event.instagram_hook),
        "instagram_body": _safe_str(wav_event.instagram_body),
        "instagram_closing": _safe_str(wav_event.instagram_closing),
        "instagram_hashtags": _safe_str(wav_event.instagram_hashtags),
        "alt_instagram": _safe_str(wav_event.alt_instagram),
        "linkedin_post": _safe_str(wav_event.linkedin_post),
        "linkedin_article": _safe_str(wav_event.linkedin_article),
        "alt_title_1": _safe_str(wav_event.alt_title_1),
        "alt_title_2": _safe_str(wav_event.alt_title_2),
        "needs_review": bool(getattr(wav_event, "needs_review", False)),
        "image": cover_url,
        "logo": logo_url,
        "gallery": _safe_list(gallery_urls),
    }

    return payload


__all__ = ["build_supabase_event_payload"]
