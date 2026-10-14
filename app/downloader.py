from pathlib import Path

import yt_dlp

from app.config import DOWNLOAD_DIR, MAX_HEIGHT

FORMAT = (
    f"bv*[height<={MAX_HEIGHT}][ext=mp4]+ba[ext=m4a]/"
    f"b[height<={MAX_HEIGHT}][ext=mp4]/"
    f"bv*[height<={MAX_HEIGHT}]+ba/b[height<={MAX_HEIGHT}]/b"
)


def download_video(url):
    opts = {
        "format": FORMAT,
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
