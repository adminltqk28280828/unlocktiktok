import telebot
import hashlib
import sqlite3
import requests
import time
import os
from datetime import datetime, timedelta
from telebot import types

# ==========================================
# 1. CẤU HÌNH HỆ THỐNG - QUOC KHANH MEDIA
# ==========================================
QK_CONFIG = {
    'token': '8562421632:AAEqooqs8sqi5DSincjE1l3Ld53YkBBI0yw',           # Thay bằng Token Bot từ @BotFather
    'admin_id': 6684980246,               # Thay bằng ID Telegram của bạn (Gõ /id để lấy)
    'brand': 'QUOC KHANH MEDIA',         # Tên thương hiệu của bạn
    'contact': 'https://zalo.me/0379378971', # Link liên hệ hỗ trợ
    'salt': 'QK_PRO_SECURE_2025'         # Mã bí mật (Phải khớp 100% với code JS)
}

bot = telebot.TeleBot(QK_CONFIG['token'])

# ==========================================
# 2. KHỞI TẠO CƠ SỞ DỮ LIỆU (SQLITE)
# ==========================================
def get_db():
    conn = sqlite3.connect('quockhanh_media.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    # Lưu người dùng đã kích hoạt Key (UID liên kết với ngày hết hạn)
    cursor.execute('''CREATE TABLE IF NOT EXISTS active_users 
                      (user_id TEXT PRIMARY KEY, key_code TEXT, expiry_date TEXT)''')
    # Lưu nhật ký hoạt động của khách hàng
    cursor.execute('''CREATE TABLE IF NOT EXISTS action_logs 
                      (user_id TEXT, task_type TEXT, target TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 3. HÀM XỬ LÝ LOGIC NỘI BỘ
# ==========================================
def is_admin(uid):
    return int(uid) == QK_CONFIG['admin_id']

def check_access(uid):
    if is_admin(uid): return True, "Admin (Vĩnh viễn)"
    conn = get_db()
    user = conn.execute("SELECT expiry_date FROM active_users WHERE user_id = ?", (str(uid),)).fetchone()
    conn.close()
    if user:
        expiry = datetime.strptime(user['expiry_date'], '%d/%m/%Y')
        if datetime.now() <= expiry: return True, user['expiry_date']
    return False, "Chưa kích hoạt"

def generate_key_js(uid, days):
    expiry = datetime.now() + timedelta(days=int(days))
    date_str = expiry.strftime("%y%m%d") # Lấy 6 số của ngày hết hạn
    # Thuật toán: SHA256(UID:SALT:YYMMDD) - Đồng bộ với script trình duyệt
    raw = f"{str(uid).strip()}:{QK_CONFIG['salt']}:{date_str}"
    hash_v = hashlib.sha256(raw.encode()).hexdigest().upper()[:6]
    return f"{date_str}{hash_v}", expiry.strftime('%d/%m/%Y')

# ==========================================
# 4. CÁC CHỨC NĂNG CHÍNH (CHECK/UNLOCK)
# ==========================================
def check_tiktok(target):
    url = f"https://www.tiktok.com/@{target.replace('@','')}"
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if res.status_code == 404: return "❌ Tài khoản KHÔNG TỒN TẠI hoặc bị xóa."
        if "webapp.user-detail" in res.text or res.status_code == 200: return "✅ Tài khoản đang HOẠT ĐỘNG."
        return "⚠️ Tài khoản bị KHÓA (Banned)."
    except: return "🌐 Lỗi kết nối máy chủ TikTok."

def check_fb(target):
    url = f"https://www.facebook.com/{target}"
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if "checkpoint" in res.url: return "⚠️ Tài khoản bị CHECKPOINT."
        if res.status_code == 404: return "❌ Tài khoản DIE hoặc không tồn tại."
        return "✅ Tài khoản SỐNG."
    except: return "🌐 Lỗi kết nối máy chủ Facebook."

# ==========================================
# 5. GIAO DIỆN VÀ LỆNH ĐIỀU KHIỂN
# ==========================================
@bot.message_handler(commands=['start', 'menu'])
def cmd_start(message):
    uid = message.from_user.id
    auth, info = check_access(uid)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📱 Unlock TikTok", callback_data="ui_tk"),
        types.InlineKeyboardButton("🔵 Unlock Facebook", callback_data="ui_fb"),
        types.InlineKeyboardButton("📞 Hỗ trợ Zalo", url=QK_CONFIG['contact'])
    )
    
    welcome = (f"🔥 **HỆ THỐNG {QK_CONFIG['brand']}**\n"
               f"━━━━━━━━━━━━━━━━━━\n"
               f"👤 Khách hàng: `{message.from_user.first_name}`\n"
               f"🆔 ID: `{uid}`\n"
               f"🛡️ Bản quyền: {info}\n"
               f"━━━━━━━━━━━━━━━━━━\n"
               "Vui lòng chọn chức năng bạn cần sử dụng:")
    bot.send_message(message.chat.id, welcome, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(commands=['genkey'])
def cmd_genkey(message):
    if not is_admin(message.from_user.id): return
    try:
        # Cú pháp: /genkey [UID_Khách] [Số_Ngày]
        _, target_uid, days = message.text.split()
        key, exp_date = generate_key_js(target_uid, days)
        
        # Lưu vào DB
        conn = get_db()
        conn.execute("INSERT OR REPLACE INTO active_users VALUES (?, ?, ?)", (target_uid, key, exp_date))
        conn.commit()
        conn.close()
        
        bot.reply_to(message, f"✅ **TẠO KEY THÀNH CÔNG**\n🔑 Key: `{key}`\n👤 Cho UID: `{target_uid}`\n📅 Hạn dùng: {exp_date}\n\n*Khách có thể dùng key này trên Bot hoặc Script JS.*")
    except:
        bot.reply_to(message, "⚠️ Cú pháp: `/genkey [UID] [Ngày]`")

@bot.message_handler(commands=['check', 'check_fb', 'unlock', 'unlock_fb'])
def handle_services(message):
    uid = message.from_user.id
    auth, _ = check_access(uid)
    if not auth:
        return bot.reply_to(message, "🚫 Bạn chưa kích hoạt bản quyền. Vui lòng liên hệ Admin!")

    cmd = message.text.split()[0][1:] # Lấy tên lệnh
    try:
        target = message.text.split()[1]
        if 'check' in cmd:
            res = check_tiktok(target) if cmd == 'check' else check_fb(target)
            bot.reply_to(message, f"📊 **Kết quả:**\n{res}")
        else:
            bot.reply_to(message, f"⏳ Đang gửi yêu cầu kháng nghị cho `@{target}`...")
            time.sleep(2)
            bot.send_message(message.chat.id, "✅ Đã gửi đơn thành công! Vui lòng chờ 24-48h.")
    except:
        bot.reply_to(message, f"⚠️ Cú pháp: `/{cmd} [username/ID]`")

# ==========================================
# 6. DUY TRÌ KẾT NỐI (ANTI-CRASH)
# ==========================================
if __name__ == '__main__':
    print(f"--- {QK_CONFIG['brand']} IS STARTING ---")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Lỗi: {e}. Thử lại sau 5s...")
            time.sleep(5)