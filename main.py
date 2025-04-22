from fastapi import FastAPI, Request
import os
import requests
from telegram import ReplyKeyboardMarkup
from bs4 import BeautifulSoup
import re

app = FastAPI()

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("TOKEN is not set!")

user_preferences = {}  # ذخیره پیش‌فرض تلفظ کاربران
API_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

def build_longman_link(word):
    return f"https://www.ldoceonline.com/dictionary/{word.lower().replace(' ', '-')}"

def build_oxford_link(word):
    return f"https://www.oxfordlearnersdictionaries.com/definition/english/{word.lower().replace(' ', '-')}"

def fetch_longman_data(word):
    url = build_longman_link(word)
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        data = []
        entries = soup.find_all("span", class_="ldoceEntry Entry")

        for entry in entries:
            pos_tag = entry.find("span", class_="POS")
            phonetic_tag = entry.find("span", class_="PRON")
            speakers = entry.find_all("span", class_="speaker")

            if not pos_tag or not speakers:
                continue

            pos = pos_tag.get_text(strip=True)
            phonetic = phonetic_tag.get_text(strip=True) if phonetic_tag else None
            british_audio, american_audio = None, None

            for spk in speakers:
                mp3_url = spk.get("data-src-mp3", "")
                if "breProns" in mp3_url and not british_audio:
                    british_audio = mp3_url
                elif "ameProns" in mp3_url and not american_audio:
                    american_audio = mp3_url

            if british_audio or american_audio:
                data.append({
                    "pos": pos,
                    "phonetic": phonetic,
                    "british": british_audio,
                    "american": american_audio
                })
        return data
    except Exception as e:
        print(f"⚠️ خطا در واکشی اطلاعات لانگمن: {e}")
        return []

def send_message(chat_id, text):
    keyboard = [["🇬🇧 British", "🇺🇸 American"], ["❓ راهنما"]]
    reply_markup = {"keyboard": keyboard, "resize_keyboard": True, "one_time_keyboard": False}

    payload = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": reply_markup
    }
    requests.post(API_URL, json=payload)

async def process_word(chat_id, word):
    longman_link = build_longman_link(word)
    oxford_link = build_oxford_link(word)
    send_message(chat_id, f"کلمه: {word}\n\n📚 Longman: {longman_link}\n📖 Oxford: {oxford_link}")

    parts_data = fetch_longman_data(word)
    preferred = user_preferences.get(chat_id, "american")

    for entry in parts_data:
        pos = entry['pos']
        phonetic = entry['phonetic']
        audio_url = entry[preferred]

        caption = f"🔉 {word} ({pos})"
        if phonetic:
            caption += f"\n📌 /{phonetic}/"

        if audio_url:
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                response = requests.get(audio_url, headers=headers)
                if response.status_code == 200 and response.headers["Content-Type"].startswith("audio"):
                    safe_word = re.sub(r'[^\w\-]+', '_', word)
                    file_name = f"{safe_word}_{preferred}_{pos}.mp3"

                    with open(file_name, "wb") as f:
                        f.write(response.content)

                    with open(file_name, "rb") as audio_file:
                        files = {'audio': audio_file}
                        data = {'chat_id': chat_id, 'caption': caption}
                        send_audio_url = f"https://api.telegram.org/bot{TOKEN}/sendAudio"
                        res = requests.post(send_audio_url, data=data, files=files)
                        print("📤 ارسال فایل صوتی:", res.json())

                    os.remove(file_name)
            except Exception as e:
                send_message(chat_id, f"❌ خطا در دانلود فایل صوتی: {e}")

@app.post("/webhook/{token}")
async def webhook(token: str, request: Request):
    try:
        if token != TOKEN:
            return {"ok": False, "error": "Invalid token"}

        data = await request.json()
        print("Received data:", data)

        if "message" in data:
            chat_id = data['message']['chat']['id']
            text = data['message'].get('text', '')

            if text == "/start" or text == "❓ راهنما":
                send_message(
                    chat_id,
                    "سلام! 👋 به ربات تلفظ خوش آمدی.\n\nیک کلمه بفرست تا لینک و تلفظش رو برات بیارم.\n\n"
                    "✅ پیش‌فرض تلفظ 🇺🇸 American است.\n"
                    "با دکمه‌های زیر هم می‌تونی تغییر بدی!"
                )

            elif text in ["🇬🇧 British", "/british"]:
                user_preferences[chat_id] = "british"
                send_message(chat_id, "✅ تلفظ پیش‌فرض روی 🇬🇧 British تنظیم شد!")

            elif text in ["🇺🇸 American", "/american"]:
                user_preferences[chat_id] = "american"
                send_message(chat_id, "✅ تلفظ پیش‌فرض روی 🇺🇸 American تنظیم شد!")

            else:
                await process_word(chat_id, text)

        return {"ok": True}
    except Exception as e:
        print("❌ خطا:", e)
        return {"ok": False, "error": str(e)}
