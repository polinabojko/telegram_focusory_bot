import telebot
from telebot.types import ReplyKeyboardMarkup
import os, json, threading, uuid
from datetime import date

TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

DATA_FILE = "data.json"

# ================= STORAGE =================

data = {
    "lang": {},
    "mood": {},
    "pomodoro_active": {},
    "notes": {},
    "note_draft": {}
}

def load():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data.update(json.load(f))

def save():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

load()

# ================= TEXT =================

TEXT = {
    "ru": {
        "menu": "🧭 Главное меню",
        "focus": "⏳ Фокус",
        "mood": "📊 Настроение",
        "notes": "📝 Заметки",
        "new_note": "➕ Новая заметка",
        "view_cat": "📂 По категории",
        "view_recent": "📅 Последние",
        "choose_cat": "Выберите категорию:",
        "enter_title": "Введите заголовок:",
        "enter_text": "Введите текст заметки:",
        "saved": "Заметка сохранена.",
        "no_notes": "Заметок нет.",
        "back": "🧭 В меню"
    },
    "en": {
        "menu": "🧭 Main menu",
        "focus": "⏳ Focus",
        "mood": "📊 Mood",
        "notes": "📝 Notes",
        "new_note": "➕ New note",
        "view_cat": "📂 By category",
        "view_recent": "📅 Recent",
        "choose_cat": "Choose category:",
        "enter_title": "Enter title:",
        "enter_text": "Enter note text:",
        "saved": "Note saved.",
        "no_notes": "No notes yet.",
        "back": "🧭 Back to menu"
    }
}

CATEGORIES = {
    "ru": ["Работа", "Личное", "Идеи", "Обучение", "Другое"],
    "en": ["Work", "Personal", "Ideas", "Learning", "Other"]
}

def lang(cid): return data["lang"].get(cid, "en")
def today(): return date.today().isoformat()

def kb(*rows):
    k = ReplyKeyboardMarkup(resize_keyboard=True)
    for r in rows:
        k.add(*r)
    return k

def main_kb(l):
    return kb(
        [TEXT[l]["focus"], TEXT[l]["mood"]],
        [TEXT[l]["notes"]]
    )

# ================= START =================

@bot.message_handler(commands=["start"])
def start(m):
    bot.send_message(
        m.chat.id,
        "Choose language / Выберите язык:",
        reply_markup=kb(["🇷🇺 Русский", "🇬🇧 English"])
    )

@bot.message_handler(func=lambda m: m.text in ["🇷🇺 Русский", "🇬🇧 English"])
def set_lang(m):
    cid = str(m.chat.id)
    data["lang"][cid] = "ru" if "Рус" in m.text else "en"
    save()
    bot.send_message(m.chat.id, TEXT[lang(cid)]["menu"], reply_markup=main_kb(lang(cid)))

# ================= NOTES =================

@bot.message_handler(func=lambda m: m.text in ["📝 Заметки", "📝 Notes"])
def notes_menu(m):
    l = lang(str(m.chat.id))
    bot.send_message(
        m.chat.id,
        TEXT[l]["notes"],
        reply_markup=kb(
            [TEXT[l]["new_note"]],
            [TEXT[l]["view_cat"], TEXT[l]["view_recent"]],
            [TEXT[l]["back"]]
        )
    )

@bot.message_handler(func=lambda m: m.text in ["➕ Новая заметка", "➕ New note"])
def new_note(m):
    cid = str(m.chat.id)
    l = lang(cid)
    data["note_draft"][cid] = {}
    bot.send_message(
        m.chat.id,
        TEXT[l]["choose_cat"],
        reply_markup=kb(CATEGORIES[l])
    )

@bot.message_handler(func=lambda m: m.text in sum(CATEGORIES.values(), []))
def note_category(m):
    cid = str(m.chat.id)
    data["note_draft"][cid]["category"] = m.text
    bot.send_message(m.chat.id, TEXT[lang(cid)]["enter_title"])

@bot.message_handler(func=lambda m: str(m.chat.id) in data["note_draft"] and "title" not in data["note_draft"][str(m.chat.id)])
def note_title(m):
    cid = str(m.chat.id)
    data["note_draft"][cid]["title"] = m.text
    bot.send_message(m.chat.id, TEXT[lang(cid)]["enter_text"])

@bot.message_handler(func=lambda m: str(m.chat.id) in data["note_draft"] and "text" not in data["note_draft"][str(m.chat.id)])
def note_text(m):
    cid = str(m.chat.id)
    draft = data["note_draft"].pop(cid)
    note = {
        "id": str(uuid.uuid4())[:8],
        "title": draft["title"],
        "text": m.text,
        "category": draft["category"],
        "date": today()
    }
    data.setdefault("notes", {}).setdefault(cid, []).append(note)
    save()
    bot.send_message(
        m.chat.id,
        TEXT[lang(cid)]["saved"],
        reply_markup=main_kb(lang(cid))
    )

@bot.message_handler(func=lambda m: m.text in ["📅 Последние", "📅 Recent"])
def recent_notes(m):
    cid = str(m.chat.id)
    l = lang(cid)
    notes = data.get("notes", {}).get(cid, [])[-10:]
    if not notes:
        bot.send_message(m.chat.id, TEXT[l]["no_notes"])
        return
    for n in notes:
        bot.send_message(
            m.chat.id,
            f"📄 {n['title']}\n{n['category']} · {n['date']}\n\n{n['text']}"
        )

@bot.message_handler(func=lambda m: m.text in ["📂 По категории", "📂 By category"])
def notes_by_cat(m):
    l = lang(str(m.chat.id))
    bot.send_message(
        m.chat.id,
        TEXT[l]["choose_cat"],
        reply_markup=kb(CATEGORIES[l])
    )

# ================= BACK =================

@bot.message_handler(func=lambda m: m.text in ["🧭 В меню", "🧭 Back to menu"])
def back(m):
    bot.send_message(
        m.chat.id,
        TEXT[lang(str(m.chat.id))]["menu"],
        reply_markup=main_kb(lang(str(m.chat.id)))
    )

# ================= RUN =================

print("Bot running")
bot.infinity_polling()
