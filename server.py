# Copyright (c) 2025 Kaustav Ray
# Free Unlimited Cloud Storage - Saved Messages Version (Telethon)

from flask import Flask, request, send_file
from telethon import TelegramClient
import os
import asyncio

# ✅ Your Telegram API credentials (from my.telegram.org)
API_ID = 20110837
API_HASH = "b9658b136c2b71af2bdb7497649ace5c"
PHONE = os.getenv("PHONE_NUMBER", "+91XXXXXXXXXX")  # Put your number or set as environment variable

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ✅ Telethon Client
client = TelegramClient("session", API_ID, API_HASH)

# ✅ Start Flask app
app = Flask(__name__)

# ✅ Start Telethon Client
loop = asyncio.get_event_loop()
loop.run_until_complete(client.start(PHONE))


@app.route("/")
def index():
    return open("index.html", "r").read()


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file:
        return "No file uploaded", 400

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    file.save(file_path)

    async def send_to_saved():
        await client.send_file("me", file_path, caption=file.filename)

    loop.run_until_complete(send_to_saved())
    os.remove(file_path)
    return "<h2>✅ File saved to Telegram Saved Messages!</h2><p><a href='/list'>📂 View Files</a></p>"


@app.route("/list")
def list_files():
    async def get_files():
        messages = await client.get_messages("me", limit=100)
        return [m for m in messages if m.file]

    messages = loop.run_until_complete(get_files())
    html = "<h2>📂 Files in Saved Messages</h2><ul>"
    for m in messages:
        name = m.file.name or "File"
        html += f"<li>{name} - <a href='/download/{m.id}'>Download</a></li>"
    html += "</ul><p><a href='/'>⬅ Upload More</a></p>"
    return html


@app.route("/download/<int:msg_id>")
def download_file(msg_id):
    file_path = os.path.join(UPLOAD_DIR, f"{msg_id}.bin")

    async def fetch_file():
        msg = await client.get_messages("me", ids=msg_id)
        await msg.download_media(file_path)

    loop.run_until_complete(fetch_file())
    return send_file(file_path, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
