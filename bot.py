import os
import csv
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# 🛠️ Cấu hình
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))  # Thay bằng Telegram ID thật của bạn

# 📂 File lưu trạng thái phản hồi
REPLY_FILE = "reply_targets.json"

# 🧠 Load trạng thái reply
def load_reply_targets():
    if os.path.exists(REPLY_FILE):
        with open(REPLY_FILE, "r") as f:
            return json.load(f)
    return {}

# 💾 Save trạng thái reply
def save_reply_targets(data):
    with open(REPLY_FILE, "w") as f:
        json.dump(data, f)

# 🧾 Lưu log tin nhắn
def log_message(user_id, username, message):
    with open("messages_log.csv", "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([datetime.now().isoformat(), user_id, username, message])

# ✅ Xử lý lệnh /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Xin chào! Gửi mình tin nhắn gì đó nhé.")

# ✅ Xử lý tin nhắn từ người dùng
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "Không có username"
    message = update.message.text

    # Trả lời người dùng
    await update.message.reply_text("✅ Đã nhận tin nhắn của bạn!")

    # Gửi về admin
    admin_text = f"📩 Tin nhắn từ @{username} (ID: {user_id}):\n\n{message}"

    # Nút trả lời lại
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔁 Trả lời lại", callback_data=f"reply_to:{user_id}")]
    ])

    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, reply_markup=keyboard)

    # Ghi log
    log_message(user_id, username, message)

# ✅ Xử lý khi admin nhấn nút "Trả lời lại"
async def reply_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("reply_to:"):
        target_user_id = int(data.split(":")[1])
        admin_id = query.from_user.id

        # Lưu trạng thái admin đang trả lời cho ai
        reply_targets = load_reply_targets()
        reply_targets[str(admin_id)] = target_user_id
        save_reply_targets(reply_targets)

        await query.message.reply_text("💬 Nhập nội dung bạn muốn gửi cho người dùng này:")

# ✅ Xử lý tin nhắn phản hồi từ admin
async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.message.from_user.id
    reply_targets = load_reply_targets()

    if str(admin_id) in reply_targets:
        target_user_id = reply_targets.pop(str(admin_id))
        save_reply_targets(reply_targets)

        message = update.message.text

        try:
            await context.bot.send_message(chat_id=target_user_id, text=f"📬 Phản hồi từ admin:\n\n{message}")
            await update.message.reply_text("✅ Đã gửi phản hồi đến người dùng.")
        except Exception as e:
            await update.message.reply_text(f"❌ Không gửi được tin nhắn: {e}")
    else:
        await update.message.reply_text("⚠️ Bạn chưa chọn người dùng để trả lời.")

# ✅ Main app
if __name__ == '__main__':
    if not BOT_TOKEN:
        print("⚠️ BOT_TOKEN chưa được thiết lập.")
        exit(1)

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(reply_button))
    app.add_handler(MessageHandler(filters.TEXT & filters.USER(ADMIN_ID), handle_admin_reply))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot đang chạy...")
    app.run_polling()
