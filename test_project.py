from pathlib import Path

from openpyxl import Workbook

from core.excel_analyzer import ExcelAnalyzer
from core.excel_editor import ExcelEditor
from core.excel_reader import ExcelReader
from core.history_manager import HistoryManager


def _build_test_file(path: Path):
    wb = Workbook()
    ws = wb.active
    ws.append(["name", "price"])
    ws.append(["item1", 100])
    ws.append(["item2", 200])
    wb.save(path)


def test_excel_core_flow(tmp_path):
    test_file = tmp_path / "test.xlsx"
    _build_test_file(test_file)

    reader = ExcelReader(str(test_file))
    wb = reader.load()
    sheet = reader.get_sheet("Sheet")

    analysis = ExcelAnalyzer(sheet).analyze_columns()
    assert analysis["price"]["type"] == "numeric"

    versions_dir = tmp_path / "versions"
    history = HistoryManager(base_dir=str(versions_dir))
    version_path = history.save_version("file1", str(test_file), "before_edit")
    assert Path(version_path).exists()

    ExcelEditor(sheet).increase_percentage(col_index=2, percent=10)
    reader.save()

    wb2 = ExcelReader(str(test_file)).load()
    ws2 = wb2["Sheet"]
    assert ws2.cell(row=2, column=2).value == 110
