# YouTube Video Downloader Bot

A simple Telegram bot that downloads YouTube videos and playlists, then sends them to your chat or a channel.

## Features

- Download a single YouTube video or a whole playlist
- Sends the video to a channel (or back to your chat) with a delete button
- Deletes the local file right after sending
- Access control: only allowed users can use the bot
- Optional Local Bot API support for files up to 2 GB

## Requirements

- Python 3.9+
- [ffmpeg](https://ffmpeg.org/)
- A bot token from [@BotFather](https://t.me/BotFather)

## Setup

```bash
pip install python-telegram-bot yt-dlp
cp config.example.json config.json
nano config.json
python bot.py
```

On Termux, install the tools first: `pkg install python ffmpeg`.

## Config

| Key | Description |
| --- | --- |
| `BOT_TOKEN` | Your bot token from BotFather |
| `LOCAL_API_URL` | Local Bot API address, e.g. `http://127.0.0.1:8081`. Leave empty for the official API (50 MB limit) |
| `MAX_HEIGHT` | Max video quality, e.g. `720` |
| `CHANNEL_ID` | Channel ID or `@username`. Leave empty to send videos to the user's chat |
| `ALLOWED_USER_IDS` | List of allowed Telegram user IDs. Empty means everyone |
| `ONLY_OWNER_CAN_DELETE` | `true` = only the requester can press Delete |
| `PROTECT_CONTENT` | `true` = block forwarding and saving of the video |

Send `/id` to the bot to get your user ID.

If you use a channel, add the bot as admin with *Post messages* and *Delete messages* permissions.

## Project Structure

```
.
├── bot.py              # Entry point
├── config.json         # Your settings (not committed)
├── config.example.json # Config template
└── app/
    ├── config.py       # Settings loader
    ├── utils.py        # URL checks
    ├── downloader.py   # yt-dlp logic
    └── handlers.py     # Telegram commands and buttons
```

## Notes

- Official Telegram API limits bot uploads to 50 MB. Use a Local Bot API server for up to 2 GB.
- Never share your `config.json` or bot token
- Only download content you have the right to download.
