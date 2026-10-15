from pathlib import Path

import yt_dlp

from app.config import DOWNLOAD_DIR, MAX_HEIGHT

def build_format(height):
    return (
        f"bv*[height<={height}][ext=mp4]+ba[ext=m4a]/"
        f"b[height<={height}][ext=mp4]/"
        f"bv*[height<={height}]+ba/b[height<={height}]/b"
    )


def download_video(url, height=MAX_HEIGHT):
    opts = {
        "format": build_format(height),
        "merge_output_format": "mp4",
        "outtmpl": str(DOWNLOAD_DIR / "%(title)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get("title", "video")
        downloads = info.get("requested_downloads")
        if downloads and downloads[0].get("filepath"):
            path = Path(downloads[0]["filepath"])
        else:
            path = Path(ydl.prepare_filename(info)).with_suffix(".mp4")
    return path, title

