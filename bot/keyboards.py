from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


def reply_home_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton("🏠 منوی اصلی"), KeyboardButton("📊 آنالیز اکسل")],
        [KeyboardButton("🧭 حالت شناور"), KeyboardButton("⌨️ حالت فیزیکی")],
        [KeyboardButton("📚 راهنما")],
        [KeyboardButton("💾 ذخیره نهایی و دریافت فایل"), KeyboardButton("↩️ Undo")],
    ]
    if is_admin:
        rows.append([KeyboardButton("⚙️ مدیریت")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def inline_home_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("📤 ارسال فایل اکسل", callback_data="file:request")],
        [InlineKeyboardButton("📊 آنالیز اکسل", callback_data="excel:analyze")],
        [InlineKeyboardButton("🧩 عملیات روی فایل", callback_data="op:menu")],
        [InlineKeyboardButton("💾 ذخیره نهایی و دریافت فایل", callback_data="save:final")],
        [InlineKeyboardButton("↩️ Undo", callback_data="undo:last")],
        [InlineKeyboardButton("📚 راهنما", callback_data="nav:help")],
        [
            InlineKeyboardButton("🧭 شناور", callback_data="ui:inline"),
            InlineKeyboardButton("⌨️ فیزیکی", callback_data="ui:reply"),
        ],
    ]
    if is_admin:
        rows.append([InlineKeyboardButton("⚙️ مدیریت", callback_data="nav:admin")])
    return InlineKeyboardMarkup(rows)


def operations_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("➕ افزودن تکی به ستون", callback_data="op:add:column:single")],
            [InlineKeyboardButton("➕ افزودن گروهی به ستون", callback_data="op:add:column:group")],
            [InlineKeyboardButton("➕ افزودن تکی به سطر", callback_data="op:add:row:single")],
            [InlineKeyboardButton("➕ افزودن گروهی به سطر", callback_data="op:add:row:group")],
            [InlineKeyboardButton("🗑 حذف تکی از ستون", callback_data="op:delete:column:single")],
            [InlineKeyboardButton("🗑 حذف گروهی از ستون", callback_data="op:delete:column:group")],
            [InlineKeyboardButton("🗑 حذف تکی از سطر", callback_data="op:delete:row:single")],
            [InlineKeyboardButton("🗑 حذف گروهی از سطر", callback_data="op:delete:row:group")],
            [InlineKeyboardButton("✏️ ادیت تکی ستون", callback_data="op:edit:column:single")],
            [InlineKeyboardButton("✏️ ادیت گروهی ستون", callback_data="op:edit:column:group")],
            [InlineKeyboardButton("✏️ ادیت تکی سطر", callback_data="op:edit:row:single")],
            [InlineKeyboardButton("✏️ ادیت گروهی سطر", callback_data="op:edit:row:group")],
            [InlineKeyboardButton("⬅️ بازگشت", callback_data="nav:home")],
        ]
    )


def selectable_buttons(prefix: str, items: list[str], selected: set[int], title_prefix: str) -> InlineKeyboardMarkup:
    rows = []
    for idx, label in enumerate(items, start=1):
        marker = "✅" if idx in selected else "🔘"
        rows.append([InlineKeyboardButton(f"{marker} {title_prefix} {idx}: {label}", callback_data=f"toggle:{prefix}:{idx}")])

    rows.extend(
        [
            [InlineKeyboardButton("✔️ تایید", callback_data=f"confirm:{prefix}"), InlineKeyboardButton("✖️ لغو", callback_data="cancel:op")],
            [InlineKeyboardButton("⬅️ بازگشت", callback_data="op:menu")],
        ]
    )
    return InlineKeyboardMarkup(rows)


def selectable_rows(prefix: str, rows_idx: list[int], selected: set[int]) -> InlineKeyboardMarkup:
    labels = [f"Row {i}" for i in rows_idx]
    return selectable_buttons(prefix, labels, selected, "سطر")


def finalize_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("💾 ذخیره نهایی و دریافت فایل", callback_data="save:final")],
            [InlineKeyboardButton("↩️ Undo", callback_data="undo:last")],
            [InlineKeyboardButton("⬅️ خانه", callback_data="nav:home")],
        ]
    )


def text_confirm_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ تایید متن", callback_data="confirm:text")],
            [InlineKeyboardButton("✖️ لغو عملیات", callback_data="cancel:op")],
            [InlineKeyboardButton("⬅️ بازگشت", callback_data="op:menu")],
        ]
    )
