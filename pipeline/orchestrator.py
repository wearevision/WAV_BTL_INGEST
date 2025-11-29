"""Orchestrator for the WAV BTL ingest pipeline.

Composes visual classification, text generation, media processing and payload
building. It avoids external side-effects (no uploads) and keeps dependency
injection to make testing simple.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

from pipeline.classifier_gemini import VisualClassification, classify_event_visual
from pipeline.media_processor import extract_frames, process_images_to_webp
from pipeline.supabase_payload import build_supabase_event_payload
from pipeline.supabase_client import SupabaseClient
from pipeline.text_generator import WavEvent, generate_event_content
from pipeline import video_processor as vp


ClassifierFn = Callable[..., VisualClassification]
TextGenFn = Callable[..., WavEvent]


@dataclass
class IngestResult:
    wav_event: WavEvent
    visual: VisualClassification
    media: Dict[str, Any]
    payload: Dict[str, Any]
    artifacts: Dict[str, Any]
    supabase_response: Optional[Dict[str, Any]] = None


def _discover_media(event_dir: str) -> Dict[str, List[str]]:
    images_ext = {".jpg", ".jpeg", ".png", ".webp"}
    videos_ext = {".mp4", ".mov", ".m4v", ".avi", ".mkv"}
    images: List[str] = []
    videos: List[str] = []

    for root, _, files in os.walk(event_dir):
        for fname in files:
            ext = Path(fname).suffix.lower()
            fpath = os.path.join(root, fname)
            if ext in images_ext:
                images.append(fpath)
            elif ext in videos_ext:
                videos.append(fpath)

    images.sort()
    videos.sort()
    return {"images": images, "videos": videos}


def _choose_classification_inputs(images: Sequence[str], videos: Sequence[str], tmp_dir: str) -> List[str]:
    if images:
        return list(images)
    if videos:
        # Fallback: extract a few frames from the first video
        return extract_frames(videos[0], output_dir=os.path.join(tmp_dir, "frames"), every_n_seconds=2.0, max_frames=3)
    return []


def ingest_event_directory(
    event_dir: str,
    output_dir: str,
    base_event_data: Optional[Dict[str, Any]] = None,
    *,
    gemini_model: str = "gemini-2.0-flash",
    gemini_temperature: float = 0.0,
    gemini_client: Any = None,
    text_provider: str = "openai",
    text_model: Optional[str] = None,
    text_temperature: float = 0.3,
    ffmpeg_path: Optional[str] = None,
    classifier_fn: ClassifierFn = classify_event_visual,
    text_fn: TextGenFn = generate_event_content,
    override_id: Optional[str] = None,
    supabase_client: Optional[SupabaseClient] = None,
    supabase_bucket: str = "events",
    supabase_prefix: Optional[str] = None,
    supabase_table: str = "events",
    upload_to_supabase: bool = False,
) -> IngestResult:
    """Process one event folder end-to-end and return all generated artifacts."""

    event_dir_path = Path(event_dir)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    discovered = _discover_media(str(event_dir_path))
    images = discovered["images"]
    videos = discovered["videos"]

    artifacts: Dict[str, Any] = {}

    # Media processing: images -> WebP + cover
    media_result = process_images_to_webp(images, os.path.join(out_dir, "images")) if images else {"webp": [], "cover": ""}
    artifacts["images"] = media_result

    gallery: List[str] = list(media_result.get("webp", []))
    cover_url = media_result.get("cover", "")
    logo_url = ""

    # Media processing: videos -> 720p transcodes + thumbnail
    video_outputs: List[str] = []
    if videos:
        videos_out_dir = out_dir / "videos"
        videos_out_dir.mkdir(parents=True, exist_ok=True)
        for idx, vid in enumerate(videos):
            out_vid = videos_out_dir / f"video_{idx:02d}_720p.mp4"
            video_outputs.append(vp.transcode_to_720p(vid, str(out_vid), ffmpeg_path=ffmpeg_path))
        gallery.extend(video_outputs)
        artifacts["videos"] = video_outputs

        if not cover_url:
            thumb_path = videos_out_dir / "cover_thumb.jpg"
            cover_url = vp.generate_thumbnail(videos[0], str(thumb_path), ffmpeg_path=ffmpeg_path)

    # Classification inputs: prefer images, else frames from first video
    classify_inputs = _choose_classification_inputs(images, videos, tmp_dir=str(out_dir))
    visual = classifier_fn(
        classify_inputs,
        model=gemini_model,
        temperature=gemini_temperature,
        client=gemini_client,
    )

    # Build base event data for text generation using classification hints
    event_data: Dict[str, Any] = {} if base_event_data is None else dict(base_event_data)
    event_data.setdefault("brand", visual.brand)
    event_data.setdefault("category", visual.category)
    event_data.setdefault("year", visual.year)
    event_data.setdefault("visual_keywords", visual.visual_keywords)
    event_data.setdefault("title_hint", visual.title_base)

    wav_event = text_fn(
        event_data,
        provider=text_provider,
        model=text_model,
        temperature=text_temperature,
    )

    media_payload = {
        "cover": cover_url,
        "logo": logo_url,
        "gallery": gallery,
    }

    # Opcional: subir a Supabase y reemplazar paths por URLs públicas
    uploaded_media = None
    if upload_to_supabase and supabase_client is not None:
        prefix = supabase_prefix or wav_event.slug
        uploaded_media = supabase_client.upload_media_paths(media_payload, prefix=prefix, bucket=supabase_bucket)
        media_payload = uploaded_media

    payload = build_supabase_event_payload(wav_event, media_payload, override_id=override_id)

    supabase_resp = None
    if upload_to_supabase and supabase_client is not None:
        supabase_resp = supabase_client.post_event(payload, table=supabase_table)

    artifacts["classification_inputs"] = classify_inputs
    artifacts["gallery"] = gallery
    if uploaded_media:
        artifacts["uploaded_media"] = uploaded_media

    return IngestResult(
        wav_event=wav_event,
        visual=visual,
        media=media_payload,
        payload=payload,
        artifacts=artifacts,
        supabase_response=supabase_resp,
    )


__all__ = ["ingest_event_directory", "IngestResult"]
