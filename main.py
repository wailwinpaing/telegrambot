
import os
import telebot
from openai import OpenAI
import time
from dotenv import load_dotenv

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
    base_url="https://api.deepseek.com/v1"
)

# --- TrueMoney Data & AI Rules (full SYSTEM_INSTRUCTION - keep as before) ---
SYSTEM_INSTRUCTION = """
သင်သည် ထိုင်းနိုင်ငံရှိ မြန်မာနိုင်ငံသားများကို TrueMoney Wallet အသုံးပြုပုံနှင့် ပတ်သက်၍ ကူညီပေးရမည့် အမျိုးသမီး အထောက်အပံ့ပေးသူ (Female Assistant) ဖြစ်သည်။
အသုံးပြုသူများကို အောက်ပါအတိုင်း တိကျသော အဆင့်ဆင့်လမ်းညွှန်ချက်များဖြင့် မြန်မာဘာသာဖြင့် ယဉ်ကျေးပျူငှာစွာ ဖြေကြားပေးပါ -

အရေးကြီးသော လမ်းညွှန်ချက်များ -
၁။ ကိုယ့်ကိုယ်ကိုယ် ရည်ညွှန်းလျှင် "ကျွန်မ" ဟု အမြဲသုံးပါ။
၂။ စာကြောင်းတိုင်း၏ အဆုံးတွင် "ရှင့်" သို့မဟုတ် "ပါရှင်" ဟု ထည့်ပြောပေးပါ။ "ခင်ဗျာ" လုံးဝမသုံးရပါ။
၃။ စာကြောင်းအဆုံးတွင် ပုဒ်ဖြတ်ပုဒ်ရပ် (။) လုံးဝမသုံးရပါ။
၄။ '🤍' emoji ကို reply တစ်ခုလုံး၏ အဆုံးသတ် "ရှင့်" သို့မဟုတ် "ပါရှင်" ၏ နောက်တွင်သာ တစ်ကြိမ်တည်း ထည့်ပေးပါ ရှင့်။

... (ကျန်တဲ့ သင့် SYSTEM_INSTRUCTION အားလုံးကို ဒီနေရာမှာ ထည့်ပါ) ...

မှတ်ချက် - အခက်အခဲရှိပါက TrueMoney Call Center 1240 ကို ခေါ်ဆိုပြီး နံပါတ် 4 ကို နှိပ်၍ မြန်မာစကားပြောဝန်ထမ်း Holiday မရှိဘဲ ဆက်သွယ်နိုင်ကြောင်း အမြဲထည့်ပြောပေးပါ ရှင့်။
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

# 🤖 Message handler
@bot.message_handler(func=lambda message: True)
def reply_to_user(message):
    try:
        response_text = get_deepseek_response(message.text)
        bot.reply_to(message, response_text)
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

# --- Run the bot ---
if __name__ == "__main__":
    print("Bot is starting with DeepSeek AI (Polling mode)...")
    bot.remove_webhook()
    time.sleep(1)
    bot.infinity_polling()
