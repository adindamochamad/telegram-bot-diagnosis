# telegram_bot_basic.py - Versi Sederhana untuk SMA
import json
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Ambil token bot dari environment variable
BOT_TOKEN = os.environ.get('BOT_TOKEN')

def baca_database():
    """Fungsi untuk membaca database penyakit dari file JSON"""
    try:
        # Buka dan baca file JSON
        with open("data_penyakit.json", "r", encoding='utf-8') as file:
            data = json.load(file)
        
        print("✅ Database berhasil dimuat")
        return data["penyakit"]  # Return bagian "penyakit" dari JSON
        
    except FileNotFoundError:
        print("❌ File data_penyakit.json tidak ditemukan!")
        return buat_database_cadangan()
    except json.JSONDecodeError:
        print("❌ Format JSON tidak valid!")
        return buat_database_cadangan()

def buat_database_cadangan():
    """Buat database cadangan jika file tidak ada"""
    print("📝 Membuat database cadangan...")
    
    database_cadangan = {
        "flu": {
            "nama": "Flu",
            "gejala": ["demam", "batuk", "pilek", "lemas"],
            "saran": "Istirahat dan minum air putih yang banyak"
        },
        "masuk_angin": {
            "nama": "Masuk Angin", 
            "gejala": ["perut kembung", "mual", "lemas"],
            "saran": "Minum air hangat dan kompres perut"
        }
    }
    
    return database_cadangan

def cari_penyakit(gejala_user):
    """Fungsi untuk mencari penyakit berdasarkan gejala"""
    
    # Baca database dari file JSON
    database = baca_database()
    
    # Ubah input user jadi huruf kecil
    gejala_user = gejala_user.lower()
    
    # Cek setiap penyakit di database
    for penyakit_id, data in database.items():
        
        # Cek apakah ada gejala yang cocok
        for gejala in data["gejala"]:
            if gejala.lower() in gejala_user:
                return data
    
    # Kalau tidak ada yang cocok
    return None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /start"""
    
    pesan_selamat_datang = """
🤖 Halo! Saya Bot Diagnosis Sederhana

Cara pakai:
• Ketik gejala yang kamu rasakan
• Contoh: "saya demam dan batuk"

Perintah yang ada:
/start - Pesan ini
/help - Bantuan
/daftar - Lihat daftar penyakit

⚠️ Ini hanya bot pembelajaran, bukan pengganti dokter!
    """
    
    await update.message.reply_text(pesan_selamat_datang)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /help"""
    
    pesan_bantuan = """
🆘 CARA MENGGUNAKAN BOT:

1. Ketik gejala yang kamu rasakan
   Contoh: "demam batuk pilek"

2. Bot akan mencari penyakit yang cocok
   
3. Bot akan kasih saran sederhana

Gejala yang bisa dikenali:
• demam, batuk, pilek, lemas → Flu
• perut kembung, mual → Masuk angin  
• pusing, sakit kepala → Sakit kepala

❗ Selalu konsultasi ke dokter untuk kepastian!
    """
    
    await update.message.reply_text(pesan_bantuan)

async def daftar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /daftar"""
    
    # Baca database dari file
    database = baca_database()
    
    pesan_daftar = "📋 DAFTAR PENYAKIT:\n\n"
    nomor = 1
    
    for penyakit_id, data in database.items():
        pesan_daftar += f"{nomor}. {data['nama']}\n"
        pesan_daftar += f"   Gejala: {', '.join(data['gejala'])}\n"
        pesan_daftar += f"   Saran: {data['saran']}\n\n"
        nomor += 1
    
    pesan_daftar += f"Total: {len(database)} penyakit dalam database"
    
    await update.message.reply_text(pesan_daftar)

async def handle_pesan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk pesan biasa (diagnosa)"""
    
    # Ambil pesan dari user
    pesan_user = update.message.text
    nama_user = update.effective_user.first_name
    
    print(f"Pesan dari {nama_user}: {pesan_user}")  # Log sederhana
    
    # Cari penyakit berdasarkan gejala
    hasil = cari_penyakit(pesan_user)
    
    # Buat balasan
    if hasil:
        balasan = f"🎯 Kemungkinan: {hasil['nama']}\n\n"
        balasan += f"💊 Saran: {hasil['saran']}\n\n"
        balasan += "⚠️ Jangan lupa konsultasi ke dokter ya!"
    else:
        balasan = f"❓ Maaf {nama_user}, gejala tidak dikenali.\n\n"
        balasan += "Coba ketik: /help untuk melihat gejala yang bisa dikenali"
    
    # Kirim balasan
    await update.message.reply_text(balasan)

def main():
    """Fungsi utama untuk menjalankan bot"""
    
    print("🤖 Memulai Bot Telegram...")
    
    # Cek apakah token ada
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN tidak ditemukan!")
        print("Pastikan sudah set environment variable BOT_TOKEN")
        return
    
    # Buat aplikasi bot
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Tambahkan handler untuk commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("daftar", daftar_command))
    
    # Tambahkan handler untuk pesan biasa
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pesan))
    
    print("✅ Bot siap digunakan!")
    print("Tekan Ctrl+C untuk berhenti")
    
    # Jalankan bot
    app.run_polling()

# Jalankan program
if __name__ == "__main__":
    main()