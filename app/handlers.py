import asyncio
import logging
import uuid

import yt_dlp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from app.config import (
    ALLOWED_USER_IDS,
    CHANNEL_ID,
    MAX_FILE_MB,
    ONLY_OWNER_CAN_DELETE,
    PROTECT_CONTENT,
)
from app.downloader import download_video
from app.utils import is_valid_url

QUALITIES = (480, 720, 1080)
PENDING_LIMIT = 200  # maksimal request yang menunggu pilihan resolusi

log = logging.getLogger(__name__)


def is_allowed(user_id):
    return not ALLOWED_USER_IDS or user_id in ALLOWED_USER_IDS


async def deny(update):
    if update.callback_query:
        await update.callback_query.answer("⛔ Kamu tidak punya akses.", show_alert=True)
    else:
        await update.effective_message.reply_text("⛔ Kamu tidak punya akses ke bot ini.")


def message_link(msg):
    chat = msg.chat
    if chat.username:  # channel public
        return f"https://t.me/{chat.username}/{msg.message_id}"
    return None


def delete_keyboard(owner_id):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🗑 Hapus", callback_data=f"del|{owner_id}")
    ]])


async def send_video_file(ctx, target, owner_id, path, title):
    """Kirim video ke target, lalu hapus file lokal. Return Message atau None."""
    if not path.exists():
        return None
    if path.stat().st_size / (1024 * 1024) > MAX_FILE_MB:
        path.unlink(missing_ok=True)
        return None
    try:
        with open(path, "rb") as f:
            return await ctx.bot.send_video(
                chat_id=target,
                video=f,
                caption=f"🎬 {title}",
                supports_streaming=True,
                reply_markup=delete_keyboard(owner_id),
                protect_content=PROTECT_CONTENT,
            )
    except Exception as e:
        log.error("Gagal kirim %s: %s", path.name, e)
        return None
    finally:
        path.unlink(missing_ok=True)


async def start(update, ctx):
    if not is_allowed(update.effective_user.id):
        await deny(update)
        return
    await update.message.reply_text(
        "🎬 *YouTube Video Downloader Bot*\n\nKirim link video YouTube, nanti videonya dikirim.",
        parse_mode="Markdown",
    )


async def help_cmd(update, ctx):
    if not is_allowed(update.effective_user.id):
        await deny(update)
        return
    await update.message.reply_text(
        f"📋 *Cara pakai:*\n\n1. Kirim link video YouTube\n2. Pilih resolusi (480p / 720p / 1080p)\n3. Tunggu video dikirim\n4. Tekan 🗑 Hapus kalau sudah selesai\n\n*Limit:* Maks {MAX_FILE_MB}MB per file",
        parse_mode="Markdown",
    )


async def id_cmd(update, ctx):
    await update.message.reply_text(
        f"User ID: `{update.effective_user.id}`\nChat ID: `{update.effective_chat.id}`",
        parse_mode="Markdown",
    )


async def handle_url(update, ctx):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await deny(update)
        return

    url = update.message.text.strip()
    if "youtube.com/playlist" in url:
        await update.message.reply_text("❌ Playlist tidak didukung. Kirim link satu video saja.")
        return
    if not is_valid_url(url):
        await update.message.reply_text("❌ URL tidak dikenali. Kirim link video YouTube yang valid.")
        return

    # Simpan URL sementara, tampilkan pilihan resolusi (callback_data maks 64 byte,
    # jadi URL tidak boleh dimasukkan langsung ke tombol).
    pending = ctx.bot_data.setdefault("pending", {})
    if len(pending) >= PENDING_LIMIT:
        pending.pop(next(iter(pending)))
    token = uuid.uuid4().hex[:10]
    pending[token] = {"url": url, "user_id": user_id}

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{q}p", callback_data=f"q|{token}|{q}") for q in QUALITIES],
        [InlineKeyboardButton("❌ Batal", callback_data=f"q|{token}|0")],
    ])
    await update.message.reply_text("🎞 Pilih resolusi video:", reply_markup=keyboard)


async def handle_quality(update, ctx):
    query = update.callback_query
    user_id = query.from_user.id
    if not is_allowed(user_id):
        await deny(update)
        return

    _, token, height_str = query.data.split("|")
    height = int(height_str)
    pending = ctx.bot_data.get("pending", {})
    item = pending.get(token)

    if not item:
        await query.answer("⌛ Pilihan kedaluwarsa. Kirim ulang link.", show_alert=True)
        await query.message.delete()
        return
    if user_id != item["user_id"]:
        await query.answer("⛔ Ini bukan request kamu.", show_alert=True)
        return

    pending.pop(token, None)
    if height == 0:
        await query.answer("Dibatalkan.")
        await query.message.delete()
        return
    if height not in QUALITIES:
        await query.answer("Resolusi tidak valid.", show_alert=True)
        return

    await query.answer()
    status = query.message
    url = item["url"]
    in_channel = bool(CHANNEL_ID)
    target = CHANNEL_ID if in_channel else query.message.chat.id

    await status.edit_text(f"⏳ Download video {height}p...")

    loop = asyncio.get_running_loop()
    try:
        path, title = await loop.run_in_executor(None, download_video, url, height)
    except yt_dlp.utils.DownloadError as e:
        log.error("Download error: %s", e)
        await status.edit_text("❌ Gagal download. Pastikan link valid dan video tidak private.")
        return
    except Exception as e:
        log.error("Error: %s", e)
        await status.edit_text("❌ Error tak terduga. Coba lagi.")
        return

    await status.edit_text("📤 Mengirim video...")
    msg = await send_video_file(ctx, target, user_id, path, f"{title} ({height}p)")
    if not msg:
        await status.edit_text(
            f"❌ Gagal kirim video (limit {MAX_FILE_MB}MB, atau bot belum jadi admin di channel)."
        )
        return

    if in_channel:
        link = message_link(msg)
        markup = (
            InlineKeyboardMarkup([[InlineKeyboardButton("📺 Buka di channel", url=link)]])
            if link else None
        )
        await status.edit_text("✅ Video terkirim ke channel.", reply_markup=markup)
    else:
        await status.delete()


async def handle_delete(update, ctx):
    query = update.callback_query
    user_id = query.from_user.id
    if not is_allowed(user_id):
        await deny(update)
        return

    owner_id = int(query.data.split("|", 1)[1])
    if ONLY_OWNER_CAN_DELETE and user_id != owner_id:
        await query.answer("⛔ Hanya yang request video ini yang bisa menghapus.", show_alert=True)
        return

    try:
        await query.message.delete()
        await query.answer("🗑 Video dihapus.")
    except Exception as e:
        log.error("Gagal hapus pesan: %s", e)
        await query.answer("❌ Gagal hapus. Pastikan bot admin dan punya izin hapus pesan.", show_alert=True)

