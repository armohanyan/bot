import json
import asyncio
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# ----------------------------
# Configuration
# ----------------------------
BOT_TOKEN = "8430722879:AAETV8oydgjRB2Ht7bSgCNusQhLi9-M0wv0"
WEBHOOK_URL = f"https://bot-ze2x.onrender.com/{BOT_TOKEN}"  # Your Render URL + token
PLATE_BASE_URL = "https://roadpolice.am/hy/plate-number-search"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

# ----------------------------
# Helper functions
# ----------------------------
def get_csrf_and_cookies():
    res = requests.get(PLATE_BASE_URL, headers={"User-Agent": UA})
    cookies = res.cookies.get_dict()  # Proper cookies dict
    soup = BeautifulSoup(res.text, "html.parser")
    token = soup.find("meta", {"name": "csrf-token"})
    if not token:
        raise Exception("CSRF token not found")
    return token["content"], cookies

def check_plate(plate: str) -> bool:
    """Check if plate is free. Returns True if free, False if taken."""
    try:
        token, cookies = get_csrf_and_cookies()
        resp = requests.post(
            PLATE_BASE_URL,
            data={"number": plate},
            headers={
                "User-Agent": UA,
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-CSRF-TOKEN": token,
                "X-Requested-With": "XMLHttpRequest",
            },
            cookies=cookies,
            timeout=10,
        )

        print(f"[DEBUG] Checking plate {plate} -> Status code: {resp.status_code}")
        
        if resp.status_code == 200:
            return True   # Plate is free
        elif resp.status_code == 422:
            return False  # Plate is taken
        else:
            print(f"[WARN] Unexpected response {resp.status_code}: {resp.text}")
            return False

    except Exception as e:
        print(f"[ERROR] Error checking plate {plate}: {e}")
        return False

# ----------------------------
# Telegram bot handlers
# ----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"[INFO] Received message from {update.effective_user.username}: {update.message.text}")
    await update.message.reply_text(
        "Welcome! Send me a plate number, and I will tell you if it's free."
    )

async def handle_plate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    plate = update.message.text.strip()
    await update.message.reply_text(f"Checking plate: {plate} ...")

    loop = asyncio.get_event_loop()
    is_free = await loop.run_in_executor(None, check_plate, plate)

    if is_free:
        await update.message.reply_text(f"✅ Plate {plate} is free!")
    else:
        await update.message.reply_text(f"❌ Plate {plate} is taken. Try another one.")

# ----------------------------
# Main
# ----------------------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_plate))

    print("[INFO] Bot is starting...")
    print(f"[INFO] Webhook URL: {WEBHOOK_URL}")

    # Run webhook server (Render will call this URL)
    app.run_webhook(
        listen="0.0.0.0",
        port=10000,  # Render free tier requires port 10000
        url_path=BOT_TOKEN,
        webhook_url=WEBHOOK_URL,
    )