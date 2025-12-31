import telebot, sqlite3, hashlib, time, os, requests
from telebot import types
from flask import Flask, request, jsonify
from threading import Thread
from datetime import datetime, timedelta

# ==========================================
# 1. CẤU HÌNH HỆ THỐNG QUOC KHANH MEDIA
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
    conn = sqlite3.connect('qkm_enterprise.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, balance REAL DEFAULT 0, role TEXT DEFAULT 'USER')''')
    c.execute('''CREATE TABLE IF NOT EXISTS keys 
                 (key_code TEXT PRIMARY KEY, uid TEXT, expiry TEXT)''')
    conn.commit()
    conn.close()

init_db()

def get_user_data(uid):
    conn = sqlite3.connect('qkm_enterprise.db')
    user = conn.execute("SELECT balance, role FROM users WHERE id=?", (uid,)).fetchone()
    if not user:
        role = 'ADMIN' if uid == QK_CONFIG['admin_id'] else 'USER'
        conn.execute("INSERT INTO users (id, balance, role) VALUES (?, 0, ?)", (uid, role))
        conn.commit()
        user = (0, role)
    conn.close()
    return user

# ==========================================
# 3. GIAO DIỆN MENU FULL CHỨC NĂNG
# ==========================================
def main_menu(uid):
    balance, role = get_user_data(uid)
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Dòng 1: Thông tin tài khoản
    markup.add(
        types.InlineKeyboardButton(f"💰 Số dư: {balance:,.0f}đ", callback_data="none"),
        types.InlineKeyboardButton("💳 Nạp Tiền (Auto)", callback_data="deposit_info")
    )
    # Dòng 2: Dịch vụ chính
    markup.add(
        types.InlineKeyboardButton("🔑 Mua Key Tool JS", callback_data="buy_tool_js"),
        types.InlineKeyboardButton("🆘 Kháng Nghị/Bẻ Khóa", callback_data="request_unlock")
    )
    # Dòng 3: Dịch vụ tương tác SMM
    markup.add(
        types.InlineKeyboardButton("🚀 Tăng Like/Follow", callback_data="smm_panel")
    )
    
    # Nút Admin độc quyền cho Khánh
    if role == 'ADMIN':
        markup.add(types.InlineKeyboardButton("👑 BẢNG QUẢN TRỊ ADMIN", callback_data="admin_master_panel"))
        
    markup.add(types.InlineKeyboardButton("📞 Hỗ Trợ Kỹ Thuật (Zalo)", url="https://zalo.me/0379378971"))
    return markup

@bot.message_handler(commands=['start', 'menu'])
def cmd_start(message):
    uid = message.from_user.id
    bot.send_message(message.chat.id, 
                     f"💎 **{QK_CONFIG['brand']} - ENTERPRISE v35.0**\n"
                     f"Chào mừng **{message.from_user.first_name}**.\n"
                     f"━━━━━━━━━━━━━━━━━━━━\n"
                     f"Vui lòng chọn chức năng bạn muốn sử dụng:", 
                     reply_markup=main_menu(uid), parse_mode="Markdown")

# ==========================================
# 4. HỆ THỐNG NẠP TIỀN & WEBHOOK
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data == "deposit_info")
def deposit_info(call):
    memo = f"QKM{call.from_user.id}"
    qr_url = f"https://img.vietqr.io/image/{QK_CONFIG['bank']['id']}-{QK_CONFIG['bank']['stk']}-compact2.png?amount=150000&addInfo={memo}"
    
    text = (f"💳 **NẠP TIỀN TỰ ĐỘNG (VIETQR)**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Chủ TK: `{QK_CONFIG['bank']['name']}`\n"
            f"🏦 Ngân hàng: `{QK_CONFIG['bank']['id']}`\n"
            f"🔢 STK: `{QK_CONFIG['bank']['stk']}`\n"
            f"📝 Nội dung: `{memo}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ **Tiền sẽ tự động cộng vào tài khoản sau 1-3 phút.**\n"
            f"⚠️ Quá 5p không nhận được vui lòng ib Admin")
    bot.send_photo(call.message.chat.id, qr_url, caption=text, parse_mode="Markdown")

@app.route('/webhook', methods=['POST'])
def auto_recharge_webhook():
    # Nhận dữ liệu từ dịch vụ API ngân hàng (như SePay/Casso)
    data = request.json
    content = data.get('content', '')
    amount = float(data.get('amount', 0))
    
    if "QKM" in content:
        try:
            user_id = int(content.replace("QKM", "").strip())
            conn = sqlite3.connect('qkm_enterprise.db')
            conn.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id))
            conn.commit()
            conn.close()
            
            bot.send_message(user_id, f"✅ **NẠP TIỀN THÀNH CÔNG**\n💰 Số dư: +{amount:,.0f}đ")
            bot.send_message(QK_CONFIG['admin_id'], f"💰 **BIẾN ĐỘNG SỐ DƯ**\n👤 ID: `{user_id}`\n💵 Tiền: +{amount:,.0f}đ")
            return jsonify({"status": "ok"}), 200
        except: pass
    return jsonify({"status": "ignored"}), 200

# ==========================================
# 5. CÁC LỆNH QUẢN TRỊ ADMIN (CHỈ KHÁNH)
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data == "admin_master_panel")
def admin_master(call):
    if call.from_user.id != QK_CONFIG['admin_id']: return
    msg = (f"👑 **MASTER ADMIN CONTROL**\n"
           f"━━━━━━━━━━━━━━━━━━━━\n"
           f"📍 `/nap [ID] [Số tiền]` : Cộng tiền cho khách\n"
           f"📍 `/genkey [UID] [Ngày]` : Tạo mã bản quyền\n"
           f"📍 `/user_list` : Xem danh sách người dùng\n"
           f"📍 `/broadcast [Nội dung]` : Gửi tin nhắn hàng loạt")
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(commands=['nap'])
def adm_nap_tien(message):
    if message.from_user.id != QK_CONFIG['admin_id']: return
    try:
        _, tid, amt = message.text.split()
        conn = sqlite3.connect('qkm_enterprise.db')
        conn.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amt, tid))
        conn.commit()
        conn.close()
        bot.send_message(tid, f"✅ **Hệ thống đã cộng {int(amt):,.0f}đ vào tài khoản của bạn.**")
        bot.reply_to(message, "Đã thực hiện nạp tiền.")
    except: bot.reply_to(message, "Sai cú pháp: `/nap [ID] [Số tiền]`")

@bot.message_handler(commands=['genkey'])
def adm_genkey(message):
    if message.from_user.id != QK_CONFIG['admin_id']: return
    try:
        _, target_uid, days = message.text.split()
        exp = datetime.now() + timedelta(days=int(days))
        date_s = exp.strftime("%y%m%d")
        raw = f"{str(target_uid).strip()}:{QK_CONFIG['salt']}:{date_s}"
        hash_val = hashlib.sha256(raw.encode()).hexdigest().upper()[:6]
        final_key = f"{date_s}{hash_val}"
        
        bot.reply_to(message, f"✅ **TẠO KEY THÀNH CÔNG**\n🔑 Key: `{final_key}`\n👤 UID: `{target_uid}`\n📅 Hạn: {exp.strftime('%d/%m/%Y')}")
    except: bot.reply_to(message, "Cú pháp: `/genkey [UID] [Ngày]`")

# ==========================================
# 6. DUY TRÌ ONLINE (RENDER/FLASK)
# ==========================================
@app.route('/')
def live_check(): return "QUOC KHANH MEDIA IS LIVE!"

def start_server(): app.run(host='0.0.0.0', port=10000)

if __name__ == '__main__':
    Thread(target=start_server).start() # Giữ Render không bị tắt
    print("--- SYSTEM IS STARTING ---")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except:
            time.sleep(5) # Tự phục hồi sau 5s khi rớt mạng