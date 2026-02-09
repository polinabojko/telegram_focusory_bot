import telebot
from telebot.types import ReplyKeyboardMarkup
import os, json, threading
from datetime import date, timedelta
from collections import Counter

TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

DATA_FILE = "data.json"

# ================= DATA =================

data = {
    "lang": {},
    "state": {},
    "mood": {},
    "pomodoro": {},
    "tasks": {},
    "notes": {},
    "draft": {}
}

def load():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data.update(json.load(f))

def save():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

load()

# ================= HELPERS =================

def cid(m): return str(m.chat.id)
def today(): return date.today().isoformat()
def week(): return (date.today(), date.today() + timedelta(days=6))
def lang(c): return data["lang"].get(c, "en")

def set_state(c, s):
    data["state"][c] = s
    save()

def get_state(c):
    return data["state"].get(c)

def kb(*rows):
    k = ReplyKeyboardMarkup(resize_keyboard=True)
    for r in rows:
        k.add(*r)
    return k

# ================= TEXT =================

T = {
    "ru": {
        "menu": "🧭 Главное меню",
        "focus": "⏳ Фокус",
        "mood": "🙂 Настроение",
        "plan": "📋 Планирование",
        "notes": "📝 Заметки",
        "stats": "📊 Статистика",
        "back": "↩️ В меню",

        "mood_q": "Как ты сегодня?",
        "moods": ["😁", "🙂", "😐", "😕", "😞"],
        "mood_saved": "Настроение сохранено.",

        "focus_q": "Выбери длительность фокуса:",
        "focus_start": "⏳ Фокус начался — {m} минут",
        "focus_done": "✅ Фокус завершён",
        "break": "☕ Перерыв — 5 минут",
        "skip": "⏭ Пропустить перерыв",
        "new_focus": "🔄 Новый фокус",
        "exit": "🚪 Выйти",

        "add_task": "➕ Добавить задачу",
        "today": "Сегодня",
        "week": "Неделя",
        "month": "Месяц",
        "nodate": "Без даты",
        "view": "📂 Посмотреть",
        "done": "✔️ Выполнено",

        "task_text": "Введите текст задачи:",
        "task_saved": "Задача добавлена.",

        "add_note": "➕ Новая заметка",
        "note_title": "Заголовок:",
        "note_text": "Текст заметки:",
        "note_saved": "Заметка сохранена.",

        "stats_focus": "⏳ Фокус:",
        "stats_mood": "🙂 Настроение:"
    },
    "en": {
        "menu": "🧭 Main menu",
        "focus": "⏳ Focus",
        "mood": "🙂 Mood",
        "plan": "📋 Planning",
        "notes": "📝 Notes",
        "stats": "📊 Statistics",
        "back": "↩️ Back",

        "mood_q": "How do you feel?",
        "moods": ["😁", "🙂", "😐", "😕", "😞"],
        "mood_saved": "Mood saved.",

        "focus_q": "Choose focus duration:",
        "focus_start": "⏳ Focus started — {m} minutes",
        "focus_done": "✅ Focus completed",
        "break": "☕ Break — 5 minutes",
        "skip": "⏭ Skip break",
        "new_focus": "🔄 New focus",
        "exit": "🚪 Exit",

        "add_task": "➕ Add task",
        "today": "Today",
        "week": "Week",
        "month": "Month",
        "nodate": "No date",
        "view": "📂 View",
        "done": "✔️ Done",

        "task_text": "Enter task:",
        "task_saved": "Task added.",

        "add_note": "➕ New note",
        "note_title": "Title:",
        "note_text": "Note text:",
        "note_saved": "Note saved.",

        "stats_focus": "⏳ Focus:",
        "stats_mood": "🙂 Mood:"
    }
}

# ================= MAIN MENU =================

def main_menu(m):
    l = lang(cid(m))
    bot.send_message(
        m.chat.id,
        T[l]["menu"],
        reply_markup=kb(
            [T[l]["focus"], T[l]["mood"]],
            [T[l]["plan"], T[l]["notes"]],
            [T[l]["stats"]]
        )
    )

# ================= START =================

@bot.message_handler(commands=["start"])
def start(m):
    bot.send_message(
        m.chat.id,
        "Choose language / Выберите язык",
        reply_markup=kb(["🇷🇺 Русский", "🇬🇧 English"])
    )

@bot.message_handler(func=lambda m: m.text in ["🇷🇺 Русский", "🇬🇧 English"])
def set_lang(m):
    data["lang"][cid(m)] = "ru" if "Рус" in m.text else "en"
    save()
    main_menu(m)

# ================= MOOD =================

@bot.message_handler(func=lambda m: m.text in ["🙂 Настроение", "🙂 Mood"])
def mood(m):
    l = lang(cid(m))
    set_state(cid(m), "mood")
    bot.send_message(m.chat.id, T[l]["mood_q"], reply_markup=kb(T[l]["moods"], [T[l]["back"]]))

@bot.message_handler(func=lambda m: get_state(cid(m)) == "mood")
def save_mood(m):
    l = lang(cid(m))
    if m.text in T[l]["moods"]:
        data["mood"][cid(m)] = {"date": today(), "value": m.text}
        set_state(cid(m), None)
        save()
        bot.send_message(m.chat.id, T[l]["mood_saved"])
        main_menu(m)

# ================= POMODORO =================

timers = {}

@bot.message_handler(func=lambda m: m.text in ["⏳ Фокус", "⏳ Focus"])
def pomodoro_menu(m):
    l = lang(cid(m))
    bot.send_message(m.chat.id, T[l]["focus_q"], reply_markup=kb(["15", "25", "50"], [T[l]["back"]]))

@bot.message_handler(func=lambda m: m.text in ["15", "25", "50"])
def start_focus(m):
    c = cid(m)
    l = lang(c)
    minutes = int(m.text)
    bot.send_message(m.chat.id, T[l]["focus_start"].format(m=minutes))
    timers[c] = threading.Timer(minutes*60, finish_focus, args=[c])
    timers[c].start()

def finish_focus(c):
    l = lang(c)
    data["pomodoro"].setdefault(c, []).append(today())
    save()
    bot.send_message(int(c), T[l]["focus_done"] + "\n" + T[l]["break"],
                     reply_markup=kb([T[l]["skip"], T[l]["new_focus"]], [T[l]["exit"]]))
    timers[c] = threading.Timer(300, end_break, args=[c])
    timers[c].start()

def end_break(c):
    l = lang(c)
    bot.send_message(int(c), T[l]["focus_q"], reply_markup=kb(["15", "25", "50"], [T[l]["exit"]]))

@bot.message_handler(func=lambda m: m.text in ["⏭ Пропустить перерыв", "⏭ Skip break"])
def skip_break(m):
    c = cid(m)
    if c in timers:
        timers[c].cancel()
    end_break(c)

@bot.message_handler(func=lambda m: m.text in ["🚪 Выйти", "🚪 Exit"])
def exit_pomo(m):
    c = cid(m)
    if c in timers:
        timers[c].cancel()
    main_menu(m)

# ================= PLANNING =================

@bot.message_handler(func=lambda m: m.text in ["📋 Планирование", "📋 Planning"])
def plan(m):
    l = lang(cid(m))
    set_state(cid(m), "plan")
    bot.send_message(m.chat.id, "📋", reply_markup=kb(
        [T[l]["add_task"], T[l]["view"]],
        [T[l]["back"]]
    ))

@bot.message_handler(func=lambda m: m.text in ["➕ Добавить задачу", "➕ Add task"])
def task_date(m):
    l = lang(cid(m))
    set_state(cid(m), "task_date")
    bot.send_message(m.chat.id, "📅", reply_markup=kb(
        [T[l]["today"], T[l]["week"]],
        [T[l]["month"], T[l]["nodate"]],
        [T[l]["back"]]
    ))
@bot.message_handler(func=lambda m: m.text in ["📂 Посмотреть", "📂 View"])
def view_tasks_menu(m):
    l = lang(cid(m))
    set_state(cid(m), "view_tasks")
    bot.send_message(
        m.chat.id,
        "📅",
        reply_markup=kb(
            [T[l]["today"], T[l]["week"]],
            [T[l]["month"], T[l]["nodate"]],
            [T[l]["back"]]
        )
    )
@bot.message_handler(func=lambda m: get_state(cid(m)) == "view_tasks")
def show_tasks(m):
    c = cid(m)
    l = lang(c)
    tasks = data["tasks"].get(c, [])
    today_date = date.today()

    filtered = []

    for t in tasks:
        d = t["date"]
        if m.text == T[l]["today"] and d == today():
            filtered.append(t)
        elif m.text == T[l]["week"] and d == "week":
            filtered.append(t)
        elif m.text == T[l]["month"] and d == "month":
            filtered.append(t)
        elif m.text == T[l]["nodate"] and d is None:
            filtered.append(t)

    if not filtered:
        bot.send_message(m.chat.id, "Задач нет." if l=="ru" else "No tasks.")
        return

    text = "📋 Задачи:\n\n" if l=="ru" else "📋 Tasks:\n\n"
    for i, t in enumerate(filtered, 1):
        status = "✔️" if t["done"] else "◻️"
        text += f"{i}. {status} {t['text']}\n"

    bot.send_message(m.chat.id, text)

@bot.message_handler(func=lambda m: get_state(cid(m)) == "task_date")
def choose_date(m):
    c = cid(m)
    l = lang(c)
    if m.text == T[l]["today"]:
        d = today()
    elif m.text == T[l]["week"]:
        d = "week"
    elif m.text == T[l]["month"]:
        d = "month"
    else:
        d = None
    data["draft"][c] = {"date": d}
    set_state(c, "task_text")
    bot.send_message(m.chat.id, T[l]["task_text"])

@bot.message_handler(func=lambda m: get_state(cid(m)) == "task_text")
def save_task(m):
    c = cid(m)
    data["tasks"].setdefault(c, []).append({
        "text": m.text,
        "date": data["draft"][c]["date"],
        "done": False
    })
    set_state(c, None)
    save()
    bot.send_message(m.chat.id, T[lang(c)]["task_saved"])
    main_menu(m)

# ================= NOTES =================

@bot.message_handler(func=lambda m: m.text in ["📝 Заметки", "📝 Notes"])
def notes(m):
    l = lang(cid(m))
    set_state(cid(m), "notes")
    bot.send_message(
        m.chat.id,
        "📝",
        reply_markup=kb(
            [T[l]["add_note"], "📂 Просмотреть заметки" if l=="ru" else "📂 View notes"],
            [T[l]["back"]]
        )
    )
@bot.message_handler(func=lambda m: m.text in ["📂 Просмотреть заметки", "📂 View notes"])
def view_notes(m):
    c = cid(m)
    l = lang(c)
    notes = data["notes"].get(c, [])

    if not notes:
        bot.send_message(m.chat.id, "Заметок пока нет." if l=="ru" else "No notes yet.")
        return

    text = "🗂 Последние заметки:\n\n" if l=="ru" else "🗂 Recent notes:\n\n"

    for n in notes[-5:][::-1]:
        text += f"• {n['title']}\n"

    bot.send_message(m.chat.id, text)

@bot.message_handler(func=lambda m: m.text in ["➕ Новая заметка", "➕ New note"])
def note_title(m):
    set_state(cid(m), "note_title")
    bot.send_message(m.chat.id, T[lang(cid(m))]["note_title"])

@bot.message_handler(func=lambda m: get_state(cid(m)) == "note_title")
def note_text(m):
    data["draft"][cid(m)] = {"title": m.text}
    set_state(cid(m), "note_text")
    bot.send_message(m.chat.id, T[lang(cid(m))]["note_text"])

@bot.message_handler(func=lambda m: get_state(cid(m)) == "note_text")
def save_note(m):
    c = cid(m)
    data["notes"].setdefault(c, []).append({
        "title": data["draft"][c]["title"],
        "text": m.text
    })
    set_state(c, None)
    save()
    bot.send_message(m.chat.id, T[lang(c)]["note_saved"])
    main_menu(m)

# ================= STATS =================

@bot.message_handler(func=lambda m: m.text in ["📊 Статистика", "📊 Statistics"])
def stats(m):
    c = cid(m)
    l = lang(c)

    mood_stats = Counter([v["value"] for v in data["mood"].values() if c in data["mood"]])
    pomo = len(data["pomodoro"].get(c, []))

    text = f"{T[l]['stats_focus']} {pomo}\n{T[l]['stats_mood']}\n"
    for k, v in mood_stats.items():
        text += f"{k}: {v}\n"

    bot.send_message(m.chat.id, text or "—")
    main_menu(m)

# ================= BACK =================

@bot.message_handler(func=lambda m: m.text in ["↩️ В меню", "↩️ Back"])
def back(m):
    set_state(cid(m), None)
    main_menu(m)

# ================= RUN =================

print("Bot running")
bot.infinity_polling()
