from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from PIL import Image, ImageDraw, ImageFont

import os

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ توکن ربات پیدا نشد! مطمئن شو متغیر محیطی رو روی Render ست کردی.")
ALLOWED_USERS = [6059296496]  # آیدی عددی مجازها

# مراحل گفتگو
DATE, DEST, PRODUCT = range(3)

# --- تابع کمکی برای نوشتن راست به چپ ---
def draw_text_rtl(draw, position, text, font, fill, box_width):
    # محاسبه عرض متن
    text_width = draw.textlength(text, font=font)
    # نقطه شروع از سمت راست باکس
    x, y = position
    draw.text((x + box_width - text_width, y), text, font=font, fill=fill)

# شروع ربات
async def start(update: Update, context):
    user_id = update.message.from_user.id
    if user_id not in ALLOWED_USERS:
        await update.message.reply_text("⛔ شما مجاز به استفاده از این ربات نیستید.")
        return ConversationHandler.END

    await update.message.reply_text("📅 لطفا تاریخ بارگیری را وارد کنید:")
    return DATE

# گرفتن تاریخ
async def get_date(update: Update, context):
    context.user_data["date"] = update.message.text
    await update.message.reply_text("📍 لطفا مقصد را وارد کنید:")
    return DEST

# گرفتن مقصد
async def get_dest(update: Update, context):
    context.user_data["dest"] = update.message.text
    await update.message.reply_text("🛢️ لطفا نوع فرآورده را وارد کنید:")
    return PRODUCT

# گرفتن فرآورده و ساخت عکس
async def get_product(update: Update, context):
    context.user_data["product"] = update.message.text

    # باز کردن تمپلیت
    img = Image.open("templates/template.png")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("fonts/IRANSansXFaNum-LightD4.ttf", 48)

    # باکس عرض برای چینش راست به چپ
    box_width = 1000  

    # درج متن‌ها
    draw_text_rtl(draw, (150, 50), f"تاریخ بارگیری: {context.user_data['date']}", font, "navy", box_width)
    draw_text_rtl(draw, (150, 150), f"مقصد: {context.user_data['dest']}", font, "navy", box_width)
    draw_text_rtl(draw, (150, 250), f"نوع فرآورده: {context.user_data['product']}", font, "navy", box_width)

    img.save("output.jpg")

    await update.message.reply_photo(photo=open("output.jpg", "rb"))
    return ConversationHandler.END

# لغو
async def cancel(update: Update, context):
    await update.message.reply_text("❌ عملیات لغو شد.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date)],
            DEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_dest)],
            PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_product)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
