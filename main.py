import os
from datetime import datetime
from pytz import timezone
import asyncio
import re
from pyrogram import Client, filters, idle
from pyrogram.errors import FloodWait, MessageNotModified
from aiohttp import web
from config import API_ID, API_HASH, BOT_TOKEN, CUSTOM_CAPTION, ADMINS, LOG_CHANNEL

routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route(request):
    return web.Response(text="I am Alive", content_type='text/html')

async def web_server():
    app = web.Application(client_max_size=30_000_000)
    app.add_routes(routes)
    return app

class Bot(Client):
    def __init__(self):
        super().__init__(
            "techifybots",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="plugins"),
            workers=200,
            sleep_threshold=15
        )

    async def start(self):
        app = web.AppRunner(await web_server())
        await app.setup()
        try:
            await web.TCPSite(app, "0.0.0.0", int(os.getenv("PORT", 8080))).start()
            print("Web server started.")
        except Exception as e:
            print(f"Web server error: {e}")


        await super().start()
        me = await self.get_me()
        print(f"Bot Started as {me.first_name}")
        if isinstance(ADMIN, int):
            try:
                await self.send_message(ADMIN, f"**{me.first_name} is started...**")
            except Exception as e:
                print(f"Error sending message to admin: {e}")
        if LOG_CHANNEL:
            try:
                now = datetime.now(timezone("Asia/Kolkata"))
                msg = (
                    f"**{me.mention} is restarted!**\n\n"
                    f"📅 Date : `{now.strftime('%d %B, %Y')}`\n"
                    f"⏰ Time : `{now.strftime('%I:%M:%S %p')}`\n"
                    f"🌐 Timezone : `Asia/Kolkata`"
                )
                await self.send_message(LOG_CHANNEL, msg)
            except Exception as e:
                print(f"Error sending to LOG_CHANNEL: {e}")

    async def stop(self, *args):
        await super().stop()
        print(f"{me.first_name} Bot stopped.")

Bot().run()
import asyncio
import re
from pyrogram import Client, filters, idle
from pyrogram.errors import FloodWait, MessageNotModified
from config import API_ID, API_HASH, BOT_TOKEN, CUSTOM_CAPTION, ADMINS

app = Client("autocaption-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

message_queue = []

REMOVE_WORDS = [
    'R∆G∆ ', 'AnimeKaizoku', 'join', 'Toonworld4all', 'psa', 'https', 'http', 'Full Bollywood Movie', 'Bollywood', 'ViSTA', 'MoviesMod',
    '(Mᴏᴏɴ Kɴɪɢʜᴛ)', 'L3G3N7', 'telegram', 'm2links', "join us", "Join Us", "t.me", "mkvcinemas",
    "moviesmod", "moviesflix", "Desiremovies", "mkvc", "cinevood", "@m2links", "skymovieshd", "(dedsincebirth)",
    "Full", "MoviesUP","B∆TM∆N","K☈N","SANKET", "ExtraFlix","MoviezVerse.net","MoviesVerse","Hollywood", "4kHdHub","CrickeTLoveRR", "Dual Audio", "HDHub4u", "PrimeFix", "email"
]

def clean_caption(caption: str) -> str:
    match = re.search(r"(.*?\b(?:mkv|mp4)\b)", caption, re.IGNORECASE)
    if match:
        caption = match.group(1)
    else:
        match = re.search(r"(.*?\b(?:esub|esubs|msub|msubs)\b)", caption, re.IGNORECASE)
        if match:
            caption = match.group(1)
    caption = re.sub(r'\b(mkv|mp4)\b', '', caption, flags=re.IGNORECASE)
    for word in REMOVE_WORDS:
        caption = re.sub(re.escape(word), '', caption, flags=re.IGNORECASE)
    caption = re.sub(r'[_\-\|\+\[\]\{\}~#$]', ' ', caption)
    caption = caption.replace('.', ' ')
    return ' '.join(caption.split())

@app.on_message(filters.private & filters.command(["start"]))
async def start_command(_, message):
    await message.reply_text(f"<b>Hello {message.from_user.mention},</b>\n\n<b>I am an AutoCaption Bot 🤖</b>")

@app.on_message(filters.private & filters.command(["help"]))
async def help_command(_, message):
    await message.reply_text("<b>Send media to a channel and I will edit the caption automatically.</b>")

@app.on_message(filters.channel)
async def queue_message(_, message):
    message_queue.append({
        "chat_id": message.chat.id,
        "message_id": message.id,
        "caption": message.caption or ""
    })

async def process_queue():
    while True:
        if message_queue:
            msg = message_queue.pop(0)
            cleaned = clean_caption(msg["caption"])
            final_caption = CUSTOM_CAPTION.format(file_caption=cleaned)
            try:
                await app.edit_message_caption(
                    chat_id=msg["chat_id"],
                    message_id=msg["message_id"],
                    caption=final_caption
                )
                print(f"[✅ Edited] {msg['message_id']}")
            except MessageNotModified:
                print(f"[⚠️ Already Clean] Message {msg['message_id']}")
            except FloodWait as e:
                print(f"[⏳ FloodWait] Waiting {e.value} sec...")
                await asyncio.sleep(e.value + 1)
                message_queue.insert(0, msg)
            except Exception as e:
                print(f"[❌ ERROR] {e} | Msg ID: {msg['message_id']}")
        await asyncio.sleep(1)

@app.on_message(filters.command("status") & filters.user(6167872503))
async def queue_status(_, message):
    await message.reply_text(f"📦 Messages in queue: {len(message_queue)}")

def main():
    print("Bot is running...")

    async def runner():
        await app.start()
        asyncio.create_task(process_queue())
        await idle()
        await app.stop()

    app.run(runner())

if __name__ == "__main__":
    main()
