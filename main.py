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
user_pos = {}  # ذخیره موقعیت تلفظ کاربران (br/us)


API_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# لیست تبدیل املای آمریکایی به بریتیش
american_to_british = {
 'acknowledgement': 'acknowledgment',
 'aluminium': 'aluminum',
 'anaemia': 'anemia',
 'analog': 'analog',
 'analyse': 'analyze',
 'analyze': 'analyse',
 'anemia': 'anaemia',
 'apologise': 'apologize',
 'apologize': 'apologise',
 'appal': 'appall',
 'appals': 'appalls',
 'appetiser': 'appetizer',
 'appetizer': 'appetiser',
 'arbour': 'arbor',
 'ardour': 'ardor',
 'armour': 'armor',
 'behavior': 'behaviour',
 'behaviour': 'behavior',
 'caecum': 'cecum',
 'caesium': 'cesium',
 'caliber': 'calibre',
 'calibre': 'caliber',
 'candour': 'candor',
 'catalogue': 'catalog',
 'catalyse': 'catalyze',
 'catalyze': 'catalyse',
 'cecum': 'caecum',
 'celiac': 'coeliac',
 'center': 'centre',
 'centre': 'center',
 'cesium': 'caesium',
 'civilise': 'civilize',
 'civilize': 'civilise',
 'clamour': 'clamor',
 'coeliac': 'celiac',
 'colonise': 'colonize',
 'colonize': 'colonise',
 'color': 'colour',
 'colour': 'color',
 'counseling': 'counselling',
 'counselling': 'counseling',
 'counsellor': 'counselor',
 'counselor': 'counsellor',
 'criticise': 'criticize',
 'criticize': 'criticise',
 'defence': 'defense',
 'defense': 'defence',
 'demeanour': 'demeanor',
 'emphasise': 'emphasize',
 'emphasize': 'emphasise',
 'encyclopaedia': 'encyclopedia',
 'encyclopedia': 'encyclopaedia',
 'endeavor': 'endeavour',
 'endeavour': 'endeavor',
 'enrollment': 'enrolment',
 'enrolment': 'enrollment',
 'equaling': 'equalling',
 'equalling': 'equaling',
 'estrogen': 'oestrogen',
 'favorite': 'favourite',
 'favour': 'favor',
 'favourite': 'favorite',
 'fervour': 'fervor',
 'fiber': 'fibre',
 'fibre': 'fiber',
 'flavor': 'flavour',
 'flavour': 'flavor',
 'foetus': 'fetus',
 'fueled': 'fuelled',
 'fueling': 'fuelling',
 'fuelled': 'fueled',
 'fuelling': 'fueling',
 'fulfil': 'fulfill',
 'fulfill': 'fulfil',
 'fulfils': 'fulfills',
 'glamor': 'glamour',
 'glamour': 'glamor',
 'goitre': 'goiter',
 'harbour': 'harbor',
 'honor': 'honour',
 'honour': 'honor',
 'humor': 'humour',
 'humour': 'humor',
 'installment': 'instalment',
 'instalment': 'installment',
 'instil': 'instill',
 'instils': 'instills',
 'jewellery': 'jewelry',
 'jewelry': 'jewellery',
 'kilometer': 'kilometre',
 'kilometre': 'kilometer',
 'labor': 'labour',
 'labour': 'labor',
 'leukaemia': 'leukemia',
 'leukemia': 'leukaemia',
 'licence': 'license', # noun in UK is 'licence', verb is 'license'
 'license': 'licence',
 'liter': 'litre',
 'litre': 'liter',
 'louver': 'louvre',
 'louvre': 'louver',
 'luster': 'lustre',
 'lustre': 'luster',
 'maneuver': 'manoeuvre',
 'manoeuvre': 'maneuver',
 'marvellous': 'marvelous',
 'meager': 'meagre',
 'meagre': 'meager',
 'mediaeval': 'medieval',
 'medieval': 'mediaeval',
 'memorise': 'memorize',
 'memorize': 'memorise',
 'meter': 'metre',
 'metre': 'meter',
 'minimise': 'minimize',
 'minimize': 'minimise',
 'modeling': 'modelling',
 'modelling': 'modeling',
 'mould': 'mold',
 'moult': 'molt',
 'moustache': 'mustache',
 'neighbor': 'neighbour',
 'neighbour': 'neighbor',
 'odor': 'odour',
 'odour': 'odor',
 'oesophagus': 'esophagus',
 'oestrogen': 'estrogen',
 'offence': 'offense',
 'offense': 'offence',
 'organise': 'organize',
 'organize': 'organise',
 'paediatric': 'pediatric',
 'paediatrician': 'pediatrician',
 'paedophile': 'pedophile',
 'paralyse': 'paralyze',
 'paralyze': 'paralyse',
 'parlour': 'parlor',
 'patronise': 'patronize',
 'patronize': 'patronise',
 'pediatric': 'paediatric',
 'pedophile': 'paedophile',
 'plough': 'plow',
 'practice': 'practise',   # noun in US/UK: practice; verb in UK: practise
 'practise': 'practice',
 'pretence': 'pretense',
 'pretense': 'pretence',
 'prise': 'prize',
 'prize': 'prise',
 'pyjamas': 'pajamas',
 'quarreling': 'quarrelling',
 'quarrelling': 'quarreling',
 'rancour': 'rancor',
 'realise': 'realize',
 'realize': 'realise',
 'recognise': 'recognize',
 'recognize': 'recognise',
 'revelled': 'reveled',
 'revelling': 'reveling',
 'rigour': 'rigor',
 'rumor': 'rumour',
 'rumour': 'rumor',
 'saber': 'sabre',
 'sabre': 'saber',
 'saviour': 'savior',
 'savor': 'savour',
 'savour': 'savor',
 'scepter': 'sceptre',
 'sceptre': 'scepter',
 'signaling': 'signalling',
 'signalling': 'signaling',
 'skilful': 'skillful',
 'skillful': 'skilful',
 'smoulder': 'smolder',
 'socialise': 'socialize',
 'socialize': 'socialise',
 'somber': 'sombre',
 'sombre': 'somber',
 'specialise': 'specialize',
 'specialize': 'specialise',
 'specter': 'spectre',
 'spectre': 'specter',
 'splendor': 'splendour',
 'splendour': 'splendor',
 'succour': 'succor',
 'theater': 'theatre',
 'theatre': 'theater',
 'traveled': 'travelled',
 'traveler': 'traveller',
 'traveling': 'travelling',
 'travelle': 'traveler',
 'travelled': 'traveled',
 'traveller': 'traveler',
 'travelling': 'traveling',
 'tumour': 'tumor',
 'valour': 'valor',
 'vapour': 'vapor',
 'vigor': 'vigour',
 'vigour': 'vigor',
 'whisky': 'whiskey',
 'wilful': 'willful'}


def build_longman_link(word):
    return f"https://www.ldoceonline.com/dictionary/{word.lower().replace(' ', '-')}"

def build_oxford_link(word):
    return f"https://www.oxfordlearnersdictionaries.com/definition/english/{word.lower().replace(' ', '-')}"

def has_invalid_parent_class(element):
    # بررسی والد‌های عنصر تا رسیدن به ریشه
    parents = element.find_parents()
    for parent in parents:
        # بررسی اینکه آیا کلاس‌ها شامل Tail یا DERIV هستند
        classes = parent.get('class', [])
        if isinstance(classes, list) and any(cls in classes for cls in ['Tail', 'DERIV']):
            return True
    return False

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
            headword_tag = entry.find("span", class_="HWD")
            if not headword_tag:
                continue

            headword = headword_tag.get_text(strip=True).lower()
            if headword != word.lower() and headword != american_to_british[word]:
                continue  # فقط مدخل‌هایی که دقیقا خود کلمه هستند
            
            pos_tag = entry.find("span", class_="POS")
            phonetic_tag = entry.find("span", class_="PRON")
            speakers = entry.find_all("span", class_="speaker")

            if not pos_tag or not speakers:
                continue
            
            isPhoneticValid = True
            if phonetic_tag is not None:
                isPhoneticValid = has_invalid_parent_class(phonetic_tag)
                if(isPhoneticValid):
                    phonetic_tag = None
                


            pos = pos_tag.get_text(strip=True)
            phonetic = phonetic_tag.get_text(strip=True) if phonetic_tag else None
            
            british_audio = None
            american_audio = None

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

# تغییر در تابع اصلی برای استفاده از وویس آکسفورد در صورت عدم پیدا شدن وویس در لانگمن
async def process_word(chat_id, word):
    fetch_oxford_audio_enabled = False
    original_word = word
    parts_data = fetch_longman_data(word)

    # اگر داده‌ای برای تلفظ نبود و معادل بریتیش وجود داشت، اونو امتحان کن
    if not parts_data and word in american_to_british:
        alt_word = american_to_british[word]
        parts_data = fetch_longman_data(alt_word)
        if parts_data:
            word = alt_word  # اگر نتیجه داشت، اون کلمه جایگزین بشه

    longman_link = build_longman_link(word)
    oxford_link = build_oxford_link(word)

    reply = {
        "chat_id": chat_id,
        "text": f"کلمه: {original_word}\n\n📚 Longman: {longman_link}\n📖 Oxford: {oxford_link}"
    }
    res = requests.post(API_URL, json=reply)

    preferred = user_preferences.get(chat_id, "american")
    user_pos = "br" if preferred == "british" else "us"
    
    if len(parts_data) == 0: fetch_oxford_audio_enabled = True
    
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
                error_reply = {
                    "chat_id": chat_id,
                    "text": f"❌ خطا در دانلود فایل صوتی: {e}"
                }
                res = requests.post(API_URL, json=error_reply)
                print("📤 ارسال پیام خطا:", res.json())
        else:
            fetch_oxford_audio_enabled = True
    
    if(fetch_oxford_audio_enabled):  
        # اگر هیچ وویسی در لانگمن نبود، وویس آکسفورد را امتحان کن
        oxford_Data = fetch_oxford_audio(word,preferred)
        if oxford_Data:
            try:
                pos = oxford_Data.pos
                phonetic = oxford_Data.phonetic
                audio_url = oxford_Data.audio_url

            caption = f"🔉 {word} ({pos})"
            if phonetic:
                caption += f"\n📌 /{phonetic}/"
            
                headers = {"User-Agent": "Mozilla/5.0"}
                response = requests.get(oxford_audio_url, headers=headers)
                    
                if response.status_code == 200 and response.headers["Content-Type"].startswith("audio"):
                    safe_word = re.sub(r'[^\w\-]+', '_', word)
                    file_name = f"{safe_word}_oxford_{user_pos}.mp3"
                    
                    with open(file_name, "wb") as f:
                        f.write(response.content)
                        
                    with open(file_name, "rb") as audio_file:
                        files = {'audio': audio_file}
                        data = {'chat_id': chat_id, 'caption': oxford_phonetic}
                        send_audio_url = f"https://api.telegram.org/bot{TOKEN}/sendAudio"
                        res = requests.post(send_audio_url, data=data, files=files)
                        print("📤 ارسال فایل صوتی از آکسفورد:", res.json())

                    os.remove(file_name)

            except Exception as e:
                error_reply = {
                    "chat_id": chat_id,
                    "text": f"❌ خطا در دانلود فایل صوتی از آکسفورد: {e}"
                }
                res = requests.post(API_URL, json=error_reply)
                print("📤 ارسال پیام خطا:", res.json())            
                
def fetch_oxford_audio(word, preferred_accent):
    url = build_oxford_link(word)
    headers = {"User-Agent": "Mozilla/5.0"}
    data = {
            "audio_url": None,
            "phonetic": None,
            "pos": None
        }  
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"❌ دریافت صفحه آکسفورد ناموفق بود. Status: {response.status_code}")
            return data

        soup = BeautifulSoup(response.text, "html.parser")

        # استخراج لینک mp3
        accent_class = 'pron-us' if preferred_accent == 'us' else 'pron-uk'
    
        audio_div = soup.find('div', class_=lambda c: c and
                         'sound' in c.split() and
                         'audio_play_button' in c.split() and
                         accent_class in c.split())
        # اگر div پیدا بشه، بررسی ویژگی data-src-mp3
        if audio_div and audio_div.has_attr('data-src-mp3'):
            audio_url = audio_div['data-src-mp3']
            # بررسی اینکه فونتیک هم موجود باشه
            phonetic = audio_div.get('title', None)
        
        else:
            print("❌ صدا برای لهجه انتخاب‌شده در آکسفورد پیدا نشد.")
            return data   

        # پیدا کردن اولین جزء کلام (POS)
        pos_tags = soup.find_all("span", class_="pos")
        
        if pos_tags:
            pos = pos_tags[0].text.strip()  # اولین جزء کلام
        else:
            pos = None

        # بازگشت اطلاعات به همراه POS و تلفظ صوتی
        data = {
            "audio_url": audio_url,
            "phonetic": phonetic,
            "pos": pos
        }
        return data

    except Exception as e:
        print(f"❌ خطا در واکشی تلفظ آکسفورد: {e}")
        return data

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