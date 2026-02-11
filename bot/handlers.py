from __future__ import annotations

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
from logic.intent_analyzer import IntentAnalyzer

session_manager = SessionManager()
intent_analyzer = IntentAnalyzer()


def _is_excel_file(name: str) -> bool:
    lower = name.lower()
    return lower.endswith(".xlsx") or lower.endswith(".xlsm")


def _op_title(op: PendingOperation) -> str:
    op_map = {"add": "افزودن", "delete": "حذف", "edit": "ادیت"}
    t_map = {"row": "سطر", "column": "ستون"}
    m_map = {"single": "تکی", "group": "گروهی"}
    return f"{op_map.get(op.op_kind, op.op_kind)} {m_map.get(op.mode, op.mode)} {t_map.get(op.target_kind, op.target_kind)}"


async def _send_home(update: Update, chat_id: int):
    session = session_manager.get(chat_id)
    is_admin = chat_id == ADMIN_ID
    if session.ui_mode == "reply":
        await update.effective_message.reply_text("🏠 منوی اصلی", reply_markup=reply_home_menu(is_admin))
    else:
        await update.effective_message.reply_text("🏠 منوی اصلی", reply_markup=inline_home_menu(is_admin))


def _analysis_text(analysis: dict) -> str:
    lines = ["✅ فایل تحلیل شد.", ""]
    lines.append(f"📚 تعداد شیت‌ها: {len(analysis['sheets'])}")
    lines.append("")
    for idx, sheet in enumerate(analysis["sheets"], start=1):
        lines.append(f"🧾 شیت {idx}: {sheet['name']}")
        lines.append(f"   • تعداد سطرها: {sheet['rows']}")
        lines.append(f"   • تعداد ستون‌ها: {sheet['cols']}")
        lines.append("   • هدرها:")
        for h_i, header in enumerate(sheet["headers"], start=1):
            lines.append(f"      {h_i}) {header}")
        lines.append("")
    lines.append("➡️ حالا بگو چه عملیاتی انجام بدم یا از منوی عملیات انتخاب کن.")
    return "\n".join(lines)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    session = session_manager.get(chat_id)

    if session.original_file_name:
        await update.message.reply_text(
            f"ℹ️ فایل قبلی هنوز در سشن موجود است: {session.original_file_name}\n"
            "می‌تونی ادامه بدی یا فایل جدید ارسال کنی."
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
            f"{_op_title(session.pending)}: ستون موردنظر را انتخاب کن.",
            reply_markup=selectable_buttons("column", headers, session.pending.selected, "ستون", allow_confirm=(mode == "group")),
        )
    else:
        session.state = BotState.SELECT_ROW
        await update.effective_message.reply_text(
            f"{_op_title(session.pending)}: سطر موردنظر را انتخاب کن.",
            reply_markup=selectable_rows("row", rows, session.pending.selected, allow_confirm=(mode == "group")),
        )


async def _ask_text_immediately(update: Update, chat_id: int):
    session = session_manager.get(chat_id)
    if not session.pending:
        return
    session.state = BotState.INPUT_TEXT

    if session.pending.mode == "group":
        await update.effective_message.reply_text(
            f"{_op_title(session.pending)}\n"
            "📝 حالا لیست متن‌ها را بفرست (می‌تونی چند پیام جداگانه بفرستی).\n"
            "هر خط یک مقدار مستقل محسوب می‌شود.\n"
            "وقتی تمام شد روی ✅ تایید متن بزن.",
            reply_markup=text_confirm_inline(),
        )
    else:
        await update.effective_message.reply_text(
            f"{_op_title(session.pending)}\n📝 حالا متن نهایی را بفرست و بعد ✅ تایید متن را بزن.",
            reply_markup=text_confirm_inline(),
        )


async def _register_operation(update: Update, chat_id: int):
    session = session_manager.get(chat_id)
    if not session.pending:
        await update.effective_message.reply_text("عملیات فعالی نیست.")
        return

    if session.pending.op_kind in {"add", "edit"} and not [x for x in session.pending.payload_lines if x.strip()]:
        await update.effective_message.reply_text("برای این عملیات باید متن معتبر ارسال کنی.")
        return

    session.op_stack.append(session.pending)
    title = _op_title(session.pending)
    session.pending = None
    session.state = BotState.READY_TO_SAVE

    await update.effective_message.reply_text(
        f"✅ عملیات ثبت شد: {title}\n"
        f"تعداد عملیات معلق: {len(session.op_stack)}\n"
        "برای ادامه عملیات، دوباره از منوی عملیات انتخاب کن.\n"
        "برای خروجی گرفتن، دکمه ذخیره نهایی را بزن.",
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
        session.undo_stack.clear()
        await update.effective_message.reply_text(f"❌ خطا در اعمال عملیات: {exc}")
        headers, rows = get_sheet_map(session.working_bytes, session.selected_sheet)
        await update.effective_message.reply_text(
            f"ساختار جدید فایل:\nتعداد ستون‌ها: {len(headers)}\nتعداد سطرهای داده: {len(rows)}",
            reply_markup=operations_menu(),
        )
        return

    session.working_bytes = current
    out_path = save_working_copy(current, session.original_file_name)
    with out_path.open("rb") as fh:
        await context.bot.send_document(
            chat_id=chat_id,
            document=fh,
            filename=session.original_file_name,
            caption="✅ فایل نهایی ذخیره و ارسال شد.",
        )
    session_manager.clear_after_save(chat_id)


async def _undo(update: Update, chat_id: int):
    session = session_manager.get(chat_id)
    if not session.op_stack:
        await update.effective_message.reply_text("Undo فقط تا قبل از ذخیره نهایی ممکن است. عملیات معلقی وجود ندارد.")
        return
    removed = session.op_stack.pop()
    await update.effective_message.reply_text(
        f"↩️ آخرین عملیات حذف شد: {_op_title(removed)}\nعملیات باقی‌مانده: {len(session.op_stack)}"
    )


async def _run_intent_text(update: Update, chat_id: int, text: str):
    intent = intent_analyzer.parse(text)
    if not intent:
        await update.message.reply_text("دستور هوشمند تشخیص داده نشد. مثال: «حذف گروهی ستون». ")
        return
    await _begin_operation(update, chat_id, intent.op_kind, intent.target_kind, intent.mode)


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

    if text == "🤖 دستور هوشمند":
        await update.message.reply_text(
            "فرمت نمونه:\n- حذف گروهی ستون\n- افزودن تکی سطر\n- ادیت تکی ستون\n"
            "یا از منوی عملیات استفاده کن."
        )
        return

    if text == "💾 ذخیره نهایی و دریافت فایل":
        await _save_final(update, chat_id, context)
        return

    if text == "↩️ Undo":
        await _undo(update, chat_id)
        return

    if text == "📚 راهنما":
        await update.message.reply_text(
            "آموزش مرحله‌ای:\n"
            "1) فایل اکسل را ارسال کن\n"
            "2) آنالیز اکسل را بزن\n"
            "3) نوع عملیات را انتخاب کن\n"
            "4) سطر/ستون را انتخاب کن\n"
            "5) اگر عملیات add/edit بود متن را بفرست و تایید کن\n"
            "6) عملیات در صف ثبت می‌شود (✅)\n"
            "7) در پایان ذخیره نهایی بزن تا فایل خروجی بگیری"
        )
        return

    if session.state == BotState.INPUT_TEXT and session.pending:
        lines = [line for line in text.splitlines() if line.strip()]
        if not lines:
            await update.message.reply_text("متن خالی ثبت نمی‌شود.")
            return
        session.pending.payload_lines.extend(lines)
        await update.message.reply_text(
            f"✅ متن دریافت شد. تعداد خطوط ثبت‌شده: {len(session.pending.payload_lines)}",
            reply_markup=text_confirm_inline(),
        )
        return

    # fallback to intent analyzer
    await _run_intent_text(update, chat_id, text)


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

    if data == "ai:menu":
        await query.message.reply_text(
            "فرمان هوشمند را متنی ارسال کن. مثال:\n"
            "«افزودن گروهی ستون» یا «حذف تکی سطر»"
        )
        return

    if data.startswith("op:"):
        _, op_kind, target_kind, mode = data.split(":", 3)
        await _begin_operation(update, chat_id, op_kind, target_kind, mode)
        return

    if data.startswith("toggle:"):
        _, kind, idx = data.split(":", 2)
        idx_int = int(idx)

        if not session.pending:
            await query.message.reply_text("عملیات فعالی نیست.")
            return

        # in single mode, immediate select -> immediate next step
        if session.pending.mode == "single":
            session.pending.selected = {idx_int}
            if session.pending.op_kind == "delete":
                await _register_operation(update, chat_id)
            else:
                await _ask_text_immediately(update, chat_id)
            return

        # group mode toggle with live markers
        if idx_int in session.pending.selected:
            session.pending.selected.remove(idx_int)
        else:
            session.pending.selected.add(idx_int)

        headers, rows = get_sheet_map(session.working_bytes, session.selected_sheet)
        if kind == "column":
            await query.message.reply_text(
                "انتخاب ستون‌ها به‌روزرسانی شد.",
                reply_markup=selectable_buttons("column", headers, session.pending.selected, "ستون", allow_confirm=True),
            )
        else:
            await query.message.reply_text(
                "انتخاب سطرها به‌روزرسانی شد.",
                reply_markup=selectable_rows("row", rows, session.pending.selected, allow_confirm=True),
            )
        return

    if data.startswith("confirm:"):
        if not session.pending or not session.pending.selected:
            await query.message.reply_text("حداقل یک مورد را انتخاب کن.")
            return

        # group mode only lands here
        if session.pending.op_kind == "delete":
            await _register_operation(update, chat_id)
        else:
            await _ask_text_immediately(update, chat_id)
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
        await query.message.reply_text("از ارسال فایل شروع کن → تحلیل → عملیات → ذخیره نهایی.")
        return

    if data == "nav:admin":
        if chat_id != ADMIN_ID:
            await query.message.reply_text("⛔ دسترسی غیرمجاز")
            return
        await query.message.reply_text("⚙️ مدیر: این بخش قابل توسعه است.")
        return

    await query.message.reply_text("گزینه نامعتبر")
