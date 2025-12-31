import telebot, sqlite3, hashlib, time, os
from telebot import types
from flask import Flask, request, jsonify
from threading import Thread

# ==========================================
# 1. CẤU HÌNH HỆ THỐNG QUOC KHANH MEDIA
# ==========================================
QK_CONFIG = {
    'token': '8562421632:AAEqooqs8sqi5DSincjE1l3Ld53YkBBI0yw',
    'admin_id': 6684980246, # ID Lê Triệu Quốc Khánh
    'brand': 'QUOC KHANH MEDIA',
    'bank': {'id': 'MB', 'stk': '7201888888', 'name': 'LE TRIEU QUOC KHANH'},
    'salt': 'QK_PRO_SECURE_2025'
}

bot = telebot.TeleBot(QK_CONFIG['token'], parse_mode="Markdown")
app = Flask('')

# ==========================================
# 2. QUẢN LÝ CƠ SỞ DỮ LIỆU (SQLITE)
# ==========================================
def init_db():
    conn = sqlite3.connect('qkm_v36.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, balance REAL DEFAULT 0, role TEXT DEFAULT 'USER')''')
    conn.commit()
    conn.close()

init_db()

def get_user_info(uid):
    conn = sqlite3.connect('qkm_v36.db')
    user = conn.execute("SELECT balance, role FROM users WHERE id=?", (uid,)).fetchone()
    if not user:
        role = 'ADMIN' if uid == QK_CONFIG['admin_id'] else 'USER'
        conn.execute("INSERT INTO users (id, balance, role) VALUES (?, 0, ?)", (uid, role))
        conn.commit()
        user = (0, role)
    conn.close()
    return user

# ==========================================
# 3. GIAO DIỆN MENU CHÍNH (FIX LỖI KHÔNG PHẢN HỒI)
# ==========================================
def main_menu(uid):
    balance, role = get_user_info(uid)
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Nút dành cho tất cả người dùng
    markup.add(
        types.InlineKeyboardButton(f"💰 Số dư: {balance:,.0f}đ", callback_data="none"),
        types.InlineKeyboardButton("💳 Nạp Tiền (VietQR)", callback_data="user_deposit")
    )
    markup.add(
        types.InlineKeyboardButton("🔑 Mua Key Tool", callback_data="user_buy_key"),
        types.InlineKeyboardButton("🚀 Dịch Vụ SMM", callback_data="user_smm")
    )
    
    # Nút Admin (Luôn hiện để Admin bấm, nhưng User bấm sẽ báo lỗi)
    markup.add(types.InlineKeyboardButton("👑 Quản Trị Hệ Thống", callback_data="admin_check_users"))
    
    markup.add(types.InlineKeyboardButton("📞 Hỗ Trợ Zalo", url="https://zalo.me/0379378971"))
    return markup

@bot.message_handler(commands=['start', 'menu'])
def cmd_start(message):
    uid = message.from_user.id
    bot.send_message(message.chat.id, 
                     f"💎 **{QK_CONFIG['brand']} - ENTERPRISE**\n"
                     f"Chào mừng bạn đến với hệ thống điều khiển v36.0.\n"
                     f"━━━━━━━━━━━━━━━━━━━━\n"
                     f"Vui lòng chọn chức năng bên dưới:", 
                     reply_markup=main_menu(uid))

# ==========================================
# 4. XỬ LÝ SỰ KIỆN MENU (CALLBACK QUERY)
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_menu_click(call):
    uid = call.from_user.id
    balance, role = get_user_info(uid)
    
    # --- KIỂM TRA QUYỀN TRUY CẬP ADMIN ---
    if call.data.startswith("admin_"):
        if uid != QK_CONFIG['admin_id']:
            bot.answer_callback_query(call.id, "❌ BẠN KHÔNG CÓ QUYỀN TRUY CẬP ADMIN!", show_alert=True)
            return
    
    # --- XỬ LÝ CÁC CHỨC NĂNG ADMIN ---
    if call.data == "admin_check_users":
        conn = sqlite3.connect('qkm_v36.db')
        users = conn.execute("SELECT id, balance FROM users LIMIT 10").fetchall()
        conn.close()
        
        user_list = "👥 **DANH SÁCH NGƯỜI DÙNG MỚI:**\n"
        for u in users:
            user_list += f"📍 ID: `{u[0]}` - Tiền: {u[1]:,.0f}đ\n"
        
        bot.edit_message_text(user_list, call.message.chat.id, call.message.message_id, 
                             reply_markup=main_menu(uid))
        bot.answer_callback_query(call.id, "✅ Đã tải danh sách người dùng.")

    # --- XỬ LÝ CÁC CHỨC NĂNG USER ---
    elif call.data == "user_deposit":
        memo = f"QKM{uid}"
        qr = f"https://img.vietqr.io/image/{QK_CONFIG['bank']['id']}-{QK_CONFIG['bank']['stk']}-compact2.png?addInfo={memo}"
        bot.send_photo(call.message.chat.id, qr, caption=f"💰 **NẠP TIỀN TỰ ĐỘNG**\nNội dung: `{memo}`")
        bot.answer_callback_query(call.id)

    elif call.data == "user_buy_key":
        bot.answer_callback_query(call.id, "🛒 Chức năng mua tool đang được bảo trì.", show_alert=True)

    else:
        bot.answer_callback_query(call.id)

# ==========================================
# 5. DUY TRÌ ONLINE & ANTI-CONFLICT
# ==========================================
@app.route('/')
def home(): return "QK Media System is Online!"

def start_server(): app.run(host='0.0.0.0', port=10000)

if __name__ == '__main__':
    Thread(target=start_server).start()
    print("--- SERVER QUOC KHANH MEDIA ĐANG CHẠY ---")
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Lỗi: {e}")
            time.sleep(5)