import asyncio
import logging

import yt_dlp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from app.config import (
    ALLOWED_USER_IDS,
    CHANNEL_ID,
    MAX_FILE_MB,
    ONLY_OWNER_CAN_DELETE,
    PROTECT_CONTENT,
)
from app.downloader import download_playlist, download_single
from app.utils import is_valid_url, looks_like_playlist

log = logging.getLogger(__name__)
MAX_SAVED_URLS = 30


def is_allowed(user_id):
    return not ALLOWED_USER_IDS or user_id in ALLOWED_USER_IDS


async def deny(update):
    if update.callback_query:
        await update.callback_query.answer("⛔ Kamu tidak punya akses.", show_alert=True)
    else:
        await update.effective_message.reply_text("⛔ Kamu tidak punya akses ke bot ini.")


def message_link(chat_id, message_id):
    if isinstance(chat_id, int) and str(chat_id).startswith("-100"):
        return f"https://t.me/c/{str(chat_id)[4:]}/{message_id}"
    if isinstance(chat_id, str) and chat_id.startswith("@"):
        return f"https://t.me/{chat_id[1:]}/{message_id}"
    return None


def build_keyboard(key):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🎬 Download Video", callback_data=f"single|{key}"),
        InlineKeyboardButton("📋 Download Playlist", callback_data=f"playlist|{key}"),
    ]])


def delete_keyboard(owner_id):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🗑 Hapus", callback_data=f"del|{owner_id}")
    ]])


async def send_video_file(ctx, target, owner_id, path, title, caption=None):
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
                caption=caption or f"🎬 {title}",
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
        "🎬 *YouTube Video Downloader Bot*\n\nKirim link YouTube.\nPilih mau download satu video atau seluruh playlist.",
        parse_mode="Markdown",
    )


async def help_cmd(update, ctx):
    if not is_allowed(update.effective_user.id):
        await deny(update)
        return
    await update.message.reply_text(
        f"📋 *Cara pakai:*\n\n1. Kirim link YouTube\n2. Pilih tombol Download\n3. Tunggu video dikirim\n4. Tekan 🗑 Hapus kalau sudah selesai\n\n*Limit:* Maks {MAX_FILE_MB}MB per file",
        parse_mode="Markdown",
    )


async def id_cmd(update, ctx):
    await update.message.reply_text(
        f"User ID: `{update.effective_user.id}`\nChat ID: `{update.effective_chat.id}`",
        parse_mode="Markdown",
    )


async def handle_url(update, ctx):
    if not is_allowed(update.effective_user.id):
        await deny(update)
        return
    url = update.message.text.strip()
    if not is_valid_url(url):
        await update.message.reply_text("❌ URL tidak dikenali. Kirim link YouTube yang valid.")
        return

    # callback_data maksimal 64 byte, jadi URL disimpan di memori dan dipanggil lewat ID pendek
    key = update.message.message_id
    urls = ctx.user_data.setdefault("urls", {})
    urls[key] = url
    while len(urls) > MAX_SAVED_URLS:
        urls.pop(next(iter(urls)))

    hint = "📋 Sepertinya ini link playlist." if looks_like_playlist(url) else "🔗 Link siap didownload."
    await update.message.reply_text(f"{hint}\n\nMau download apa?", reply_markup=build_keyboard(key))


async def handle_download(update, ctx):
    query = update.callback_query
    user_id = query.from_user.id
    if not is_allowed(user_id):
        await deny(update)
        return
    await query.answer()

    mode, key = query.data.split("|", 1)
    url = ctx.user_data.get("urls", {}).get(int(key)) if key.isdigit() else None
    if not url:
        await query.edit_message_text("⌛ Link sudah kadaluarsa. Kirim ulang link-nya.")
        return

    in_channel = bool(CHANNEL_ID)
    target = CHANNEL_ID if in_channel else update.effective_chat.id
    loop = asyncio.get_running_loop()

    if mode == "single":
        await query.edit_message_text("⏳ Download video...")
        try:
            path, title = await loop.run_in_executor(None, download_single, url)
        except yt_dlp.utils.DownloadError as e:
            log.error("Download error: %s", e)
            await query.edit_message_text("❌ Gagal download. Pastikan link valid dan video tidak private.")
            return
        except Exception as e:
            log.error("Error: %s", e)
            await query.edit_message_text("❌ Error tak terduga. Coba lagi.")
            return

        await query.edit_message_text("📤 Mengirim video...")
        msg = await send_video_file(ctx, target, user_id, path, title)
        if not msg:
            await query.edit_message_text(
                f"❌ Gagal kirim video (limit {MAX_FILE_MB}MB, atau bot belum jadi admin di channel)."
            )
            return

        if in_channel:
            link = message_link(target, msg.message_id)
            markup = (
                InlineKeyboardMarkup([[InlineKeyboardButton("📺 Buka di channel", url=link)]])
                if link else None
            )
            await query.edit_message_text("✅ Video terkirim ke channel.", reply_markup=markup)
        else:
            await query.delete_message()

    elif mode == "playlist":
        await query.edit_message_text("⏳ Mengambil info playlist...")
        try:
            results = await loop.run_in_executor(None, download_playlist, url)
        except Exception as e:
            log.error("Playlist error: %s", e)
            await query.edit_message_text("❌ Gagal download playlist.")
            return
        if not results:
            await query.edit_message_text("❌ Tidak ada video yang berhasil didownload.")
            return

        total = len(results)
        sent = 0
        skipped = 0
        for i, (path, title) in enumerate(results, 1):
            await query.edit_message_text(f"📤 Mengirim {i}/{total}: {title[:40]}...")
            msg = await send_video_file(ctx, target, user_id, path, title, caption=f"🎬 {title} ({i}/{total})")
            if msg:
                sent += 1
            else:
                skipped += 1

        dest = "ke channel" if in_channel else "ke chat ini"
        summary = f"✅ Selesai! {sent} video dikirim {dest}."
        if skipped:
            summary += f"\n⚠️ {skipped} video dilewati (terlalu besar atau gagal kirim)."
        await query.edit_message_text(summary)


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
