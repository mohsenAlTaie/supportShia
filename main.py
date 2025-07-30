import logging
import re
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes
)
from datetime import datetime, timedelta

# بيانات الأدمن والبوت
ADMIN_ID = 7249021797  # معرفك على تيليجرام (int)
TOKEN = "8065737535:AAFoeDvK5P94YAcRwixjjfB4olR3iD2kHsw"

# قائمة السبام المؤقت
SPAM_USERS = {}

# رسائل البوت
WELCOME_MESSAGE = (
    "✨ أهلاً بك في مركز الدعم السري ✨\n\n"
    "هنا فقط لدعم الرصيد (آسيا/زين). أرسل كود الرصيد (16 أو 17 رقم) أو صورة واضحة للكارت.\n"
    "أي مخالفة (صور عشوائية، صور غير الرصيد، رسائل سب/عشوائية) = سبام/حظر مؤقت 10 دقائق."
)

SUCCESS_MESSAGE = "✅ تم استلام رسالتك بنجاح! شكراً لدعمك يا بطل. 🌹"
ERROR_MESSAGE = (
    "🚫 فقط صور كارت الرصيد الأصلية أو رقم الرصيد. "
    "أي صورة أخرى أو رسالة عشوائية تعتبر مخالفة.\nتم حظرك مؤقتاً لمدة 10 دقائق."
)
SPAM_MESSAGE = "🚫 أنت محظور مؤقتاً! حاول بعد 10 دقائق."

# دالة التحقق من كود الرصيد
def is_recharge_code(text):
    return bool(re.fullmatch(r"\d{16,17}", text.strip()))

# دالة تحقق السبام
def is_spam(user_id):
    now = datetime.now()
    if user_id in SPAM_USERS:
        until = SPAM_USERS[user_id]
        if now < until:
            return True
        else:
            del SPAM_USERS[user_id]
    return False

# إضافة للمخالفين
def add_spam(user_id):
    SPAM_USERS[user_id] = datetime.now() + timedelta(minutes=10)

# رسالة الترحيب
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE)

# استقبال الرسائل
async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message

    # سبام؟
    if is_spam(user.id):
        await msg.reply_text(SPAM_MESSAGE)
        return

    # نص فقط (كود رصيد)
    if msg.text:
        if is_recharge_code(msg.text):
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"💳 رصيد جديد: `{msg.text}`\nID: `{user.id}`", parse_mode="Markdown")
            await msg.reply_text(SUCCESS_MESSAGE)
        else:
            add_spam(user.id)
            await msg.reply_text(ERROR_MESSAGE)
        return

    # صورة فقط
    if msg.photo:
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=msg.photo[-1].file_id, caption=f"💳 رصيد بصورة من شخص مجهول\nID: `{user.id}`", parse_mode="Markdown")
        await msg.reply_text(SUCCESS_MESSAGE)
        return

    # غير ذلك = سبام
    add_spam(user.id)
    await msg.reply_text(ERROR_MESSAGE)

# MAIN
def main():
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, handle_msg))
    app.run_polling()

if __name__ == "__main__":
    main()