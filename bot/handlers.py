from __future__ import annotations

from dataclasses import dataclass

from telegram import Update
from telegram.ext import ContextTypes

from bot.context_manager import ContextManager, FSMState
from bot.decision_engine import DecisionEngine
from bot.excel_engine import ExcelEngine
from bot.intent_detection import Intent, IntentDetectionEngine
from bot.ui_renderer import UIRenderer

ctx_manager = ContextManager()
intent_engine = IntentDetectionEngine()
decision_engine = DecisionEngine(ctx_manager)
excel_engine = ExcelEngine()
ui = UIRenderer()


@dataclass
class PendingFilter:
    column: str | None = None
    keyword: str | None = None


pending_filters: dict[int, PendingFilter] = {}


def _context(user_id: int):
    return ctx_manager.get_user_context(user_id)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ctx = _context(user_id)
    suggest_export = ctx_manager.should_suggest_export(user_id)
    await update.effective_message.reply_text(
        "به excel_ai_bot خوش آمدی.\nاین نسخه کاملاً آفلاین و rule-based/NLP سبک است.",
        reply_markup=ui.reply_menu(ctx),
    )
    await update.effective_message.reply_text(
        "منوی شناور:",
        reply_markup=ui.inline_menu(ctx, suggest_export=suggest_export),
    )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    doc = update.message.document
    if not doc:
        return
    if not doc.file_name.lower().endswith((".xlsx", ".xlsm")):
        await update.message.reply_text("فقط فایل اکسل پشتیبانی می‌شود.")
        return

    file = await context.bot.get_file(doc.file_id)
    data = await file.download_as_bytearray()
    file_id, original_path, working_path = excel_engine.store_original_and_working(user_id, doc.file_name, bytes(data))

    ctx_manager.register_file(user_id, file_id, doc.file_name, original_path, working_path)
    ctx = _context(user_id)
    ctx.active_file_id = file_id
    ctx.state = FSMState.FILE_UPLOADED
    ctx.active_operation = None
    ctx_manager.upsert_user_context(ctx)

    await update.message.reply_text(f"✅ فایل دریافت شد: {doc.file_name}\nبرای تحلیل، دکمه Analyze file را بزن.")


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    if not data.startswith("intent:"):
        return
    command = data.split(":", 1)[1]
    text_map = {
        "analyze": "analyze",
        "filter": "filter",
        "export": "export",
        "back": "back",
        "reset": "reset",
        "reuse": "reuse analysis",
    }
    fake_update = Update(update.update_id, message=query.message)
    query.message.text = text_map.get(command, command)  # type: ignore[attr-defined]
    await handle_message(fake_update, context)


async def _execute_decision(update: Update, context: ContextTypes.DEFAULT_TYPE, decision):
    user_id = update.effective_user.id
    ctx = _context(user_id)

    if decision.route == "help":
        if decision.action == "show_help":
            await update.effective_message.reply_text(ui.help_text())
        elif decision.action == "request_file":
            await update.effective_message.reply_text("ابتدا فایل اکسل را ارسال کن.")
        elif decision.action == "need_analyze_first":
            await update.effective_message.reply_text("اول باید فایل را analyze کنی.")
        elif decision.action == "reset":
            ctx_manager.reset_user(user_id)
            pending_filters.pop(user_id, None)
            await update.effective_message.reply_text("سشن ریست شد.")
        elif decision.action == "back":
            ctx.state = FSMState.ANALYZED if ctx.active_file_id else FSMState.IDLE
            ctx_manager.upsert_user_context(ctx)
            await update.effective_message.reply_text("بازگشت انجام شد.")
        return

    if decision.route == "excel":
        record = ctx_manager.get_file_record(ctx.active_file_id) if ctx.active_file_id else None
        if not record:
            await update.effective_message.reply_text("فایل فعالی ندارید.")
            return

        if decision.action == "analyze":
            if record["analyzed"] == 1 and record["analysis_json"]:
                import json

                analysis = json.loads(record["analysis_json"])
            else:
                analysis = excel_engine.analyze(record["working_path"])
                ctx_manager.mark_analyzed(ctx.active_file_id, analysis)
            ctx.state = FSMState.ANALYZED
            ctx_manager.upsert_user_context(ctx)
            ctx_manager.log_operation(user_id, ctx.active_file_id, "analyze", "exit")
            await update.effective_message.reply_text(ui.analysis_text(analysis), reply_markup=ui.inline_menu(ctx, ctx_manager.should_suggest_export(user_id)))
            return

        if decision.action == "filter":
            pf = pending_filters.setdefault(user_id, PendingFilter())
            if not pf.column:
                ctx.state = FSMState.FILTERING
                ctx_manager.upsert_user_context(ctx)
                await update.effective_message.reply_text(
                    "فیلتر: نام ستون و کلیدواژه را با فرمت زیر بفرست:\ncolumn=<name>;keyword=<text>"
                )
                return
            excel_engine.filter_contains(record["working_path"], excel_engine.analyze(record["working_path"])["sheets"][0]["name"], pf.column, pf.keyword or "")
            pending_filters.pop(user_id, None)
            ctx.state = FSMState.READY_EXPORT
            ctx_manager.upsert_user_context(ctx)
            ctx_manager.log_operation(user_id, ctx.active_file_id, "filter", "exit")
            suggest = ctx_manager.should_suggest_export(user_id)
            msg = "✅ فیلتر اعمال شد."
            if suggest:
                msg += "\n💡 با توجه به روند قبلی‌ات، الان Export پیشنهاد می‌شود."
            await update.effective_message.reply_text(msg, reply_markup=ui.inline_menu(ctx, suggest_export=suggest))
            return

        if decision.action == "export":
            out_path = excel_engine.export(record["working_path"], record["original_name"])
            with open(out_path, "rb") as fh:
                await context.bot.send_document(chat_id=user_id, document=fh, filename=record["original_name"], caption="فایل خروجی")
            ctx.state = FSMState.DONE
            ctx_manager.upsert_user_context(ctx)
            ctx_manager.log_operation(user_id, ctx.active_file_id, "export", "exit")
            return

    await update.effective_message.reply_text("دستور قابل اجرا نیست.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message:
        return
    user_id = update.effective_user.id
    text = (update.effective_message.text or "").strip()

    if text == "/start":
        await start(update, context)
        return

    # pending filter input capture
    ctx = _context(user_id)
    if ctx.state == FSMState.FILTERING and "column=" in text and "keyword=" in text:
        parts = dict(chunk.split("=", 1) for chunk in text.split(";") if "=" in chunk)
        pending_filters[user_id] = PendingFilter(column=parts.get("column"), keyword=parts.get("keyword"))
        intent = Intent(name="filter", raw_text=text, target="column")
        decision = decision_engine.decide(user_id, intent)
        await _execute_decision(update, context, decision)
        return

    mapping = {
        "📊 آنالیز": "analyze",
        "🧪 فیلتر": "filter",
        "📤 خروجی": "export",
        "📚 راهنما": "help",
        "⬅️ بازگشت": "back",
        "🧹 ریست": "reset",
    }
    normalized = mapping.get(text, text)

    intent = intent_engine.detect(normalized)
    decision = decision_engine.decide(user_id, intent)
    await _execute_decision(update, context, decision)
