import json
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import asyncio

# Telegram bot token
TOKEN = "8430722879:AAETV8oydgjRB2Ht7bSgCNusQhLi9-M0wv0"

BASE_URL = "https://roadpolice.am/hy/plate-number-search"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# Get CSRF token and cookies
def get_session():
    res = requests.get(BASE_URL, headers=HEADERS)
    cookies = res.cookies.get_dict()
    soup = BeautifulSoup(res.text, "html.parser")
    token = soup.find("meta", {"name": "csrf-token"})["content"]
    return token, cookies

# Check a single plate
def check_plate(plate, token, cookies):
    try:
        data = {"number": plate}
        res = requests.post(
            BASE_URL,
            headers={**HEADERS, "X-CSRF-TOKEN": token, "X-Requested-With": "XMLHttpRequest"},
            cookies=cookies,
            data=data,
        )
        if res.status_code == 200:
            return "Free"
        else:
            return "Taken"
    except:
        return "Error"

# Handle /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome! Send me plate numbers separated by space or comma, and I will tell you which ones are free."
    )

# Handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text:
        return

    plates = [p.strip() for p in text.replace(",", " ").split() if p.strip()]
    if not plates:
        await update.message.reply_text("Please send valid plate numbers separated by space or comma.")
        return

    await update.message.reply_text(f"Checking {len(plates)} plate(s)... ⏳")

    token, cookies = get_session()
    results = []

    free_plates = []

    for plate in plates:
        status = check_plate(plate, token, cookies)
        results.append(f"{plate}: {status}")
        if status == "Free":
            free_plates.append(plate)
        await asyncio.sleep(0.5)  # polite delay

    # Save free plates to JSON
    if free_plates:
        with open("free_plates.json", "w", encoding="utf-8") as f:
            json.dump(free_plates, f, indent=2, ensure_ascii=False)

    await update.message.reply_text("\n".join(results))

# Main
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()