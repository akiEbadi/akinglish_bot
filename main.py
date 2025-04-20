from fastapi import FastAPI, Request
import os
from dotenv import load_dotenv
import httpx
from telegram import Bot
from telegram.constants import ParseMode
from bs4 import BeautifulSoup
import requests

load_dotenv()

TOKEN = os.getenv('TOKEN')
bot = Bot(token=TOKEN)

app = FastAPI()

def build_longman_link(word):
    return f"https://www.ldoceonline.com/dictionary/{word.lower().replace(' ', '-')}"

def build_oxford_link(word):
    return f"https://www.oxfordlearnersdictionaries.com/definition/english/{word.lower().replace(' ', '-')}"

def fetch_longman_phonetics(word):
    url = build_longman_link(word)
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return None
        soup = BeautifulSoup(response.text, "html.parser")

        hyphen_tag = soup.find("span", class_="HYPHENATION")
        hyphenation = hyphen_tag.text.strip() if hyphen_tag else None

        pron_tag = soup.find("span", class_="PRON")
        british_ipa = pron_tag.text.strip() if pron_tag else None

        amevar_tag = soup.find("span", class_="AMEVARPRON")
        american_ipa = amevar_tag.get_text(separator=" ", strip=True).replace("$", "").strip() if amevar_tag else None

        return {
            "hyphenation": hyphenation,
            "british_ipa": british_ipa,
            "american_ipa": american_ipa
        }
    except Exception as e:
        print(f"⚠️ خطا در واکشی فونتیک: {e}")
        return None

def fetch_longman_data(word):
    url = build_longman_link(word)
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return {}

        soup = BeautifulSoup(response.text, "html.parser")
        audio_tags = soup.find_all("span", class_="speaker")
        audio_results = {}

        for tag in audio_tags:
            if tag.has_attr("data-src-mp3"):
                mp3_url = tag["data-src-mp3"]
                if "breProns" in mp3_url:
                    audio_results["british"] = mp3_url
                elif "ameProns" in mp3_url:
                    audio_results["american"] = mp3_url

        return audio_results
    except Exception as e:
        print(f"⚠️ خطا در واکشی اطلاعات لانگمن: {e}")
        return {}

async def process_word(chat_id, word):
    longman_link = build_longman_link(word)
    oxford_link = build_oxford_link(word)

    await bot.send_message(
        chat_id=chat_id,
        text=f"کلمه: {word}\n\n📚 Longman: {longman_link}\n\n📖 Oxford: {oxford_link}",
        parse_mode=ParseMode.HTML
    )

    phonetics = fetch_longman_phonetics(word)
    if phonetics:
        message = f"کلمه: {word}"
        if phonetics["hyphenation"]:
            message += f"\n🔸 {phonetics['hyphenation']}"
        if phonetics["british_ipa"]:
            message += f"\n🇬🇧 BrE: /{phonetics['british_ipa']}/"
        if phonetics["american_ipa"]:
            message += f"\n🇺🇸 AmE: /{phonetics['american_ipa']}/"

        await bot.send_message(chat_id=chat_id, text=message)

    audio_urls = fetch_longman_data(word)

    for accent in ["british", "american"]:
        caption = f"🔉 {accent.capitalize()} ({word})"
        ipa = phonetics[accent + "_ipa"] if phonetics else None
        if ipa:
            caption += f"\n💡 {ipa}"

        if accent in audio_urls:
            url = audio_urls[accent]
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                response = requests.get(url, headers=headers)

                if response.status_code == 200 and response.headers["Content-Type"].startswith("audio"):
                    file_name = f"{word}_{accent}.mp3"
                    with open(file_name, "wb") as f:
                        f.write(response.content)

                    await bot.send_audio(chat_id=chat_id, audio=open(file_name, "rb"), caption=caption)
                    os.remove(file_name)

                else:
                    await bot.send_message(chat_id=chat_id, text=f"⚠️ تلفظ {accent} پیدا نشد.")
            except Exception as e:
                await bot.send_message(chat_id=chat_id, text=f"❌ خطا در دانلود {accent}: {e}")
        else:
            await bot.send_message(chat_id=chat_id, text=f"⚠️ تلفظ {accent} در لانگمن موجود نیست.")

@app.post("/webhook/{token}")
async def webhook(token: str, request: Request):
    if token != os.getenv('TOKEN'):
        return {"ok": False, "error": "Invalid token"}

    data = await request.json()
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        word = data["message"]["text"].strip()
        await process_word(chat_id, word)
    return {"ok": True}
