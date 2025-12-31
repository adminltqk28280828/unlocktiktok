import telebot
import hashlib
import sqlite3
import time
import os
from datetime import datetime, timedelta
from flask import Flask, request
from threading import Thread
from telebot import types

# ==========================================
# 1. CẤU HÌNH HỆ THỐNG - QUOC KHANH MEDIA
# ==========================================
QK_CONFIG = {
    'token': '8562421632:AAEqooqs8sqi5DSincjE1l3Ld53YkBBI0yw', # Token của Khánh
    'admin_id': 6684980246,                                 # ID Telegram của Khánh
    'brand': 'QUOC KHANH MEDIA',
    'salt': 'QK_PRO_SECURE_2025'                            # Phải khớp với JS
}

bot = telebot.TeleBot(QK_CONFIG['token'])
app = Flask('')

# ==========================================
# 2. SERVER NHẬN BÁO CÁO (FIX LỖI image_235078.jpg)
# ==========================================
@app.route('/')
def home():
    return "QK Media System is Online 24/7!"

@app.route('/report', methods=['POST'])
def handle_report():
    data = request.json
    uid = data.get('uid')
    task = data.get('task')
    # Gửi thông báo về Admin khi khách bấm nút trên trình duyệt
    msg = (f"🚀 **QK MEDIA - HÀNH ĐỘNG MỚI**\n"
           f"━━━━━━━━━━━━━━━━━━━━\n"
           f"👤 Khách hàng: `{uid}`\n"
           f"🛠️ Hành động: {task}\n"
           f"⏰ Thời gian: {datetime.now().strftime('%H:%M:%S')}")
    bot.send_message(QK_CONFIG['admin_id'], msg, parse_mode="Markdown")
    return {"status": "success"}, 200

# ==========================================
# 3. GIAO DIỆN MENU BOT CHUYÊN NGHIỆP
# ==========================================
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🆘 Cứu Tài Khoản Hack", callback_data="service_recovery"),
        types.InlineKeyboardButton("🚀 Tăng Tương Tác (SMM)", callback_data="service_smm"),
        types.InlineKeyboardButton("🔑 Tạo Key Tool JS", callback_data="admin_genkey"),
        types.InlineKeyboardButton("📞 Liên hệ Hỗ trợ", url="https://zalo.me/0379378971")
    )
    return markup

@bot.message_handler(commands=['start', 'menu'])
def cmd_start(message):
    text = (f"💎 **CHÀO MỪNG ĐẾN VỚI {QK_CONFIG['brand']}**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Hệ thống cung cấp giải pháp mở khóa, khôi phục tài khoản và dịch vụ SMM chuyên nghiệp.")
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu())

# ==========================================
# 4. XỬ LÝ KHÔI PHỤC TÀI KHOẢN (RECOVERY)
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data == "service_recovery")
def ask_recovery_info(call):
    msg = bot.send_message(call.message.chat.id, "⚠️ **KHÔI PHỤC TÀI KHOẢN:**\nVui lòng nhập **Link/UID** bị hack và **mô tả tình trạng** (Ví dụ: Bị đổi mail):")
    bot.register_next_step_handler(msg, process_recovery)

def process_recovery(message):
    # Gửi thông tin cứu acc về cho Admin
    bot.send_message(QK_CONFIG['admin_id'], f"🆘 **YÊU CẦU CỨU ACC**\n👤 Khách: `{message.from_user.id}`\n📜 Thông tin: {message.text}")
    bot.send_message(message.chat.id, "✅ **Thông tin đã được gửi cho Admin.** Vui lòng chờ phản hồi.", reply_markup=main_menu())

# ==========================================
# 5. XỬ LÝ DỊCH VỤ TƯƠNG TÁC (SMM)
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data == "service_smm")
def smm_panel(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔵 Facebook (Like/Follow)", callback_data="smm_fb"),
        types.InlineKeyboardButton("📱 TikTok (View/Follow)", callback_data="smm_tk"),
        types.InlineKeyboardButton("🔙 Quay lại Menu", callback_data="back_main")
    )
    bot.edit_message_text("🚀 **CHỌN DỊCH VỤ TĂNG TƯƠNG TÁC:**", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("smm_"))
def process_smm_order(call):
    if call.data == "back_main":
        return bot.edit_message_text(f"💎 **{QK_CONFIG['brand']}**", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
    
    platform = "Facebook" if "fb" in call.data else "TikTok"
    msg = bot.send_message(call.message.chat.id, f"📥 **DỊCH VỤ {platform.upper()}:**\nVui lòng nhập **Link** cần tăng và **Số lượng**:")
    bot.register_next_step_handler(msg, lambda m: (
        bot.send_message(QK_CONFIG['admin_id'], f"🛒 **ĐƠN HÀNG SMM**\n👤 Khách: `{m.from_user.id}`\n📦 Chi tiết: {m.text}"),
        bot.send_message(m.chat.id, "✅ Đã nhận đơn hàng! Admin sẽ xử lý ngay.", reply_markup=main_menu())
    ))

# ==========================================
# 6. DUY TRÌ ONLINE & CHỐNG SẬP (ANTI-CRASH)
# ==========================================
def run_web():
    app.run(host='0.0.0.0', port=10000)

if __name__ == '__main__':
    # Chạy Web Server song song để giữ Render Online
    Thread(target=run_web).start()
    print(f"--- {QK_CONFIG['brand']} SERVER IS ONLINE ---")
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            # Tự phục hồi khi gặp lỗi Connection Reset
            print(f"Hệ thống tự phục hồi sau lỗi: {e}")
            time.sleep(5)