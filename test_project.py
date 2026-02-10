from core.excel_reader import ExcelReader
from core.excel_analyzer import ExcelAnalyzer
from core.excel_editor import ExcelEditor
from core.history_manager import HistoryManager
from openpyxl import Workbook
import os

TEST_FILE = "storage/uploads/test.xlsx"

# ساخت فایل تست
wb = Workbook()
ws = wb.active
ws.append(["name", "price"])
ws.append(["item1", 100])
ws.append(["item2", 200])
wb.save(TEST_FILE)

print("✔ فایل تست ساخته شد")

reader = ExcelReader(TEST_FILE)
wb = reader.load()
sheet = reader.get_sheet("Sheet")

analyzer = ExcelAnalyzer(sheet)
info = analyzer.analyze_columns()
print("✔ آنالیز ستون‌ها:", info)

history = HistoryManager()
history.save_version("testfile", TEST_FILE, "before_edit")
print("✔ نسخه ذخیره شد")

editor = ExcelEditor(sheet)
editor.increase_percentage(col_index=2, percent=10)

wb.save(TEST_FILE)
print("✔ ویرایش انجام شد")

print("🎯 تست با موفقیت کامل شد")
