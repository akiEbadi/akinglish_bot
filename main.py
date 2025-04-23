from fastapi import FastAPI, Request
import os
import requests
from telegram import Bot
from telegram.constants import ParseMode
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
    return f"\nhttps://www.oxfordlearnersdictionaries.com/definition/english/{word.lower().replace(' ', '-')}"

def fetch_longman_data(word):
    url = build_longman_link(word)
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        data = []

        # فقط بخش‌های از نوع ldoceEntry Entry
        entries = soup.find_all("span", class_="ldoceEntry Entry")

        for entry in entries:
            pos_tag = entry.find("span", class_="POS")
            phonetic_tag = entry.find("span", class_="PRON")
            speakers = entry.find_all("span", class_="speaker")

            if not pos_tag or not speakers:
                continue  # اگه POS یا تلفظ صوتی نباشه رد کن

            pos = pos_tag.get_text(strip=True)
            phonetic = phonetic_tag.get_text(strip=True) if phonetic_tag else None

            british_audio = None
            american_audio = None

            for spk in speakers:
                mp3_url = spk.get("data-src-mp3", "")
                print(f"🔊 پیدا شده: {mp3_url}")  # برای بررسی URL های صوتی
                if "breProns" in mp3_url and not british_audio:
                    british_audio = mp3_url
                elif "ameProns" in mp3_url and not american_audio:
                    american_audio = mp3_url

            # فقط در صورتی که حداقل یکی از صداها وجود داشته باشه
            if british_audio or american_audio:
                data.append({
                    "pos": pos,
                    "phonetic": phonetic,
                    "british": british_audio,
                    "american": american_audio
                })
        # اگر هیچ وویسی پیدا نکردیم، از همه speaker ها استفاده کنیم
        if not data:
            print("هیچ وویسی در بخش ldoceEntry Entry پیدا نشد. جستجو در کل صفحه...")
            speakers = soup.find_all("span", class_="speaker")

            british_audio = None
            american_audio = None

            # جستجو برای تمامی speaker ها در صفحه
            for spk in speakers:
                mp3_url = spk.get("data-src-mp3", "")
                print(f"🔊 پیدا شده: {mp3_url}")  # برای بررسی URL های صوتی
                if "breProns" in mp3_url and not british_audio:
                    british_audio = mp3_url
                elif "ameProns" in mp3_url and not american_audio:
                    american_audio = mp3_url

            # در نهایت اگر هیچ کدام پیدا نشد، از اولین وویس موجود استفاده خواهیم کرد
            if american_audio:
                data.append({
                    "pos": "default",
                    "phonetic": None,
                    "american": american_audio,
                    "british": None
                })
            elif british_audio:
                data.append({
                    "pos": "default",
                    "phonetic": None,
                    "british": british_audio,
                    "american": None
                })
        return data

    except Exception as e:
        print(f"⚠️ خطا در واکشی اطلاعات لانگمن: {e}")
        return []


async def process_word(chat_id, word):
    longman_link = build_longman_link(word)
    oxford_link =  build_oxford_link(word)

    reply = {
                "chat_id": chat_id, 
                "text": f"کلمه: {word}\n\n📚 Longman: {longman_link}\n📖 Oxford: {oxford_link}"            }
    res = requests.post(API_URL, json=reply)

    parts_data = fetch_longman_data(word)

    preferred = user_preferences.get(chat_id, "american")  # پیش‌فرض: امریکن

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
                        files = {
                        'audio': audio_file
                        }
                        data = {
                        'chat_id': chat_id,
                        'caption': caption
                        }
                        send_audio_url = f"https://api.telegram.org/bot{TOKEN}/sendAudio"
                        res = requests.post(send_audio_url, data=data, files=files)
                        print("📤 ارسال فایل صوتی:", res.json())

                    os.remove(file_name)

            except Exception as e:
                error_reply = {
                    "chat_id": chat_id,
                    "text": f"❌ خطا در دانلود فایل صوتی: {e}"
                }
                res = requests.post(API_URL, json=error_reply)
                print("📤 ارسال پیام خطا:", res.json())
        
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

            if text == "/start":
                print(f"START: 👤 کاربر جدید: {chat_id}")
                reply = {
                    "chat_id": chat_id,
                    "text": (
                        "سلام! 👋 به ربات تلفظ خوش آمدید.\n\n"
                        "یک کلمه برای من ارسال کن تا لینک، فونتیک و تلفظ صوتی آن را برات بفرستم.\n\n"
                        "✅ پیش‌فرض تلفظ 🇺🇸 American است.\n"
                        "می‌توانید با ارسال /british تلفظ را به 🇬🇧 British تغییر دهید و با /american برگردانید."
                    )
                }
                res = requests.post(API_URL, json=reply)
                print("📤 ارسال پیام خوش‌آمد:", res.json())

            elif text == "/british":
                user_preferences[chat_id] = "british"
                reply = {
                    "chat_id": chat_id,
                    "text": "✅ تلفظ پیش‌فرض روی 🇬🇧 British تنظیم شد!"
                }
                res = requests.post(API_URL, json=reply)
                print("📤 ارسال تغییر تنظیم British:", res.json())

            elif text == "/american":
                user_preferences[chat_id] = "american"
                reply = {"chat_id": chat_id, "text": f"پیامت رسید: {text}"}
                res = requests.post(API_URL, json=reply)
                print("📤 جواب به تلگرام ارسال شد:", res.json())
            else:
                await process_word(chat_id, text)
        return {"ok": True}
    except Exception as e:
        print("❌ خطا:", e)
        return {"ok": False, "error": str(e)}
