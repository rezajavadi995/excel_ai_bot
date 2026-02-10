from pathlib import Path

from openpyxl import Workbook

from core.excel_analyzer import ExcelAnalyzer
from core.excel_editor import ExcelEditor
from core.excel_reader import ExcelReader
from logic.blueprint_validator import BlueprintValidator
from logic.fake_ai import FakeAI
from logic.intent_parser import IntentParser


def _build_test_file(path: Path):
    wb = Workbook()
    ws = wb.active
    ws.append(["name", "price"])
    ws.append(["item1", 100])
    ws.append(["item2", 200])
    wb.save(path)


def test_ai_command_flow(tmp_path):
    test_file = tmp_path / "test.xlsx"
    _build_test_file(test_file)

    reader = ExcelReader(str(test_file))
    wb = reader.load()
    sheet = reader.get_sheet("Sheet")

    analysis = ExcelAnalyzer(sheet).analyze_columns()
    parser = IntentParser(FakeAI())

    blueprint = parser.parse(
        "ستون price رو ۱۰ درصد افزایش بده",
        {"sheets": ["Sheet"], "columns": analysis},
    )

    BlueprintValidator(analysis).validate(blueprint)
    ExcelEditor(sheet).execute_blueprint(blueprint, analysis)
    reader.save()

    wb2 = ExcelReader(str(test_file)).load()
    ws2 = wb2["Sheet"]
    assert ws2.cell(row=2, column=2).value == 110
