import telebot
from telebot import types

# --- تنظیمات اصلی ربات شما ---
BOT_TOKEN = '8840402398:AAGnYTSXg2CU_Mm-6pbfg6q0obZe_b2FwAY'
ADMIN_ID = 8509165435  # آیدی عددی تلگرام شما که از userinfobot گرفتید

bot = telebot.TeleBot(BOT_TOKEN)

# دیتابیس موقت برای مراحل خرید
user_states = {}
orders = {}

def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🛒 ثبت سفارش سی‌پی کالاف"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_states[message.chat.id] = None
    bot.send_message(message.chat.id, "سلام! به ربات خدمات کالاف دیوتی خوش آمدید. برای شروع روی دکمه زیر کلیک کنید:", reply_markup=main_keyboard())

@bot.message_handler(func=lambda message: message.text == "🛒 ثبت سفارش سی‌پی کالاف")
def choose_product(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("بسته ۸۰ سی‌پی - ۵۰ هزار تومان", callback_data="prod_80cp"))
    markup.add(types.InlineKeyboardButton("بسته ۴۲۰ سی‌پی - ۲۵۰ هزار تومان", callback_data="prod_420cp"))
    bot.send_message(message.chat.id, "لطفاً بسته مورد نظر خود را انتخاب کنید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("prod_"))
def product_selected(call):
    chat_id = call.message.chat.id
    product_name = call.data.replace("prod_", "")
    orders[chat_id] = {"product": product_name, "status": "waiting_receipt"}
    user_states[chat_id] = "waiting_receipt"
    card_info = f"🔹 شما محصول {product_name} را انتخاب کردید.\n\n💳 شماره کارت جهت واریز:\n`۶۰۳۷-۹۹۷۹-۱۲۳۴-۵۶۷۸`\n\n⚠️ لطفاً پس از واریز، عکس فیش را ارسال کنید."
    bot.edit_message_text(card_info, chat_id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(content_types=['photo'], func=lambda message: user_states.get(message.chat.id) == "waiting_receipt")
def receive_receipt(message):
    chat_id = message.chat.id
    photo_id = message.photo[-1].file_id
    orders[chat_id] = {"product": orders.get(chat_id, {}).get("product", "نامشخص"), "receipt": photo_id}
    user_states[chat_id] = "pending_admin_approval"
    bot.send_message(chat_id, "⏳ فیش شما دریافت شد و در حال بررسی توسط ادمین است.")
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ تایید پرداخت", callback_data=f"admin_approve_{chat_id}"), 
        types.InlineKeyboardButton("❌ رد پرداخت", callback_data=f"admin_reject_{chat_id}")
    )
    bot.send_photo(ADMIN_ID, photo_id, caption=f"🔔 فیش جدید!\n👤 کاربر: {message.from_user.first_name}\n📦 محصول: {orders[chat_id]['product']}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_approve_") or call.data.startswith("admin_reject_"))
def admin_decision(call):
    data = call.data.split("_")
    action = data[1]  # اصلاح خطای قبلی برای تشخیص درست تایید یا رد
    user_id = int(data[2])
    
    if action == "approve":
        user_states[user_id] = "waiting_credentials"
        bot.send_message(user_id, "✅ پرداخت با موفقیت تایید شد!\n\n🔑 لطفاً جیمیل و رمز عبور بازی کالاف خود را ارسال کنید:")
        bot.edit_message_caption("✅ تایید شد. منتظر مشخصات...", call.message.chat.id, call.message.message_id)
    elif action == "reject":
        user_states[user_id] = None
        bot.send_message(user_id, "❌ پرداخت شما رد شد.")
        bot.edit_message_caption("❌ رد شد.", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "waiting_credentials")
def receive_credentials(message):
    chat_id = message.chat.id
    user_states[chat_id] = "waiting_time_setting"
    bot.send_message(chat_id, "📩 اطلاعات ارسال شد. منتظر تعیین زمان باشید.")
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⏱ تعیین زمان انجام", callback_data=f"settime_{chat_id}"))
    bot.send_message(ADMIN_ID, f"🔐 مشخصات اکانت کاربر {chat_id}:\n\n{message.text}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("settime_"))
def ask_admin_for_time(call):
    user_id = call.data.split("_")[1]
    user_states[ADMIN_ID] = f"typing_time_{user_id}"
    bot.send_message(ADMIN_ID, f"لطفاً زمان انجام را تایپ کنید (مثلاً: ۲ ساعت دیگر):")

@bot.message_handler(func=lambda message: message.chat.id == ADMIN_ID and str(user_states.get(ADMIN_ID)).startswith("typing_time_"))
def send_time_to_user(message):
    user_id = int(user_states[ADMIN_ID].replace("typing_time_", ""))
    user_states[ADMIN_ID] = None
    
    bot.send_message(user_id, f"⏳ سفارش شما در حال انجام شدن است.\n⏱ زمان تقریبی: {message.text}")
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⭐ سفارش انجام شد", callback_data=f"complete_{user_id}"))
    bot.send_message(ADMIN_ID, f"زمان ارسال شد. پس از اتمام کار دکمه زیر را بزنید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("complete_"))
def complete_order(call):
    user_id = int(call.data.split("_")[1])
    bot.send_message(user_id, "🎉 سفارش شما انجام شد! با تشکر از خرید شما.")
    bot.edit_message_text("✅ سفارش خاتمه یافت.", call.message.chat.id, call.message.message_id)

print("ربات فعال شد...")
bot.infinity_polling()
