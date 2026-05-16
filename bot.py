# ============================================
# FILE NAME = bot.py
# ============================================

import telebot
from telebot import types
import requests
import threading
import time

from database import db, cursor
from config import *

# ============================================

bot = telebot.TeleBot(BOT_TOKEN)

last_messages = {}

# ============================================
# DELETE LAST MESSAGE
# ============================================

def delete_last(chat_id):

    try:

        if chat_id in last_messages:
            bot.delete_message(
                chat_id,
                last_messages[chat_id]
            )

    except:
        pass

# ============================================
# SEND MESSAGE
# ============================================

def send_message(chat_id, text, markup=None):

    delete_last(chat_id)

    msg = bot.send_message(
        chat_id,
        text,
        parse_mode="HTML",
        reply_markup=markup
    )

    last_messages[chat_id] = msg.message_id

# ============================================
# ADD USER
# ============================================

def add_user(user):

    cursor.execute(
        "SELECT * FROM users WHERE user_id=?",
        (user.id,)
    )

    check = cursor.fetchone()

    if not check:

        cursor.execute("""
        INSERT INTO users(
            user_id,
            name,
            username
        )

        VALUES(?,?,?)
        """, (

            user.id,
            user.first_name,
            str(user.username)

        ))

        db.commit()

# ============================================
# CHECK FORCE JOIN
# ============================================

def is_joined(user_id):

    try:

        a = bot.get_chat_member(
            CHANNEL_1,
            user_id
        )

        b = bot.get_chat_member(
            CHANNEL_2,
            user_id
        )

        if a.status in ["member", "administrator", "creator"] and b.status in ["member", "administrator", "creator"]:
            return True

        return False

    except:
        return False

# ============================================
# HOME PANEL
# ============================================

def home(chat_id, user):

    cursor.execute("""
    SELECT balance
    FROM users
    WHERE user_id=?
    """, (user.id,))

    bal = cursor.fetchone()[0]

    markup = types.InlineKeyboardMarkup(
        row_width=2
    )

    markup.add(

        types.InlineKeyboardButton(
            "🔴 Get Number",
            callback_data="get_number"
        ),

        types.InlineKeyboardButton(
            "🟢 OTP Group",
            url="https://t.me/muqeetxotp"
        )

    )

    markup.add(

        types.InlineKeyboardButton(
            "💸 Withdraw",
            callback_data="withdraw"
        )

    )

    text = f"""
╔══❖•ೋ° 🌟 °ೋ•❖══╗

👋 Welcome @{user.username}

💰 Balance:
{bal} taka

✨ Select option below

╚══❖•ೋ° 🌟 °ೋ•❖══╝
"""

    send_message(
        chat_id,
        text,
        markup
    )

# ============================================
# START
# ============================================

@bot.message_handler(commands=['start'])
def start(message):

    add_user(message.from_user)

    if not is_joined(message.from_user.id):

        markup = types.InlineKeyboardMarkup()

        markup.add(

            types.InlineKeyboardButton(
                "📢 Join Channel 1",
                url=f"https://t.me/{CHANNEL_1.replace('@','')}"
            )

        )

        markup.add(

            types.InlineKeyboardButton(
                "📢 Join Channel 2",
                url=f"https://t.me/{CHANNEL_2.replace('@','')}"
            )

        )

        markup.add(

            types.InlineKeyboardButton(
                "✅ Verify",
                callback_data="verify"
            )

        )

        send_message(
            message.chat.id,
            "⚠️ Join all channels first",
            markup
        )

        return

    home(
        message.chat.id,
        message.from_user
    )

# ============================================
# ADMIN COMMAND
# ============================================

@bot.message_handler(commands=['admin'])
def admin(message):

    msg = bot.send_message(
        message.chat.id,
        "🔐 Enter Admin Password"
    )

    bot.register_next_step_handler(
        msg,
        admin_password
    )

# ============================================
# ADMIN PASSWORD
# ============================================

def admin_password(message):

    if message.text != ADMIN_PASSWORD:

        send_message(
            message.chat.id,
            "❌ Wrong Password"
        )

        return

    markup = types.InlineKeyboardMarkup()

    markup.add(

        types.InlineKeyboardButton(
            "👥 Users Database",
            callback_data="users_database"
        )

    )

    markup.add(

        types.InlineKeyboardButton(
            "📂 Ranges",
            callback_data="ranges"
        )

    )

    send_message(
        message.chat.id,
        "👑 ADMIN PANEL",
        markup
    )

# ============================================
# CALLBACKS
# ============================================

@bot.callback_query_handler(func=lambda call: True)
def callback(call):

    uid = call.from_user.id

    # ========================================
    # VERIFY
    # ========================================

    if call.data == "verify":

        if is_joined(uid):

            home(
                call.message.chat.id,
                call.from_user
            )

        else:

            bot.answer_callback_query(
                call.id,
                "❌ Join channels first"
            )

    # ========================================
    # USERS DATABASE
    # ========================================

    elif call.data == "users_database":

        cursor.execute("""
        SELECT
        name,
        username,
        balance,
        total_numbers,
        total_otps

        FROM users
        """)

        users = cursor.fetchall()

        if not users:

            send_message(
                call.message.chat.id,
                "❌ No Users Found"
            )

            return

        text = "👥 USERS DATABASE\n\n"

        for user in users:

            text += f"""
━━━━━━━━━━━━━━

👤 Name:
{user[0]}

🆔 Username:
@{user[1]}

💰 Balance:
{user[2]}

📱 Total Numbers:
{user[3]}

🔑 Total OTPs:
{user[4]}

━━━━━━━━━━━━━━
"""

        send_message(
            call.message.chat.id,
            text
        )

    # ========================================
    # RANGES PANEL
    # ========================================

    elif call.data == "ranges":

        cursor.execute("""
        SELECT range_text
        FROM ranges
        """)

        ranges = cursor.fetchall()

        markup = types.InlineKeyboardMarkup()

        for r in ranges:

            markup.add(

                types.InlineKeyboardButton(
                    r[0],
                    callback_data=f"remove_range_{r[0]}"
                )

            )

        markup.add(

            types.InlineKeyboardButton(
                "➕ Add Range",
                callback_data="add_range"
            )

        )

        send_message(
            call.message.chat.id,
            "📂 ALL RANGES",
            markup
        )

    # ========================================
    # ADD RANGE
    # ========================================

    elif call.data == "add_range":

        msg = bot.send_message(
            call.message.chat.id,
            "📥 Send New Range"
        )

        bot.register_next_step_handler(
            msg,
            add_range_process
        )

    # ========================================
    # REMOVE RANGE
    # ========================================

    elif call.data.startswith("remove_range_"):

        range_text = call.data.replace(
            "remove_range_",
            ""
        )

        markup = types.InlineKeyboardMarkup(
            row_width=2
        )

        markup.add(

            types.InlineKeyboardButton(
                "✅ Yes",
                callback_data=f"yes_remove_{range_text}"
            ),

            types.InlineKeyboardButton(
                "❌ No",
                callback_data="ranges"
            )

        )

        send_message(
            call.message.chat.id,
            f"""
⚠️ Remove This Range?

📂 {range_text}
""",
            markup
        )

    # ========================================
    # YES REMOVE
    # ========================================

    elif call.data.startswith("yes_remove_"):

        range_text = call.data.replace(
            "yes_remove_",
            ""
        )

        cursor.execute("""
        DELETE FROM ranges
        WHERE range_text=?
        """, (range_text,))

        db.commit()

        send_message(
            call.message.chat.id,
            f"""
✅ Range Removed

📂 {range_text}
"""
        )

    # ========================================
    # GET NUMBER
    # ========================================

    elif call.data == "get_number":

        cursor.execute("""
        SELECT range_text
        FROM ranges
        """)

        ranges = cursor.fetchall()

        markup = types.InlineKeyboardMarkup()

        for r in ranges:

            markup.add(

                types.InlineKeyboardButton(
                    r[0],
                    callback_data=f"range_{r[0]}"
                )

            )

        send_message(
            call.message.chat.id,
            "📱 Select Range",
            markup
        )

    # ========================================
    # SELECT RANGE
    # ========================================

    elif call.data.startswith("range_"):

        range_text = call.data.replace(
            "range_",
            ""
        )

        try:

            r = requests.post(
                BASE_URL + "/api/v1/numbers/get",

                json={
                    "range": range_text,
                    "format": "national"
                },

                headers=HEADERS
            )

            data = r.json()

            number = data["number"]

            number_id = data["number_id"]

            full_number = f"+228{number}"

            cursor.execute("""
            INSERT INTO numbers(
                user_id,
                number_id,
                number,
                range_text
            )

            VALUES(?,?,?,?)
            """, (

                uid,
                number_id,
                full_number,
                range_text

            ))

            cursor.execute("""
            UPDATE users
            SET total_numbers = total_numbers + 1
            WHERE user_id=?
            """, (uid,))

            db.commit()

            markup = types.InlineKeyboardMarkup(
                row_width=2
            )

            markup.add(

                types.InlineKeyboardButton(
                    "🔄 Change Number",
                    callback_data=f"range_{range_text}"
                ),

                types.InlineKeyboardButton(
                    "📂 Change Range",
                    callback_data="get_number"
                )

            )

            markup.add(

                types.InlineKeyboardButton(
                    "🟢 OTP Group",
                    url="https://t.me/muqeetxotp"
                )

            )

            text = f"""
╔══❖•ೋ° ☎️ °ೋ•❖══╗

🌍 Country:
Togo 🇹🇬

📱 Number:
<code>{full_number}</code>

⏰ Expire:
30 Minutes

🔍 Waiting For OTP...

╚══❖•ೋ° ☎️ °ೋ•❖══╝
"""

            send_message(
                call.message.chat.id,
                text,
                markup
            )

            threading.Thread(
                target=check_otp,
                args=(uid, number_id, full_number)
            ).start()

        except Exception as e:

            send_message(
                call.message.chat.id,
                f"❌ Error\n\n{e}"
            )

    # ========================================
    # WITHDRAW PANEL
    # ========================================

    elif call.data == "withdraw":

        markup = types.InlineKeyboardMarkup()

        markup.add(

            types.InlineKeyboardButton(
                "➕ Add Wallet",
                callback_data="add_wallet"
            )

        )

        markup.add(

            types.InlineKeyboardButton(
                "💸 Withdraw Money",
                callback_data="withdraw_money"
            )

        )

        send_message(
            call.message.chat.id,
            "💰 WITHDRAW PANEL",
            markup
        )

    # ========================================
    # ADD WALLET
    # ========================================

    elif call.data == "add_wallet":

        msg = bot.send_message(
            call.message.chat.id,
            "📥 Send TRC20 Wallet"
        )

        bot.register_next_step_handler(
            msg,
            save_wallet
        )

    # ========================================
    # WITHDRAW MONEY
    # ========================================

    elif call.data == "withdraw_money":

        cursor.execute("""
        SELECT balance
        FROM users
        WHERE user_id=?
        """, (uid,))

        bal = cursor.fetchone()[0]

        if bal < MIN_WITHDRAW:

            send_message(
                call.message.chat.id,
                "❌ Minimum Withdraw 100 Taka"
            )

            return

        msg = bot.send_message(
            call.message.chat.id,
            "💵 Enter Amount"
        )

        bot.register_next_step_handler(
            msg,
            withdraw_process
        )

# ============================================
# ADD RANGE PROCESS
# ============================================

def add_range_process(message):

    range_text = message.text

    try:

        cursor.execute("""
        INSERT INTO ranges(range_text)
        VALUES(?)
        """, (range_text,))

        db.commit()

        send_message(
            message.chat.id,
            f"""
✅ Range Added

📂 {range_text}
"""
        )

    except:

        send_message(
            message.chat.id,
            "❌ Range Already Exists"
        )

# ============================================
# SAVE WALLET
# ============================================

def save_wallet(message):

    cursor.execute("""
    UPDATE users
    SET wallet=?
    WHERE user_id=?
    """, (

        message.text,
        message.from_user.id

    ))

    db.commit()

    send_message(
        message.chat.id,
        "✅ Wallet Saved"
    )

# ============================================
# WITHDRAW PROCESS
# ============================================

def withdraw_process(message):

    amount = float(message.text)

    cursor.execute("""
    SELECT balance
    FROM users
    WHERE user_id=?
    """, (message.from_user.id,))

    bal = cursor.fetchone()[0]

    if amount > bal:

        send_message(
            message.chat.id,
            "❌ Insufficient Balance"
        )

        return

    cursor.execute("""
    UPDATE users
    SET balance = balance - ?
    WHERE user_id=?
    """, (

        amount,
        message.from_user.id

    ))

    db.commit()

    bot.send_message(
        WITHDRAW_GROUP_ID,

f"""
💸 NEW WITHDRAW REQUEST

👤 Name:
{message.from_user.first_name}

🆔 Username:
@{message.from_user.username}

💰 Amount:
{amount}

#muqeetwithdraw
"""
    )

    send_message(
        message.chat.id,
        """
✅ Withdraw Request Sent

⏳ Wait 24 Hours
"""
    )

# ============================================
# OTP CHECKER
# ============================================

def check_otp(user_id, number_id, number):

    country_name = "Togo"
    country_flag = "🇹🇬"

    hidden_number = (
        number[:6]
        + "xxxxx" +
        number[-3:]
    )

    for _ in range(300):

        time.sleep(2)

        try:

            s = requests.get(
                BASE_URL + f"/api/v1/numbers/{number_id}/sms",
                headers=HEADERS
            ).json()

            if s.get("otp"):

                otp = s["otp"]

                service = s.get(
                    "service",
                    "Unknown"
                )

                full_sms = s.get(
                    "full_sms",
                    "No Message"
                )

                markup = types.InlineKeyboardMarkup()

                markup.add(

                    types.InlineKeyboardButton(
                        "🤖 OTP BOT",
                        url="https://t.me/xamuqeet_bot"
                    )

                )

                bot.send_message(
                    OTP_GROUP_ID,

f"""
╔══❖•ೋ° 🔥 OTP RECEIVED 🔥 °ೋ•❖══╗

🌍 Country:
{country_name} {country_flag}

📱 Number:
<code>{hidden_number}</code>

🏢 Service:
{service}

🔑 OTP Code:
<code>{otp}</code>

📩 Full Message:
<code>{full_sms}</code>

╚══❖•ೋ° 🔥 °ೋ•❖══╝
""",

                    parse_mode="HTML",
                    reply_markup=markup
                )

                cursor.execute("""
                UPDATE users
                SET

                total_otps = total_otps + 1,

                balance = balance + ?

                WHERE user_id=?
                """, (

                    OTP_REWARD,
                    user_id

                ))

                db.commit()

                break

        except:
            pass

# ============================================
# RUN BOT
# ============================================

print("✅ BOT RUNNING")

bot.infinity_polling()
