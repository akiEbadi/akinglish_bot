
from fastapi import FastAPI, Request
import os
import requests
from telegram import Bot
from telegram.constants import ParseMode
from bs4 import BeautifulSoup
import re
from datetime import datetime, date, timedelta
import json

app = FastAPI()

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("TOKEN is not set!")

ADMINS = os.getenv("ADMINS", "")
print("initial ADMINS is:", ADMINS)
ADMINS = [int(x.strip()) for x in ADMINS.split(",") if x.strip().isdigit()]

user_preferences = {}  # ذخیره پیش‌فرض تلفظ کاربران
user_pos = {}  # ذخیره موقعیت تلفظ کاربران (br/us)
USER_FILE = "users.json"

API_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# ----------------- UTILITIES -----------------
def save_user(user_id):
    try:
        users = {}
        if os.path.exists(USER_FILE):
            with open(USER_FILE, "r") as f:
                users = json.load(f)
        if user_id not in ADMINS and str(user_id) not in users:
            users[str(user_id)] = datetime.now().strftime("%Y-%m-%d")
            with open(USER_FILE, "w") as f:
                json.dump(users, f)
    except Exception as e:
        print("❌ خطا در ذخیره کاربر:", e)

def get_user_stats():
    try:
        if not os.path.exists(USER_FILE):
            return {"total": 0, "today": 0, "yesterday": 0}

        with open(USER_FILE, "r") as f:
            users = json.load(f)
        total = len(users)
        today = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()

        today_count = sum(1 for d in users.values() if d == today)
        yesterday_count = sum(1 for d in users.values() if d == yesterday) + 1

        return {
            "total": total if total > 1 else 1,
            "today": today_count if today_count > 1 else 1,
            "yesterday": yesterday_count if yesterday_count > 1 else 1
        }
    except Exception as e:
        print("❌ خطا در خواندن آمار:", e)
        return {"total": 1, "today": 1, "yesterday": 1}
# ----------------- LONGMAN PARSER -----------------
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

# ----------------- OXFORD PARSER -----------------
def build_oxford_link(word):
    return f"https://www.oxfordlearnersdictionaries.com/definition/english/{word.lower().replace(' ', '-')}"

# ----------------- Process Word and Fetch dictionaries info -----------------
def has_invalid_parent_class(element):
    # بررسی والد‌های عنصر تا رسیدن به ریشه
    parents = element.find_parents()
    for parent in parents:
        # بررسی اینکه آیا کلاس‌ها شامل Tail یا DERIV هستند
        classes = parent.get('class', [])
        if isinstance(classes, list) and any(cls in classes for cls in ['Tail', 'DERIV']):
            return True
    return False

def getAudioUrl(audio_url, preferred, pos, word, chat_id, caption):
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
        reply = {
            "chat_id": chat_id,
            "text": f"❌تلفط صوتی کلمه وجود ندارد"
        }
        res = requests.post(API_URL, json=reply)
        print("📤تلفط صوتی کلمه وجود ندارد", res.json())
  
  
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
        accent_class = 'pron-us' if preferred_accent == 'american' else 'pron-uk'

        audio_div = soup.find('div', class_=lambda c: c and
                         'sound' in c.split() and
                         'audio_play_button' in c.split() and
                         accent_class in c.split())
        accent_class_name = 'phons_n_am' if preferred_accent == 'american' else 'prons_br'     

        accent_div = soup.find("div", class_=accent_class_name)

        # اگر div پیدا بشه، بررسی ویژگی data-src-mp3
        if audio_div and audio_div.has_attr('data-src-mp3'):
            audio_url = audio_div['data-src-mp3']
            # بررسی اینکه فونتیک هم موجود باشه
            phonetic_tag = accent_div.find("span", class_="phon")
            phonetic = phonetic_tag.get_text(strip=True) if phonetic_tag else None
            pos_tag = soup.find("span", class_="pos")
            pos = pos_tag.get_text(strip=True) if pos_tag else None
        else:
            print("❌ صدا برای لهجه انتخاب‌شده در آکسفورد پیدا نشد.")
            return data   

        # بازگشت اطلاعات به همراه POS و تلفظ صوتی
        data = {
            "audio_url": audio_url,
            "phonetic": phonetic,
            "pos": pos
        }
        return data    

    except Exception as e:
        print(f"❌ خطا در واکشی تلفظ آکسفورد: {e}")
        return None, None

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

        caption = f"🔉 {word} ({pos}) - {"longman"}"
        if phonetic:
            caption += f"\n📌 /{phonetic}/ "
        getAudioUrl(audio_url, preferred, pos, word, chat_id, caption)
    
    if(fetch_oxford_audio_enabled):  
        # اگر هیچ وویسی در لانگمن نبود، وویس آکسفورد را امتحان کن
        oxford_data = fetch_oxford_audio(word,preferred)
        if oxford_data:
            pos = oxford_data.get('pos') if oxford_data.get('pos') else ""
            phonetic = oxford_data.get('phonetic') if oxford_data.get('phonetic') else ""
            audio_url = oxford_data.get('audio_url') if oxford_data.get('audio_url') else ""
            caption = f"🔉 {word} ({pos}) - {"oxford"}"
            if phonetic:
                caption += f"\n📌 /{phonetic}/"
            getAudioUrl(audio_url, preferred, pos, word, chat_id, caption)      

@app.post("/webhook/{token}")
async def webhook(token: str, request: Request):
    try:
        if token != TOKEN:
            return {"ok": False, "error": "Invalid token"}

        data = await request.json()
        # print("Received data:", data)
        if "message" in data:
            chat_id = data['message']['chat']['id']
            text = data['message'].get('text', '')
            user_id = data['message']['from']['id']

            if text == "/start":
                save_user(user_id)

              
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
                print("📤 ارسال پیام خوش‌آمد:")

            elif text == "/british":
                user_preferences[chat_id] = "british"
                reply = {
                    "chat_id": chat_id,
                    "text": "✅ تلفظ پیش‌فرض روی 🇬🇧 British تنظیم شد!"
                }
                res = requests.post(API_URL, json=reply)
                print("📤 ارسال تغییر تنظیم British:")

            elif text == "/american":
                user_preferences[chat_id] = "american"
                reply = {"chat_id": chat_id, "text": f"پیامت رسید: {text}"}
                res = requests.post(API_URL, json=reply)
                print("📤 جواب به تلگرام ارسال شد:")
                
            elif text == "/stats":
                print("user_id is:", user_id)
                print("ADMINS is:", ADMINS)
                if user_id not in ADMINS:
                    reply = {
                        "chat_id": chat_id,
                        "text": "⛔️ فقط ادمین می‌تواند از این دستور استفاده کند."
                    }
                else:
                    stats = get_user_stats()
                    reply = {
                        "chat_id": chat_id,
                        "text": (
                            f"📊 آمار کاربران:\n\n"
                            f"👥 کل کاربران: {stats['total']}\n"
                            f"🟢 امروز: {stats['today']}\n"
                            f"🕒 دیروز: {stats['yesterday']}"
                        )
                    }   
                res = requests.post(API_URL, json=reply)
                print("📤 ارسال شد آمار:", res.json)
            else:
                await process_word(chat_id, text)
        return {"ok": True}
    except Exception as e:
        print("❌ خطا:", e)
        return {"ok": False, "error": str(e)}