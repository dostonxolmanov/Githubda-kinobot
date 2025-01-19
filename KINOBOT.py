import telebot
import sqlite3
from random import randrange

API_TOKEN = '7003120805:AAFyPEp3b4uEhspu1N9wKOoFKrz6_lnwJNg'
bot = telebot.TeleBot(API_TOKEN)
admins = [6395115934, 5419398541]

# Reklama holati
is_broadcasting = False

# Bot foydalanuvchilari ro'yxati
users = set()
groups = set()

conn = sqlite3.connect('videos.db', check_same_thread=False)
cursor = conn.cursor()

# Videolar uchun jadval yaratish
cursor.execute('''CREATE TABLE IF NOT EXISTS videos
                  (id INTEGER PRIMARY KEY, file_id TEXT)''')
conn.commit()

# Jadvaldagi eng katta IDni olish
def get_next_id():
    cursor.execute('SELECT MAX(id) FROM videos')
    max_id = cursor.fetchone()[0]
    return (max_id or 0) + 1

# Videoni qabul qilish va saqlash
@bot.message_handler(content_types=['video'])
def handle_video(message):
    if message.from_user.id in admins:
        file_id = message.video.file_id
        next_id = get_next_id()
        cursor.execute('INSERT INTO videos (id, file_id) VALUES (?, ?)', (next_id, file_id))
        conn.commit()
        bot.reply_to(message, f"Video bazaga {next_id} kod ostida saqlandi")

# Foydalanuvchi raqam yuborganida video jo'natish
@bot.message_handler(func=lambda message: message.text.isdigit())
def send_video(message):
    video_id = int(message.text)
    cursor.execute('SELECT file_id FROM videos WHERE id = ?', (video_id,))
    result = cursor.fetchone()
    
    if result:
        file_id = result[0]
        bot.send_video(message.chat.id, file_id,caption='Kino kodi: '+str(video_id))
    else:
        bot.reply_to(message, "Kino topilmadi")

# Botni ishga tushirish va xush kelibsiz xabar yuborish
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if message.chat.type == "private":
        users.add(user_id)
    elif message.chat.type in ["group", "supergroup"]:
        groups.add(message.chat.id)
    bot.reply_to(message, f"Assalomu alaykum  {message.from_user.first_name} 👋  botimizga xush kelibsiz.\n\n✍🏻 Kino kodini yuboring.")
    

# /menu komandasi
@bot.message_handler(commands=['menu'])
def send_menu(message):
    if message.from_user.id in admins:
        bot.reply_to(message, "📋 MENU\n/rek - Reklama yuborish\n/stop - Reklama yuborishni to'xtatish\n/statistika - Bot statistikasi")
    else:
        bot.reply_to(message, "Menu faqat adminlar uchun ishlaydi")

# /rek komandasi
@bot.message_handler(commands=['rek'])
def set_broadcasting(message):
    global is_broadcasting
    if message.from_user.id in admins:
        is_broadcasting = True
        bot.reply_to(message, "Reklama rejimi yoqildi. Endi yuborilgan har qanday xabar barcha foydalanuvchilarga uzatiladi.\nReklama rejimini oʻchirish uchun /stop buyrugʻini yuboring")
    else:
        bot.reply_to(message, "Sizda bu buyruqni bajarish uchun ruxsat yo'q.")

# /stop komandasi
@bot.message_handler(commands=['stop'])
def stop_broadcasting(message):
    global is_broadcasting
    if message.from_user.id in admins:
        is_broadcasting = False
        bot.reply_to(message, "Reklama rejimi to'xtatildi.")
    else:
        bot.reply_to(message, "Sizda bu buyruqni bajarish uchun ruxsat yo'q.")

# /statistika komandasi
@bot.message_handler(commands=['statistika'])
def send_statistics(message):
    if message.from_user.id in admins:
        user_count = len(users)
        group_count = len(groups)
        bot.reply_to(message, f"Bot azolari soni: {user_count}\nGuruhlar soni: {group_count}")
    else:
        bot.reply_to(message, "Sizda bu buyruqni bajarish uchun ruxsat yo'q.")

# Foydalanuvchilarga xabarni yuborish funksiyasi
def broadcast_message(message):
    for user in users:
        try:
            if message.content_type == 'text':
                bot.send_message(user, message.text)
            elif message.content_type == 'photo':
                bot.send_photo(user, message.photo[-1].file_id, caption=message.caption)
            elif message.content_type == 'video':
                bot.send_video(user, message.video.file_id, caption=message.caption)
            elif message.content_type == 'voice':
                bot.send_voice(user, message.voice.file_id)
            elif message.content_type == 'audio':
                bot.send_audio(user, message.audio.file_id, caption=message.caption)
            elif message.content_type == 'document':
                bot.send_document(user, message.document.file_id, caption=message.caption)
            elif message.content_type == 'sticker':
                bot.send_sticker(user, message.sticker.file_id)
            elif message.content_type == 'animation':
                bot.send_animation(user, message.animation.file_id, caption=message.caption)
            elif message.content_type == 'video_note':
                bot.send_video_note(user, message.video_note.file_id)
        except Exception as e:
            print(f"Error sending message to user {user}: {e}")

# Har qanday xabarni qabul qilish
@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'video', 'voice', 'audio', 'document', 'sticker', 'animation', 'video_note'])
def handle_all_messages(message):
    global is_broadcasting
    user_id = message.from_user.id

    # Yangi foydalanuvchilarni qo'shish
    if message.chat.type == "private":
        users.add(user_id)
    elif message.chat.type in ["group", "supergroup"]:
        groups.add(message.chat.id)

    # Broadcasting logic
    if is_broadcasting and message.from_user.id in admins:
        broadcast_message(message)

# Botni ishga tushirish
bot.polling()