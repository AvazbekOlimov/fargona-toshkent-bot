from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_ID
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

user_data = {}

def save_to_sheet(data):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key("1k_yxJ-L_AGPU5l1CaN1GhU9korXdhouU9nMlKGCmXLw").sheet1

    sheet.append_row([
        data['ism'],
        data['telefon'],
        data.get('kishi', '—'),
        data['yo_nalish'],
        data['vaqt'],
        data.get('extra', '—'),
        datetime.now().strftime("%Y-%m-%d %H:%M")
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Assalomu alaykum! Ismingizni yozing:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id in user_data and user_data[user_id].get('awaiting_extra'):
        user_data[user_id]['extra'] = text
        user_data[user_id]['awaiting_extra'] = False
        await update.message.reply_text(
            "✅ Qo‘shimcha ma’lumot qabul qilindi.\nEndi buyurtmani tugatish uchun quyidagi tugmani bosing.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Tugatish", callback_data="finish_order")]
            ])
        )
        return

    if user_id not in user_data:
        user_data[user_id] = {'ism': text}
        await update.message.reply_text("Telefon raqamingizni yozing:")
    elif 'telefon' not in user_data[user_id]:
        user_data[user_id]['telefon'] = text
        keyboard = [
            [InlineKeyboardButton("1 kishi", callback_data="kishi_1"), InlineKeyboardButton("2 kishi", callback_data="kishi_2")],
            [InlineKeyboardButton("3 kishi", callback_data="kishi_3"), InlineKeyboardButton("4 kishi", callback_data="kishi_4")]
        ]
        await update.message.reply_text("❓ Nechi kishilik buyurtma bermoqchisiz?", reply_markup=InlineKeyboardMarkup(keyboard))

async def kishi_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    kishi_soni = query.data.replace("kishi_", "")
    user_data[user_id]['kishi'] = f"{kishi_soni} kishi"

    keyboard = [
        [InlineKeyboardButton("Farg'ona → Toshkent", callback_data="yo_farg_tosh")],
        [InlineKeyboardButton("Toshkent → Farg'ona", callback_data="yo_tosh_farg")]
    ]
    await query.message.reply_text("📍 Qayerdan qayerga ketmoqchisiz?", reply_markup=InlineKeyboardMarkup(keyboard))

async def direction_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "yo_farg_tosh":
        user_data[user_id]['yo_nalish'] = "Farg'ona → Toshkent"
    else:
        user_data[user_id]['yo_nalish'] = "Toshkent → Farg'ona"

    time_buttons = [
        ["00:00 – 02:00", "02:00 – 04:00"],
        ["04:00 – 06:00", "06:00 – 08:00"],
        ["08:00 – 10:00", "10:00 – 12:00"],
        ["12:00 – 14:00", "14:00 – 16:00"],
        ["16:00 – 18:00", "18:00 – 20:00"],
        ["20:00 – 22:00", "22:00 – 00:00"]
    ]
    keyboard = [
        [InlineKeyboardButton(text, callback_data=f"vaqt_{text.replace(':','').replace('–','_').replace(' ','')}") for text in row]
        for row in time_buttons
    ]
    await query.message.reply_text("🕒 Qachon ketmoqchisiz?", reply_markup=InlineKeyboardMarkup(keyboard))

async def time_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    cb = query.data.replace("vaqt_", "")
    # Masalan: 1200_1400 → 12:00 – 14:00
    vaqt_boshi = cb[:2] + ":" + cb[2:4]
    vaqt_oxiri = cb[5:7] + ":" + cb[7:9]
    vaqt = f"{vaqt_boshi} – {vaqt_oxiri}"
    user_data[user_id]['vaqt'] = vaqt

    keyboard = [
        [
            InlineKeyboardButton("➕ Qo‘shimcha ma’lumot", callback_data="add_extra"),
            InlineKeyboardButton("✅ Tugatish", callback_data="finish_order")
        ]
    ]
    await query.message.reply_text(
        "Buyurtmani tugatishdan oldin boshqa ma’lumot qo‘shmoqchisiz?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def add_extra_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    await query.message.reply_text(
        "Qo‘shimcha ma’lumotni yozing.\n\n📌 Misollar:\n- Ayol kishi\n- Yuk katta\n- Old o‘rindiqda o‘tirmoqchi\n- Bolalar bilan ketiladi"
    )
    user_data[user_id]['awaiting_extra'] = True

async def finish_order_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    info = user_data.get(user_id)

    if not info:
        await query.message.reply_text("Buyurtma topilmadi. Iltimos, /start buyrug‘i bilan qayta boshlang.")
        return

    # Google Sheets'ga yozamiz
    save_to_sheet(info)

    # Adminga xabar yuborish
    msg_admin = (
        f"📥 Yangi buyurtma:\n"
        f"👤 Ism: {info['ism']}\n"
        f"📞 Telefon: {info['telefon']}\n"
        f"👥 Kishilar soni: {info.get('kishi', 'Nomaʼlum')}\n"
        f"🛣️ Yo‘nalish: {info['yo_nalish']}\n"
        f"🕒 Vaqt: {info['vaqt']}\n"
    )
    if 'extra' in info:
        msg_admin += f"📝 Qo‘shimcha: {info['extra']}"

    await context.bot.send_message(chat_id=ADMIN_ID, text=msg_admin)

    # Foydalanuvchiga tasdiq
    msg_user = (
        "✅ Buyurtmangiz qabul qilindi. Tez orada haydovchimiz siz bilan bogʻlanadi.\n\n"
        "📝 Arizangiz:\n"
        f"👤 Ism: {info['ism']}\n"
        f"📞 Telefon: {info['telefon']}\n"
        f"👥 Kishilar soni: {info.get('kishi', 'Nomaʼlum')}\n"
        f"🛣️ Yo‘nalish: {info['yo_nalish']}\n"
        f"🕒 Vaqt: {info['vaqt']}\n"
    )
    if 'extra' in info:
        msg_user += f"📝 Qo‘shimcha: {info['extra']}"

    await query.message.reply_text(
        msg_user,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Yana buyurtma berish", callback_data="new_order")]
        ])
    )

    # Ma'lumotni o'chirib yuboramiz
    del user_data[user_id]


async def new_order_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_data.pop(user_id, None)
    await query.message.reply_text("Yangi buyurtma boshlaymiz. Ismingizni yozing:")
