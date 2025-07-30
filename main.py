import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
)
from datetime import datetime, timedelta

ADMIN_ID = 7249021797
TOKEN = "8065737535:AAFoeDvK5P94YAcRwixjjfB4olR3iD2kHsw"

SPAM_USERS = {}
SECRET_MODE = {}  # user_id -> True/False

# رسائل البوت
WELCOME_MESSAGE = (
    "✨ أهلاً بك في مركز الدعم السري ✨\n\n"
    "هنا فقط لدعم الرصيد (آسيا/زين). أرسل كود الرصيد (16 أو 17 رقم) أو صورة واضحة للكارت.\n"
    "أي مخالفة (صور عشوائية، صور غير الرصيد، رسائل سب/عشوائية) = سبام/حظر مؤقت 10 دقائق.\n\n"
    "ويمكنك أيضاً مراسلة الإدارة سرياً عبر الزر بالأسفل."
)

SUCCESS_MESSAGE = "✅ تم استلام رسالتك بنجاح! شكراً لدعمك يا بطل. 🌹"
ERROR_MESSAGE = (
    "🚫 فقط صور كارت الرصيد الأصلية أو رقم الرصيد. "
    "أي صورة أخرى أو رسالة عشوائية تعتبر مخالفة.\nتم حظرك مؤقتاً لمدة 10 دقائق."
)
SPAM_MESSAGE = "🚫 أنت محظور مؤقتاً! حاول بعد 10 دقائق."
SECRET_PROMPT = "✉️ أرسل الآن رسالتك السرية للإدارة. هويتك تبقى سرية."
SECRET_SENT = "✅ تم إرسال رسالتك للإدارة بسرية! يمكنك انتظار الرد."

# التحقق من كود الرصيد
def is_recharge_code(text):
    return bool(re.fullmatch(r"\d{16,17}", text.strip()))

# تحقق السبام
def is_spam(user_id):
    now = datetime.now()
    if user_id in SPAM_USERS:
        until = SPAM_USERS[user_id]
        if now < until:
            return True
        else:
            del SPAM_USERS[user_id]
    return False

def add_spam(user_id):
    SPAM_USERS[user_id] = datetime.now() + timedelta(minutes=10)

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✉️ إرسال رسالة سرية للإدارة", callback_data="send_secret_msg")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE, reply_markup=main_keyboard())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    if query.data == "send_secret_msg":
        SECRET_MODE[user_id] = True
        await query.message.reply_text(SECRET_PROMPT)

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message

    # سبام؟
    if is_spam(user.id):
        await msg.reply_text(SPAM_MESSAGE)
        return

    # وضع الرسالة السرية
    if SECRET_MODE.get(user.id):
        # ترسل للإدارة مع معرف المستخدم
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📩 رسالة سرية من ID: `{user.id}`\n\n{msg.text or '<بدون نص>'}",
            parse_mode="Markdown"
        )
        await msg.reply_text(SECRET_SENT)
        SECRET_MODE[user.id] = False
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

# الرد من الأدمن (الإدارة) للمستخدم المجهول - فقط الأدمن يكتب: /reply <ID> الرسالة
async def reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ فقط الإدارة تستطيع استخدام هذا الأمر.")
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("استخدم هكذا:\n/reply <ID> رسالتك")
        return
    user_id = int(args[0])
    reply_text = " ".join(args[1:])
    await context.bot.send_message(chat_id=user_id, text=f"👤 رسالة من الإدارة:\n{reply_text}")
    await update.message.reply_text("✅ تم إرسال رسالتك للمستخدم.")

def main():
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(MessageHandler(filters.PHOTO, handle_msg))
    app.add_handler(CommandHandler("reply", reply_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
