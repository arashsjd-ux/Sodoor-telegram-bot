from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from PIL import Image, ImageDraw, ImageFont

TOKEN = "8365532605:AAGpYT5-XQMCFxx6jdzBxOuX9RM1eDACuRY"
ALLOWED_USERS = [989134238719] # آیدی عددی تلگرام خودت و دوستانت

# مراحل گفتگو
DATE, DEST, PRODUCT = range(3)

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
img = Image.open("template.jpg")
draw = ImageDraw.Draw(img)
font = ImageFont.truetype("B Nazanin.ttf", 40)

# درج متن‌ها (مختصات تقریبی)
draw.text((150, 50), f"تاریخ بارگیری: {
    context.user_data['date']}", font = font, fill = "navy")
draw.text((150, 150), f"مقصد: {
    context.user_data['dest']}", font = font, fill = "navy")
draw.text((150, 250), f"نوع فرآورده: {
    context.user_data['product']}", font = font, fill = "navy")

img.save("output.jpg")

await update.message.reply_photo(photo = open("output.jpg", "rb"))
return ConversationHandler.END

# لغو
async def cancel(update: Update, context):
await update.message.reply_text("❌ عملیات لغو شد.")
return ConversationHandler.END

def main():
app = Application.builder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points = [CommandHandler("start", start)],
    states = {
        DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date)],
        DEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_dest)],
        PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_product)],
    },
    fallbacks = [CommandHandler("cancel", cancel)],
)

app.add_handler(conv_handler)
app.run_polling()

if __name__ == "__main__":
main()