import telebot
import hashlib
import time
import os
from datetime import datetime, timedelta
from flask import Flask, request
from threading import Thread
from telebot import types

# ==========================================
# 1. CẤU HÌNH HỆ THỐNG QUOC KHANH MEDIA
# ==========================================
QK_CONFIG = {
    'token': '8562421632:AAEqooqs8sqi5DSincjE1l3Ld53YkBBI0yw', # Token của Khánh
    'admin_id': 6684980246,                                 # ID Telegram của Khánh
    'brand': 'QUOC KHANH MEDIA',
    'salt': 'QK_PRO_SECURE_2025',                            # PHẢI KHỚP 100% VỚI JS
    'support': 'https://zalo.me/0379378971'
}

bot = telebot.TeleBot(QK_CONFIG['token'])
app = Flask('')

# ==========================================
# 2. PROXY REPORT (FIX CSP)
# ==========================================
@app.route('/')
def home():
    return f"{QK_CONFIG['brand']} Server is Online!"

@app.route('/report', methods=['POST'])
def handle_report():
    data = request.json
    uid = data.get('uid', 'N/A')
    task = data.get('task', 'N/A')
    msg = (f"🚀 **HÀNH ĐỘNG MỚI**\n"
           f"👤 UID khách: `{uid}`\n"
           f"🛠️ Công việc: {task}\n"
           f"⏰ Lúc: {datetime.now().strftime('%H:%M:%S')}")
    bot.send_message(QK_CONFIG['admin_id'], msg, parse_mode="Markdown")
    return {"status": "success"}, 200

# ==========================================
# 3. CÔNG THỨC TẠO KEY (UID + NGÀY)
# ==========================================
def generate_license_key(uid, days):
    # Lấy ngày hết hạn
    expiry = datetime.now() + timedelta(days=int(days))
    date_str = expiry.strftime("%y%m%d") # Định dạng YYMMDD
    
    # Công thức băm: UID + SALT + DATE (Đảm bảo dành riêng cho từng người)
    raw_str = f"{str(uid).strip()}:{QK_CONFIG['salt']}:{date_str}"
    hash_v = hashlib.sha256(raw_str.encode()).hexdigest().upper()[:6]
    
    # Key hoàn chỉnh = Ngày (6 số) + Hash (6 ký tự)
    final_key = f"{date_str}{hash_v}"
    return final_key, expiry.strftime('%d/%m/%Y')

# ==========================================
# 4. MENU VÀ CHỨC NĂNG ADMIN
# ==========================================
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🆘 Cứu Tài Khoản Hack", callback_data="svc_recovery"),
        types.InlineKeyboardButton("🚀 Dịch Vụ SMM", callback_data="svc_smm"),
        types.InlineKeyboardButton("🔑 Tạo Key Tool", callback_data="adm_key_info"),
        types.InlineKeyboardButton("📞 Hỗ Trợ Zalo", url=QK_CONFIG['support'])
    )
    return markup

@bot.message_handler(commands=['start', 'menu'])
def start(message):
    text = (f"💎 **CHÀO MỪNG ĐẾN VỚI {QK_CONFIG['brand']}**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Hệ thống quản trị dịch vụ mạng xã hội chuyên nghiệp.")
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu())

# --- LỆNH TẠO KEY (CHỈ ADMIN MỚI CHẠY ĐƯỢC) ---
@bot.message_handler(commands=['genkey'])
def cmd_genkey(message):
    # Kiểm tra quyền Admin
    if message.from_user.id != QK_CONFIG['admin_id']:
        return bot.reply_to(message, "❌ Bạn không có quyền sử dụng lệnh này!")
    
    try:
        # Cú pháp: /genkey [UID] [Ngày]
        parts = message.text.split()
        target_uid = parts[1]
        num_days = parts[2]
        
        key, exp_date = generate_license_key(target_uid, num_days)
        
        res = (f"✅ **TẠO KEY THÀNH CÔNG**\n"
               f"━━━━━━━━━━━━━━━━━━━━\n"
               f"🔑 Key: `{key}`\n"
               f"👤 UID: `{target_uid}`\n"
               f"⏳ Hạn dùng: {num_days} ngày ({exp_date})\n"
               f"━━━━━━━━━━━━━━━━━━━━\n"
               f"👉 Khách hàng dán mã này vào trình duyệt để kích hoạt.")
        bot.send_message(message.chat.id, res, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, "⚠️ Cú pháp lỗi! Hãy dùng: `/genkey [UID] [Số ngày]`")

# --- CÁC MODULE KHÁC ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == "svc_recovery":
        msg = bot.send_message(call.message.chat.id, "⚠️ **KHÔI PHỤC ACC:** Nhập Link/UID và tình trạng bị hack:")
        bot.register_next_step_handler(msg, lambda m: bot.send_message(QK_CONFIG['admin_id'], f"🆘 **CỨU ACC:**\n{m.text}"))
    elif call.data == "svc_smm":
        bot.send_message(call.message.chat.id, "🚀 **DỊCH VỤ SMM:** Vui lòng liên hệ Admin để báo giá gói Tương tác.")

# ==========================================
# 5. KHỞI CHẠY & ANTI-CONFLICT
# ==========================================
def run_flask():
    app.run(host='0.0.0.0', port=10000)

if __name__ == '__main__':
    Thread(target=run_flask).start()
    print(f"--- {QK_CONFIG['brand']} SERVER IS ONLINE ---")
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception:
            # Tự phục hồi khi rớt mạng
            time.sleep(5)