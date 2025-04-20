TOKEN = "7922002458:AAG87Cpd7j5shClnOiLnuVb1wre5-X3DwEQ"


from fastapi import FastAPI, Request
import os
import httpx
from telegram import Bot
from telegram.constants import ParseMode
from bs4 import BeautifulSoup
import requests
import re


bot = Bot(token=TOKEN)
user_preferences = {}
app = FastAPI()

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
        entries = soup.find_all("span", class_="PRON")
        pos_tags = soup.find_all("span", class_="POS")
        speakers = soup.find_all("span", class_="speaker")

        data = []
        added = set()

        for index, pos_tag in enumerate(pos_tags):
            pos = pos_tag.get_text(strip=True)
            phonetic = None
            british_audio = None
            american_audio = None

            # جلوگیری از تکرار pos
            if pos in added:
                continue
            added.add(pos)

            if index < len(entries):
                phonetic = entries[index].get_text(strip=True)

            for spk in speakers:
                src = spk.get("data-src-mp3", "")
                if "breProns" in src and not british_audio:
                    british_audio = src
                elif "ameProns" in src and not american_audio:
                    american_audio = src

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

async def process_word(chat_id, word):
    longman_link = build_longman_link(word)
    oxford_link = build_oxford_link(word)

    await bot.send_message(
        chat_id=chat_id,
        text=f"کلمه: {word}\n\n📚 Longman: {longman_link}\n📖 Oxford: {oxford_link}",
        parse_mode=ParseMode.HTML
    )

    parts_data = fetch_longman_data(word)
    preferred = user_preferences.get(chat_id, "american")

    sent_pos = set()

    for entry in parts_data:
        pos = entry['pos']
        phonetic = entry['phonetic']
        audio_url = entry[preferred]

        if not audio_url or pos in sent_pos:
            continue

        sent_pos.add(pos)

        caption = f"🔉 {word} ({pos})"
        if phonetic:
            caption += f"\n📌 /{phonetic}/"

        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(audio_url, headers=headers)
            if response.status_code == 200 and response.headers["Content-Type"].startswith("audio"):
                safe_word = re.sub(r'[^\w\-]+', '_', word)
                file_name = f"{safe_word}_{preferred}_{pos}.mp3"

                with open(file_name, "wb") as f:
                    f.write(response.content)

                with open(file_name, "rb") as audio_file:
                    await bot.send_audio(chat_id=chat_id, audio=audio_file, caption=caption)

                os.remove(file_name)

        except Exception as e:
            await bot.send_message(chat_id=chat_id, text=f"❌ خطا در دانلود فایل صوتی: {e}")

@app.post("/webhook/{token}")
async def webhook(token: str, request: Request):
    if token != TOKEN:
        return {"ok": False, "error": "Invalid token"}

    data = await request.json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "").strip()

        if text == "/start":
            await bot.send_message(
                chat_id=chat_id,
                text="سلام! 👋 به ربات تلفظ خوش آمدید.\n\nیک کلمه برای من ارسال کن تا لینک، فونتیک و تلفظ صوتی آن را برات بفرستم.\n\n✅ پیش‌فرض تلفظ 🇺🇸 American است.\nمی‌توانید با ارسال /british تلفظ را به 🇬🇧 British تغییر دهید و با /american برگردانید."
            )

        elif text == "/british":
            user_preferences[chat_id] = "british"
            await bot.send_message(chat_id=chat_id, text="✅ تلفظ پیش‌فرض روی 🇬🇧 British تنظیم شد!")

        elif text == "/american":
            user_preferences[chat_id] = "american"
            await bot.send_message(chat_id=chat_id, text="✅ تلفظ پیش‌فرض روی 🇺🇸 American تنظیم شد!")

        else:
            await process_word(chat_id, text)

    return {"ok": True}
