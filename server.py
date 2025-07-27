# Copyright (c) 2025 Kaustav Ray
# Telegram Cloud Storage - Web Login Version

from flask import Flask, request, redirect, send_file, render_template_string
from telethon import TelegramClient
import os, asyncio

# ✅ Your Telegram API credentials
API_ID = 20110837
API_HASH = "b9658b136c2b71af2bdb7497649ace5c"

client = TelegramClient("session", API_ID, API_HASH)
loop = asyncio.get_event_loop()

app = Flask(__name__)
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Track login state
login_data = {"phone": None, "sent_code": False}

# HTML Templates
login_page = """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Telegram Login</title></head>
<body style="font-family:sans-serif;text-align:center;padding:40px;">
<h2>📱 Telegram Login</h2>
<form method="POST" action="/send_code">
  <input type="text" name="phone" placeholder="+91..." required>
  <button type="submit">Send Code</button>
</form>
</body>
</html>
"""

otp_page = """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Enter OTP</title></head>
<body style="font-family:sans-serif;text-align:center;padding:40px;">
<h2>🔑 Enter OTP</h2>
<form method="POST" action="/verify_code">
  <input type="text" name="code" placeholder="12345" required>
  <button type="submit">Verify</button>
</form>
</body>
</html>
"""

@app.route("/")
def index():
    if not os.path.exists("session.session"):
        return redirect("/login")
    return open("index.html").read()

@app.route("/login")
def login():
    if login_data["sent_code"]:
        return otp_page
    return login_page

@app.route("/send_code", methods=["POST"])
def send_code():
    phone = request.form["phone"]
    login_data["phone"] = phone

    async def send():
        await client.connect()
        await client.send_code_request(phone)

    loop.run_until_complete(send())
    login_data["sent_code"] = True
    return redirect("/login")

@app.route("/verify_code", methods=["POST"])
def verify_code():
    code = request.form["code"]

    async def verify():
        await client.sign_in(login_data["phone"], code)

    loop.run_until_complete(verify())
    return redirect("/")

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file:
        return "No file uploaded", 400
    path = os.path.join(UPLOAD_DIR, file.filename)
    file.save(path)

    async def send_to_saved():
        await client.send_file("me", path, caption=file.filename)

    loop.run_until_complete(send_to_saved())
    os.remove(path)
    return "<h2>✅ File saved to Telegram Saved Messages!</h2><p><a href='/list'>📂 View Files</a></p>"

@app.route("/list")
def list_files():
    async def get_files():
        messages = await client.get_messages("me", limit=50)
        return [m for m in messages if m.file]

    messages = loop.run_until_complete(get_files())
    html = "<h2>📂 Files</h2><ul>"
    for m in messages:
        name = m.file.name or "File"
        html += f"<li>{name} - <a href='/download/{m.id}'>Download</a></li>"
    html += "</ul><p><a href='/'>⬅ Upload More</a></p>"
    return html

@app.route("/download/<int:msg_id>")
def download(msg_id):
    file_path = os.path.join(UPLOAD_DIR, f"{msg_id}.bin")

    async def fetch_file():
        msg = await client.get_messages("me", ids=msg_id)
        await msg.download_media(file_path)

    loop.run_until_complete(fetch_file())
    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
