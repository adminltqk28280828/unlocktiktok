import telebot
import sqlite3
import hashlib
import time
import os
from telebot import types
from flask import Flask, request, jsonify
from threading import Thread
from datetime import datetime, timedelta

# ==========================================
# 1. CẤU HÌNH DOANH NGHIỆP QUOC KHANH MEDIA
# ==========================================
QK_CONFIG = {
    'token': '8562421632:AAEqooqs8sqi5DSincjE1l3Ld53YkBBI0yw',
    'admin_id': 6684980246, # ID Lê Triệu Quốc Khánh
    'brand': 'QUOC KHANH MEDIA',
    'ceo': 'Lê Triệu Quốc Khánh',
    'bank': {'id': 'MB', 'stk': '0379378971', 'name': 'LE TRIEU QUOC KHANH'},
    'salt': 'QK_PRO_SECURE_2025'
}

bot = telebot.TeleBot(QK_CONFIG['token'], parse_mode="Markdown")
app = Flask('')

# ==========================================
# 2. HỆ THỐNG DATABASE ĐA LUỒNG (SỬA LỖI CỘNG TIỀN)
# ==========================================
def get_db_connection():
    # Thêm check_same_thread=False để đảm bảo Flask và Bot dùng chung DB không bị lỗi treo
    conn = sqlite3.connect('qk_enterprise_v38.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY, 
                    balance REAL DEFAULT 0, 
                    role TEXT DEFAULT 'USER')''')
    conn.commit()
    conn.close()

init_db()

def get_user_data(uid):
    conn = get_db_connection()
    user = conn.execute("SELECT balance, role FROM users WHERE id=?", (uid,)).fetchone()
    if not user:
        role = 'ADMIN' if uid == QK_CONFIG['admin_id'] else 'USER'
        conn.execute("INSERT INTO users (id, balance, role) VALUES (?, 0, ?)", (uid, 0, role))
        conn.commit()
        user = conn.execute("SELECT balance, role FROM users WHERE id=?", (uid,)).fetchone()
    conn.close()
    return user

# ==========================================
# 3. GIAO DIỆN MENU LUXURY (SỬA LỖI ĐƠ NÚT)
# ==========================================
def main_menu(uid):
    user = get_user_data(uid)
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Nút số dư có chức năng làm mới (Refresh)
    markup.add(
        types.InlineKeyboardButton(f"💰 Số dư: {user['balance']:,.0f}đ", callback_data="refresh_balance"),
        types.InlineKeyboardButton("💳 Nạp Tiền Auto", callback_data="u_deposit")
    )
    markup.add(
        types.InlineKeyboardButton("🔑 Mua Key Tool", callback_data="u_buy_key"),
        types.InlineKeyboardButton("🚀 Dịch Vụ SMM", callback_data="u_smm")
    )
    
    # Chỉ hiện nút Admin nếu đúng là Khánh
    if user['role'] == 'ADMIN':
        markup.add(types.InlineKeyboardButton("👑 BẢNG QUẢN TRỊ ADMIN", callback_data="a_master_panel"))
        
    markup.add(types.InlineKeyboardButton("📞 Hỗ Trợ Zalo", url="https://zalo.me/0379378971"))
    return markup

@bot.message_handler(commands=['start', 'menu'])
def cmd_start(message):
    uid = message.from_user.id
    bot.send_message(message.chat.id, 
                     f"💎 **{QK_CONFIG['brand']}**\nHệ thống v38.0 đã sẵn sàng phục vụ.", 
                     reply_markup=main_menu(uid))

# ==========================================
# 4. LỆNH NẠP TIỀN ADMIN (LỆNH CHUẨN)
# ==========================================
@bot.message_handler(commands=['nap'])
def admin_manual_recharge(message):
    if message.from_user.id != QK_CONFIG['admin_id']: return
    try:
        # Cú pháp: /nap ID_USER SO_TIEN
        parts = message.text.split()
        target_id = int(parts[1])
        amount = float(parts[2])
        
        conn = get_db_connection()
        conn.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, target_id))
        conn.commit() # Lưu thay đổi vào database ngay lập tức
        conn.close()
        
        bot.send_message(target_id, f"✅ **NẠP TIỀN THÀNH CÔNG**\nSố dư đã cộng: +{amount:,.0f}đ\nNhấn /start để xem số dư mới.")
        bot.reply_to(message, f"🎯 Đã cộng {amount:,.0f}đ cho ID `{target_id}` thành công.")
    except Exception as e:
        bot.reply_to(message, "⚠️ Sai cú pháp! Hãy dùng: `/nap [ID] [Số tiền]`")

# ==========================================
# 5. XỬ LÝ NÚT BẤM (CALLBACK)
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def btn_handler(call):
    uid = call.from_user.id
    
    # Kiểm tra quyền Admin khi bấm nút Quản trị
    if call.data.startswith("a_") and uid != QK_CONFIG['admin_id']:
        bot.answer_callback_query(call.id, "❌ BẠN KHÔNG CÓ QUYỀN TRUY CẬP!", show_alert=True)
        return

    if call.data == "u_deposit":
        memo = f"QKM{uid}"
        qr = f"https://img.vietqr.io/image/{QK_CONFIG['bank']['id']}-{QK_CONFIG['bank']['stk']}-compact2.png?addInfo={memo}"
        bot.send_photo(call.message.chat.id, qr, caption=f"💰 **NẠP TIỀN AUTO**\nNội dung: `{memo}`")
        bot.answer_callback_query(call.id)
    
    elif call.data == "refresh_balance":
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=main_menu(uid))
        bot.answer_callback_query(call.id, "🔄 Đã cập nhật số dư mới nhất!")

    elif call.data == "a_master_panel":
        msg = f"👑 **LỆNH ADMIN QUOC KHANH MEDIA**\n📍 `/nap [ID] [Tiền]`\n📍 `/genkey [UID] [Ngày]`"
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=main_menu(uid))
        bot.answer_callback_query(call.id)
    
    else:
        bot.answer_callback_query(call.id)

# ==========================================
# 6. DUY TRÌ ONLINE (RENDER)
# ==========================================
@app.route('/')
def live_check(): return "QK MEDIA CORE v38 ONLINE"

def start_flask(): app.run(host='0.0.0.0', port=10000)

if __name__ == '__main__':
    Thread(target=start_flask).start()
    print("--- SYSTEM STARTING ---")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception:
            time.sleep(5) # Tự phục hồi sau lỗi rớt mạng