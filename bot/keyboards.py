from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


def reply_home_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton("🏠 منوی اصلی"), KeyboardButton("📊 آنالیز اکسل")],
        [KeyboardButton("🤖 دستیار هوشمند"), KeyboardButton("📚 راهنما")],
        [KeyboardButton("🧭 منوی شناور"), KeyboardButton("⌨️ منوی فیزیکی")],
    ]
    if is_admin:
        rows.append([KeyboardButton("⚙️ مدیریت")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def inline_home_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("📊 اکسل", callback_data="nav:excel")],
        [InlineKeyboardButton("🤖 دستیار هوشمند", callback_data="nav:ai")],
        [InlineKeyboardButton("📚 راهنما", callback_data="nav:help")],
        [
            InlineKeyboardButton("🧭 شناور", callback_data="ui:inline"),
            InlineKeyboardButton("⌨️ فیزیکی", callback_data="ui:reply"),
        ],
    ]
    if is_admin:
        rows.append([InlineKeyboardButton("⚙️ مدیریت", callback_data="nav:admin")])
    return InlineKeyboardMarkup(rows)


def inline_excel_menu(columns: dict | None = None) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("🔎 تحلیل فایل", callback_data="excel:analyze")],
        [InlineKeyboardButton("⬅️ بازگشت", callback_data="nav:home")],
    ]

    if columns:
        for col in columns:
            rows.append(
                [
                    InlineKeyboardButton(f"➕ {col} 10%", callback_data=f"inc:{col}"),
                    InlineKeyboardButton(f"➖ {col} 10%", callback_data=f"dec:{col}"),
                ]
            )
            rows.append([InlineKeyboardButton(f"🗑 حذف {col}", callback_data=f"del:{col}")])
        rows.append([InlineKeyboardButton("⬅️ منوی اکسل", callback_data="nav:excel")])
    return InlineKeyboardMarkup(rows)


def inline_ai_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✍️ ارسال دستور متنی", callback_data="ai:text")],
            [InlineKeyboardButton("🧪 نمونه دستور", callback_data="ai:examples")],
            [InlineKeyboardButton("⬅️ بازگشت", callback_data="nav:home")],
        ]
    )


def inline_admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📈 وضعیت ربات", callback_data="admin:status")],
            [InlineKeyboardButton("🔐 تنظیمات امنیتی", callback_data="admin:security")],
            [InlineKeyboardButton("⬅️ بازگشت", callback_data="nav:home")],
        ]
    )
