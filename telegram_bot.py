# telegram_bot.py - Production Ready Version
import json
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# UPDATE 123 123123
# Setup logging untuk production
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("BOT_TOKEN not found in environment variables!")
    exit(1)

# Welcome message
WELCOME_MESSAGE = """
🤖 **Selamat datang di Bot Diagnosis Penyakit!**

Saya bisa membantu menganalisis gejala yang kamu rasakan.

**Cara menggunakan:**
- Ketik gejala yang kamu rasakan
- Pisahkan dengan koma jika lebih dari 1
- Contoh: "demam, batuk, pilek"

**Perintah tersedia:**
/start - Pesan selamat datang
/help - Panduan penggunaan
/daftar - Lihat daftar penyakit
/stats - Statistik bot (admin only)

⚠️ **Disclaimer:** Bot ini hanya untuk referensi awal. Selalu konsultasi ke dokter untuk diagnosis yang akurat!
"""

# Global variables untuk tracking
user_queries = {}
bot_stats = {
    "total_queries": 0,
    "unique_users": set(),
    "popular_symptoms": {}
}

def baca_database():
    """Baca database penyakit dengan error handling yang robust"""
    try:
        # Coba baca dari file lokal
        with open("data_penyakit.json", "r", encoding='utf-8') as file:
            data = json.load(file)
        logger.info("✅ Database loaded successfully")
        return data["penyakit"]
    except FileNotFoundError:
        logger.error("❌ data_penyakit.json not found, creating default database")
        return create_default_database()
    except json.JSONDecodeError:
        logger.error("❌ Invalid JSON format in data_penyakit.json")
        return create_default_database()
    except Exception as e:
        logger.error(f"❌ Unexpected error loading database: {e}")
        return create_default_database()

def create_default_database():
    """Buat database default jika file tidak ada"""
    default_db = {
        "flu": {
            "nama": "Influenza",
            "gejala": ["demam", "batuk", "pilek", "lemas", "sakit kepala"],
            "tingkat": "ringan",
            "saran": "Istirahat cukup, minum air putih yang banyak, konsumsi vitamin C"
        },
        "masuk_angin": {
            "nama": "Masuk Angin",
            "gejala": ["perut kembung", "mual", "lemas", "tidak nafsu makan"],
            "tingkat": "ringan",
            "saran": "Minum air hangat, kompres perut dengan air hangat, hindari makanan dingin"
        },
        "gastritis": {
            "nama": "Gastritis",
            "gejala": ["perut sakit", "mual", "kembung", "perih ulu hati"],
            "tingkat": "sedang",
            "saran": "Hindari makanan pedas dan asam, makan teratur, konsultasi dokter"
        },
        "demam_berdarah": {
            "nama": "Demam Berdarah Dengue",
            "gejala": ["demam tinggi", "sakit kepala hebat", "nyeri otot", "mual", "ruam kulit"],
            "tingkat": "berat",
            "saran": "⚠️ SEGERA ke dokter atau rumah sakit untuk pemeriksaan lebih lanjut!"
        }
    }
    
    # Simpan ke file untuk next time
    try:
        with open("data_penyakit.json", "w", encoding='utf-8') as file:
            json.dump({"penyakit": default_db}, file, indent=2, ensure_ascii=False)
        logger.info("✅ Default database created and saved")
    except Exception as e:
        logger.error(f"❌ Failed to save default database: {e}")
    
    return default_db

def diagnosa(gejala_user):
    """Diagnosa dengan algorithm yang lebih sophisticated"""
    database = baca_database()
    
    if len(database) == 0:
        return "❌ Maaf, database penyakit tidak tersedia saat ini."
    
    # Clean dan normalize input
    gejala_bersih = []
    for gejala in gejala_user:
        cleaned = gejala.lower().strip()
        if cleaned and len(cleaned) > 1:  # Filter input yang terlalu pendek
            gejala_bersih.append(cleaned)
    
    if not gejala_bersih:
        return "❌ Tidak ada gejala valid yang terdeteksi. Coba ketik: demam, batuk, pilek"
    
    # Cek dengan setiap penyakit
    hasil = []
    for data_penyakit in database.values():
        cocok = 0
        total_gejala_penyakit = len(data_penyakit["gejala"])
        
        for gejala in gejala_bersih:
            # Exact match dan partial match
            for gejala_db in data_penyakit["gejala"]:
                if gejala in gejala_db.lower() or gejala_db.lower() in gejala:
                    cocok += 1
                    break
        
        if cocok > 0:
            # Hitung confidence score
            confidence = (cocok / len(gejala_bersih)) * 100
            coverage = (cocok / total_gejala_penyakit) * 100
            
            hasil.append({
                "nama": data_penyakit["nama"],
                "cocok": cocok,
                "confidence": confidence,
                "coverage": coverage,
                "saran": data_penyakit["saran"],
                "tingkat": data_penyakit["tingkat"]
            })
    
    if len(hasil) == 0:
        return "❓ Gejala tidak dikenali dalam database kami.\n\n💡 Coba dengan gejala yang lebih umum seperti: demam, batuk, pilek, mual, sakit kepala\n\n🏥 Sebaiknya konsultasi ke dokter untuk diagnosis yang akurat!"
    
    # Sort by confidence dan coverage
    hasil.sort(key=lambda x: (x["confidence"] + x["coverage"]) / 2, reverse=True)
    terbaik = hasil[0]
    
    # Format response berdasarkan confidence level
    if terbaik["confidence"] >= 70:
        confidence_emoji = "🎯"
        confidence_text = "Kemungkinan besar"
    elif terbaik["confidence"] >= 40:
        confidence_emoji = "🤔"
        confidence_text = "Mungkin"
    else:
        confidence_emoji = "❓"
        confidence_text = "Kemungkinan kecil"
    
    # Build response message
    pesan = f"{confidence_emoji} **{confidence_text}: {terbaik['nama']}**\n"
    pesan += f"📊 Confidence: {terbaik['confidence']:.0f}%\n\n"
    
    if terbaik["tingkat"] == "berat":
        pesan += f"🚨 **PERHATIAN! Kondisi Serius!**\n"
    elif terbaik["tingkat"] == "sedang":
        pesan += f"⚠️ **Perlu Perhatian**\n"
    
    pesan += f"💊 **Saran:** {terbaik['saran']}\n\n"
    
    # Tambahan info jika ada hasil lain
    if len(hasil) > 1:
        pesan += f"📋 **Kemungkinan lain:** "
        other_diseases = [h["nama"] for h in hasil[1:3]]  # Max 2 alternatif
        pesan += ", ".join(other_diseases) + "\n\n"
    
    pesan += f"⚠️ **Disclaimer:** Selalu konsultasi ke dokter untuk diagnosis yang akurat!"
    
    return pesan

def track_user_query(user_id, username, query, result):
    """Track user queries untuk analytics"""
    global bot_stats
    
    bot_stats["total_queries"] += 1
    bot_stats["unique_users"].add(user_id)
    
    # Track popular symptoms
    symptoms = [s.strip().lower() for s in query.split(",")]
    for symptom in symptoms:
        if symptom in bot_stats["popular_symptoms"]:
            bot_stats["popular_symptoms"][symptom] += 1
        else:
            bot_stats["popular_symptoms"][symptom] = 1
    
    # Store user query history
    if user_id not in user_queries:
        user_queries[user_id] = []
    
    user_queries[user_id].append({
        "query": query,
        "result": result[:100] + "..." if len(result) > 100 else result,  # Truncate for storage
        "timestamp": str(datetime.now())
    })
    
    logger.info(f"Query tracked: User {username} ({user_id}) - {query}")

# Handler functions
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /start"""
    user = update.effective_user
    logger.info(f"User {user.username} ({user.id}) started the bot")
    
    await update.message.reply_text(
        WELCOME_MESSAGE,
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /help"""
    pesan_help = """
🆘 **PANDUAN LENGKAP PENGGUNAAN BOT**

**🔹 Cara Diagnosa:**
1. Ketik gejala yang kamu rasakan
2. Pisahkan dengan koma jika lebih dari 1
3. Contoh: `demam, batuk, pilek`

**🔹 Perintah Tersedia:**
- `/start` - Pesan selamat datang
- `/help` - Panduan ini
- `/daftar` - Lihat daftar penyakit dalam database
- `/stats` - Statistik penggunaan bot

**🔹 Contoh Gejala yang Dikenali:**
- Flu: demam, batuk, pilek, lemas, sakit kepala
- Masuk angin: perut kembung, mual, lemas
- Gastritis: perut sakit, mual, kembung, perih ulu hati
- Demam berdarah: demam tinggi, sakit kepala hebat, nyeri otot

**🔹 Tips Penggunaan:**
- Gunakan bahasa Indonesia yang sederhana
- Semakin spesifik gejala, semakin akurat hasil
- Bot ini untuk referensi awal, bukan pengganti dokter

⚠️ **Penting:** Selalu konsultasi ke tenaga medis profesional untuk diagnosis dan pengobatan yang tepat!
    """
    
    await update.message.reply_text(pesan_help, parse_mode='Markdown')

async def daftar_penyakit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /daftar"""
    database = baca_database()
    
    if len(database) == 0:
        await update.message.reply_text("❌ Database penyakit tidak tersedia saat ini.")
        return
    
    pesan = "📋 **DAFTAR PENYAKIT DALAM DATABASE:**\n\n"
    nomor = 1
    
    for key, data in database.items():
        tingkat_emoji = {
            "ringan": "🟢",
            "sedang": "🟡", 
            "berat": "🔴"
        }.get(data["tingkat"], "⚪")
        
        pesan += f"{nomor}. {tingkat_emoji} **{data['nama']}** ({data['tingkat'].title()})\n"
        pesan += f"   Gejala: {', '.join(data['gejala'][:3])}{'...' if len(data['gejala']) > 3 else ''}\n\n"
        nomor += 1
    
    pesan += f"📊 **Total: {len(database)} penyakit dalam database**\n"
    pesan += f"🔄 Database diperbarui secara berkala"
    
    await update.message.reply_text(pesan, parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /stats - Basic analytics"""
    global bot_stats
    
    # Simple admin check (bisa diperbaiki dengan proper admin system)
    admin_ids = [123456789]  # Replace dengan user ID admin yang sebenarnya
    
    user_id = update.effective_user.id
    is_admin = user_id in admin_ids
    
    if is_admin:
        # Admin stats - detailed
        top_symptoms = sorted(bot_stats["popular_symptoms"].items(), 
                            key=lambda x: x[1], reverse=True)[:5]
        
        pesan = f"""
📊 **STATISTIK BOT (ADMIN)**

👥 **Pengguna:**
- Total queries: {bot_stats['total_queries']}
- Unique users: {len(bot_stats['unique_users'])}

🔥 **Gejala Terpopuler:**
"""
        for symptom, count in top_symptoms:
            pesan += f"• {symptom}: {count}x\n"
        
        pesan += f"\n🤖 **Status:** Bot berjalan normal di Railway"
        
    else:
        # Public stats - limited
        pesan = f"""
📊 **STATISTIK BOT**

🤖 **Status:** Online dan berjalan normal
📊 **Total Queries:** {bot_stats['total_queries']}
👥 **Active Users:** {len(bot_stats['unique_users'])}
💾 **Database:** {len(baca_database())} penyakit tersedia

🆔 **User ID kamu:** `{user_id}`
        """
    
    await update.message.reply_text(pesan, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk pesan biasa (diagnosa)"""
    user_message = update.message.text
    user = update.effective_user
    
    # Log incoming message
    logger.info(f"Received message from {user.username} ({user.id}): {user_message}")
    
    # Handle greeting messages
    greetings = ["halo", "hai", "hello", "hi", "selamat"]
    if any(greeting in user_message.lower() for greeting in greetings):
        await update.message.reply_text(
            f"Halo {user.first_name}! 👋\n\n"
            "Saya siap membantu menganalisis gejala kesehatan kamu.\n"
            "Coba ceritakan gejala yang kamu rasakan ya!\n\n"
            "Contoh: `demam, batuk, pilek`",
            parse_mode='Markdown'
        )
        return
    
    # Handle thank you messages
    thanks = ["terima kasih", "thanks", "makasih", "thx"]
    if any(thank in user_message.lower() for thank in thanks):
        await update.message.reply_text(
            "Sama-sama! 😊\n\n"
            "Semoga informasinya membantu. Jangan lupa konsultasi ke dokter ya!\n"
            "Stay healthy! 💪"
        )
        return
    
    # Process diagnosis
    try:
        # Split gejala berdasarkan koma
        gejala_list = user_message.split(",")
        
        # Diagnosa
        hasil = diagnosa(gejala_list)
        
        # Track analytics
        track_user_query(user.id, user.username, user_message, hasil)
        
        # Send response
        await update.message.reply_text(hasil, parse_mode='Markdown')
        
        logger.info(f"Diagnosis completed for user {user.id}")
        
    except Exception as e:
        logger.error(f"Error processing message from {user.id}: {e}")
        await update.message.reply_text(
            "❌ Maaf, terjadi kesalahan saat memproses permintaan kamu.\n\n"
            "Coba lagi dengan format: `gejala1, gejala2, gejala3`\n"
            "Contoh: `demam, batuk, pilek`",
            parse_mode='Markdown'
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Main function"""
    logger.info("🤖 Starting Telegram Bot Diagnosis Penyakit...")
    logger.info(f"🔧 Environment: {'Production' if os.environ.get('RAILWAY_ENVIRONMENT') else 'Development'}")
    
    # Validate BOT_TOKEN
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN is required!")
        return
    
    try:
        # Create application
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("daftar", daftar_penyakit))
        app.add_handler(CommandHandler("stats", stats_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Add error handler
        app.add_error_handler(error_handler)
        
        logger.info("✅ All handlers added successfully")
        logger.info("🚀 Bot is starting... Press Ctrl+C to stop")
        
        # Run the bot
        app.run_polling(
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        raise

if __name__ == "__main__":
    # Import datetime here to avoid circular imports
    from datetime import datetime
    main()