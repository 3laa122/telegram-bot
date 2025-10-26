import os
import random
import logging
import datetime
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# إعداد اللوج
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask لتشغيل السيرفر على Render
app_flask = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")  # خليه في Render

# ========= بيانات ========= #
user_lang = {}
reminders = [
    "💭 علاء بيقولك صلِّ على سيدنا محمد ﷺ",
    "📿 سبحان الله وبحمده",
    "🕌 لا تنس ذكر الله",
    "💫 الحمد لله دائمًا وأبدًا"
]

azkar_ar = [
    "أستغفر الله العظيم وأتوب إليه",
    "سبحان الله وبحمده، سبحان الله العظيم",
    "لا إله إلا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير"
]
duaa_ar = [
    "اللهم ارزقني علماً نافعاً ورزقاً طيباً وعملاً متقبلاً",
    "اللهم اجعل القرآن ربيع قلبي ونور صدري وجلاء حزني"
]
ayahs_ar = [
    "﴿ وَقُل رَّبِّ زِدْنِي عِلْمًا ﴾",
    "﴿ إِنَّ مَعَ الْعُسْرِ يُسْرًا ﴾"
]
hadiths_ar = [
    "قال ﷺ: تبسمك في وجه أخيك صدقة",
    "قال ﷺ: خيركم من تعلم القرآن وعلمه"
]
questions_ar = [
    ("كم عدد أركان الإسلام؟", "خمسة"),
    ("من هو أول من أسلم من الرجال؟", "أبو بكر الصديق")
]

# English
azkar_en = [
    "Subhan Allah wa bihamdih",
    "Alhamdulillah always",
    "Astaghfirullah wa atubu ilayh"
]
duaa_en = [
    "O Allah, grant me knowledge and wisdom",
    "O Allah, forgive me and my parents"
]
ayahs_en = [
    "Indeed, with hardship comes ease",
    "My Lord, increase me in knowledge"
]
hadiths_en = [
    "The best among you are those who learn the Qur’an and teach it",
    "Smiling at your brother is charity"
]
questions_en = [
    ("How many pillars of Islam?", "Five"),
    ("Who was the first male Muslim?", "Abu Bakr Al-Siddiq")
]

def get_random(items):
    return random.choice(items)

# ========= اللغة ========= #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇪🇬 عربي", callback_data="lang_ar"),
         InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]
    ]
    await update.message.reply_text("اختر اللغة / Choose your language:", reply_markup=InlineKeyboardMarkup(keyboard))

async def set_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    user_lang[query.message.chat_id] = lang
    if lang == "ar":
        await query.edit_message_text("✅ تم اختيار اللغة العربية.\nاستخدم الأوامر: /ذكر /دعاء /آية /حديث /سؤال /تذكير")
    else:
        await query.edit_message_text("✅ English selected.\nUse commands: /zekr /duaa /ayah /hadith /quiz /daily")

# ========= أوامر عربية ========= #
async def zekr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_random(azkar_ar))

async def duaa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_random(duaa_ar))

async def ayah(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_random(ayahs_ar))

async def hadith(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_random(hadiths_ar))

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q, a = get_random(questions_ar)
    await update.message.reply_text(f"❓ {q}\n💡 الجواب: {a}")

async def reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_random(reminders))

# ========= English ========= #
async def zekr_en(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_random(azkar_en))

async def duaa_en(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_random(duaa_en))

async def ayah_en(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_random(ayahs_en))

async def hadith_en(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_random(hadiths_en))

async def quiz_en(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q, a = get_random(questions_en)
    await update.message.reply_text(f"❓ {q}\n💡 Answer: {a}")

async def reminder_en(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_random(reminders))

# ========= تذكير تلقائي كل 6 ساعات ========= #
async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    msg = random.choice(reminders)
    for chat_id in list(user_lang.keys()):
        try:
            await context.bot.send_message(chat_id=chat_id, text=msg)
        except Exception as e:
            logger.warning(f"فشل إرسال التذكير إلى {chat_id}: {e}")

async def setup_reminders(app):
    job_queue = app.job_queue
    job_queue.run_repeating(send_reminder, interval=datetime.timedelta(hours=6), first=10)

# ========= Flask ping ========= #
@app_flask.route('/')
def home():
    return "✅ RafeeqakBot running fine!"

# ========= تشغيل البوت ========= #
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(set_lang))

    # Arabic
    app.add_handler(CommandHandler("ذكر", zekr))
    app.add_handler(CommandHandler("دعاء", duaa))
    app.add_handler(CommandHandler("آية", ayah))
    app.add_handler(CommandHandler("حديث", hadith))
    app.add_handler(CommandHandler("سؤال", quiz))
    app.add_handler(CommandHandler("تذكير", reminder))

    # English
    app.add_handler(CommandHandler("zekr", zekr_en))
    app.add_handler(CommandHandler("duaa", duaa_en))
    app.add_handler(CommandHandler("ayah", ayah_en))
    app.add_handler(CommandHandler("hadith", hadith_en))
    app.add_handler(CommandHandler("quiz", quiz_en))
    app.add_handler(CommandHandler("reminder", reminder_en))

    await setup_reminders(app)
    logger.info("🤖 RafeeqakBot is running...")
    await app.run_polling()

if __name__ == "__main__":
    import threading, asyncio
    threading.Thread(target=lambda: app_flask.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))).start()
    asyncio.run(main())
