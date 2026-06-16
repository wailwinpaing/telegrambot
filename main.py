import os
import telebot
import sqlite3
import time
import requests
import io
import threading
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from PIL import Image

# Load environment variables from .env file
load_dotenv()

# --- Tokens (Retrieved from Environment Variables) ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Check if tokens are provided
if not TOKEN:
    print("Error: TELEGRAM_TOKEN not found in .env file")
    exit(1)
if not DEEPSEEK_API_KEY:
    print("Error: DEEPSEEK_API_KEY not found in .env file")
    exit(1)

# Library initialization
bot = telebot.TeleBot(TOKEN)
# DeepSeek client (OpenAI-compatible)
deepseek_client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# ------------------ DATABASE SETUP ------------------
def setup_database():
    conn = sqlite3.connect('telegram_bot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        reg_date TEXT,
        last_seen TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        visit_date TEXT
    )''')
    conn.commit()
    conn.close()

def register_user(user_id, username, first_name, last_name):
    conn = sqlite3.connect('telegram_bot.db')
    c = conn.cursor()
    c.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
    if c.fetchone() is None:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute('INSERT INTO users (user_id, username, first_name, last_name, reg_date, last_seen) VALUES (?,?,?,?,?,?)',
                  (user_id, username, first_name, last_name, now, now))
        conn.commit()
    conn.close()

def update_last_seen(user_id):
    conn = sqlite3.connect('telegram_bot.db')
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('UPDATE users SET last_seen = ? WHERE user_id = ?', (now, user_id))
    c.execute('INSERT INTO visits (user_id, visit_date) VALUES (?, ?)', (user_id, now))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('telegram_bot.db')
    c = conn.cursor()
    c.execute('SELECT user_id FROM users')
    users = c.fetchall()
    conn.close()
    return [u[0] for u in users]

# --- TrueMoney Data & AI Rules ---
SYSTEM_INSTRUCTION = """
သင်သည် ထိုင်းနိုင်ငံရှိ မြန်မာနိုင်ငံသားများကို TrueMoney Wallet အသုံးပြုပုံနှင့် ပတ်သက်၍ ကူညီပေးရမည့် အမျိုးသမီး အထောက်အပံ့ပေးသူ (Female Assistant) ဖြစ်သည်။
အသုံးပြုသူများကို အောက်ပါအတိုင်း တိကျသော အဆင့်ဆင့်လမ်းညွှန်ချက်များဖြင့် မြန်မာဘာသာဖြင့် ယဉ်ကျေးပျူငှာစွာ ဖြေကြားပေးပါ -

အရေးကြီးသော လမ်းညွှန်ချက်များ -
၁။ ကိုယ့်ကိုယ်ကိုယ် ရည်ညွှန်းလျှင် "ကျွန်မ" ဟု အမြဲသုံးပါ။
၂။ စာကြောင်းတိုင်း၏ အဆုံးတွင် "ရှင့်" သို့မဟုတ် "ပါရှင်" ဟု ထည့်ပြောပေးပါ။ "ခင်ဗျာ" လုံးဝမသုံးရပါ။
၃။ စာကြောင်းအဆုံးတွင် ပုဒ်ဖြတ်ပုဒ်ရပ် (။) လုံးဝမသုံးရပါ။
၄။ '🤍' emoji ကို reply တစ်ခုလုံး၏ အဆုံးသတ် "ရှင့်" သို့မဟုတ် "ပါရှင်" ၏ နောက်တွင်သာ တစ်ကြိမ်တည်း ထည့်ပေးပါ ရှင့်။
၅။ အသုံးပြုသူကို အမြဲတမ်း ယဉ်ကျေးပျူငှာစွာနှင့် စိတ်ရှည်စွာ ဖြေကြားပေးပါ။

(မှတ်ချက် - TrueMoney နှင့်ပတ်သက်သော အချက်အလက် ၂၉ ချက်ကို အသုံးပြု၍ ဖြေကြားပေးပါ)
"""

# --- Helper function to call DeepSeek API ---
def get_deepseek_response(user_message):
    try:
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=2048
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error from DeepSeek API: {str(e)}"

# --- NEW: Function to analyze image using DeepSeek Vision API ---
# Note: Ensure your DeepSeek API provider supports 'deepseek-vl' or 'deepseek-chat' with vision.
def analyze_image_with_deepseek(image_url, user_question):
    try:
        response = deepseek_client.chat.completions.create(
            model="deepseek-vl", # Update model if necessary
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_url}},
                        {"type": "text", "text": f"{user_question} (မြန်မာလို ဖြေပေးပါ)"}
                    ]
                }
            ],
            temperature=0.7,
            max_tokens=2048
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"ပုံကိုဖတ်ရာတွင် အမှားရှိနေပါတယ်: {str(e)}"

def get_public_image_url(file_id):
    try:
        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
        return file_url
    except Exception as e:
        return None

# ------------------ BOT HANDLERS ------------------

@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id
    register_user(message.from_user.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)
    update_last_seen(message.from_user.id)

    welcome_msg = "မင်္ဂလာပါရှင့် ဘာများကူညီပေးရမလဲရှင့် ကျွန်မကတော့ ကိုပိုင်ရဲ့ AI Assistant တစ်ယောက်ဖြစ်ပါတယ် သိလိုရာ အားလုံးကို မေးမြန်းနိုင်ပါတယ်ရှင့်🤍"
    bot.reply_to(message, welcome_msg)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        register_user(message.from_user.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)
        update_last_seen(message.from_user.id)

        photo = message.photo[-1]
        file_id = photo.file_id
        user_question = message.caption if message.caption else "ဒီပုံထဲမှာ ဘာတွေပါလဲ"

        processing_msg = bot.reply_to(message, "📸 ပုံကို ခွဲခြမ်းစိတ်ဖြာနေပါတယ် ခဏစောင့်ပါရှင့်...")
        image_url = get_public_image_url(file_id)

        if image_url:
            analysis_result = analyze_image_with_deepseek(image_url, user_question)
            bot.send_message(
                message.chat.id,
                f"🖼️ **ပုံအကြောင်းအရာ**\n\n{analysis_result}\n\n🤍",
                reply_to_message_id=message.message_id,
                parse_mode='Markdown'
            )
            bot.delete_message(message.chat.id, processing_msg.message_id)
        else:
            bot.edit_message_text("❌ ပုံကို ဖတ်လို့မရပါဘူး", message.chat.id, processing_msg.message_id)
    except Exception as e:
        bot.reply_to(message, f"အမှား: {str(e)}")

@bot.message_handler(func=lambda message: True)
def reply_to_user(message):
    chat_id = message.chat.id
    try:
        register_user(message.from_user.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)
        update_last_seen(message.from_user.id)

        response_text = get_deepseek_response(message.text)
        bot.reply_to(message, response_text)
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

# ------------------ SCHEDULER ------------------
def send_daily_greeting_to_all():
    users = get_all_users()
    today = datetime.now().strftime("%Y/%m/%d")
    msg = f"🌞 {today} မှာ သာယာသော နေ့လေး ဖြစ်ပါစေရှင့် 🤍"
    for uid in users:
        try:
            bot.send_message(uid, msg)
            print(f"Sent greeting to {uid}")
        except Exception as e:
            print(f"Failed to send to {uid}: {e}")

# --- Run the bot ---
if __name__ == "__main__":
    setup_database()

    # Scheduler Setup (နေ့စဉ် မနက် ၈ နာရီ)
    scheduler = BackgroundScheduler(timezone="Asia/Yangon")
    scheduler.add_job(send_daily_greeting_to_all, 'cron', hour=8, minute=0)
    scheduler.start()

    print("Bot is starting with DeepSeek AI (Polling mode)...")
    bot.remove_webhook()
    time.sleep(1)
    bot.infinity_polling()
