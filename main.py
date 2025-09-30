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
    # در محیط Render این متغیر باید تنظیم شده باشد
    logger.error("❌ توکن ربات پیدا نشد! مطمئن شو متغیر محیطی رو روی Render ست کردی.")
    TOKEN = "YOUR_FALLBACK_TOKEN"

# =========================================================================
# ⚙️ تنظیمات اصلی و مختصات (مهم‌ترین بخش برای ویرایش)
# =========================================================================

# ۱. افزودن کاربر جدید
ALLOWED_USERS = [6059296496, 6433828400]

# ۲. تعریف تنظیمات برای هر خط
FONT_PATH = "fonts/IRANSansXFaNum-LightD4.ttf" # مسیر فونت اصلی

# تعریف تنظیمات (مختصات، اندازه فونت و عرض باکس) برای هر خط
# (X_Start: مختصات شروع نگارش از سمت چپ کادر متنی برای محاسبه RTL)
LINE_CONFIGS = {
    "date": {
        "text_prefix": "تاریخ بارگیری: ",
        "x_start": 150, # مختصات X شروع کادر متنی
        "y_position": 50, # مختصات Y
        "font_size": 48,
        "box_width": 1000, # عرض کادر متنی (برای محاسبه چینش راست به چپ)
        "color": "navy"
    },
    "dest": {
        "text_prefix": "مقصد: ",
        "x_start": 150,
        "y_position": 150,
        "font_size": 55, # مثال: فونت بزرگتر برای خط دوم
        "box_width": 1000,
        "color": "black"
    },
    "product": {
        "text_prefix": "نوع فرآورده: ",
        "x_start": 150,
        "y_position": 250,
        "font_size": 48,
        "box_width": 1000,
        "color": "#333333" # استفاده از کد رنگ
    }
}

# =========================================================================
# 🤖 منطق ربات
# =========================================================================

# مراحل گفتگو
DATE, DEST, PRODUCT = range(3)

# --- تابع کمکی برای نوشتن راست به چپ با قابلیت اتصال حروف ---
def draw_text_rtl(draw, position, text, font, fill, box_width):
    """
    متن فارسی را ابتدا reshaped (اتصال حروف) و سپس Bidi (چینش راست به چپ) کرده و روی تصویر می‌کشد.
    """
    # ۱. اتصال حروف فارسی (Reshape)
    reshaped_text = arabic_reshaper.reshape(text)
    # ۲. چینش راست به چپ (Bidi)
    bidi_text = get_display(reshaped_text)

    # محاسبه عرض متن برای متن Bidi شده
    text_width = draw.textlength(bidi_text, font=font)
    # نقطه شروع از سمت راست باکس تعیین شده
    x, y = position
    
    # توجه: نگارش از نقطه (x_start + box_width - text_width) انجام می‌شود 
    # تا متن در عرض 'box_width' از سمت راست تراز شود.
    draw.text((x + box_width - text_width, y), bidi_text, font=font, fill=fill)

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
            (config_date['x_start'], config_date['y_position']), 
            text_date, 
            font_date, 
            config_date['color'], 
            config_date['box_width']
        )
        
        # 2. درج مقصد
        config_dest = LINE_CONFIGS["dest"]
        font_dest = ImageFont.truetype(FONT_PATH, config_dest["font_size"])
        text_dest = f"{config_dest['text_prefix']}{context.user_data['dest']}"
        draw_text_rtl(
            draw, 
            (config_dest['x_start'], config_dest['y_position']), 
            text_dest, 
            font_dest, 
            config_dest['color'], 
            config_dest['box_width']
        )
        
        # 3. درج فرآورده
        config_product = LINE_CONFIGS["product"]
        font_product = ImageFont.truetype(FONT_PATH, config_product["font_size"])
        text_product = f"{config_product['text_prefix']}{context.user_data['product']}"
        draw_text_rtl(
            draw, 
            (config_product['x_start'], config_product['y_position']), 
            text_product, 
            font_product, 
            config_product['color'], 
            config_product['box_width']
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
