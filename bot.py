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
    'salt': 'QK_PRO_SECURE_2025',                            # Phải khớp 100% với JS
    'support': 'https://zalo.me/0379378971'
}

bot = telebot.TeleBot(QK_CONFIG['token'])
app = Flask('')

# ==========================================
# 2. PROXY REPORT & UPTIME SERVER
# ==========================================
# Giữ Render không ngủ và nhận báo cáo từ Facebook (Fix lỗi CSP)
@app.route('/')
def home():
    return f"{QK_CONFIG['brand']} Server is Online 24/7!"

@app.route('/report', methods=['POST'])
def handle_browser_report():
    data = request.json
    uid = data.get('uid', 'N/A')
    task = data.get('task', 'N/A')
    report_msg = (f"🚀 **QK MEDIA - HÀNH ĐỘNG MỚI**\n"
                  f"━━━━━━━━━━━━━━━━━━━━\n"
                  f"👤 UID khách: `{uid}`\n"
                  f"🛠️ Công việc: {task}\n"
                  f"⏰ Lúc: {datetime.now().strftime('%H:%M:%S')}")
    bot.send_message(QK_CONFIG['admin_id'], report_msg, parse_mode="Markdown")
    return {"status": "success"}, 200

# ==========================================
# 3. HÀM TẠO KEY BẢN QUYỀN (ĐỒNG BỘ JS)
# ==========================================
def generate_license_key(uid, days):
    expiry = datetime.now() + timedelta(days=int(days))
    date_str = expiry.strftime("%y%m%d")
    raw = f"{str(uid).strip()}:{QK_CONFIG['salt']}:{date_str}"
    hash_v = hashlib.sha256(raw.encode()).hexdigest().upper()[:6]
    return f"{date_str}{hash_v}", expiry.strftime('%d/%m/%Y')

# ==========================================
# 4. HỆ THỐNG MENU ĐA TẦNG (FULL OPTION)
# ==========================================
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🆘 Cứu Tài Khoản Hack", callback_data="svc_recovery"),
        types.InlineKeyboardButton("🚀 Dịch Vụ SMM (Tương Tác)", callback_data="svc_smm"),
        types.InlineKeyboardButton("🔑 Tạo Key Tool JS", callback_data="adm_key_info"),
        types.InlineKeyboardButton("📞 Liên Hệ Admin", url=QK_CONFIG['support'])
    )
    return markup

@bot.message_handler(commands=['start', 'menu'])
def start_cmd(message):
    text = (f"💎 **CHÀO MỪNG ĐẾN VỚI {QK_CONFIG['brand']}**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Hệ thống cung cấp dịch vụ mở khóa, khôi phục tài khoản và tăng tương tác mạng xã hội chuyên nghiệp.")
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu())

# --- XỬ LÝ KHÔI PHỤC TÀI KHOẢN ---
@bot.callback_query_handler(func=lambda call: call.data == "svc_recovery")
def recovery_flow(call):
    msg = bot.send_message(call.message.chat.id, "⚠️ **KHÔI PHỤC TÀI KHOẢN:**\nVui lòng dán **Link/UID** bị hack và mô tả tình trạng:")
    bot.register_next_step_handler(msg, process_recovery_step)

def process_recovery_step(message):
    bot.send_message(QK_CONFIG['admin_id'], f"🆘 **YÊU CẦU CỨU ACC**\n👤 Khách: `{message.from_user.id}`\n📜 Info: {message.text}")
    bot.send_message(message.chat.id, "✅ Đã gửi yêu cầu cho Admin!", reply_markup=main_menu())

# --- XỬ LÝ DỊCH VỤ SMM ---
@bot.callback_query_handler(func=lambda call: call.data == "svc_smm")
def smm_panel(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔵 Facebook (Like/Follow)", callback_data="smm_fb"),
        types.InlineKeyboardButton("📱 TikTok (View/Follow)", callback_data="smm_tk"),
        types.InlineKeyboardButton("🔙 Quay lại Menu", callback_data="back_home")
    )
    bot.edit_message_text("🚀 **DỊCH VỤ TĂNG TƯƠNG TÁC:**", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("smm_"))
def smm_order_flow(call):
    if call.data == "back_home":
        return bot.edit_message_text(f"💎 **{QK_CONFIG['brand']}**", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
    platform = "Facebook" if "fb" in call.data else "TikTok"
    msg = bot.send_message(call.message.chat.id, f"📥 **DỊCH VỤ {platform.upper()}:**\nNhập **Link** cần chạy và **Số lượng**:")
    bot.register_next_step_handler(msg, lambda m: (
        bot.send_message(QK_CONFIG['admin_id'], f"🛒 **ĐƠN HÀNG SMM**\n👤 Khách: `{m.from_user.id}`\n📦 Chi tiết: {m.text}"),
        bot.send_message(m.chat.id, "✅ Đã nhận đơn hàng!", reply_markup=main_menu())
    ))

# --- LỆNH ADMIN TẠO KEY ---
@bot.message_handler(commands=['genkey'])
def adm_genkey(message):
    if message.from_user.id != QK_CONFIG['admin_id']: return
    try:
        _, uid, days = message.text.split()
        key, exp = generate_license_key(uid, days)
        bot.reply_to(message, f"✅ **TẠO KEY THÀNH CÔNG**\n🔑 Key: `{key}`\n👤 UID: `{uid}`\n📅 Hạn: {exp}")
    except:
        bot.reply_to(message, "⚠️ Cú pháp: `/genkey [UID] [Ngày]`")

# ==========================================
# 5. KHỞI CHẠY & ANTI-CRASH LOOP
# ==========================================
def start_flask():
    app.run(host='0.0.0.0', port=10000)

if __name__ == '__main__':
    Thread(target=start_flask).start()
    print(f"--- {QK_CONFIG['brand']} IS ONLINE ---")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            # Tự động kết nối lại khi gặp lỗi Connection Reset
            print(f"Lỗi: {e}. Đang phục hồi sau 5s...")
            time.sleep(5)