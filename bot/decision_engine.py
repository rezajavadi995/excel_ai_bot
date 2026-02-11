from __future__ import annotations

from dataclasses import dataclass

from bot.context_manager import ContextManager, FSMState
from bot.intent_detection import Intent


@dataclass
class Decision:
    route: str  # excel | help | fallback
    action: str
    payload: dict


class DecisionEngine:
    def __init__(self, context_manager: ContextManager):
        self.ctx = context_manager

    def decide(self, user_id: int, intent: Intent) -> Decision:
        ctx = self.ctx.get_user_context(user_id)

        if intent.name in {"help"}:
            return Decision(route="help", action="show_help", payload={})

        if intent.name in {"reset"}:
            return Decision(route="help", action="reset", payload={})

        if intent.name == "back":
            return Decision(route="help", action="back", payload={})

        if intent.name == "analyze":
            if not ctx.active_file_id:
                ctx.state = FSMState.WAIT_FILE
                self.ctx.upsert_user_context(ctx)
                return Decision(route="help", action="request_file", payload={})
            ctx.state = FSMState.ANALYZED
            ctx.active_operation = "analyze"
            self.ctx.upsert_user_context(ctx)
            self.ctx.log_operation(user_id, ctx.active_file_id, "analyze", "enter")
            return Decision(route="excel", action="analyze", payload={"file_id": ctx.active_file_id})

        if intent.name == "filter":
            if ctx.state not in {FSMState.ANALYZED, FSMState.FILTERING, FSMState.READY_EXPORT}:
                return Decision(route="help", action="need_analyze_first", payload={})
            ctx.state = FSMState.FILTERING
            ctx.active_operation = "filter"
            self.ctx.upsert_user_context(ctx)
            self.ctx.log_operation(user_id, ctx.active_file_id, "filter", "enter")
            return Decision(route="excel", action="filter", payload={"file_id": ctx.active_file_id})

        if intent.name == "export":
            if ctx.state not in {FSMState.FILTERING, FSMState.READY_EXPORT, FSMState.ANALYZED}:
                return Decision(route="help", action="need_analyze_first", payload={})
            ctx.state = FSMState.DONE
            ctx.active_operation = "export"
            self.ctx.upsert_user_context(ctx)
            self.ctx.log_operation(user_id, ctx.active_file_id, "export", "enter")
            return Decision(route="excel", action="export", payload={"file_id": ctx.active_file_id})

        return Decision(route="fallback", action="unknown", payload={"text": intent.raw_text})
