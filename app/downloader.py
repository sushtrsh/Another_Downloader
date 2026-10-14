from pathlib import Path

import yt_dlp

from app.config import DOWNLOAD_DIR, MAX_HEIGHT

FORMAT = (
    f"bv*[height<={MAX_HEIGHT}][ext=mp4]+ba[ext=m4a]/"
    f"b[height<={MAX_HEIGHT}][ext=mp4]/"
    f"bv*[height<={MAX_HEIGHT}]+ba/b[height<={MAX_HEIGHT}]/b"
)


def _opts(outtmpl, playlist):
    return {
        "format": FORMAT,
        "merge_output_format": "mp4",
        "outtmpl": str(DOWNLOAD_DIR / outtmpl),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": not playlist,
        "ignoreerrors": playlist,
    }


def _final_path(ydl, info):
    downloads = info.get("requested_downloads")
    if downloads and downloads[0].get("filepath"):
        return Path(downloads[0]["filepath"])
    return Path(ydl.prepare_filename(info)).with_suffix(".mp4")


def download_single(url):
    with yt_dlp.YoutubeDL(_opts("%(title)s.%(ext)s", playlist=False)) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get("title", "video")
        path = _final_path(ydl, info)
    return path, title


def download_playlist(url):
    results = []
    with yt_dlp.YoutubeDL(_opts("%(playlist_index)02d - %(title)s.%(ext)s", playlist=True)) as ydl:
        info = ydl.extract_info(url, download=True)
        for entry in info.get("entries", []):
            if not entry:
                continue
            title = entry.get("title", "video")
            path = _final_path(ydl, entry)
            if path.exists():
                results.append((path, title))
    return results
