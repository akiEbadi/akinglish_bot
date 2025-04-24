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

user_preferences = {}

API_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

SPELLING_VARIANTS = {
    'acknowledgement': 'acknowledgment', 'acknowledgment': 'acknowledgement',
    'aluminium': 'aluminum', 'aluminum': 'aluminium',
    'anaemia': 'anemia', 'anemia': 'anaemia',
    'analyse': 'analyze', 'analyze': 'analyse',
    'apologise': 'apologize', 'apologize': 'apologise',
    'appal': 'appall', 'appall': 'appal',
    'appals': 'appalls', 'appalls': 'appals',
    'appetiser': 'appetizer', 'appetizer': 'appetiser',
    'arbour': 'arbor', 'arbor': 'arbour',
    'ardour': 'ardor', 'ardor': 'ardour',
    'armour': 'armor', 'armor': 'armour',
    'behavior': 'behaviour', 'behaviour': 'behavior',
    'caecum': 'cecum', 'cecum': 'caecum',
    'caesium': 'cesium', 'cesium': 'caesium',
    'caliber': 'calibre', 'calibre': 'caliber',
    'candour': 'candor', 'candor': 'candour',
    'catalogue': 'catalog', 'catalog': 'catalogue',
    'catalyse': 'catalyze', 'catalyze': 'catalyse',
    'celiac': 'coeliac', 'coeliac': 'celiac',
    'center': 'centre', 'centre': 'center',
    'civilise': 'civilize', 'civilize': 'civilise',
    'clamour': 'clamor', 'clamor': 'clamour',
    'colonise': 'colonize', 'colonize': 'colonise',
    'color': 'colour', 'colour': 'color',
    'counseling': 'counselling', 'counselling': 'counseling',
    'counsellor': 'counselor', 'counselor': 'counsellor',
    'criticise': 'criticize', 'criticize': 'criticise',
    'defence': 'defense', 'defense': 'defence',
    'demeanour': 'demeanor', 'demeanor': 'demeanour',
    'emphasise': 'emphasize', 'emphasize': 'emphasise',
    'encyclopaedia': 'encyclopedia', 'encyclopedia': 'encyclopaedia',
    'endeavor': 'endeavour', 'endeavour': 'endeavor',
    'enrollment': 'enrolment', 'enrolment': 'enrollment',
    'equaling': 'equalling', 'equalling': 'equaling',
    'estrogen': 'oestrogen', 'oestrogen': 'estrogen',
    'favorite': 'favourite', 'favourite': 'favorite',
    'favour': 'favor', 'favor': 'favour',
    'fervour': 'fervor', 'fervor': 'fervour',
    'fiber': 'fibre', 'fibre': 'fiber',
    'flavor': 'flavour', 'flavour': 'flavor',
    'foetus': 'fetus', 'fetus': 'foetus',
    'fueled': 'fuelled', 'fuelled': 'fueled',
    'fueling': 'fuelling', 'fuelling': 'fueling',
    'fulfil': 'fulfill', 'fulfill': 'fulfil',
    'fulfils': 'fulfills', 'fulfills': 'fulfils',
    'glamor': 'glamour', 'glamour': 'glamor',
    'goitre': 'goiter', 'goiter': 'goitre',
    'harbour': 'harbor', 'harbor': 'harbour',
    'honor': 'honour', 'honour': 'honor',
    'humor': 'humour', 'humour': 'humor',
    'installment': 'instalment', 'instalment': 'installment',
    'instil': 'instill', 'instill': 'instil',
    'instils': 'instills', 'instills': 'instils',
    'jewellery': 'jewelry', 'jewelry': 'jewellery',
    'kilometer': 'kilometre', 'kilometre': 'kilometer',
    'labor': 'labour', 'labour': 'labor',
    'leukaemia': 'leukemia', 'leukemia': 'leukaemia',
    'licence': 'license', 'license': 'licence',
    'liter': 'litre', 'litre': 'liter',
    'louver': 'louvre', 'louvre': 'louver',
    'luster': 'lustre', 'lustre': 'luster',
    'maneuver': 'manoeuvre', 'manoeuvre': 'maneuver',
    'marvellous': 'marvelous', 'marvelous': 'marvellous',
    'meager': 'meagre', 'meagre': 'meager',
    'mediaeval': 'medieval', 'medieval': 'mediaeval',
    'memorise': 'memorize', 'memorize': 'memorise',
    'meter': 'metre', 'metre': 'meter',
    'minimise': 'minimize', 'minimize': 'minimise',
    'modeling': 'modelling', 'modelling': 'modeling',
    'mould': 'mold', 'mold': 'mould',
    'moult': 'molt', 'molt': 'moult',
    'moustache': 'mustache', 'mustache': 'moustache',
    'neighbor': 'neighbour', 'neighbour': 'neighbor',
    'odor': 'odour', 'odour': 'odor',
    'oesophagus': 'esophagus', 'esophagus': 'oesophagus',
    'organise': 'organize', 'organize': 'organise',
    'paediatric': 'pediatric', 'pediatric': 'paediatric',
    'paediatrician': 'pediatrician', 'pediatrician': 'paediatrician',
    'paedophile': 'pedophile', 'pedophile': 'paedophile',
    'paralyse': 'paralyze', 'paralyze': 'paralyse',
    'parlour': 'parlor', 'parlor': 'parlour',
    'patronise': 'patronize', 'patronize': 'patronise',
    'plough': 'plow', 'plow': 'plough',
    'practice': 'practise', 'practise': 'practice',
    'pretence': 'pretense', 'pretense': 'pretence',
    'prise': 'prize', 'prize': 'prise',
    'pyjamas': 'pajamas', 'pajamas': 'pyjamas',
    'quarreling': 'quarrelling', 'quarrelling': 'quarreling',
    'rancour': 'rancor', 'rancor': 'rancour',
    'realise': 'realize', 'realize': 'realise',
    'recognise': 'recognize', 'recognize': 'recognise',
    'revelled': 'reveled', 'reveled': 'revelled',
    'revelling': 'reveling', 'reveling': 'revelling',
    'rigour': 'rigor', 'rigor': 'rigour',
    'rumor': 'rumour', 'rumour': 'rumor',
    'saber': 'sabre', 'sabre': 'saber',
    'saviour': 'savior', 'savior': 'saviour',
    'savor': 'savour', 'savour': 'savor',
    'scepter': 'sceptre', 'sceptre': 'scepter',
    'signaling': 'signalling', 'signalling': 'signaling',
    'skilful': 'skillful', 'skillful': 'skilful',
    'smoulder': 'smolder', 'smolder': 'smoulder',
    'socialise': 'socialize', 'socialize': 'socialise',
    'somber': 'sombre', 'sombre': 'somber',
    'specialise': 'specialize', 'specialize': 'specialise',
    'specter': 'spectre', 'spectre': 'specter',
    'splendor': 'splendour', 'splendour': 'splendor',
    'succour': 'succor', 'succor': 'succour',
    'theater': 'theatre', 'theatre': 'theater',
    'traveled': 'travelled', 'travelled': 'traveled',
    'traveler': 'traveller', 'traveller': 'traveler',
    'traveling': 'travelling', 'travelling': 'traveling',
    'tumour': 'tumor', 'tumor': 'tumour',
    'valour': 'valor', 'valor': 'valour',
    'vapour': 'vapor', 'vapor': 'vapour',
    'vigor': 'vigour', 'vigour': 'vigor',
    'whisky': 'whiskey', 'whiskey': 'whisky',
    'wilful': 'willful', 'willful': 'wilful'
}

def build_longman_link(word):
    return f"https://www.ldoceonline.com/dictionary/{word.lower().replace(' ', '-')}"

def fetch_longman_data(word):
    def extract_data_from_html(html):
        soup = BeautifulSoup(html, "html.parser")
        entries = soup.find_all("span", class_="ldoceEntry Entry")
        data = []

        for entry in entries:
            pos_tag = entry.find("span", class_="POS")
            phonetic_tag = entry.find("span", class_="PRON")
            speakers = entry.find_all("span", class_="speaker")

            if not pos_tag or not speakers:
                continue

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

    url = build_longman_link(word)
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return []

    data = extract_data_from_html(response.text)
    if not data and word in SPELLING_VARIANTS:
        alt_word = SPELLING_VARIANTS[word]
        url = build_longman_link(alt_word)
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = extract_data_from_html(response.text)

    if not data:
        soup = BeautifulSoup(response.text, "html.parser")
        speakers = soup.find_all("span", class_="speaker")
        for spk in speakers:
            mp3_url = spk.get("data-src-mp3", "")
            if mp3_url:
                accent = "british" if "breProns" in mp3_url else "american"
                data.append({
                    "pos": "",
                    "phonetic": None,
                    "british": mp3_url if accent == "british" else None,
                    "american": mp3_url if accent == "american" else None
                })
                break

    return data
