from logic.intent_analyzer import IntentAnalyzer


def test_intent_add_single_column():
    analyzer = IntentAnalyzer()
    intent = analyzer.parse("افزودن تکی ستون")
    assert intent
    assert intent.op_kind == "add"
    assert intent.target_kind == "column"
    assert intent.mode == "single"


def test_intent_delete_group_row():
    analyzer = IntentAnalyzer()
    intent = analyzer.parse("حذف گروهی سطر")
    assert intent
    assert intent.op_kind == "delete"
    assert intent.target_kind == "row"
    assert intent.mode == "group"
