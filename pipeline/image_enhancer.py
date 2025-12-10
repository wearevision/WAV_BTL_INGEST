"""Image enhancement module with Pillow-based processing."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Optional

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


def enhance_image(
    input_path: str,
    output_path: str,
    max_size: int = 2048,
    sharpen: float = 1.3,
    color_boost: float = 1.15,
    contrast: float = 1.05,
    quality: int = 92,
) -> str:
    """
    Enhance image quality with Pillow-based processing.
    
    Strategy:
    - Resize to optimal web size (max 2048px)
    - Apply unsharp mask for clarity
    - Boost color saturation
    - Slight contrast enhancement
    - High-quality WebP compression
    
    Args:
        input_path: Path to input image
        output_path: Path to save enhanced image
        max_size: Maximum dimension (maintains aspect ratio)
        sharpen: Sharpness enhancement (1.0 = no change, 1.3 recommended)
        color_boost: Color saturation (1.0 = no change, 1.15 recommended)
        contrast: Contrast enhancement (1.0 = no change, 1.05 recommended)
        quality: WebP quality (0-100, 92 recommended)
        
    Returns:
        Path to enhanced image
    """
    # Load image
    img = Image.open(input_path)
    
    # Fix orientation based on EXIF
    img = ImageOps.exif_transpose(img)
    
    img = img.convert("RGB")
    
    # Resize if needed (maintains aspect ratio)
    if max(img.size) > max_size:
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    
    # Apply unsharp mask (better than simple sharpening)
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
    
    # Sharpen
    if sharpen != 1.0:
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(sharpen)
    
    # Color boost
    if color_boost != 1.0:
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(color_boost)
    
    # Contrast
    if contrast != 1.0:
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(contrast)
    
    # Save as high-quality WebP
    dirname = os.path.dirname(output_path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    img.save(output_path, format="WEBP", quality=quality, method=6)
    
    return output_path


def enhance_batch(
    input_paths: list[str],
    output_dir: str,
    **kwargs
) -> list[str]:
    """
    Enhance multiple images in batch.
    
    Args:
        input_paths: List of input image paths
        output_dir: Directory to save enhanced images
        **kwargs: Arguments passed to enhance_image()
        
    Returns:
        List of output paths
    """
    output_paths = []
    os.makedirs(output_dir, exist_ok=True)
    
    for i, input_path in enumerate(input_paths, 1):
        filename = Path(input_path).stem + ".webp"
        output_path = os.path.join(output_dir, filename)
        
        try:
            enhance_image(input_path, output_path, **kwargs)
            output_paths.append(output_path)
            print(f"  ✅ Enhanced {i}/{len(input_paths)}: {filename}")
        except Exception as e:
            print(f"  ❌ Failed {filename}: {e}")
    
    return output_paths


__all__ = ["enhance_image", "enhance_batch"]
