from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

def main_menu(is_admin=False):
    keyboard = [
        [KeyboardButton("📊 آنالیز اکسل"), KeyboardButton("✏️ ویرایش اکسل")],
        [KeyboardButton("📚 راهنما")]
    ]
    if is_admin:
        keyboard.append([KeyboardButton("⚙️ مدیریت")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def edit_options(columns):
    # دکمه‌های شناور بر اساس ستون‌ها
    buttons = []
    for col in columns:
        buttons.append([InlineKeyboardButton(f"{col} ↑%", callback_data=f"inc:{col}")])
        buttons.append([InlineKeyboardButton(f"{col} ↓%", callback_data=f"dec:{col}")])
        buttons.append([InlineKeyboardButton(f"{col} حذف", callback_data=f"del:{col}")])
    return InlineKeyboardMarkup(buttons)

def admin_options():
    # تنظیمات ماژولار مدیر
    buttons = [
        [InlineKeyboardButton("➕ اضافه کردن دکمه", callback_data="admin:add_button")],
        [InlineKeyboardButton("✏️ ویرایش دکمه‌ها", callback_data="admin:edit_button")],
        [InlineKeyboardButton("🗑 حذف دکمه", callback_data="admin:delete_button")]
    ]
    return InlineKeyboardMarkup(buttons)
