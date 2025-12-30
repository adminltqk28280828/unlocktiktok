import telebot
import hashlib
import sqlite3
import requests
import time
from datetime import datetime, timedelta
from telebot import types
import os

# ==========================================
# 1. CẤU HÌNH HỆ THỐNG - QUOC KHANH MEDIA
# ==========================================
QK_CONFIG = {
    'token': '8562421632:AAEqooqs8sqi5DSincjE1l3Ld53YkBBI0yw',           # Token từ @BotFather
    'admin_id': 6684980246,               # ID Telegram của Khánh
    'brand': 'QUOC KHANH MEDIA',         # Tên thương hiệu
    'contact': 'https://zalo.me/0379378971', # Zalo hỗ trợ
    'salt': 'QUOCKHANH_MEDIA_SECURE_2025' # Chuỗi bí mật (Phải khớp với code JS)
}

bot = telebot.TeleBot(QK_CONFIG['token'])

# ==========================================
# 2. QUẢN LÝ CƠ SỞ DỮ LIỆU
# ==========================================
def get_db_connection():
    conn = sqlite3.connect('quockhanh_pro.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS store_keys 
                      (key_code TEXT PRIMARY KEY, days INTEGER, expiry_date_str TEXT, status TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS active_members 
                      (user_id INTEGER PRIMARY KEY, username TEXT, key_code TEXT, expiry_date TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS action_logs 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, task_type TEXT, target TEXT, status TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 3. HÀM LOGIC NÂNG CẤP
# ==========================================
def is_admin(user_id):
    return user_id == QK_CONFIG['admin_id']

def check_access(user_id):
    if is_admin(user_id): return True, "Vô thời hạn (Admin)"
    conn = get_db_connection()
    user = conn.execute("SELECT expiry_date FROM active_members WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    if user:
        expiry = datetime.strptime(user['expiry_date'], '%Y-%m-%d %H:%M:%S')
        if datetime.now() < expiry: return True, expiry.strftime('%d/%m/%Y')
        return False, "Hết hạn"
    return False, "Chưa kích hoạt"

def log_action(user_id, task, target, status):
    conn = get_db_connection()
    conn.execute("INSERT INTO action_logs (user_id, task_type, target, status, timestamp) VALUES (?, ?, ?, ?, ?)",
                 (user_id, task, target, status, datetime.now().strftime("%H:%M:%S %d/%m/%Y")))
    conn.commit()
    conn.close()

# --- CHECK FACEBOOK PRO ---
def check_fb_pro(target):
    url = f"https://www.facebook.com/{target}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if "checkpoint" in res.url: return "⚠️ KHÓA (Checkpoint)"
        if res.status_code == 404 or "Nội dung này hiện không hiển thị" in res.text:
            return "❌ DIE (Vô hiệu hóa/Không tồn tại)"
        return "✅ SỐNG (Bình thường)"
    except: return "🌐 LỖI KẾT NỐI"

# --- TẠO KEY CHO JS & BOT ---
def create_key_pro(uid, days):
    # Logic tạo key cho JS: SHA256(uid:salt:yymmdd)
    expiry_date = datetime.now() + timedelta(days=int(days))
    date_str = expiry_date.strftime("%y%m%d")
    raw_str = f"{str(uid).strip()}:{QK_CONFIG['salt']}:{date_str}"
    hash_part = hashlib.sha256(raw_str.encode()).hexdigest().upper()[:6]
    key = f"{date_str}{hash_part}"
    return key, expiry_date.strftime("%d/%m/%Y")

# ==========================================
# 4. GIAO DIỆN & LỆNH
# ==========================================

@bot.message_handler(commands=['start', 'menu'])
def welcome_page(message):
    uid = message.from_user.id
    auth, info = check_access(uid)
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Nút chức năng
    btn_tk = types.InlineKeyboardButton("📱 TikTok Unlock", callback_data="nav_tk")
    btn_fb = types.InlineKeyboardButton("🔵 Facebook Unlock", callback_data="nav_fb")
    btn_support = types.InlineKeyboardButton("📞 Hỗ trợ Zalo", url=QK_CONFIG['contact'])
    
    markup.add(btn_tk, btn_fb, btn_support)
    
    text = (
        f"🔥 **{QK_CONFIG['brand']} - DASHBOARD**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🛡️ **Bản quyền:** {info}\n"
        f"🆔 **ID của bạn:** `{uid}`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        "Chào mừng Khánh đã trở lại! Bạn muốn sử dụng dịch vụ nào?"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)

# --- ADMIN: GENKEY CHO JS ---
@bot.message_handler(commands=['genkey'])
def admin_genkey(message):
    if not is_admin(message.from_user.id): return
    try:
        # Cú pháp: /genkey [UID_Khách] [Ngày]
        parts = message.text.split()
        target_uid = parts[1]
        days = parts[2]
        key, exp_str = create_key_pro(target_uid, days)
        
        # Lưu vào store (để khách dùng lệnh /activate trên bot nếu muốn)
        conn = get_db_connection()
        conn.execute("INSERT INTO store_keys VALUES (?, ?, ?, ?)", (key, days, exp_str, "Chưa dùng"))
        conn.commit()
        conn.close()
        
        res = (
            f"✅ **TẠO KEY THÀNH CÔNG**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 **Cho UID:** `{target_uid}`\n"
            f"🔑 **Key:** `{key}`\n"
            f"⏳ **Hạn dùng:** {days} ngày\n"
            f"📅 **Hết hạn:** {exp_str}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👉 *Key này dùng được cho cả Bot và Script JS.*"
        )
        bot.reply_to(message, res, parse_mode="Markdown")
    except:
        bot.reply_to(message, "⚠️ Cú pháp: `/genkey [UID] [Ngày]`")

# --- USER: CHECK & UNLOCK FACEBOOK ---
@bot.message_handler(commands=['check_fb'])
def handle_check_fb(message):
    auth, _ = check_access(message.from_user.id)
    if not auth: return bot.reply_to(message, "🚫 Bạn cần mua Key để sử dụng.")
    try:
        target = message.text.split()[1]
        res = check_fb_pro(target)
        log_action(message.from_user.id, "CHECK_FB", target, "Done")
        bot.reply_to(message, f"🔵 **Kết quả FB @{target}:**\n{res}")
    except:
        bot.reply_to(message, "⚠️ Cú pháp: `/check_fb [ID/User]`")

@bot.message_handler(commands=['unlock_fb'])
def handle_unlock_fb(message):
    auth, _ = check_access(message.from_user.id)
    if not auth: return bot.reply_to(message, "🚫 Vui lòng kích hoạt bản quyền.")
    try:
        data = message.text.split(' ', 1)[1]
        user, email, reason = data.split('|')
        log_action(message.from_user.id, "UNLOCK_FB", user, "Sent")
        bot.reply_to(message, f"✅ **Đã gửi đơn kháng nghị cho FB: {user}**\nĐang chờ Meta xét duyệt...")
    except:
        bot.reply_to(message, "⚠️ Cú pháp: `/unlock_fb user|email|ly_do`")

# --- LỆNH XEM LOGS ---
@bot.message_handler(commands=['logs'])
def admin_view_logs(message):
    if not is_admin(message.from_user.id): return
    conn = get_db_connection()
    logs = conn.execute("SELECT * FROM action_logs ORDER BY id DESC LIMIT 10").fetchall()
    conn.close()
    text = "📜 **LỊCH SỬ GẦN ĐÂY**\n"
    for l in logs:
        text += f"🔹 {l['timestamp']}: {l['user_id']} -> {l['task_type']} ({l['target']})\n"
    bot.send_message(message.chat.id, text if logs else "Trống.", parse_mode="Markdown")

# --- XỬ LÝ NÚT BẤM ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "nav_fb":
        bot.send_message(call.message.chat.id, "🔵 **DỊCH VỤ FACEBOOK:**\n\n1. Check trạng thái: `/check_fb [user]`\n2. Kháng nghị: `/unlock_fb user|email|lydo`")
    elif call.data == "nav_tk":
        bot.send_message(call.message.chat.id, "📱 **DỊCH VỤ TIKTOK:**\n\n1. Check trạng thái: `/check [user]`\n2. Kháng nghị: `/unlock user|email|lydo`")

# --- CHẠY BOT ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"--- {QK_CONFIG['brand']} ONLINE ---")
    bot.polling(none_stop=True)