"""FFmpeg wrapper utilities for WAV media pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Optional


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def transcode_to_720p(
    video_path: str,
    output_path: str,
    crf: int = 23,
    preset: str = "veryfast",
    ffmpeg_path: Optional[str] = None,
) -> str:
    """Transcode a video to 720p MP4 (H.264 + AAC)."""
    try:
        import ffmpeg  # type: ignore
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError("Falta la dependencia ffmpeg-python. Instala `ffmpeg-python`.") from exc

    out_path = Path(output_path)
    _ensure_dir(out_path.parent)

    stream = ffmpeg.input(video_path)
    stream = ffmpeg.output(
        stream,
        str(out_path),
        vcodec="libx264",
        vf="scale=-2:720",
        crf=crf,
        preset=preset,
        acodec="aac",
        movflags="+faststart",
    )
    stream = ffmpeg.overwrite_output(stream)
    stream.run(cmd=ffmpeg_path or "ffmpeg", quiet=True)
    return str(out_path)


def generate_thumbnail(
    video_path: str,
    output_path: str,
    at_time: str = "00:00:01",
    width: int = 720,
    ffmpeg_path: Optional[str] = None,
) -> str:
    """Generate a thumbnail image from a video at the specified timestamp."""
    try:
        import ffmpeg  # type: ignore
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError("Falta la dependencia ffmpeg-python. Instala `ffmpeg-python`.") from exc

    out_path = Path(output_path)
    _ensure_dir(out_path.parent)

    stream = ffmpeg.input(video_path, ss=at_time)
    stream = ffmpeg.filter(stream, "scale", width, -2)
    stream = ffmpeg.output(stream, str(out_path), vframes=1)
    stream = ffmpeg.overwrite_output(stream)
    stream.run(cmd=ffmpeg_path or "ffmpeg", quiet=True)
    return str(out_path)


def extract_clip(
    video_path: str,
    output_path: str,
    start_time: str = "00:00:00",
    duration: int = 5,
    ffmpeg_path: Optional[str] = None,
) -> str:
    """Extract a short clip from a video."""
    try:
        import ffmpeg  # type: ignore
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError("Falta la dependencia ffmpeg-python. Instala `ffmpeg-python`.") from exc

    out_path = Path(output_path)
    _ensure_dir(out_path.parent)

    stream = ffmpeg.input(video_path, ss=start_time, t=duration)
    stream = ffmpeg.output(stream, str(out_path), c="copy")
    stream = ffmpeg.overwrite_output(stream)
    stream.run(cmd=ffmpeg_path or "ffmpeg", quiet=True)
    return str(out_path)


__all__ = ["transcode_to_720p", "generate_thumbnail", "extract_clip"]
