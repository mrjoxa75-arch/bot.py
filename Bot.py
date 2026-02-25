import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from google import genai

# -----------------------------
# TELEGRAM & GEMINI CONFIG
# -----------------------------
TOKEN = "8634715798:AAGk-eszQ01GQETy1ejve0v01Mh27M5AN3Q"
GEMINI_API_KEY = "AIzaSyDZsQi98S70tfSxXpB0u0RpZ5sVcBuCTfc"

# Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

# -----------------------------
# USER DATA
# -----------------------------
user_data_links = {}

# -----------------------------
# START COMMAND
# -----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎵 Qo'shiq/video linki yoki savol yozing.\n\n"
        "📌 Link yuborsangiz: audio/video chiqaradi\n"
        "💬 Matn yozsangiz: AI javob beradi"
    )

# -----------------------------
# HANDLE MESSAGE
# -----------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # Agar link bo'lmasa → AI chat
    if not text.startswith("http"):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=text
            )
            await update.message.reply_text(response.text)
        except Exception as e:
            await update.message.reply_text(f"❌ AI javobida xatolik: {str(e)}")
        return

    # Agar link bo'lsa → videoni audio/video ajratish
    user_data_links[update.effective_user.id] = text

    keyboard = [
        [InlineKeyboardButton("🎥 Video chiqarish", callback_data="video")],
        [InlineKeyboardButton("🎧 Videodagi qo'shiq", callback_data="extract_music")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Qaysi format kerak?", reply_markup=reply_markup)

# -----------------------------
# BUTTON HANDLER
# -----------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    link = user_data_links.get(user_id)

    if not link:
        await query.message.reply_text("Avval link yoki savol yuboring!")
        return

    os.makedirs("downloads", exist_ok=True)

    try:
        # 1️⃣ AUDIO MP3 / VIDEODAGI QO'SHIQ
        if query.data in ["music", "extract_music"]:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'downloads/%(title)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'noplaylist': True
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=True)
                filename = ydl.prepare_filename(info)

            filename = filename.rsplit(".", 1)[0] + ".mp3"

            with open(filename, "rb") as f:
                await query.message.reply_audio(
                    audio=f,
                    title=info.get("title"),
                    performer=info.get("uploader")
                )

            os.remove(filename)

        # 2️⃣ VIDEO
        elif query.data == "video":
            ydl_opts = {
                'format': 'best',
                'outtmpl': 'downloads/%(title)s.%(ext)s',
                'quiet': True,
                'noplaylist': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=True)
                filename = ydl.prepare_filename(info)

            with open(filename, "rb") as f:
                await query.message.reply_video(f)

            os.remove(filename)

    except Exception as e:
        await query.message.reply_text(f"❌ Xatolik yuz berdi: {str(e)}")

# -----------------------------
# MAIN
# -----------------------------
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(button_handler))

print("Bot ishga tushdi...")
app.run_polling()