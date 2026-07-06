import telebot
import json
import os

TOKEN = '8840402398:AAGnYTSXg2CU_Mm-6pbfg6q0obZe_b2FwAY'
ADMIN_ID = 8509165435  # آیدی عددی تلگرام شما
CARD_NUMBER = "۶۰۳۷-۹۹۸۱-۲۵۹۶-۳۸۰۰"
CARD_NAME = "محمدطاها شریفی"

bot = telebot.TeleBot(TOKEN)
DATA_FILE = "users_state.json"

def get_data():
    if not os.path.exists(DATA_FILE): return {}
    with open(DATA_FILE, "r") as f: return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f)

@bot.message_handler(commands=['start'])
def start_cmd(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton("ثبت سفارش جدید 🛒"))
    bot.send_message(message.chat.id, "سلام به ربات فروشگاه کالاف دیوتی خوش آمدید!", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == "ثبت سفارش جدید 🛒")
def order_step(message):
    text = f"لطفاً مبلغ سفارش را به شماره کارت زیر واریز کنید و تصویر فیش واریزی را ارسال کنید:\n\n💳 شماره کارت:\n`{CARD_NUMBER}`\n\n👤 به نام:\n*{CARD_NAME}*\n\n⚠️ لطفاً پس از واریز، عکس فیش را بفرستید."
    bot.send_message(message.chat.id, text, parse_mode="Markdown")
    data = get_data()
    data[str(message.chat.id)] = {"state": "AWAITING_RECEIPT"}
    save_data(data)

@bot.message_handler(content_types=['photo'])
def handle_receipt(message):
    user_id = str(message.chat.id)
    data = get_data()
    if user_id in data and data[user_id]["state"] == "AWAITING_RECEIPT":
        file_id = message.photo[-1].file_id
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("✅ تایید فیش", callback_data=f"verify_{user_id}"), telebot.types.InlineKeyboardButton("❌ رد فیش", callback_data=f"reject_{user_id}"))
        bot.send_photo(ADMIN_ID, file_id, caption=f"فیش جدید از کاربر: {user_id}\nنام: {message.from_user.first_name}", reply_markup=markup)
        bot.send_message(user_id, "فیش شما برای بررسی به ادمین ارسال شد. لطفاً منتظر بمانید...")
        data[user_id]["state"] = "CHECKING_RECEIPT"
        save_data(data)

@bot.callback_query_handler(func=lambda call: not call.data.startswith("time"))
def callback_handler(call):
    data = get_data()
    action, target_user = call.data.split("_")
    if action == "verify":
        bot.edit_message_caption("✅ این فیش تایید شد.", chat_id=ADMIN_ID, message_id=call.message.message_id)
        bot.send_message(target_user, "پرداخت با موفقیت تایید شد! 🎉\nلطفاً جیمیل و رمز عبور بازی کالاف دیوتی خود را در قالب یک پیام ارسال کنید.")
        data[target_user] = {"state": "AWAITING_CREDENTIALS"}
        save_data(data)
    elif action == "reject":
        bot.edit_message_caption("❌ این فیش رد شد.", chat_id=ADMIN_ID, message_id=call.message.message_id)
        bot.send_message(target_user, "متاسفانه فیش واریزی شما تایید نشد. لطفا دوباره بررسی و ارسال کنید.")
        data[target_user] = {"state": "AWAITING_RECEIPT"}
        save_data(data)
    elif action == "done":
        bot.edit_message_text(f"سفارش کاربر {target_user} تحویل داده شد.", chat_id=ADMIN_ID, message_id=call.message.message_id)
        bot.send_message(target_user, "🎁 سفارش شما با موفقیت انجام شد! می‌توانید وارد اکانت خود شوید.")
        if target_user in data: del data[target_user]
        save_data(data)

@bot.message_handler(func=lambda msg: True)
def handle_account_details(message):
    user_id = str(message.chat.id)
    data = get_data()
    if user_id in data and data[user_id]["state"] == "AWAITING_CREDENTIALS":
        account_info = message.text
        bot.send_message(ADMIN_ID, f"مشخصات اکانت کاربر {user_id}:\n\n`{account_info}`", parse_mode="Markdown")
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("⏱ ۱ ساعت", callback_data=f"time1_{user_id}"), telebot.types.InlineKeyboardButton("⏱ ۳ ساعت", callback_data=f"time3_{user_id}"), telebot.types.InlineKeyboardButton("⏱ ۲۴ ساعت", callback_data=f"time24_{user_id}"))
        bot.send_message(ADMIN_ID, "زمان انجام سفارش را انتخاب کنید:", reply_markup=markup)
        bot.send_message(user_id, "اطلاعات اکانت شما دریافت شد. در حال هماهنگی برای انجام سفارش...")
        data[user_id]["state"] = "SETTING_TIME"
        save_data(data)

@bot.callback_query_handler(func=lambda call: call.data.startswith("time"))
def time_handler(call):
    data = get_data()
    time_info, target_user = call.data.split("_")
    hours = time_info.replace("time", "")
    text_time = f"{hours} ساعت آینده" if hours != "24" else "فردا"
    bot.send_message(target_user, f"سفارش شما در حال انجام شدن است و تا {text_time} تحویل داده می‌شود.")
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("✅ سفارش انجام شد", callback_data=f"done_{target_user}"))
    bot.edit_message_text(f"زمان {text_time} برای کاربر {target_user} ثبت شد. پس از اتمام کار دکمه زیر را بزنید:", chat_id=ADMIN_ID, message_id=call.message.message_id, reply_markup=markup)

if __name__ == '__main__':
    print("Bot is running...")
    bot.infinity_polling()
