"""Lightweight media helpers: frames, WebP conversion, covers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List, Sequence

from PIL import Image, ImageOps


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _as_list(values: Iterable[str]) -> List[str]:
    return [v for v in values if v is not None]


def convert_to_webp(image_path: str, output_dir: str, quality: int = 90) -> str:
    """Convert a single image to WebP and return destination path."""
    out_dir = Path(output_dir)
    _ensure_dir(out_dir)
    dest = out_dir / (Path(image_path).stem + ".webp")

    with Image.open(image_path) as im:
        im = ImageOps.exif_transpose(im)
        im = im.convert("RGB")
        im.save(dest, format="WEBP", quality=quality, method=6)
    return str(dest)


def make_cover(image_path: str, output_path: str, max_size: int = 1600, quality: int = 90) -> str:
    """Generate a cover image scaled so the longest side is max_size."""
    out_path = Path(output_path)
    _ensure_dir(out_path.parent)

    try:
        resample = Image.Resampling.LANCZOS  # Pillow >= 10
    except Exception:  # pragma: no cover - compatibility
        resample = Image.LANCZOS  # type: ignore[attr-defined]

    with Image.open(image_path) as im:
        im = ImageOps.exif_transpose(im)
        im = im.convert("RGB")
        im.thumbnail((max_size, max_size), resample)
        im.save(out_path, format="WEBP", quality=quality, method=6)
    return str(out_path)


def process_images_to_webp(
    images: Sequence[str],
    output_dir: str,
    quality: int = 90,
    cover_max_px: int = 1600,
) -> dict:
    """Batch convert images to WebP and optionally create a cover from the first."""
    webp_paths: List[str] = []
    out_dir = Path(output_dir)
    _ensure_dir(out_dir)

    for img in images:
        webp_paths.append(convert_to_webp(img, output_dir, quality=quality))

    cover_path = ""
    if images:
        cover_path = make_cover(images[0], os.path.join(output_dir, "cover.webp"), max_size=cover_max_px, quality=quality)

    return {"webp": webp_paths, "cover": cover_path}


def extract_frames(
    video_path: str,
    output_dir: str,
    every_n_seconds: float = 2.0,
    max_frames: int = 5,
    ffmpeg_path: str | None = None,
) -> List[str]:
    """Extract frames from a video using ffmpeg. Returns list of frame paths."""
    try:
        import ffmpeg  # type: ignore
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError("Falta la dependencia ffmpeg-python. Instala `ffmpeg-python`.") from exc

    out_dir = Path(output_dir)
    _ensure_dir(out_dir)
    pattern = out_dir / "frame_%03d.jpg"

    fps_value = 1.0 / every_n_seconds if every_n_seconds > 0 else 1.0
    stream = ffmpeg.input(video_path)
    stream = ffmpeg.filter(stream, "fps", fps=fps_value)
    stream = ffmpeg.output(stream, str(pattern), vframes=max_frames)
    stream = ffmpeg.overwrite_output(stream)
    stream.run(cmd=ffmpeg_path or "ffmpeg", quiet=True)

    frames = sorted(out_dir.glob("frame_*.jpg"))
    return _as_list(str(p) for p in frames[:max_frames])


__all__ = [
    "convert_to_webp",
    "make_cover",
    "process_images_to_webp",
    "extract_frames",
]
