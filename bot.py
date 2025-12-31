import telebot
import sqlite3
import hashlib
import time
import os
import requests
import json
from telebot import types
from flask import Flask, request, jsonify
from threading import Thread
from datetime import datetime, timedelta

# ==========================================
# 1. CẤU HÌNH DOANH NGHIỆP
# ==========================================
QK_CONFIG = {
    'token': '8584344283:AAGDhLs_Q-cfLXmpEElcD11fcox505703-U',
    'admin_id': 6684980246, # ID Lê Triệu Quốc Khánh
    'brand': 'QUOC KHANH MEDIA',
    'ceo': 'Lê Triệu Quốc Khánh',
    'bank': {'id': 'MB', 'stk': '7201888888', 'name': 'LE TRIEU QUOC KHANH'},
    'salt': 'QK_PRO_SECURE_2025',
    'version': '37.0 Titan'
}

# Khởi tạo Bot và Server
bot = telebot.TeleBot(QK_CONFIG['token'], parse_mode="Markdown")
app = Flask('')

# ==========================================
# 2. HỆ THỐNG CƠ SỞ DỮ LIỆU (DATABASE CORE)
# ==========================================
def db_query(query, params=(), fetch=False):
    conn = sqlite3.connect('qk_titan.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(query, params)
    data = cursor.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return data

def init_system_db():
    # Bảng người dùng
    db_query('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY, 
                balance REAL DEFAULT 0, 
                role TEXT DEFAULT 'USER',
                total_deposit REAL DEFAULT 0,
                join_date TEXT)''')
    # Bảng mã Key
    db_query('''CREATE TABLE IF NOT EXISTS keys (
                key_code TEXT PRIMARY KEY, 
                uid TEXT, 
                expiry TEXT,
                status TEXT DEFAULT 'ACTIVE')''')
    # Bảng nhật ký giao dịch
    db_query('''CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid INTEGER,
                action TEXT,
                amount REAL,
                time TEXT)''')

init_system_db()

# ==========================================
# 3. MÔ ĐUN QUẢN LÝ TÀI CHÍNH (FINTECH)
# ==========================================
def get_user(uid):
    res = db_query("SELECT balance, role, total_deposit FROM users WHERE id=?", (uid,), True)
    if not res:
        now = datetime.now().strftime("%d/%m/%Y")
        role = 'ADMIN' if uid == QK_CONFIG['admin_id'] else 'USER'
        db_query("INSERT INTO users (id, balance, role, total_deposit, join_date) VALUES (?, 0, ?, 0, ?)", (uid, role, now))
        return (0, role, 0)
    return res[0]

# ==========================================
# 4. GIAO DIỆN NGƯỜI DÙNG (USER UI/UX)
# ==========================================
def main_menu(uid):
    bal, role, _ = get_user(uid)
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    markup.add(
        types.InlineKeyboardButton(f"💰 Số dư: {bal:,.0f}đ", callback_data="none"),
        types.InlineKeyboardButton("💳 Nạp Tiền Tự Động", callback_data="u_deposit")
    )
    markup.add(
        types.InlineKeyboardButton("🛍️ Cửa Hàng Tool", callback_data="u_shop"),
        types.InlineKeyboardButton("🚀 Dịch Vụ SMM", callback_data="u_smm")
    )
    markup.add(
        types.InlineKeyboardButton("🔑 Kiểm Tra Key", callback_data="u_key_check"),
        types.InlineKeyboardButton("🆘 Hỗ Trợ Kỹ Thuật", callback_data="u_support")
    )
    
    if role == 'ADMIN':
        markup.add(types.InlineKeyboardButton("👑 BẢNG ĐIỀU KHIỂN QUẢN TRỊ", callback_data="a_master"))
        
    return markup

@bot.message_handler(commands=['start', 'menu'])
def welcome(message):
    uid = message.from_user.id
    text = (f"💎 **{QK_CONFIG['brand']}**\n"
            f"Chào mừng Đối tác **{message.from_user.first_name}**.\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Hệ thống vận hành bởi: **{QK_CONFIG['ceo']}**\n"
            f"Phiên bản: `{QK_CONFIG['version']}`\n"
            f"Vui lòng chọn dịch vụ chuyên nghiệp:")
    bot.send_message(message.chat.id, text, reply_markup=main_menu(uid))

# ==========================================
# 5. XỬ LÝ SỰ KIỆN MENU (CALLBACK HANDLER)
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    uid = call.from_user.id
    bal, role, _ = get_user(uid)

    # CHỨC NĂNG NGƯỜI DÙNG
    if call.data == "u_deposit":
        memo = f"QKM{uid}"
        qr = f"https://img.vietqr.io/image/{QK_CONFIG['bank']['id']}-{QK_CONFIG['bank']['stk']}-compact2.png?amount=100000&addInfo={memo}"
        cap = (f"💰 **NẠP TIỀN TỰ ĐỘNG**\n"
               f"━━━━━━━━━━━━━━━━━━━━\n"
               f"🏦 Ngân hàng: `{QK_CONFIG['bank']['id']}`\n"
               f"🔢 STK: `{QK_CONFIG['bank']['stk']}`\n"
               f"👤 Chủ TK: `{QK_CONFIG['bank']['name']}`\n"
               f"📝 Nội dung: `{memo}`\n"
               f"━━━━━━━━━━━━━━━━━━━━\n"
               f"⚠️ *Tiền tự động cộng sau 1-3 phút.*")
        bot.send_photo(call.message.chat.id, qr, caption=cap)

    elif call.data == "u_shop":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔑 Mua Key FB Unlock (150k)", callback_data="buy_fb_150"))
        markup.add(types.InlineKeyboardButton("🔙 Quay lại", callback_data="back_home"))
        bot.edit_message_text("🛒 **CỬA HÀNG TOOL ĐỘC QUYỀN**", call.message.chat.id, call.message.message_id, reply_markup=markup)

    # CHỨC NĂNG ADMIN (PHÂN QUYỀN)
    elif call.data.startswith("a_"):
        if role != 'ADMIN':
            bot.answer_callback_query(call.id, "❌ BẠN KHÔNG CÓ QUYỀN ADMIN!", show_alert=True)
            return
        
        if call.data == "a_master":
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("👥 Người dùng", callback_data="a_users"),
                types.InlineKeyboardButton("📊 Doanh thu", callback_data="a_stats"),
                types.InlineKeyboardButton("📢 Gửi tin hàng loạt", callback_data="a_broadcast"),
                types.InlineKeyboardButton("🔙 Menu chính", callback_data="back_home")
            )
            bot.edit_message_text("👑 **HỆ THỐNG QUẢN TRỊ TITAN**", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == "back_home":
        bot.edit_message_text(f"💎 **{QK_CONFIG['brand']}**", call.message.chat.id, call.message.message_id, reply_markup=main_menu(uid))

# ==========================================
# 6. LỆNH ADMIN (COMMANDS)
# ==========================================
@bot.message_handler(commands=['nap'])
def admin_add_money(message):
    if message.from_user.id != QK_CONFIG['admin_id']: return
    try:
        _, tid, amt = message.text.split()
        db_query("UPDATE users SET balance = balance + ? WHERE id = ?", (amt, tid))
        db_query("INSERT INTO logs (uid, action, amount, time) VALUES (?, 'ADMIN_ADD', ?, ?)", 
                 (tid, amt, datetime.now().strftime("%H:%M:%S")))
        bot.send_message(tid, f"✅ **{QK_CONFIG['brand']}**\nTài khoản của bạn đã được cộng: +{int(amt):,.0f}đ")
        bot.reply_to(message, "Đã thực thi.")
    except: bot.reply_to(message, "Cú pháp: `/nap [ID] [Tiền]`")

@bot.message_handler(commands=['genkey'])
def admin_gen_key(message):
    if message.from_user.id != QK_CONFIG['admin_id']: return
    try:
        _, target_uid, days = message.text.split()
        exp = datetime.now() + timedelta(days=int(days))
        date_str = exp.strftime("%y%m%d")
        raw = f"{str(target_uid).strip()}:{QK_CONFIG['salt']}:{date_str}"
        h = hashlib.sha256(raw.encode()).hexdigest().upper()[:6]
        key = f"{date_str}{h}"
        db_query("INSERT INTO keys (key_code, uid, expiry) VALUES (?, ?, ?)", (key, target_uid, exp.strftime("%d/%m/%Y")))
        bot.reply_to(message, f"✅ **TẠO KEY THÀNH CÔNG**\n🔑 Key: `{key}`\n👤 UID: `{target_uid}`\n📅 Hạn: {exp.strftime('%d/%m/%Y')}")
    except: bot.reply_to(message, "Cú pháp: `/genkey [UID] [Ngày]`")

# ==========================================
# 7. WEBHOOK NẠP TIỀN TỰ ĐỘNG (AUTO-PAY)
# ==========================================
@app.route('/webhook', methods=['POST'])
def recharge_hook():
    data = request.json
    memo = data.get('content', '') # Phải chứa QKM[UID]
    amount = float(data.get('amount', 0))
    
    if "QKM" in memo:
        try:
            target_id = int(memo.replace("QKM", "").strip())
            db_query("UPDATE users SET balance = balance + ?, total_deposit = total_deposit + ? WHERE id = ?", 
                     (amount, amount, target_id))
            bot.send_message(target_id, f"✅ **NẠP TIỀN THÀNH CÔNG**\nSố dư đã cập nhật: +{amount:,.0f}đ")
            bot.send_message(QK_CONFIG['admin_id'], f"💰 **KHÁCH NẠP TIỀN**\n👤 ID: `{target_id}`\n💵 Tiền: {amount:,.0f}đ")
            return jsonify({"status": "success"}), 200
        except: pass
    return jsonify({"status": "ignored"}), 200

# ==========================================
# 8. DUY TRÌ SERVER & ANTI-CONFLICT
# ==========================================
@app.route('/')
def live(): return f"{QK_CONFIG['brand']} Server Online"

def start_flask():
    app.run(host='0.0.0.0', port=10000)

if __name__ == '__main__':
    Thread(target=start_flask).start() # Giữ Render online
    print(f"--- {QK_CONFIG['brand']} IS STARTING ---")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            time.sleep(5) # Tự phục hồi