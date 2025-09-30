from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from PIL import Image, ImageDraw, ImageFont

import os
import logging

# تنظیم لاگ‌گیری
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    logger.error("❌ توکن ربات پیدا نشد! مطمئن شو متغیر محیطی رو روی Render ست کردی.")
    TOKEN = "YOUR_FALLBACK_TOKEN"

# =========================================================================
# ⚙️ تنظیمات اصلی و مختصات (مهم‌ترین بخش برای ویرایش)
# =========================================================================

# ۱. لیست کاربران مجاز (شامل کاربر جدید 6433828400)
ALLOWED_USERS = [6059296496, 6433828400]

# ۲. تعریف مسیر فونت
FONT_PATH = "fonts/IRANSansXFaNum-LightD4.ttf"

# ۳. تنظیمات مختصات، اندازه فونت و رنگ برای هر خط
# (توجه: با حذف bidi/reshaper، باید از فونتی استفاده کنید که به طور پیش‌فرض اتصال حروف خوبی داشته باشد)
LINE_CONFIGS = {
    "date": {
        "text_prefix": "تاریخ بارگیری: ",
        "x_position": 1150, # مختصات X (برای چینش RTL)
        "y_position": 50,    # مختصات Y
        "font_size": 48,
        "color": "navy"
    },
    "dest": {
        "text_prefix": "مقصد: ",
        "x_position": 1150,
        "y_position": 150,
        "font_size": 48, 
        "color": "navy"
    },
    "product": {
        "text_prefix": "نوع فرآورده: ",
        "x_position": 1150,
        "y_position": 250,
        "font_size": 48,
        "color": "navy"
    }
}
# توجه: x_position در اینجا نقطه مرجع راست متن است.

# =========================================================================
# 🤖 منطق ربات
# =========================================================================

# مراحل گفتگو
DATE, DEST, PRODUCT = range(3)

# --- تابع کمکی برای نوشتن راست به چپ (اصلی شما) ---
def draw_text_rtl(draw, position, text, font, fill):
    """
    متن را بر اساس موقعیت X (که نقطه راست متن است) چینش راست به چپ می‌کند.
    """
    # محاسبه عرض متن
    text_width = draw.textlength(text, font=font)
    # نقطه شروع نگارش (X اصلی - عرض متن)
    x, y = position
    draw.text((x - text_width, y), text, font=font, fill=fill)


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
    try:
        context.user_data["product"] = update.message.text

        template_path = "templates/template.png"
        
        if not os.path.exists(template_path):
            await update.message.reply_text(f"خطا: فایل تمپلیت در مسیر '{template_path}' پیدا نشد.")
            return ConversationHandler.END
        if not os.path.exists(FONT_PATH):
            await update.message.reply_text(f"خطا: فایل فونت در مسیر '{FONT_PATH}' پیدا نشد.")
            return ConversationHandler.END

        # باز کردن تمپلیت
        img = Image.open(template_path)
        draw = ImageDraw.Draw(img)

        # 1. درج تاریخ
        config_date = LINE_CONFIGS["date"]
        font_date = ImageFont.truetype(FONT_PATH, config_date["font_size"])
        text_date = f"{config_date['text_prefix']}{context.user_data['date']}"
        draw_text_rtl(
            draw, 
            (config_date['x_position'], config_date['y_position']), 
            text_date, 
            font_date, 
            config_date['color']
        )
        
        # 2. درج مقصد
        config_dest = LINE_CONFIGS["dest"]
        font_dest = ImageFont.truetype(FONT_PATH, config_dest["font_size"])
        text_dest = f"{config_dest['text_prefix']}{context.user_data['dest']}"
        draw_text_rtl(
            draw, 
            (config_dest['x_position'], config_dest['y_position']), 
            text_dest, 
            font_dest, 
            config_dest['color']
        )
        
        # 3. درج فرآورده
        config_product = LINE_CONFIGS["product"]
        font_product = ImageFont.truetype(FONT_PATH, config_product["font_size"])
        text_product = f"{config_product['text_prefix']}{context.user_data['product']}"
        draw_text_rtl(
            draw, 
            (config_product['x_position'], config_product['y_position']), 
            text_product, 
            font_product, 
            config_product['color']
        )

        output_path = "output.jpg"
        img.save(output_path)

        with open(output_path, "rb") as photo_file:
            await update.message.reply_photo(photo=photo_file)
            
    except Exception as e:
        logger.error(f"Error in get_product: {e}")
        await update.message.reply_text(f"❌ خطایی در پردازش رخ داد: {e}")

    return ConversationHandler.END

# لغو
async def cancel(update: Update, context):
    await update.message.reply_text("❌ عملیات لغو شد.")
    return ConversationHandler.END

def main():
    """راه‌اندازی ربات."""
    app = Application.builder().token(TOKEN).build()
    logger.info("ربات با موفقیت ساخته شد.")

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
    logger.info("شروع گوش دادن به پیام‌ها (Polling)...")
    app.run_polling(poll_interval=1.0)

if __name__ == "__main__":
    main()
