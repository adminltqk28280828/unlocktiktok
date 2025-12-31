import telebot, sqlite3, hashlib, time, os, requests
from telebot import types
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta

# ==========================================
# 1. CẤU HÌNH HỆ THỐNG
# ==========================================
QK_CONFIG = {
    'token': '8562421632:AAEqooqs8sqi5DSincjE1l3Ld53YkBBI0yw',
    'admin_id': 6684980246, # ID của Lê Triệu Quốc Khánh
    'brand': 'QUOC KHANH MEDIA',
    'bank': {'id': 'MB', 'stk': '7201888888', 'name': 'LE TRIEU QUOC KHANH'},
    'salt': 'QK_PRO_SECURE_2025'
}

bot = telebot.TeleBot(QK_CONFIG['token'])
app = Flask('')

# ==========================================
# 2. CƠ SỞ DỮ LIỆU (DATABASE)
# ==========================================
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, balance REAL DEFAULT 0, role TEXT DEFAULT 'USER')''')
    conn.commit()
    conn.close()

init_db()

def get_user(uid):
    conn = sqlite3.connect('database.db')
    user = conn.execute("SELECT balance, role FROM users WHERE id=?", (uid,)).fetchone()
    if not user:
        role = 'ADMIN' if uid == QK_CONFIG['admin_id'] else 'USER'
        conn.execute("INSERT INTO users (id, balance, role) VALUES (?, 0, ?)", (uid, role))
        conn.commit()
        user = (0, role)
    conn.close()
    return user

# ==========================================
# 3. GIAO DIỆN MENU SIÊU CẤP
# ==========================================
def main_menu(uid):
    balance, role = get_user(uid)
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Nút dịch vụ chính
    markup.add(
        types.InlineKeyboardButton(f"💰 Số dư: {balance:,.0f}đ", callback_data="none"),
        types.InlineKeyboardButton("💳 Nạp Tiền (Auto)", callback_data="deposit")
    )
    markup.add(
        types.InlineKeyboardButton("🔑 Mua Key Tool", callback_data="buy_tool"),
        types.InlineKeyboardButton("🆘 Cứu Tài Khoản", callback_data="recovery")
    )
    
    # Menu riêng cho Admin
    if role == 'ADMIN':
        markup.add(types.InlineKeyboardButton("👑 QUẢN TRỊ VIÊN", callback_data="admin_panel"))
        
    markup.add(types.InlineKeyboardButton("📞 Hỗ Trợ Zalo", url="https://zalo.me/0379378971"))
    return markup

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    uid = message.from_user.id
    bot.send_message(message.chat.id, 
                     f"💎 **{QK_CONFIG['brand']}**\nChào mừng bạn đến với hệ thống Enterprise v33.0.", 
                     reply_markup=main_menu(uid), parse_mode="Markdown")

# ==========================================
# 4. HỆ THỐNG NẠP TIỀN VIETQR
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data == "deposit")
def handle_deposit(call):
    # Nội dung chuyển khoản định danh theo UID khách
    memo = f"QKM{call.from_user.id}"
    qr_url = f"https://img.vietqr.io/image/{QK_CONFIG['bank']['id']}-{QK_CONFIG['bank']['stk']}-compact2.png?addInfo={memo}"
    
    text = (f"💰 **THÔNG TIN CHUYỂN KHOẢN**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Chủ TK: `{QK_CONFIG['bank']['name']}`\n"
            f"🏦 Ngân hàng: `{QK_CONFIG['bank']['id']}`\n"
            f"🔢 STK: `{QK_CONFIG['bank']['stk']}`\n"
            f"📝 Nội dung: `{memo}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ *Hệ thống tự động cộng tiền khi nhận được giao dịch.*\n"
            f"⚠️ Quá 5p không nhận được vui lòng ib admin")
    bot.send_photo(call.message.chat.id, qr_url, caption=text, parse_mode="Markdown")

# ==========================================
# 5. CHỨC NĂNG ADMIN (DÀNH RIÊNG CHO KHÁNH)
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def show_admin_commands(call):
    if call.from_user.id != QK_CONFIG['admin_id']: return
    
    msg = (f"👑 **BẢNG LỆNH ADMIN**\n"
           f"━━━━━━━━━━━━━━━━━━━━\n"
           f"📍 `/nap [ID] [Tiền]` : Nạp tiền cho khách\n"
           f"📍 `/gen [UID] [Ngày]` : Tạo key tool\n"
           f"📍 `/users` : Thống kê người dùng\n"
           f"📍 `/thongbao [Text]` : Gửi tin toàn hệ thống")
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(commands=['nap'])
def admin_set_balance(message):
    if message.from_user.id != QK_CONFIG['admin_id']: return
    try:
        _, target_id, amount = message.text.split()
        conn = sqlite3.connect('database.db')
        conn.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, target_id))
        conn.commit()
        conn.close()
        bot.send_message(target_id, f"✅ **NẠP THÀNH CÔNG**\nBạn vừa được cộng {int(amount):,.0f}đ vào tài khoản.")
        bot.reply_to(message, "Đã cập nhật số dư cho khách.")
    except: bot.reply_to(message, "Cú pháp: `/nap [ID] [Số tiền]`")

# ==========================================
# 6. DUY TRÌ ONLINE (RENDER/UPTIMEROBOT)
# ==========================================
@app.route('/')
def health_check(): return "QK Media Core is Online!"

def run_flask(): app.run(host='0.0.0.0', port=10000)

if __name__ == '__main__':
    Thread(target=run_flask).start() # Giữ Render không ngủ
    print(f"--- {QK_CONFIG['brand']} IS STARTING ---")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception:
            time.sleep(5) # Tự phục hồi khi gặp lỗi image_219ce8.png