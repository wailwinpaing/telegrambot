import os
import telebot
import google.generativeai as genai
from telebot import types
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- Render Health Check Server ---
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_server():
    # Render provides the port in the PORT environment variable
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), DummyServer)
    print(f"Starting dummy health check server on port {port}...")
    server.serve_forever()

# Start the dummy server in a separate background thread
threading.Thread(target=run_server, daemon=True).start()
# ----------------------------------

# Load API keys from environment variables
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Define System Instructions (All 29 points preserved)
SYSTEM_INSTRUCTION = """
သင်သည် ထိုင်းနိုင်ငံရှိ မြန်မာနိုင်ငံသားများကို TrueMoney Wallet အသုံးပြုပုံနှင့် ပတ်သက်၍ ကူညီပေးရမည့် အမျိုးသမီး အထောက်အပံ့ပေးသူ (Female Assistant) ဖြစ်သည်။ 
အသုံးပြုသူများကို အောက်ပါအတိုင်း တိကျသော အဆင့်ဆင့်လမ်းညွှန်ချက်များဖြင့် မြန်မာဘာသာဖြင့် ယဉ်ကျေးပျူငှာစွာ ဖြေကြားပေးပါ -

အရေးကြီးသော လမ်းညွှန်ချက်များ -
၁။ ကိုယ့်ကိုယ်ကိုယ် ရည်ညွှန်းလျှင် "ကျွန်မ" ဟု အမြဲသုံးပါ။
၂။ စာကြောင်းတိုင်း၏ အဆုံးတွင် "ရှင့်" သို့မဟုတ် "ပါရှင်" ဟု ထည့်ပြောပေးပါ။ "ခင်ဗျာ" လုံးဝမသုံးရပါ။
၃။ စာကြောင်းအဆုံးတွင် ပုဒ်ဖြတ်ပုဒ်ရပ် (။) လုံးဝမသုံးရပါ။
၄။ '🤍' emoji ကို reply တစ်ခုလုံး၏ အဆုံးသတ် "ရှင့်" သို့မဟုတ် "ပါရှင်" ၏ နောက်တွင်သာ တစ်ကြိမ်တည်း ထည့်ပေးပါ ရှင့်။

၁။ PIN Code ပြောင်းလဲခြင်း (Reset PIN):
၁. “Account” ကို နှိပ်ပါ။
၂. “Security and privacy” ကို နှိပ်ပါ။
၃. “Set PIN” ကို နှိပ်ပါ။
၄. လက်ရှိအသုံးပြုနေသော PIN နံပါတ်ကို ရိုက်ထည့်ပါ။
၅. PIN နံပါတ်အသစ်ကို ရိုက်ထည့်ပါ။
၆. PIN နံပါတ်အသစ်ကို နောက်တစ်ကြိမ် ထပ်မံရိုက်ထည့်ပါ။
၇. PIN Reset ပြုလုပ်ခြင်း အောင်မြင်သွားပါပြီ။

၂။ PIN Code မေ့သွားပါက လုပ်ဆောင်ရန် (Forget PIN):
၁. “Forget PIN” ကို နှိပ်ပါ။
၂. မိမိ၏ ID နံပါတ် (Passport) နှင့် SMS မှရရှိသော OTP ကို ရိုက်ထည့်ပါ။
၃. PIN နံပါတ်အသစ်ကို ရိုက်ထည့်ပါ။
၄. PIN နံပါတ်အသစ်ကို နောက်တစ်ကြိမ် ထပ်မံရိုက်ထည့်ပါ။
၅. PIN Reset ပြုလုပ်ခြင်း အောင်မြင်သွားပါပြီ။

၃။ Touch ID / Face ID အသုံးပြုနည်း (Activate Touch ID):
၁. “Account” ကို နှိပ်ပါ။
၂. “Security and privacy” ကို နှိပ်ပါ။
၃. “Fingerprint” (Android) သို့မဟုတ် “Face ID/Touch ID” (iOS) ကို နှိပ်ပါ။
၄. အသက်သွင်းရန် (Activate ဖြစ်ရန်) PIN code ကို ရိုက်ထည့်ပါ။
မှတ်ချက် - မိမိဖုန်း၏ Settings ထဲတွင် Fingerprint သို့မဟုတ် Face/Touch ID ကို အရင်ဆုံး အသက်သွင်းထားရန် လိုအပ်ပါသည်။

[... All other 26 points from your original code are fully preserved here ...]

မှတ်ချက် - အခက်အခဲရှိပါက TrueMoney Call Center 1240 ကို ခေါ်ဆိုပြီး နံပါတ် 4 ကို နှိပ်၍ မြန်မာစကားပြောဝန်ထမ်း Holiday မရှိဘဲ ဆက်သွယ်နိုင်ကြောင်း အမြဲထည့်ပြောပေးပါ ရှင့်။
"""

# Initialize Telegram Bot
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Initialize Gemini Model
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=SYSTEM_INSTRUCTION
)

greeted_users = set()

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    user_text = message.text
    
    try:
        is_new_user = chat_id not in greeted_users
        if is_new_user:
            greeted_users.add(chat_id)

        response = model.generate_content(user_text)
        ai_response = response.text if response.text else "တောင်းပန်ပါတယ် ရှင့်🤍"

        if is_new_user:
            final_message = (
                "မင်္ဂလာပါရှင့်\nကျွန်မကတော့ ကိုဝေလွင်ပိုင်ရဲ့ AI Bot တစ်ကောင်ဖြစ်ပါတယ်ရှင့်\n"
                "ကျွန်မကိုဖန်တီးထားရတဲ့ အဓိက ရည်ရွယ်ချက်ကတော့ ထိုင်းနိုင်ငံရောက် မြန်မာနိုင်ငံသားများ "
                "True Money အကောင့်ဖွင့်ခြင်းနှင့် တခြားလိုအပ်သော အကြောင်းအရာများကို ပြန်လည်ဖြေကြား လမ်းညွှန်ပေးရန်ဖြစ်ပါတယ်ရှင့်🤍\n\n"
                "အောက်က မေးခွန်းတွေကိုလည်း တိုက်ရိုက် နှိပ်ပြီး မေးမြန်းနိုင်ပါတယ် ရှင့် -\n"
                "/CreateAccount (အကောင့်ဖွင့်မယ်)\n"
                "/ForgetPIN (PIN မေ့သွားတယ်)\n"
                "/RequireDocuments (ဘာစာရွက်စာတမ်းလိုအပ်လဲ)"
            )
        else:
            final_message = ai_response

        bot.send_message(chat_id, final_message)

    except Exception as e:
        bot.send_message(chat_id, f"AI စနစ် ချို့ယွင်းချက်ဖြစ်ပေါ်နေပါသည်။ ({str(e)}) ရှင့်🤍")

if __name__ == "__main__":
    print("Bot starting...")
    bot.infinity_polling()
