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

READ_LIST_FROM_ENV = True if os.getenv("READ_LIST_FROM_ENV").lower() == "true" else False
READ_LIST_FROM_ENV = False

 # ذخیره پیش‌فرض تلفظ کاربران
user_dic_preference = {}
user_accent_preference = {}
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
        else:
            with open(USER_FILE, "w") as f:
                json.dump({}, f)
        if str(user_id) not in ADMINS and str(user_id) not in users:
            users[str(user_id)] = datetime.now().strftime("%Y-%m-%d")
            with open(USER_FILE, "w") as f:
                json.dump(users, f)
            print(">>>>>>>>>>>>>>>>> Users:", users)
    except Exception as e:
        print("❌ خطا در ذخیره کاربر:", e)

def get_user_stats():
    try:
        if not os.path.exists(USER_FILE):
            return {"total": 1, "today": 1, "yesterday": 1}

        with open(USER_FILE, "r") as f:
            users = json.load(f)
        total = len(users)
        today = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()

        today_count = sum(1 for d in users.values() if d == today)
        yesterday_count = sum(1 for d in users.values() if d == yesterday)

        return {
            "total": total + 1,
            "today": today_count + 1,
            "yesterday": yesterday_count + 1
        }
    except Exception as e:
        print("❌ خطا در خواندن آمار:", e)
        return {"total": 1, "today": 1, "yesterday": 1}
# ----------------- LONGMAN PARSER -----------------
# لیست تبدیل املای آمریکایی به بریتیش یا برعکس بر اساس لانگمن یا آکسفورد
equivalnet_spelling_list = {
 'acknowledgement': 'acknowledgment',
 'aluminium': 'aluminum',
 'anemia': 'anaemia',
 'analog': 'analogue',
#  'analyse': 'analyze',
 'analyze': 'analyse',
 'apologise': 'apologize',
#  'apologize': 'apologise',
 'appall': 'appal',
 'appetiser': 'appetizer',
#  'appetizer': 'appetiser',
 'arbor': 'arbour',
 'ardor': 'ardour',
 'armor': 'armour',
 'behavior': 'behaviour',
#  'behaviour': 'behavior',
 'cecum': 'caecum', # oxford
 'caecum': 'cecum',# oxford
 'caeca': 'caecum',# oxford - plural
 'caecum': 'caecum',# oxford - plural
 'cesium': 'caesium',
 'Cs': 'cesium',
 'caliber': 'calibre',
#  'calibre': 'caliber',
 'candor': 'candour',
 'catalog': 'catalogue',
 'catalyze': 'catalyse',
 'categorise': 'categorize',
 'cecum': 'caecum',
 'center': 'centre',
#  'centre': 'center',
 'cesium': 'caesium',
 'characterisation': 'characterization',
 'civilise': 'civilize',
#  'civilize': 'civilise',
 'clamor': 'clamour',
 'celiac': 'coeliac',
 'coeliac': 'celiac disease',
 'colonise': 'colonize',
 'colonize': 'colonise',
 'color': 'colour',
 'counseling': 'counselling',
#  'counselling': 'counseling',
#  'counsellor': 'counselor',
 'counselor': 'counsellor',
 'criticise': 'criticize',
#  'criticize': 'criticise',
 'defence': 'defense', # noun in UK is 'defence', verb is 'defense'
 'defense': 'defence',
 'demeanor': 'demeanour',
 'emphasise': 'emphasize',
#  'emphasize': 'emphasise',
 'encyclopaedia': 'encyclopedia',
#  'encyclopedia': 'encyclopaedia',
 'endeavor': 'endeavour',
#  'endeavour': 'endeavor',
 'enrollment': 'enrolment',
#  'enrolment': 'enrollment',
 'equaling': 'equal',
 'equalling': 'equal',
 'estrogen': 'oestrogen',
 'favorite': 'favourite',
 'favour': 'favor',
 'favourite': 'favorite',
 'fervor': 'fervour',
 'fiber': 'fibre',
 'fibre': 'fiber',
 'flavor': 'flavour',
#  'flavour': 'flavor',
 'fetus': 'foetus',
 'fueled': 'fuel',
 'fuelled': 'fuel',
 'fueling': 'fuelling',
 'fuelled': 'fueled',
 'fueling': 'fuel',
 'fuelling': 'fuel',
 'fulfill': 'fulfil',
#  'fulfils': 'fulfills',
 'glamor': 'glamour',
#  'glamour': 'glamor',
 'goiter': 'goitre',
 'harbor': 'harbour',
#  'honor': 'honour',
 'honour': 'honor',
#  'humor': 'humour',
 'humour': 'humor',
 'installment': 'instalment',
#  'instalment': 'installment',
 'instill': 'instil',
 'jewelry': 'jewellery',
#  'jewelry': 'jewellery',
 'kilometer': 'kilometre',
#  'kilometre': 'kilometer',
 'labor': 'labour',
#  'labour': 'labor',
 'leukaemia': 'leukemia',
#  'leukemia': 'leukaemia',
 'licence': 'license', # noun in UK is 'licence', verb is 'license' or 'licence'
 'license': 'licence',
 'liter': 'litre',
#  'litre': 'liter',
 'louver': 'louvre',
#  'louvre': 'louver',
 'luster': 'lustre',
#  'lustre': 'luster',
 'maneuver': 'manoeuvre',
#  'manoeuvre': 'maneuver',
 'marvelous': 'marvellous',
 'meager': 'meagre',
#  'meagre': 'meager',
 'mediaeval': 'medieval',
#  'medieval': 'mediaeval',
 'memorise': 'memorize',
#  'memorize': 'memorise',
 'meter': 'metre',
 'metre': 'meter',
 'minimise': 'minimize',
#  'minimize': 'minimise',
 'modeling': 'modelling',
 'mold': 'mould',
 'molt': 'moult',
 'mustache': 'moustache',
 'neighbor': 'neighbour',
#  'neighbour': 'neighbor',
 'odor': 'odour',
#  'odour': 'odor',
 'esophagus': 'oesophagus',
 'oestrogen': 'estrogen',
#  'offence': 'offense',
 'offense': 'offence',
 'organise': 'organize',
#  'organize': 'organise',
 'organisation': 'organzsation',
 'pediatric': 'paediatric',
 'pediatrician': 'paediatrician',
 'pedophile': 'paedophile',
#  'paralyse': 'paralyze',
 'paralyze': 'paralyse',
 'parlor': 'parlour',
 'patronise': 'patronize',
#  'patronize': 'patronise',
 'plow': 'plough',
 'practice': 'practise',   # noun in US/UK: practice; verb in UK: practise
 'practise': 'practice',
#  'pretence': 'pretense',
 'pretense': 'pretence',
 'prise': 'prize',
#  'prize': 'prise',
 'pajamas': 'pyjamas',
 'quarreling': 'quarrel',
 'quarrelling': 'quarrel',
 'rancor': 'rancour',
 'realise': 'realize',
#  'realize': 'realise',
 'recognise': 'recognize',
#  'recognize': 'recognise',
 'reveled': 'revel',
 'revelled': 'revel',
 'revelling': 'reveling',
 'rigor': 'rigour',
 'rumor': 'rumour',
#  'rumour': 'rumor',
 'saber': 'sabre',
#  'sabre': 'saber',
 'savior': 'saviour',
 'savor': 'savour',
#  'savour': 'savor',
 'scepter': 'sceptre',
#  'sceptre': 'scepter',
 'signaling': 'signal',
 'signalling': 'signal',
#  'skilful': 'skillful',
 'skillful': 'skilful',
 'smolder': 'smoulder',
 'socialise': 'socialize',
#  'socialize': 'socialise',
 'somber': 'sombre',
#  'sombre': 'somber',
 'specialise': 'specialize',
#  'specialize': 'specialise',
 'specter': 'spectre',
#  'spectre': 'specter',
 'splendor': 'splendour',
#  'splendour': 'splendor',
 'succor': 'succour',
 'tarif': 'tariff',
 'theater': 'theatre',
#  'theatre': 'theater',
 'traveled': 'travel',
 'travelled': 'travel',
 'traveler': 'traveller',
 'traveling': 'travelling',
#  'travelle': 'traveler',
#  'travelled': 'traveled',
#  'traveller': 'traveler',
#  'travelling': 'traveling',
 'tumor': 'tumour',
 'valor': 'valour',
 'vapor': 'vapour',
 'vigor': 'vigour',
#  'vigour': 'vigor',
 'visualisation': 'visualization',
 'whiskey': 'whisky',
 'whiskey': 'whiskies',
 'whiskey': 'whiskeys',
 'willful': 'wilful',
 'women': 'woman',
 }
BIO_SPELLING = os.getenv("Equivalnet_Spelling_List")
if READ_LIST_FROM_ENV and BIO_SPELLING:
    with open(BIO_SPELLING, "r") as f:
        equivalnet_spelling_list = json.load(f)

# Irregular plural forms
irregular_plural_list = {
  "children": "child",
  "feet": "foot",
  "geese": "goose",
  "men": "man",
  "women": "woman",
  "teeth": "tooth",
  "mice": "mouse",
  "lice": "louse",
  "oxen": "ox",
  "people": "person",
  "dice": "die",
  "cacti": "cactus",
  "fungi": "fungus",
  "nuclei": "nucleus",
  "syllabi": "syllabus",
  "alumni": "alumnus",
  "antennae": "antenna",
  "formulae": "formula",
  "bacteria": "bacterium",
  "media": "medium",
  "data": "datum",
  "criteria": "criterion",
  "phenomena": "phenomenon",
  "theses": "thesis",
  "analyses": "analysis",
  "diagnoses": "diagnosis",
  "parentheses": "parenthesis",
  "prognoses": "prognosis",
  "synopses": "synopsis",
  "axes": "axis",
  "matrices": "matrix",
  "vertices": "vertex",
  "indices": "index",
  "appendices": "appendix",
  "beaux": "beau",
  "chateaux": "chateau",
  "tableaux": "tableau",
  "lives": "life",
  "knives": "knife",
  "wives": "wife",
  "leaves": "leaf",
  "wolves": "wolf",
  "selves": "self",
  "elves": "elf",
  "loaves": "loaf",
  "halves": "half",
  "scarves": "scarf",
  "calves": "calf",
  "hooves": "hoof"
}

BIO_SPELLING = os.getenv("Irregular_Plural_List")
if READ_LIST_FROM_ENV and BIO_SPELLING:
    with open(BIO_SPELLING, "r") as f:
        irregular_plural_list = json.load(f)
        
# find possible forms
def find_alternative_words(word):
    alternative_words = [word]
    
    # Check for equivalent spelling
    if word in equivalnet_spelling_list:
        alternative_words.append(equivalnet_spelling_list[word])
    # Irregulars
    if word in irregular_plural_list:
        alternative_words.append(irregular_plural_list[word])

    # Regular patterns
    if word.endswith('ies'):
        alternative_words.append(re.sub('ies$', 'y', word))
    if word.endswith('es'):
        alternative_words.append(re.sub('es$', '', word))
    if word.endswith('s') and not word.endswith('ss'):
        alternative_words.append(re.sub('s$', '', word))
    if word.endswith('ing'):
        alternative_words.append(re.sub('ing$', '', word))
        alternative_words.append(re.sub('ing$', 'e', word))
    if word.endswith('ed'):
        alternative_words.append(re.sub('ed$', '', word))
        alternative_words.append(re.sub('ed$', 'e', word))

    return list(alternative_words)


def build_longman_link(word):
    return f"https://www.ldoceonline.com/dictionary/{word.lower().replace(' ', '-')}"
BIO_SPELLING = os.getenv("Irregular_Plural_List")
if READ_LIST_FROM_ENV and BIO_SPELLING:
    with open(BIO_SPELLING, "r") as f:
        irregular_plural_list = json.load(f)
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

async def get_audio_url(audio_url, preferred_accent, pos, word, chat_id, caption):
    if audio_url:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(audio_url, headers=headers)

            if response.status_code == 200 and response.headers["Content-Type"].startswith("audio"):
                safe_word = re.sub(r'[^\w\-]+', '_', word)
                file_name = f"{safe_word}_{preferred_accent}_{pos}.mp3"

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
  
async def fetch_longman_data(word, preferred_accent = "american"):
    url = build_longman_link(word)
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return []
        accent_class = 'pron-us' if preferred_accent == 'american' else 'pron-uk'

        soup = BeautifulSoup(response.text, "html.parser")
        data = []

        entries = soup.find_all("span", class_="ldoceEntry Entry")
        
        for entry in entries:
            headword_tag = entry.find("span", class_="HWD")
            
            if not headword_tag:
                continue
        
            headword = headword_tag.get_text(strip=True).lower()
            if headword != word.lower() and headword != equivalnet_spelling_list.get(word, word):
                continue  # فقط مدخل‌هایی که دقیقا خود کلمه هستند

            pos_tag = entry.find("span", class_="POS")
            phonetic_tag = entry.find("span", class_="PRON")
            speakers = entry.find_all("span", class_="speaker")


            if (not pos_tag and word not in irregular_plural_list) or not speakers:
                continue
            
            isPhoneticValid = True
            if phonetic_tag is not None:
                isPhoneticValid = has_invalid_parent_class(phonetic_tag)
                if(isPhoneticValid):
                    phonetic_tag = None 
            if pos_tag:
                pos = pos_tag.get_text(strip=True)
            else:
                pos = ""
            if phonetic_tag:
                phonetic = phonetic_tag.get_text(strip=True) if phonetic_tag else None
            else:
                phonetic = ""
            audio_url = None
            british_audio = None
            american_audio = None

            for spk in speakers:
                mp3_url = spk.get("data-src-mp3", "")

                if "breProns" in mp3_url and not british_audio:
                    british_audio = mp3_url
                elif "ameProns" in mp3_url and not american_audio:
                    american_audio = mp3_url
            # اگر هیچ کدام از صداها پیدا نشد، ادامه بده     
            if (preferred_accent == 'british' and british_audio) or (preferred_accent == 'american' and american_audio):
                audio_url = british_audio if preferred_accent == 'british' else american_audio
                data.append({
                    "word": word,
                    "url": url,
                    "pos": pos,
                    "phonetic": phonetic,
                    "audio_url": audio_url,
                    # "british": british_audio,
                    # "american": american_audio
                })

        return data

    except Exception as e:
        print(f"⚠️ خطا در واکشی اطلاعات لانگمن: {e}")
        return []

async def fetch_oxford_data(word, preferred_accent = "american"):
    url = build_oxford_link(word)
    headers = {"User-Agent": "Mozilla/5.0"}
    data = []  
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"❌ دریافت صفحه آکسفورد ناموفق بود. Status: {response.status_code}")
            alt_url = build_oxford_link(word)
            return data

        soup = BeautifulSoup(response.text, "html.parser")
        print("🔍 دریافت صفحه آکسفورد:", url)
        print("response.text", response.text)
        print("oxford soup", soup)
        soup
        if not soup return data
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
        data.append({
            "word": word, 
            "url": url,
            "audio_url": audio_url,
            "phonetic": phonetic,
            "pos": pos
        })
        return data    

    except Exception as e:
        print(f"❌ خطا در واکشی تلفظ آکسفورد: {e}")
        return None

# تغییر در تابع اصلی برای استفاده از وویس آکسفورد در صورت عدم پیدا شدن وویس در لانگمن
async def process_word(chat_id, word):
    initial_word = word
    longman_word = word
    oxford_word = word
    longman_data_fetched = False
    oxford_data_fetched = False
    original_word = word
    preferred_dic = user_dic_preference.get(chat_id, "longman_oxford")
    preferred_accent = user_accent_preference.get(chat_id, "american")
    fetch_longman_enabled = True if preferred_dic == "longman" or preferred_dic == "longman_oxford" else False
    fetch_oxford_enabled = True if preferred_dic == "oxford" or preferred_dic == "longman_oxford" else False
    fetch_both_dic_enabled = True if preferred_dic == "longman_oxford" else False

    if fetch_longman_enabled:
        longman_data = await fetch_longman_data(word, preferred_accent)
    else:
        longman_data = None
    if longman_data:
        longman_data_fetched = True
    else:
        longman_data_fetched = False
    
    if fetch_oxford_enabled:
        oxford_data = await fetch_oxford_data(word, preferred_accent)
    else:
        oxford_data = None
    if oxford_data:
        oxford_data_fetched = True
    else:
        oxford_data = await fetch_oxford_data(f"{word.lower()}1", preferred_accent)
        oxford_data_fetched = True if oxford_data else False

        
    alternative_words = find_alternative_words(word)
    longman_equivalnet_replaced = False
    oxford_equivalnet_replaced = False

    if fetch_longman_enabled and not longman_data_fetched and len(alternative_words) > 0:
        for alt_word in alternative_words:
            longman_data = await fetch_longman_data(alt_word, preferred_accent)
            if longman_data:
                longman_word = alt_word  # اگر نتیجه داشت، اون کلمه جایگزین بشه
                longman_equivalnet_replaced = True
                longman_data_fetched = True
                break

    if fetch_oxford_enabled and not oxford_data_fetched and len(alternative_words) > 0:
        for alt_word in alternative_words:
            oxford_data = await fetch_oxford_data(alt_word, preferred_accent)
            if oxford_data:
                oxford_word = alt_word  # اگر نتیجه داشت، اون کلمه جایگزین بشه
                oxford_equivalnet_replaced = True
                oxford_data_fetched = True
                break
    if (fetch_both_dic_enabled and not longman_data_fetched and not oxford_data_fetched) or (not longman_data_fetched and not oxford_data_fetched and word == original_word):
        reply = {
            "chat_id": chat_id,
            "text": f"❌کلمه یا تلفظ صوتی کلمه در دیکشنری یا دیکشنری های مورد نظر وجود ندارد وجود ندارد"
        }
        res = requests.post(API_URL, json=reply)
        print("📤تلفظ صوتی کلمه وجود ندارد", res.json())
        return    
    longman_link = longman_data[0].get('url') if (longman_data_fetched and len(longman_data)>0) else None

    oxford_link = oxford_data[0].get('url') if (oxford_data_fetched and len(oxford_data)>0) else None
    
    longman_replaced_word = longman_word if longman_equivalnet_replaced else word
    oxford_replaced_word = oxford_word if oxford_equivalnet_replaced else word
    if(fetch_both_dic_enabled):
        message = f"کلمه: {original_word}\n\n📚 Longman: {longman_link}\n📖 Oxford: {oxford_link}"
    elif fetch_longman_enabled and longman_data_fetched:
        message = f"کلمه: {original_word}\n\n📚 Longman: {longman_link}"
    elif fetch_oxford_enabled and oxford_data_fetched:
        message = f"کلمه: {original_word}\n\n📖 Oxford: {oxford_link}"
    else:
        message = "این کلمه در دیکشنری های مورد نظر وجود ندارد"
    reply = {
        "chat_id": chat_id,
        "text": message
    }
    res = requests.post(API_URL, json=reply)           

    if longman_data_fetched:
        for entry in longman_data:
            pos = entry['pos']
            phonetic = entry['phonetic']
            audio_url = entry['audio_url']
            # entry[preferred_accent]
            pos_caption = f"({pos})" if pos else ""
            caption = f"🔉 {longman_replaced_word} {pos_caption} - longman"
            if phonetic:
                caption += f"\n📌 /{phonetic}/ "
            await get_audio_url(audio_url, preferred_accent, pos, longman_word, chat_id, caption)
    elif fetch_longman_enabled:
        reply = {
            "chat_id": chat_id,
            "text": f"❌کلمه یا تلفظ صوتی کلمه در دیکشنری لانگمن وجود ندارد وجود ندارد"
        }
        res = requests.post(API_URL, json=reply)
        print("📤تلفظ صوتی کلمه وجود ندارد", res.json())
        return 
        
    if oxford_data_fetched:
        for entry in oxford_data:
            pos = entry['pos']
            phonetic = entry['phonetic']
            audio_url = entry['audio_url']
            pos_caption = f"({pos})" if pos else ""
            caption = f"🔉 {oxford_replaced_word} {pos_caption} - oxford"
            if phonetic:
                caption += f"\n📌 /{phonetic}/"
            await get_audio_url(audio_url, preferred_accent, pos, oxford_word, chat_id, caption)
    elif oxford_data_fetched:    
        reply = {
            "chat_id": chat_id,
            "text": f"❌کلمه یا تلفظ صوتی کلمه در دیکشنری آکسفورد وجود ندارد وجود ندارد"
        }
        res = requests.post(API_URL, json=reply)
        print("📤تلفظ صوتی کلمه وجود ندارد", res.json())
        return 
    
# ----------------- FastAPI Webhook -----------------
@app.post("/webhook/{token}")
async def webhook(token: str, request: Request):
    try:
        if token != TOKEN:
            return {"ok": False, "error": "Invalid token"}
        global ADMINS
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
                user_accent_preference[chat_id] = "british"
                reply = {
                    "chat_id": chat_id,
                    "text": "✅ تلفظ پیش‌فرض روی 🇬🇧 British تنظیم شد!"
                }
                res = requests.post(API_URL, json=reply)
                print("📤 ارسال تغییر تنظیم British:")

            elif text == "/american":
                user_accent_preference[chat_id] = "american"
                reply = {
                    "chat_id": chat_id,
                    "text": "✅ تلفظ پیش‌فرض روی 🇬🇧 American تنظیم شد!"
                }
                res = requests.post(API_URL, json=reply)
                print("📤 جواب به تلگرام ارسال شد:")
            elif text == "/longman":
                user_dic_preference[chat_id] = "longman"
                reply = {
                    "chat_id": chat_id,
                    "text": "✅ دیکشنری پیش‌فرض روی دیکشنری لانگمن تنظیم شد!"
                }
                res = requests.post(API_URL, json=reply)
                print("📤 جواب به تلگرام ارسال شد:")
            elif text == "/oxford":
                user_dic_preference[chat_id] = "oxford"
                reply = {
                    "chat_id": chat_id,
                    "text": "✅ دیکشنری پیش‌فرض روی دیکشنری آکسفورد تنظیم شد!"
                }
                res = requests.post(API_URL, json=reply)
                print("📤 جواب به تلگرام ارسال شد:") 
            elif text == "/longman_oxford":
                user_dic_preference[chat_id] = "longman_oxford"
                reply = {
                    "chat_id": chat_id,
                    "text": "✅ دیکشنری پیش‌فرض روی هر دو دیکشنری لانگمن و آکسفورد تنظیم شد!"
                }
                res = requests.post(API_URL, json=reply)
                print("📤 جواب به تلگرام ارسال شد:")   
            elif text == "/stats":
                if str(user_id) not in ADMINS:
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
                save_user(user_id)
                await process_word(chat_id, text)
        return {"ok": True}
    except Exception as e:
        print("❌ خطا:", e)
        return {"ok": False, "error": str(e)}