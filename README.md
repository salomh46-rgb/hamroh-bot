# 🤖 Hamroh Bot — Aqlli Virtual Hamroh (AI Telegram Bot)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.12" />
  <img src="https://img.shields.io/badge/Aiogram-3.x-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" alt="Aiogram 3" />
  <img src="https://img.shields.io/badge/Google%20Gemini-3.6%20Flash-orange?style=for-the-badge&logo=google&logoColor=white" alt="Gemini AI" />
  <img src="https://img.shields.io/badge/Edge--TTS-Neural%20Voices-green?style=for-the-badge&logo=microsoft&logoColor=white" alt="Edge TTS" />
  <img src="https://img.shields.io/badge/License-MIT-purple?style=for-the-badge" alt="License MIT" />
</p>

---

## 📖 Loyiha Haqida (About the Project)

**Hamroh Bot** — keksa nuroniy otaxon va onaxonlarimiz hamda yosh bolajonlar uchun mo'ljallangan ko'p tilli (O'zbek / Rus) ijtimoiy **AI virtual hamroh**.

Bot har bir oila a'zosining yosh xususiyatlari, qiziqishlari va ehtiyojlarini inobatga olgan holda individual yondashuvni taklif qiladi:
- **Keksalar uchun:** Tibbiy dori eslatmalari, shoshilinch SOS/Shifokor qo'ng'irog'i, aqliy tetiklik uchun xotira mashqlari, qalbga orom beruvchi retro musiqalar va samimiy, hurmatli ovozli suhbat.
- **Bolalar uchun:** Gemini Vision orqali chizilgan rasmlarni tahlil qilish, sehrli interaktiv kvest-ertaklar, hayvonlar olami viktorinasi, kunlik kitobxonlik rejasi va qiziqarli topishmoqlar.

---

## ✨ Asosiy Imkoniyatlar (Key Features)

### 👵 Otaxon va Onaxonlar Rejimi:
* **💊 Dori eslatmalari (Medication Reminders):** Har kuni belgilangan soatda (masalan: `08:30`) dori ichishni ovozli va matnli xabarnoma orqali mehr bilan eslatib turadi (APScheduler).
* **📞 Shifokor & SOS (Emergency Contact):** 103 (Tez yordam) ga bir zumda ulanish, shaxsiy shifokor yoki farzand telefon raqamini saqlash va 1 tugma bilan chaqiruv yo'llash.
* **🧠 Xotira mashqlari (Memory Training):** Demensiya profilaktikasi va miya faolligini oshirish uchun qiziqarli savol-javoblar va dildan suhbat.
* **🎵 Oltin taronalar (70-80-90-yillar):** Mumtoz va retro qo'shiqlar, xalq navolari va romanslar to'plami.
* **📻 Foydali videolar & Hikmatlar:** Tabobat, 60+ yengil gimnastika va tasalli beruvchi dono rivoyatlar.
* **🎙️ Ovozli AI suhbatdosh:** Ko'zi charchamasligi uchun bot barcha javoblarni ravon neyron ovozda (`Madina`, `Sardor`, `Svetlana`, `Dmitry`) o'qib beradi.

---

### 🧒 Bolajonlar (Kichkintoy) Rejimi:
* **🎨 Sehrli mo'yqalam (AI Drawing Analysis):** Bola chizgan rasmini suratga olib yuboradi. **Gemini Vision (Multimodal)** rasmni ko'rib, uni maqtaydi, ranglar va qahramonlarni topadi va rag'batlantiruvchi **+15 ball** beradi.
* **🗺️ Interaktiv Kvest-Ertak:** Bola o'zi qaror qabul qiladigan 3 bosqichli sarguzasht ertaklar olami.
* **📚 Kitobxonlik daqiqasi (Daily Reading):** Kunlik 5 sahifa mutolaa topshirig'i va o'qilgan kitob bo'yicha suhbat.
* **🐾 Hayvonlar olami viktorinasi:** Jonivorlarning ovozlari va qiziqarli odatlari haqida audio testlar.
* **🎮 Qiziqarli topishmoqlar & 🏆 Ball tizimi:** Har bir vazifa uchun yulduzchalar va faxriy unvonlar.

---

## 🎙️ Ko'p Tilli Neyron Ovoz Tizimi (TTS & STT)

Bot foydalanuvchining ismi orqali uning jinsini va odobli murojaat shaklini avtomatik aniqlaydi:

| Til | Rejim / Jins | Hurmatli Murojaat | Neyron Ovoz (Edge-TTS) |
| :--- | :--- | :--- | :--- |
| 🇺🇿 O'zbek | Ayol (Onaxon) | *«Nigina ona», «Onajon»* | `uz-UZ-MadinaNeural` |
| 🇺🇿 O'zbek | Erkak (Otaxon) | *«Jasur ota», «Otaxonto'ram»* | `uz-UZ-SardorNeural` |
| 🇷🇺 Rus | Ayol (Бабушка) | *«Уважаемая Каролина»* | `ru-RU-SvetlanaNeural` |
| 🇷🇺 Rus | Erkak (Дедушка) | *«Уважаемый Александр»* | `ru-RU-DmitryNeural` |

> 🛡️ **Odob qoidalari:** Hech qanday erish, noo'rin so'zlar ("jonim", "asalim") ishlatilmaydi. Faqat samimiy va yuksak ehtiromli muloqot!

---

## 🛠️ Texnologiyalar Steki (Tech Stack)

- **Til:** Python 3.12+
- **Bot Freymvorki:** [Aiogram 3.x](https://docs.aiogram.dev/) (Asinxron Telegram Bot API)
- **Sun'iy Intellekt:** Google Gemini API (`gemini-3.6-flash` — Multimodal Audio, Vision, Text)
- **Ovoz Generatsiyasi (TTS):** Microsoft Edge TTS (Yuqori sifatli tabiiy neyron ovozlar)
- **Vazifalar Rejalashtiruvchisi:** APScheduler (Dori eslatmalari uchun kronomatchi)
- **Ma'lumotlar Bazasi:** PostgreSQL (Ishlab chiqarish) / SQLite3 (Lokal avtomatik fallback)

---

## 🚀 O'rnatish va Ishga Tushirish (Quickstart)

### 1. Repozitoriyni klonlash:
```bash
git clone https://github.com/salomh46-rgb/hamroh-bot.git
cd hamroh-bot
```

### 2. Virtual muhitni yaratish va faollashtirish:
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# Linux / MacOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Kerakli kutubxonalarni o'rnatish:
```bash
pip install -r requirements.txt
```

### 4. Muhit o'zgaruvchilarini sozlash:
`.env.example` faylidan nusxa olib, `.env` faylini yarating va tokenlarni kiriting:
```bash
cp .env.example .env
```
`.env` fayli namunasi:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.6-flash
ADMIN_ID=your_telegram_id
```

### 5. Botni ishga tushirish:
```bash
python bot.py
```

---

## 📂 Loyiha Tuzilishi (Project Structure)

```text
hamroh_bot/
├── bot.py                  # Botni ishga tushiruvchi asosiy fayl
├── config.py               # Muhit konfiguratsiyasi va parametrlar
├── database.py             # SQLite / PostgreSQL drayveri va jadvallar
├── gemini_service.py       # Gemini AI (NLP, Vision, Multimodal Audio)
├── tts_service.py          # Edge-TTS neyron ovoz servisi
├── scheduler_service.py    # Dori eslatmalari avtomatizatsiyasi
├── keyboards.py            # Doimiy (persistent) klaviaturalar va tugmalar
├── handlers/               # Xabarlar va voqealarni boshqaruvchi modullar
│   ├── __init__.py         # Routerlar to'plami
│   ├── start.py            # Onboarding (Til, Rejim, Ism tahlili)
│   ├── reminders.py        # Dori eslatmalarini boshqarish
│   ├── sos.py              # 103 Tez yordam va shifokor bilan aloqa
│   ├── memory.py           # Xotirani mustahkamlash mashqlari
│   ├── music.py            # 70-80-90-yillar retro taronalari
│   ├── drawing.py          # AI Vision orqali rasm tahlili
│   ├── reading.py          # Bolalar kitobxonlik daqiqasi
│   ├── animal_quiz.py      # Hayvonlar ovozi testi va faktlar
│   ├── kvest.py            # Sehrli interaktiv kvest-ertaklar
│   ├── ertak.py            # Yangi ertaklar to'qish va audio ijro
│   ├── quiz.py             # Mantiqiy topishmoqlar va ball tizimi
│   ├── voice.py            # Ovozli xabarlarni tushunish va javob berish
│   ├── chat.py             # Oddiy matnli suhbat
│   └── admin.py            # Admin boshqaruv paneli
├── requirements.txt        # Kerakli Python paketlari
├── .gitignore              # Git e'tiborsiz qoldiradigan fayllar
└── README.md               # To'liq texnik va foydalanuvchi qo'llanmasi
```

---

## 👨‍💻 Muallif va Ruxsatnoma (Author & License)

- **Muallif:** [Javohirbek Asqarov (Jasper)](https://t.me/Jasper_Asqarov)
- **Bot:** [@hamrroh_bot](https://t.me/hamrroh_bot)
- Ushbu loyiha **MIT License** litsenziyasi ostida ochiq taqdim etiladi.
