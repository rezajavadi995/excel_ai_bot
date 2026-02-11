from bot.context_manager import ContextManager, FSMState, UserContext
from bot.decision_engine import DecisionEngine
from bot.intent_detection import IntentDetectionEngine


def test_intent_detection_regex_and_target():
    eng = IntentDetectionEngine()
    intent = eng.detect("افزودن گروهی ستون")
    assert intent.name == "add"
    assert intent.target == "column"
    assert intent.mode == "group"


def test_context_pattern_suggest_export(tmp_path):
    cm = ContextManager(str(tmp_path / "ctx.db"))
    uid = 11
    cm.log_operation(uid, "f1", "analyze", "exit")
    cm.log_operation(uid, "f1", "filter", "exit")
    cm.log_operation(uid, "f1", "analyze", "exit")
    cm.log_operation(uid, "f1", "filter", "exit")
    assert cm.should_suggest_export(uid)


def test_decision_requires_file_for_analyze(tmp_path):
    cm = ContextManager(str(tmp_path / "ctx2.db"))
    de = DecisionEngine(cm)
    intent = IntentDetectionEngine().detect("analyze")
    decision = de.decide(5, intent)
    assert decision.action == "request_file"
    ctx = cm.get_user_context(5)
    assert ctx.state == FSMState.WAIT_FILE
