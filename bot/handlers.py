from __future__ import annotations

from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from bot.keyboards import (
    finalize_inline,
    inline_home_menu,
    operations_menu,
    reply_home_menu,
    selectable_buttons,
    selectable_rows,
    text_confirm_inline,
)
from bot.workflow import BotState, PendingOperation, SessionManager, analyze_workbook, apply_operation, get_sheet_map, save_working_copy
from config import ADMIN_ID

session_manager = SessionManager()


def _is_excel_file(name: str) -> bool:
    lower = name.lower()
    return lower.endswith(".xlsx") or lower.endswith(".xlsm")


async def _send_home(update: Update, chat_id: int):
    session = session_manager.get(chat_id)
    is_admin = chat_id == ADMIN_ID
    if session.ui_mode == "reply":
        await update.effective_message.reply_text("🏠 منوی اصلی", reply_markup=reply_home_menu(is_admin))
    else:
        await update.effective_message.reply_text("🏠 منوی اصلی", reply_markup=inline_home_menu(is_admin))


def _analysis_text(analysis: dict) -> str:
    lines = ["✅ فایل تحلیل شد.", f"تعداد شیت‌ها: {len(analysis['sheets'])}"]
    for sheet in analysis["sheets"]:
        lines.append(
            f"- شیت: {sheet['name']} | سطر: {sheet['rows']} | ستون: {sheet['cols']} | هدرها: {', '.join(str(h) for h in sheet['headers'])}"
        )
    lines.append("حالا انتخاب کن چه عملیاتی انجام بدم.")
    return "\n".join(lines)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    session = session_manager.get(chat_id)

    if session.original_file_name:
        await update.message.reply_text(
            f"ℹ️ فایل قبلی هنوز در سشن موجود است: {session.original_file_name}\n"
            "اگر بخوای می‌تونی ادامه بدی یا فایل جدید بفرستی."
        )

    await _send_home(update, chat_id)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    session = session_manager.get(chat_id)

    document = update.message.document
    if not document or not document.file_name or not _is_excel_file(document.file_name):
        await update.message.reply_text("❌ فقط فایل اکسل با پسوند xlsx/xlsm پشتیبانی می‌شود.")
        return

    telegram_file = await context.bot.get_file(document.file_id)
    file_bytes = await telegram_file.download_as_bytearray()

    session.original_file_name = document.file_name
    session.original_bytes = bytes(file_bytes)
    session.working_bytes = bytes(file_bytes)
    session.op_stack.clear()
    session.undo_stack.clear()
    session.pending = None

    analysis = analyze_workbook(session.working_bytes)
    session.selected_sheet = analysis["sheets"][0]["name"] if analysis["sheets"] else None
    session.state = BotState.ANALYZED

    await update.message.reply_text(_analysis_text(analysis), reply_markup=operations_menu())


async def _begin_operation(update: Update, chat_id: int, op_kind: str, target_kind: str, mode: str):
    session = session_manager.get(chat_id)
    if not session.working_bytes or not session.selected_sheet:
        await update.effective_message.reply_text("ابتدا فایل اکسل ارسال کن.")
        return

    session.pending = PendingOperation(op_kind=op_kind, target_kind=target_kind, mode=mode)
    headers, rows = get_sheet_map(session.working_bytes, session.selected_sheet)

    if target_kind == "column":
        session.state = BotState.SELECT_COLUMN
        await update.effective_message.reply_text(
            "برای عملیات روی ستون، ستون(ها) را انتخاب کنید.",
            reply_markup=selectable_buttons("column", headers, session.pending.selected, "ستون"),
        )
    else:
        session.state = BotState.SELECT_ROW
        await update.effective_message.reply_text(
            "برای عملیات روی سطر، سطر(ها) را انتخاب کنید.",
            reply_markup=selectable_rows("row", rows, session.pending.selected),
        )


async def _toggle_selection(update: Update, chat_id: int, kind: str, idx: int):
    session = session_manager.get(chat_id)
    if not session.pending:
        await update.effective_message.reply_text("عملیات فعالی وجود ندارد.")
        return

    if session.pending.mode == "single":
        session.pending.selected = {idx}
    else:
        if idx in session.pending.selected:
            session.pending.selected.remove(idx)
        else:
            session.pending.selected.add(idx)

    headers, rows = get_sheet_map(session.working_bytes, session.selected_sheet)
    if kind == "column":
        await update.effective_message.reply_text(
            "انتخاب ستون‌ها به‌روزرسانی شد.",
            reply_markup=selectable_buttons("column", headers, session.pending.selected, "ستون"),
        )
    else:
        await update.effective_message.reply_text(
            "انتخاب سطرها به‌روزرسانی شد.",
            reply_markup=selectable_rows("row", rows, session.pending.selected),
        )


async def _confirm_selection(update: Update, chat_id: int):
    session = session_manager.get(chat_id)
    if not session.pending or not session.pending.selected:
        await update.effective_message.reply_text("حداقل یک مورد را انتخاب کن.")
        return

    if session.pending.op_kind == "delete":
        session.state = BotState.CONFIRM_OPERATION
        await update.effective_message.reply_text(
            "عملیات حذف انتخاب شد. برای ثبت در stack روی تایید نهایی کلیک کن.",
            reply_markup=finalize_inline(),
        )
        return

    session.state = BotState.INPUT_TEXT
    if session.pending.mode == "group":
        await update.effective_message.reply_text(
            "متن‌ها را خط‌به‌خط بفرست.\nمی‌توانی چند پیام متوالی بفرستی.\nبرای تایید نهایی از دکمه «✅ تایید متن» استفاده کن.",
            reply_markup=reply_home_menu(chat_id == ADMIN_ID),
        )
    else:
        await update.effective_message.reply_text("متن موردنظر را بفرست، سپس تایید کن.", reply_markup=text_confirm_inline())


async def _register_operation(update: Update, chat_id: int):
    session = session_manager.get(chat_id)
    if not session.pending:
        await update.effective_message.reply_text("عملیات فعالی نیست.")
        return

    if session.pending.op_kind in {"add", "edit"} and not session.pending.payload_lines:
        await update.effective_message.reply_text("برای این عملیات باید متن ارسال کنید.")
        return

    session.op_stack.append(session.pending)
    session.pending = None
    session.state = BotState.READY_TO_SAVE

    await update.effective_message.reply_text(
        f"✅ عملیات در صف ذخیره شد. تعداد عملیات معلق: {len(session.op_stack)}",
        reply_markup=finalize_inline(),
    )


async def _save_final(update: Update, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    session = session_manager.get(chat_id)
    if not session.working_bytes or not session.original_file_name:
        await update.effective_message.reply_text("فایل فعالی وجود ندارد.")
        return
    if not session.op_stack:
        await update.effective_message.reply_text("هیچ عملیاتی برای ذخیره وجود ندارد.")
        return

    current = session.working_bytes
    try:
        for op in session.op_stack:
            session.undo_stack.append(current)
            current = apply_operation(current, session.selected_sheet, op)
    except Exception as exc:  # noqa: BLE001
        # اعتبارسنجی ایندکس منقضی و ...
        session.undo_stack.clear()
        await update.effective_message.reply_text(f"❌ خطا در اعمال عملیات: {exc}")
        headers, rows = get_sheet_map(session.working_bytes, session.selected_sheet)
        await update.effective_message.reply_text(
            f"ساختار جدید فایل:\nستون‌ها: {len(headers)} | سطرها: {len(rows) + 1}",
            reply_markup=operations_menu(),
        )
        return

    session.working_bytes = current
    out_path = save_working_copy(current, session.original_file_name)
    await context.bot.send_document(
        chat_id=chat_id,
        document=out_path.open("rb"),
        filename=session.original_file_name,
        caption="✅ فایل نهایی ذخیره و ارسال شد.",
    )

    session_manager.clear_after_save(chat_id)


async def _undo(update: Update, chat_id: int):
    session = session_manager.get(chat_id)
    if not session.op_stack:
        await update.effective_message.reply_text("Undo فقط تا قبل از ذخیره نهایی مجاز است. عملیات معلقی وجود ندارد.")
        return
    removed = session.op_stack.pop()
    await update.effective_message.reply_text(
        f"↩️ آخرین عملیات صف حذف شد: {removed.op_kind}/{removed.target_kind}/{removed.mode}.\n"
        f"عملیات باقی‌مانده: {len(session.op_stack)}"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()
    session = session_manager.get(chat_id)

    if text in {"/start", "🏠 منوی اصلی"}:
        await start(update, context)
        return

    if text == "🧭 حالت شناور":
        session.ui_mode = "inline"
        await update.message.reply_text("✅ حالت شناور فعال شد")
        await _send_home(update, chat_id)
        return

    if text == "⌨️ حالت فیزیکی":
        session.ui_mode = "reply"
        await update.message.reply_text("✅ حالت فیزیکی فعال شد", reply_markup=reply_home_menu(chat_id == ADMIN_ID))
        return

    if text == "📊 آنالیز اکسل":
        if not session.working_bytes:
            session.state = BotState.WAIT_FILE
            await update.message.reply_text("لطفاً فایل اکسل را ارسال کن تا تحلیل هوشمند انجام شود.")
            return
        analysis = analyze_workbook(session.working_bytes)
        session.state = BotState.ANALYZED
        await update.message.reply_text(_analysis_text(analysis), reply_markup=operations_menu())
        return

    if text == "💾 ذخیره نهایی و دریافت فایل":
        await _save_final(update, chat_id, context)
        return

    if text == "↩️ Undo":
        await _undo(update, chat_id)
        return

    if text == "📚 راهنما":
        await update.message.reply_text(
            "راهنمای سریع:\n"
            "1) فایل اکسل بفرست\n"
            "2) آنالیز اکسل\n"
            "3) عملیات (افزودن/حذف/ادیت)\n"
            "4) تایید عملیات‌ها\n"
            "5) ذخیره نهایی و دریافت فایل"
        )
        return

    if session.state == BotState.INPUT_TEXT and session.pending:
        if text == "":
            await update.message.reply_text("متن خالی ثبت نمی‌شود.")
            return
        session.pending.payload_lines.append(text)
        await update.message.reply_text(
            f"✅ متن دریافت شد. تعداد خطوط فعلی: {len(session.pending.payload_lines)}\n"
            "در صورت اتمام، روی دکمه ✅ تایید متن بزن.",
            reply_markup=text_confirm_inline(),
        )
        return

    await update.message.reply_text("ورودی نامعتبر برای وضعیت فعلی. از منو استفاده کن.")


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat.id
    data = query.data
    session = session_manager.get(chat_id)

    if data == "nav:home":
        await _send_home(update, chat_id)
        return

    if data == "file:request":
        session.state = BotState.WAIT_FILE
        await query.message.reply_text("📤 فایل اکسل (.xlsx/.xlsm) را ارسال کن.")
        return

    if data == "excel:analyze":
        if not session.working_bytes:
            await query.message.reply_text("ابتدا فایل اکسل را ارسال کن.")
            return
        analysis = analyze_workbook(session.working_bytes)
        session.state = BotState.ANALYZED
        await query.message.reply_text(_analysis_text(analysis), reply_markup=operations_menu())
        return

    if data == "op:menu":
        if not session.working_bytes:
            await query.message.reply_text("ابتدا فایل اکسل را ارسال کن.")
            return
        session.state = BotState.SELECT_OPERATION
        await query.message.reply_text("نوع عملیات را انتخاب کن:", reply_markup=operations_menu())
        return

    if data.startswith("op:"):
        _, op_kind, target_kind, mode = data.split(":", 3)
        await _begin_operation(update, chat_id, op_kind, target_kind, mode)
        return

    if data.startswith("toggle:"):
        _, kind, idx = data.split(":", 2)
        await _toggle_selection(update, chat_id, kind, int(idx))
        return

    if data.startswith("confirm:"):
        await _confirm_selection(update, chat_id)
        return

    if data == "confirm:text":
        await _register_operation(update, chat_id)
        return

    if data == "cancel:op":
        session.pending = None
        session.state = BotState.SELECT_OPERATION
        await query.message.reply_text("❎ عملیات لغو شد.", reply_markup=operations_menu())
        return

    if data == "save:final":
        await _save_final(update, chat_id, context)
        return

    if data == "undo:last":
        await _undo(update, chat_id)
        return

    if data == "ui:inline":
        session.ui_mode = "inline"
        await query.message.reply_text("✅ حالت شناور فعال شد", reply_markup=inline_home_menu(chat_id == ADMIN_ID))
        return

    if data == "ui:reply":
        session.ui_mode = "reply"
        await query.message.reply_text("✅ حالت فیزیکی فعال شد", reply_markup=reply_home_menu(chat_id == ADMIN_ID))
        return

    if data == "nav:help":
        await query.message.reply_text("برای شروع، فایل اکسل را ارسال کن و سپس آنالیز اکسل را بزن.")
        return

    if data == "nav:admin":
        if chat_id != ADMIN_ID:
            await query.message.reply_text("⛔ دسترسی غیرمجاز")
            return
        await query.message.reply_text("⚙️ مدیر: این بخش قابل توسعه است.")
        return

    await query.message.reply_text("گزینه نامعتبر")
