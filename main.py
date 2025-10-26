# bot.py
# -*- coding: utf-8 -*-
"""
RafeeqakBot — أذكار وصلاة وأدعية + اختبار ديني تفاعلي
- python-telegram-bot v20+
- أوقات صلاة ديناميكية يوميًا حسب الموقع (طريقة الهيئة المصرية للمساحة: فجر 19.5°/عشاء 17.5°)
- بنك أسئلة كبير مع أزرار اختيار ونتائج
- حفظ المشتركين/الإعدادات/التقدّم
- تعديل: رسالة التذكير الساعية أصبحت "علاء بيقولك صلي على سيدنا محمد" ثم "صلي على سيدنا محمد ﷺ"
- تأكيد: أذكار الصباح والمساء عربية بالكامل
"""

from __future__ import annotations
import datetime
import logging
import math
import random
from typing import Dict, Tuple, Iterable, List, Set

import pytz
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    Defaults,
    PicklePersistence,
)

# =====================[ إعدادات عامة ]=====================
# 🔴 تم تضمين التوكن بناءً على طلبك — لا تنشر الملف علنًا.
TOKEN = "7969492080:AAFz46hEWgCnjL1O0F9E7Jz-iW4DbJsYKRc"

DEFAULT_TZ = pytz.timezone("Africa/Cairo")
DEFAULT_LAT = 30.0444
DEFAULT_LON = 31.2357

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("RafeeqakBot")

# مفاتيح التخزين
SUBSCRIBERS_KEY = "subscribers"      # set(chat_id)
SETTINGS_KEY    = "settings"         # dict(chat_id -> dict(lat,lon,tz))
JOBS_KEY        = "jobs_index"       # dict(chat_id -> set(job_names_for_today))

# =====================[ محتوى الأذكار والأدعية ]=====================
# تأكيد أن الأذكار كاملة بالعربية
AZKAR_SABAH: List[str] = [
    "أصبحتُ وأصبحَ الملكُ لله، والحمدُ لله، لا إله إلا الله وحده لا شريك له، له الملك وله الحمد، وهو على كل شيء قدير.",
    "اللهم بك أصبحنا وبك أمسينا وبك نحيا وبك نموت وإليك النشور.",
    "رضيتُ بالله ربًّا وبالإسلام دينًا وبمحمد ﷺ نبيًّا.",
    "اللهم إني أصبحتُ منك في نعمةٍ وعافيةٍ وسِتر، فأتمّ عليّ نعمتَك وعافيتك وسترك في الدنيا والآخرة.",
    "أعوذُ بكلماتِ الله التامات من شر ما خلق (ثلاثًا).",
    "سبحان الله وبحمده عدد خلقه ورضا نفسه وزنة عرشه ومداد كلماته.",
    "سبحان الله وبحمده (100 مرة).",
]

AZKAR_MASAA: List[str] = [
    "أمسينا وأمسى الملك لله، والحمد لله، لا إله إلا الله وحده لا شريك له، له الملك وله الحمد، وهو على كل شيء قدير.",
    "اللهم بك أمسينا وبك أصبحنا وبك نحيا وبك نموت وإليك المصير.",
    "حسبيَ اللهُ لا إله إلا هو عليه توكّلتُ وهو ربُّ العرش العظيم (سبع مرات).",
    "اللهم إني أمسيتُ منك في نعمةٍ وعافيةٍ وسِتر، فأتمّ عليّ نعمتَك وعافيتك وسترك في الدنيا والآخرة.",
    "أعوذُ بكلماتِ الله التامات من شر ما خلق (ثلاثًا).",
    "اللهم صلِّ وسلم على نبينا محمد.",
]

RUQYA_SHORT: List[str] = [
    "أعوذُ بكلماتِ الله التامات من شر ما خلق.",
    "بسم الله الذي لا يضرّ مع اسمه شيء في الأرض ولا في السماء وهو السميع العليم (ثلاثًا).",
    "اللهم رب الناس أذهب البأس واشفِ أنت الشافي لا شفاء إلا شفاؤك شفاءً لا يغادر سقمًا.",
    "حسبيَ اللهُ لا إله إلا هو عليه توكّلتُ وهو رب العرش العظيم.",
    "اللهم أبطل كل سحرٍ وعينٍ وحسدٍ ومسٍّ، واحفظني بحفظك.",
]

DUAA_STUDENTS: List[str] = [
    "اللهم افتح لي أبواب رحمتك، وانشر عليّ خزائن علمك، ووفقني للفهم والحفظ والعمل.",
    "اللهم لا سهل إلا ما جعلته سهلًا، وأنت تجعل الحزن إذا شئت سهلًا.",
    "ربّ اشرح لي صدري ويسّر لي أمري واحلل عقدةً من لساني يفقهوا قولي.",
    "اللهم علّمني ما ينفعني، وانفعني بما علّمتني، وزدني علمًا.",
    "اللهم ذكّرني ما نُسّيته، وعلّمني ما جهلته، وارزقني فهم النبيين وحفظ المرسلين.",
    "اللهم ارزقني ثبات الذهن، وصفاء القلب، وجودة الفهم، وبركة الوقت.",
]

DUAA_STUDY: List[str] = [
    "اللهم إني أعوذ بك من العجز والكسل، وأسألك همةً تعلو بي لطاعتك وطلب العلم.",
    "اللهم ارزقني حسن التخطيط، وحُسن الاستذكار، واصرف عني الملهيات.",
    "اللهم بارك لي في وقتي وذاكرتي، واجعل النتائج خيرًا مما أرجو.",
    "اللهم إنّي أسألك توفيقًا في المذاكرة، وإلهامًا للصواب يوم الاختبار.",
]

# =====================[ بنك أسئلة الاختبار الديني ]=====================
QUIZ_QUESTIONS: List[dict] = [
    {"question":"كم عدد أركان الإسلام؟","options":["3","4","5","6"],"answer":"5"},
    {"question":"كم عدد أركان الإيمان؟","options":["4","5","6","7"],"answer":"6"},
    {"question":"من هو أول من أسلم من الرجال؟","options":["عمر بن الخطاب","أبو بكر الصديق","علي بن أبي طالب","عثمان بن عفان"],"answer":"أبو بكر الصديق"},
    {"question":"أول من أسلم من الصبيان؟","options":["علي بن أبي طالب","أنس بن مالك","الزبير بن العوام","عبدالله بن عباس"],"answer":"علي بن أبي طالب"},
    {"question":"ما السورة التي تُسمى قلب القرآن؟","options":["يس","البقرة","الكهف","الإخلاص"],"answer":"يس"},
    {"question":"أطول سورة في القرآن؟","options":["البقرة","آل عمران","النساء","الأعراف"],"answer":"البقرة"},
    {"question":"أقصر سورة في القرآن؟","options":["الفلق","الكوثر","الإخلاص","العصر"],"answer":"الكوثر"},
    {"question":"أول آية نزلت؟","options":["الفاتحة","اقرأ باسم ربك الذي خلق","يا أيها المدثر","الم"],"answer":"اقرأ باسم ربك الذي خلق"},
    {"question":"كم عدد ركعات صلاة الفجر؟","options":["ركعة","ركعتان","ثلاث","أربع"],"answer":"ركعتان"},
    {"question":"كم عدد ركعات صلاة المغرب؟","options":["ركعتان","ثلاث","أربع","خمس"],"answer":"ثلاث"},
    {"question":"ليلة القدر في العشر الأواخر من شهر؟","options":["محرم","رمضان","ذو الحجة","شعبان"],"answer":"رمضان"},
]

# =====================[ حساب أوقات الصلاة (PrayTimes)]=====================
class PrayTimes:
    def __init__(self, fajr_angle=19.5, isha_angle=17.5):
        self.fajr_angle = fajr_angle
        self.isha_angle = isha_angle
        self.asr_shadow_factor = 1  # الشافعي/المالكي

    @staticmethod
    def _to_julian(date: datetime.date) -> float:
        y, m, d = date.year, date.month, date.day
        if m <= 2:
            y -= 1
            m += 12
        A = y // 100
        B = 2 - A + (A // 4)
        jd = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + B - 1524.5
        return jd

    @staticmethod
    def _sun_position(jd):
        D = jd - 2451545.0
        g = math.radians((357.529 + 0.98560028 * D) % 360)
        q = (280.459 + 0.98564736 * D) % 360
        L = math.radians((q + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g)) % 360)
        e = math.radians(23.439 - 0.00000036 * D)
        RA = math.atan2(math.cos(e) * math.sin(L), math.cos(L))
        decl = math.asin(math.sin(e) * math.sin(L))
        EqT = (q / 15) - (math.degrees(RA) / 15)
        EqT = (EqT + 24) % 24
        return decl, EqT

    @staticmethod
    def _hour_angle(lat, decl, angle):
        lat, decl, angle = map(math.radians, (lat, decl, angle))
        cosH = (math.cos(angle) - math.sin(lat) * math.sin(decl)) / (math.cos(lat) * math.cos(decl))
        if cosH < -1 or cosH > 1:
            return None
        H = math.degrees(math.acos(cosH)) / 15.0
        return H

    @staticmethod
    def _asr_hour_angle(lat, decl, factor):
        lat, decl = map(math.radians, (lat, decl))
        angle = -math.degrees(math.atan(1.0 / (factor + math.tan(abs(lat - decl)))))
        return angle

    def times_for(self, date: datetime.date, lat: float, lon: float, tz: pytz.BaseTzInfo) -> Dict[str, datetime.datetime]:
        jd = self._to_julian(date)
        decl, EqT = self._sun_position(jd)

        noon = 12 + lon / 15 - EqT  # الظهر

        def time_to_dt(hours: float) -> datetime.datetime:
            h = int(hours)
            m = int((hours - h) * 60)
            s = int(round(((hours - h) * 60 - m) * 60))
            local = datetime.datetime(date.year, date.month, date.day, h, m, s)
            return tz.localize(local)

        H_sun = self._hour_angle(lat, math.degrees(decl), 90.833)  # شروق/غروب
        if H_sun is None:
            raise ValueError("لا يمكن حساب الشروق/الغروب لهذه الإحداثيات/التاريخ.")

        sunrise = noon - H_sun
        sunset  = noon + H_sun

        H_fajr = self._hour_angle(lat, math.degrees(decl), 90 + self.fajr_angle)
        H_isha = self._hour_angle(lat, math.degrees(decl), 90 + self.isha_angle)
        if H_fajr is None or H_isha is None:
            raise ValueError("تعذّر حساب الفجر/العشاء لهذه الإحداثيات/التاريخ.")

        fajr = sunrise - (H_fajr - H_sun)
        isha = sunset + (H_isha - H_sun)

        asr_angle = self._asr_hour_angle(lat, math.degrees(decl), self.asr_shadow_factor)
        H_asr = self._hour_angle(lat, math.degrees(decl), 90 - asr_angle)
        asr = noon + H_asr

        return {
            "Fajr": time_to_dt(fajr),
            "Sunrise": time_to_dt(sunrise),
            "Dhuhr": time_to_dt(noon),
            "Asr": time_to_dt(asr),
            "Maghrib": time_to_dt(sunset),
            "Isha": time_to_dt(isha),
        }

PRAY = PrayTimes()

# =====================[ مساعدات ]=====================
from typing import Set as _Set

def get_settings(context: ContextTypes.DEFAULT_TYPE) -> Dict[int, dict]:
    data = context.application.bot_data.get(SETTINGS_KEY)
    if data is None:
        data = {}
        context.application.bot_data[SETTINGS_KEY] = data
    return data

def get_subscribers(context: ContextTypes.DEFAULT_TYPE) -> _Set[int]:
    subs = context.application.bot_data.get(SUBSCRIBERS_KEY)
    if subs is None:
        subs = set()
        context.application.bot_data[SUBSCRIBERS_KEY] = subs
    return subs

def get_jobs_index(context: ContextTypes.DEFAULT_TYPE) -> Dict[int, _Set[str]]:
    j = context.application.bot_data.get(JOBS_KEY)
    if j is None:
        j = {}
        context.application.bot_data[JOBS_KEY] = j
    return j

def user_conf(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> dict:
    settings = get_settings(context)
    conf = settings.get(chat_id)
    if conf is None:
        conf = {"lat": DEFAULT_LAT, "lon": DEFAULT_LON, "tz": DEFAULT_TZ.zone}
        settings[chat_id] = conf
    return conf

def fmt_hm(dt: datetime.datetime) -> str:
    return dt.strftime("%H:%M")

def keyboard_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❓ سؤال ديني", callback_data="ask_question"),
         InlineKeyboardButton("🧠 اختبار ديني", callback_data="start_quiz")],
        [InlineKeyboardButton("📍 موقعي", callback_data="show_loc"),
         InlineKeyboardButton("🕰️ اليوم", callback_data="show_today")],
    ])

async def safe_send(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str) -> None:
    try:
        await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception as e:
        logger.warning(f"فشل الإرسال إلى {chat_id}: {e}")

def format_azkar_html(title: str, items: Iterable[str]) -> str:
    out = [f"<b>{title}</b>", ""]
    for i, z in enumerate(items, 1):
        out.append(f"<b>{i}.</b> {z}")
    return "\n".join(out)

# =====================[ جدولة ديناميكية يومية ]=====================
async def schedule_for_chat_today(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    conf = user_conf(context, chat_id)
    lat, lon, tzname = conf["lat"], conf["lon"], conf["tz"]
    tz = pytz.timezone(tzname)

    today = datetime.datetime.now(tz).date()
    try:
        t = PRAY.times_for(today, lat, lon, tz)
    except Exception as e:
        logger.error(f"حساب الأوقات فشل لـ {chat_id}: {e}")
        return

    jobs_index = get_jobs_index(context)
    existed = jobs_index.get(chat_id, set())
    for name in existed:
        for j in context.application.job_queue.get_jobs_by_name(name):
            j.schedule_removal()
    jobs_index[chat_id] = set()

    schedule_list = [
        ("الفجر", t["Fajr"]),
        ("الظهر", t["Dhuhr"]),
        ("العصر", t["Asr"]),
        ("المغرب", t["Maghrib"]),
        ("العشاء", t["Isha"]),
    ]
    now = datetime.datetime.now(tz)
    for salah, when_dt in schedule_list:
        if when_dt <= now:
            continue
        job_name = f"pray_{chat_id}_{today.isoformat()}_{salah}"
        context.application.job_queue.run_once(
            prayer_job_callback,
            when=when_dt,
            name=job_name,
            data={"chat_id": chat_id, "salah": salah, "time": when_dt.astimezone(tz)},
        )
        jobs_index[chat_id].add(job_name)

async def prayer_job_callback(context: ContextTypes.DEFAULT_TYPE) -> None:
    d = context.job.data or {}
    chat_id = d.get("chat_id")
    salah = d.get("salah")
    when_dt = d.get("time")
    if chat_id is None or salah is None:
        return
    text = f"🔔 <b>تنبيه صلاة {salah}</b>\n\nحان الآن موعد صلاة <b>{salah}</b> ({fmt_hm(when_dt)})."
    await safe_send(context, chat_id, text)

async def daily_rescheduler(context: ContextTypes.DEFAULT_TYPE) -> None:
    for cid in list(get_subscribers(context)):
        await schedule_for_chat_today(context, cid)

# ⏰ التذكير الساعي: تعديل النص كما طلبت — سطر تمهيدي باسم "علاء" ثم رسالة الصلاة على النبي ﷺ
async def hourly_salawat_broadcast(context: ContextTypes.DEFAULT_TYPE) -> None:
    subs = get_subscribers(context)
    if not subs:
        return
    text = (
        "<b>🕌 علاء بيقولك صلي على سيدنا محمد</b>\n"
        "صلّي على سيدنا محمد ﷺ"
    )
    for cid in subs:
        await safe_send(context, cid, text)

def setup_global_jobs(app: Application) -> None:
    jq = app.job_queue
    jq.run_daily(daily_rescheduler, time=datetime.time(hour=0, minute=5, tzinfo=DEFAULT_TZ), name="daily_rescheduler")
    for h in range(6, 23):
        jq.run_daily(hourly_salawat_broadcast, time=datetime.time(hour=h, minute=0, tzinfo=DEFAULT_TZ), name=f"hourly_salawat_{h}")

# =====================[ أوامر عامة ]=====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cid = update.effective_chat.id
    subs = get_subscribers(context)
    subs.add(cid)
    user_conf(context, cid)
    await schedule_for_chat_today(context, cid)

    name = update.effective_user.mention_html()
    msg = (
        f"أهلًا يا {name}! 👋\n"
        "تم <b>تفعيل الاشتراك</b> وتنظيم أوقات الصلاة لليوم حسب موقعك.\n\n"
        "<b>أوامر سريعة:</b>\n"
        "/help — المساعدة\n"
        "/mylocation — عرض الموقع المستخدم\n"
        "/setlocation &lt;lat&gt; &lt;lon&gt; [tz]\n"
        "/today — أوقات صلاة اليوم\n"
        "/sabah — أذكار الصباح\n"
        "/masaa — أذكار المساء\n"
        "/duaa_students — أدعية للطلاب\n"
        "/duaa_study — أدعية للمذاكرة\n"
        "/ruqya — رقية شرعية مختصرة\n"
        "/quiz [n] — اختبار ديني بعدد n من الأسئلة (افتراضي 10)\n"
    )
    await update.message.reply_html(msg, reply_markup=keyboard_main())

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html(
        "<b>مساعدة:</b>\n"
        "/subscribe — تفعيل التنبيهات\n"
        "/unsubscribe — إيقاف التنبيهات\n"
        "/mylocation — عرض الموقع المستخدم\n"
        "/setlocation &lt;lat&gt; &lt;lon&gt; [tz]\n"
        "/today — عرض أوقات اليوم\n"
        "/sabah — أذكار الصباح\n"
        "/masaa — أذكار المساء\n"
        "/duaa_students — أدعية للطلاب\n"
        "/duaa_study — أدعية للمذاكرة\n"
        "/ruqya — رقية شرعية مختصرة\n"
        "/quiz [n] — بدء اختبار ديني\n"
    )

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    subs = get_subscribers(context)
    cid = update.effective_chat.id
    if cid in subs:
        await update.message.reply_html("✅ أنت مشترك بالفعل.")
    else:
        subs.add(cid)
        await schedule_for_chat_today(context, cid)
        await update.message.reply_html("✅ تم الاشتراك وتفعيل الجداول لليوم.")

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    subs = get_subscribers(context)
    cid = update.effective_chat.id
    if cid in subs:
        subs.remove(cid)
        await update.message.reply_html("🛑 تم إلغاء الاشتراك. بإمكانك العودة بـ /subscribe.")
    else:
        await update.message.reply_html("ℹ️ لست مشتركًا أصلًا.")

async def mylocation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cid = update.effective_chat.id
    conf = user_conf(context, cid)
    await update.message.reply_html(
        f"<b>موقعك المستخدم:</b>\n"
        f"Lat: <code>{conf['lat']}</code>, Lon: <code>{conf['lon']}</code>\n"
        f"Timezone: <code>{conf['tz']}</code>"
    )

async def setlocation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cid = update.effective_chat.id
    args = context.args
    if len(args) < 2:
        await update.message.reply_html("استخدم: /setlocation &lt;lat&gt; &lt;lon&gt; [tz]\nمثال: /setlocation 30.0444 31.2357 Africa/Cairo")
        return
    try:
        lat = float(args[0])
        lon = float(args[1])
        tzname = args[2] if len(args) >= 3 else user_conf(context, cid).get("tz", DEFAULT_TZ.zone)
        tz = pytz.timezone(tzname)
    except Exception as e:
        await update.message.reply_html(f"حدث خطأ في الإدخال: {e}\nتأكد من القيم.")
        return

    settings = get_settings(context)
    settings[cid] = {"lat": lat, "lon": lon, "tz": tz.zone}
    await schedule_for_chat_today(context, cid)
    await update.message.reply_html(f"✅ تم ضبط موقعك: {lat}, {lon} | {tz.zone}\nوأُعيدت جدولة تنبيهات اليوم.")

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cid = update.effective_chat.id
    conf = user_conf(context, cid)
    tz = pytz.timezone(conf["tz"])
    date = datetime.datetime.now(tz).date()
    try:
        t = PRAY.times_for(date, conf["lat"], conf["lon"], tz)
    except Exception as e:
        await update.message.reply_html(f"تعذر حساب الأوقات: {e}")
        return

    text = (
        "<b>🕰️ أوقات صلاة اليوم:</b>\n\n"
        f"• الفجر: {fmt_hm(t['Fajr'])}\n"
        f"• الشروق: {fmt_hm(t['Sunrise'])}\n"
        f"• الظهر: {fmt_hm(t['Dhuhr'])}\n"
        f"• العصر: {fmt_hm(t['Asr'])}\n"
        f"• المغرب: {fmt_hm(t['Maghrib'])}\n"
        f"• العشاء: {fmt_hm(t['Isha'])}\n"
    )
    await update.message.reply_html(text)

async def show_prayer_times(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await today(update, context)

async def cmd_sabah(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html(format_azkar_html("☀️ أذكار الصباح", AZKAR_SABAH))

async def cmd_masaa(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html(format_azkar_html("🌙 أذكار المساء", AZKAR_MASAA))

async def duaa_students(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html(format_azkar_html("🎓 أدعية للطلاب", DUAA_STUDENTS))

async def duaa_study(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html(format_azkar_html("📚 أدعية للمذاكرة", DUAA_STUDY))

async def ruqya(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html(
        format_azkar_html("🛡️ رقية شرعية مختصرة", RUQYA_SHORT) +
        "\n\n<i>تنبيه: ليست جهة علاجية، والأفضل القراءة بتدبر مع الأخذ بالأسباب.</i>"
    )

# =====================[ الاختبار الديني ]=====================
# user_data['quiz'] = {"qs": List[dict], "i": int, "score": int, "total": int}

def _quiz_build_keyboard(options: List[str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(opt, callback_data=f"quiz_ans:{idx}")] for idx, opt in enumerate(options)]
    )

async def _quiz_send_question(update_or_chat, context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    quiz = context.user_data.get("quiz")
    if not quiz:
        return
    i = quiz["i"]
    q = quiz["qs"][i]
    text = f"🧠 <b>سؤال {i+1}/{quiz['total']}</b>\n\n{q['question']}"
    kb = _quiz_build_keyboard(q["options"])
    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML, reply_markup=kb)

async def quiz_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cid = update.effective_chat.id
    try:
        n = int(context.args[0]) if context.args else 10
    except:
        n = 10
    n = max(1, min(n, len(QUIZ_QUESTIONS)))

    sample = random.sample(QUIZ_QUESTIONS, k=n)
    for q in sample:
        opts = q["options"][:]
        random.shuffle(opts)
        q["options"] = opts

    context.user_data["quiz"] = {"qs": sample, "i": 0, "score": 0, "total": n}
    await _quiz_send_question(update, context, cid)

async def _quiz_next_or_finish(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    quiz = context.user_data["quiz"]
    quiz["i"] += 1
    if quiz["i"] >= quiz["total"]:
        score = quiz["score"]
        total = quiz["total"]
        percent = int(round(score * 100 / total))
        medal = "🏅" if percent >= 80 else ("✅" if percent >= 60 else "📘")
        msg = (
            f"{medal} <b>انتهى الاختبار</b>\n"
            f"نتيجتك: <b>{score}/{total}</b> ({percent}%)\n"
            "أحسنت! تقدر تعيد بـ /quiz أو تغيّر العدد: /quiz 20"
        )
        await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode=ParseMode.HTML)
        context.user_data["quiz"] = None
    else:
        await _quiz_send_question(None, context, chat_id)

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    cid = q.message.chat.id
    data = q.data or ""

    if data == "ask_question":
        await context.bot.send_message(
            chat_id=cid,
            text=("تفضّل بكتابة سؤالك الآن! 💬\n"
                  "<i>ملاحظة: لست جهة إفتاء رسمية — لِلأمور المُعقّدة ارجع لأهل العلم.</i>"),
            parse_mode=ParseMode.HTML,
        )
        return
    if data == "show_today":
        dummy_update = Update(update.update_id, message=q.message)
        await today(dummy_update, context)
        return
    if data == "show_loc":
        dummy_update = Update(update.update_id, message=q.message)
        await mylocation(dummy_update, context)
        return
    if data == "start_quiz":
        context.user_data["quiz"] = None
        context.args = ["5"]
        dummy_update = Update(update.update_id, message=q.message)
        await quiz_cmd(dummy_update, context)
        return

    if data.startswith("quiz_ans:"):
        idx_str = data.split(":", 1)[1]
        try:
            choice_idx = int(idx_str)
        except:
            return
        quiz = context.user_data.get("quiz")
        if not quiz:
            await context.bot.send_message(chat_id=cid, text="لا يوجد اختبار فعّال. ابدأ بـ /quiz")
            return
        i = quiz["i"]
        qobj = quiz["qs"][i]
        options = qobj["options"]
        if not (0 <= choice_idx < len(options)):
            return
        chosen = options[choice_idx]
        correct = qobj["answer"]

        if chosen == correct:
            quiz["score"] += 1
            fb = "✅ إجابة صحيحة!"
        else:
            fb = f"❌ إجابة غير صحيحة.\nالصحيح: <b>{correct}</b>"

        await context.bot.send_message(chat_id=cid, text=fb, parse_mode=ParseMode.HTML)
        await _quiz_next_or_finish(context, cid)
        return

# =====================[ نقطة الدخول ]=====================

def setup_global_jobs(app: Application) -> None:
    jq = app.job_queue
    jq.run_daily(daily_rescheduler, time=datetime.time(hour=0, minute=5, tzinfo=DEFAULT_TZ), name="daily_rescheduler")
    for h in range(6, 23):
        jq.run_daily(hourly_salawat_broadcast, time=datetime.time(hour=h, minute=0, tzinfo=DEFAULT_TZ), name=f"hourly_salawat_{h}")


def main() -> None:
    persistence = PicklePersistence(filepath="bot_data.pickle")
    defaults = Defaults(parse_mode=ParseMode.HTML, tzinfo=DEFAULT_TZ)

    app: Application = (
        ApplicationBuilder()
        .token(TOKEN)
        .persistence(persistence)
        .defaults(defaults)
        .build()
    )

    # أوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))
    app.add_handler(CommandHandler("prayer_times", show_prayer_times))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("mylocation", mylocation))
    app.add_handler(CommandHandler("setlocation", setlocation))
    app.add_handler(CommandHandler("sabah", cmd_sabah))
    app.add_handler(CommandHandler("masaa", cmd_masaa))
    app.add_handler(CommandHandler("duaa_students", duaa_students))
    app.add_handler(CommandHandler("duaa_study", duaa_study))
    app.add_handler(CommandHandler("ruqya", ruqya))
    app.add_handler(CommandHandler("quiz", quiz_cmd))

    # الأزرار (Callback)
    app.add_handler(CallbackQueryHandler(handle_callback_query))

    # وظائف عامة (مجدول)
    setup_global_jobs(app)

    logger.info("🤖 RafeeqakBot بدأ العمل")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
