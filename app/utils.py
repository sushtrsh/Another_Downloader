import re

URL_PATTERN = re.compile(
    r"(https?://)?(www\.)?"
    r"(youtube\.com/watch|youtu\.be/|music\.youtube\.com/)"
    r"[\w\-?=&%/]+"
)


def is_valid_url(text):
    return bool(URL_PATTERN.search(text))
