import telebot
import time
import hashlib
from flask import Flask
from threading import Thread
from telebot import types

# ==========================================
# 1. CẤU HÌNH QUOC KHANH MEDIA
# ==========================================
QK_CONFIG = {
    'token': '8562421632:AAEqooqs8sqi5DSincjE1l3Ld53YkBBI0yw',
    'admin_id': 6684980246,
    'brand': 'QUOC KHANH MEDIA',
    'support': 'https://zalo.me/0379378971'
}

bot = telebot.TeleBot(QK_CONFIG['token'])
app = Flask('')

@app.route('/')
def home(): return "QK Media System is Online!" # Giữ Render không ngủ

# ==========================================
# 2. GIAO DIỆN MENU CHÍNH
# ==========================================
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("🛠️ Khôi Phục Tài Khoản", callback_query_id="recovery")
    btn2 = types.InlineKeyboardButton("🚀 Dịch Vụ Tương Tác", callback_data="smm_menu")
    btn3 = types.InlineKeyboardButton("🔑 Tạo Key Tool", callback_data="gen_key_info")
    btn4 = types.InlineKeyboardButton("📞 Hỗ Trợ Zalo", url=QK_CONFIG['support'])
    markup.add(btn1, btn2, btn3, btn4)
    return markup

@bot.message_handler(commands=['start', 'menu'])
def welcome(message):
    text = (f"💎 **CHÀO MỪNG ĐẾN VỚI {QK_CONFIG['brand']}**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Hệ thống cung cấp giải pháp bẻ khóa, khôi phục và tăng tương tác mạng xã hội hàng đầu.")
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu())

# ==========================================
# 3. XỬ LÝ DỊCH VỤ TƯƠNG TÁC (SMM)
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data == "smm_menu")
def smm_menu(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔵 Facebook (Like/Follow)", callback_data="smm_fb"),
        types.InlineKeyboardButton("📱 TikTok (View/Follow)", callback_data="smm_tk"),
        types.InlineKeyboardButton("🔙 Quay lại", callback_data="back_main")
    )
    bot.edit_message_text("🚀 **CHỌN NỀN TẢNG TƯƠNG TÁC:**", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("smm_"))
def smm_order(call):
    platform = "Facebook" if "fb" in call.data else "TikTok"
    msg = bot.send_message(call.message.chat.id, f"📥 **DỊCH VỤ {platform.upper()}:**\nVui lòng dán **Link bài viết/Link Profile** cần tăng tương tác:")
    bot.register_next_step_handler(msg, process_smm_link, platform)

def process_smm_link(message, platform):
    link = message.text
    msg = bot.send_message(message.chat.id, "🔢 Nhập **số lượng** cần tăng (Ví dụ: 1000):")
    bot.register_next_step_handler(msg, process_smm_final, platform, link)

def process_smm_final(message, platform, link):
    qty = message.text
    # Gửi thông tin về cho Admin
    report = (f"🛒 **ĐƠN HÀNG MỚI (SMM)**\n"
              f"━━━━━━━━━━━━━━━━━━━━\n"
              f"👤 Khách: `{message.from_user.id}`\n"
              f"🌐 Nền tảng: {platform}\n"
              f"🔗 Link: {link}\n"
              f"🔢 Số lượng: {qty}")
    bot.send_message(QK_CONFIG['admin_id'], report, parse_mode="Markdown")
    bot.send_message(message.chat.id, "✅ **Gửi yêu cầu thành công!** Admin sẽ xử lý đơn hàng của bạn ngay.", reply_markup=main_menu())

# ==========================================
# 4. XỬ LÝ KHÔI PHỤC TÀI KHOẢN (RECOVERY)
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data == "service_tk" or call.data == "service_fb")
def handle_recovery(call):
    platform = "Facebook" if "fb" in call.data else "TikTok"
    msg = bot.send_message(call.message.chat.id, f"⚠️ **KHÔI PHỤC {platform.upper()}:**\nVui lòng nhập **UID/Link tài khoản** bị hack:")
    bot.register_next_step_handler(msg, process_recovery_uid, platform)

def process_recovery_uid(message, platform):
    uid = message.text
    msg = bot.send_message(message.chat.id, "📝 Mô tả tình trạng (Ví dụ: Bị đổi Email, SĐT):")
    bot.register_next_step_handler(msg, process_recovery_final, platform, uid)

def process_recovery_final(message, platform, uid):
    desc = message.text
    report = (f"🆘 **YÊU CẦU CỨU ACC**\n"
              f"━━━━━━━━━━━━━━━━━━━━\n"
              f"👤 Khách: `{message.from_user.id}`\n"
              f"🌐 Nền tảng: {platform}\n"
              f"🆔 UID: `{uid}`\n"
              f"📜 Tình trạng: {desc}")
    bot.send_message(QK_CONFIG['admin_id'], report, parse_mode="Markdown")
    bot.send_message(message.chat.id, "✅ **Đã gửi thông tin cho Admin.** Vui lòng chờ phản hồi qua Zalo hoặc Telegram.", reply_markup=main_menu())

# ==========================================
# 5. CÁC NÚT QUAY LẠI & KEY INFO
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data == "back_main")
def back_to_main(call):
    bot.edit_message_text(f"💎 **CHÀO MỪNG ĐẾN VỚI {QK_CONFIG['brand']}**", call.message.chat.id, call.message.message_id, reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data == "gen_key_info")
def key_info(call):
    bot.answer_callback_query(call.id, "Lệnh Admin: /genkey [UID] [Ngày]")

# ==========================================
# 6. DUY TRÌ ONLINE & CHỐNG SẬP
# ==========================================
def run_web():
    app.run(host='0.0.0.0', port=10000)

if __name__ == '__main__':
    Thread(target=run_web).start()
    print(f"--- {QK_CONFIG['brand']} SERVER IS ONLINE ---")
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            # Tự động kết nối lại sau 5s khi gặp lỗi mạng
            time.sleep(5)