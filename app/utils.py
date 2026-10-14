import re

URL_PATTERN = re.compile(
    r"(https?://)?(www\.)?"
    r"(youtube\.com/(watch|playlist)|youtu\.be/|music\.youtube\.com/)"
    r"[\w\-?=&%/]+"
)

PLAYLIST_PATTERN = re.compile(
    r"(youtube\.com/playlist\?list=|"
    r"youtube\.com/watch\?.*list=|"
    r"youtu\.be/.*\?.*list=)"
)


def is_valid_url(text):
    return bool(URL_PATTERN.search(text))


def looks_like_playlist(url):
    return bool(PLAYLIST_PATTERN.search(url))
