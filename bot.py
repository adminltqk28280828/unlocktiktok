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
    'token': '8562421632:AAEqooqs8sqi5DSincjE1l3Ld53YkBBI0yw',
    'admin_id': 6684980246,
    'brand': 'QUOC KHANH MEDIA',
    'salt': 'QK_PRO_SECURE_2025'
}

bot = telebot.TeleBot(QK_CONFIG['token'])
app = Flask('')

# ==========================================
# 2. SERVER NHẬN BÁO CÁO (FIX CSP)
# ==========================================
@app.route('/')
def home():
    return f"{QK_CONFIG['brand']} Server is Online!"

@app.route('/report', methods=['POST'])
def handle_browser_report():
    data = request.json
    uid = data.get('uid', 'Unknown')
    task = data.get('task', 'Action')
    msg = (f"🚀 **QK MEDIA - HÀNH ĐỘNG MỚI**\n"
           f"━━━━━━━━━━━━━━━━━━━━\n"
           f"👤 UID Khách: `{uid}`\n"
           f"🛠️ Công việc: {task}\n"
           f"⏰ Lúc: {datetime.now().strftime('%H:%M:%S')}")
    bot.send_message(QK_CONFIG['admin_id'], msg, parse_mode="Markdown")
    return {"status": "success"}, 200

# ==========================================
# 3. HỆ THỐNG MENU ĐA TẦNG SIÊU CẤP
# ==========================================
def get_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🆘 Cứu Acc Bị Hack", callback_data="svc_recovery"),
        types.InlineKeyboardButton("🚀 Dịch Vụ SMM (Tương Tác)", callback_data="svc_smm"),
        types.InlineKeyboardButton("🔑 Tạo Key Tool", callback_data="adm_key"),
        types.InlineKeyboardButton("📞 Liên Hệ Zalo", url="https://zalo.me/0379378971")
    )
    return markup

@bot.message_handler(commands=['start', 'menu'])
def welcome_user(message):
    text = (f"💎 **CHÀO MỪNG ĐẾN VỚI {QK_CONFIG['brand']}**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Vui lòng chọn dịch vụ chuyên nghiệp bên dưới:")
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=get_main_menu())

# --- MODULE KHÔI PHỤC TÀI KHOẢN (RECOVERY) ---
@bot.callback_query_handler(func=lambda call: call.data == "svc_recovery")
def recovery_choice(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔵 Facebook Hack", callback_data="rec_fb"),
        types.InlineKeyboardButton("📱 TikTok Hack", callback_data="rec_tk"),
        types.InlineKeyboardButton("🔙 Quay lại", callback_data="back_main")
    )
    bot.edit_message_text("⚠️ **BẠN CẦN CỨU TÀI KHOẢN NÀO?**", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("rec_"))
def ask_rec_info(call):
    platform = "Facebook" if "fb" in call.data else "TikTok"
    msg = bot.send_message(call.message.chat.id, f"📥 **KHÔI PHỤC {platform.upper()}:**\nVui lòng nhập **Link/UID** bị hack và mô tả tình trạng:")
    bot.register_next_step_handler(msg, process_rec_final, platform)

def process_rec_final(message, platform):
    bot.send_message(QK_CONFIG['admin_id'], f"🆘 **YÊU CẦU CỨU ACC**\n👤 Khách: `{message.from_user.id}`\n🌐 Nền tảng: {platform}\n📜 Thông tin: {message.text}")
    bot.send_message(message.chat.id, "✅ Đã gửi yêu cầu cho Admin. Bạn vui lòng chờ phản hồi!", reply_markup=get_main_menu())

# --- MODULE DỊCH VỤ SMM (TƯƠNG TÁC) ---
@bot.callback_query_handler(func=lambda call: call.data == "svc_smm")
def smm_menu(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔵 Facebook (Like/Follow)", callback_data="smm_fb"),
        types.InlineKeyboardButton("📱 TikTok (View/Follow)", callback_data="smm_tk"),
        types.InlineKeyboardButton("🔙 Quay lại", callback_data="back_main")
    )
    bot.edit_message_text("🚀 **DỊCH VỤ TƯƠNG TÁC MXH:**", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("smm_"))
def smm_link(call):
    platform = "Facebook" if "fb" in call.data else "TikTok"
    msg = bot.send_message(call.message.chat.id, f"🔗 **DỊCH VỤ {platform.upper()}:**\nVui lòng dán **Link** cần chạy:")
    bot.register_next_step_handler(msg, smm_qty, platform)

def smm_qty(message, platform):
    link = message.text
    msg = bot.send_message(message.chat.id, "🔢 Nhập **số lượng** cần chạy:")
    bot.register_next_step_handler(msg, smm_final, platform, link)

def smm_final(message, platform, link):
    qty = message.text
    bot.send_message(QK_CONFIG['admin_id'], f"🛒 **ĐƠN HÀNG SMM**\n👤 Khách: `{message.from_user.id}`\n🌐 Nền tảng: {platform}\n🔗 Link: {link}\n🔢 Số lượng: {qty}")
    bot.send_message(message.chat.id, "✅ Đã nhận đơn hàng thành công!", reply_markup=get_main_menu())

# --- NÚT QUAY LẠI & ADMIN ---
@bot.callback_query_handler(func=lambda call: call.data == "back_main")
def back_main(call):
    bot.edit_message_text(f"💎 **CHÀO MỪNG ĐẾN VỚI {QK_CONFIG['brand']}**", call.message.chat.id, call.message.message_id, reply_markup=get_main_menu())

# ==========================================
# 4. KHỞI CHẠY & ANTI-CRASH
# ==========================================
def run_web():
    app.run(host='0.0.0.0', port=10000)

if __name__ == '__main__':
    Thread(target=run_web).start()
    print(f"--- {QK_CONFIG['brand']} SERVER ONLINE ---")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            time.sleep(5)