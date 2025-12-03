#!/usr/bin/env python3
"""
Compress videos for web delivery.
- Target: < 5MB per video
- Format: H.264 MP4
- Resolution: Max 1280x720
- Bitrate: Adaptive based on file size
"""
import os
import subprocess
from pathlib import Path
import shutil

def get_video_size_mb(video_path: Path) -> float:
    """Get video file size in MB."""
    return video_path.stat().st_size / (1024 * 1024)

def compress_video(input_path: Path, output_path: Path, target_mb: float = 5.0) -> bool:
    """
    Compress video to target size using ffmpeg.
    Returns True if successful.
    """
    try:
        # Get video duration
        duration_cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(input_path)
        ]
        result = subprocess.run(duration_cmd, capture_output=True, text=True)
        duration = float(result.stdout.strip())
        
        # Calculate target bitrate (in kbps)
        # Formula: (target_size_MB * 8192) / duration_seconds
        target_bitrate = int((target_mb * 8192) / duration)
        
        # Compress with ffmpeg
        cmd = [
            'ffmpeg', '-y', '-i', str(input_path),
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '28',
            '-maxrate', f'{target_bitrate}k',
            '-bufsize', f'{target_bitrate * 2}k',
            '-vf', 'scale=1280:720:force_original_aspect_ratio=decrease',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-movflags', '+faststart',
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except Exception as e:
        print(f"    ❌ Compression failed: {e}")
        return False

def process_event_videos(event_dir: Path, dry_run: bool = False):
    """Process all videos in an event directory."""
    # Find video files
    video_patterns = ['clip_*.mp4', 'clip_*.MP4', 'video_*.mp4', 'video_*.MP4']
    videos = []
    for pattern in video_patterns:
        videos.extend(event_dir.glob(pattern))
    
    if not videos:
        return
    
    print(f"\n📂 {event_dir.name}")
    
    for video in videos:
        size_mb = get_video_size_mb(video)
        
        if size_mb <= 5.0:
            print(f"  ✅ {video.name}: {size_mb:.1f}MB (already optimized)")
            continue
        
        if dry_run:
            print(f"  🔄 {video.name}: {size_mb:.1f}MB → would compress to ~5MB")
            continue
        
        # Compress to temp file
        temp_output = video.parent / f"{video.stem}_compressed.mp4"
        print(f"  🔄 {video.name}: {size_mb:.1f}MB → compressing...")
        
        if compress_video(video, temp_output, target_mb=5.0):
            new_size = get_video_size_mb(temp_output)
            print(f"    ✅ Compressed: {size_mb:.1f}MB → {new_size:.1f}MB")
            
            # Replace original
            shutil.move(str(temp_output), str(video))
        else:
            if temp_output.exists():
                temp_output.unlink()

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Compress videos for web")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    args = parser.parse_args()
    
    base_dir = Path("organized_events")
    if not base_dir.exists():
        print("❌ 'organized_events' directory not found.")
        return
    
    # Check if ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ ffmpeg not found. Please install it first:")
        print("   brew install ffmpeg")
        return
    
    event_dirs = [d for d in base_dir.iterdir() if d.is_dir() and d.name != "OJO"]
    event_dirs.sort()
    
    print(f"🎬 Processing videos in {len(event_dirs)} events...")
    if args.dry_run:
        print("   [DRY RUN MODE]")
    
    for event_dir in event_dirs:
        process_event_videos(event_dir, dry_run=args.dry_run)
    
    print("\n✨ Done!")

if __name__ == "__main__":
    main()
