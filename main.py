from core.excel_reader import ExcelReader
from core.excel_analyzer import ExcelAnalyzer
from core.excel_editor import ExcelEditor
from core.history_manager import HistoryManager

file_path = "test.xlsx"

reader = ExcelReader(file_path)
wb = reader.load()

sheet = reader.get_sheet(wb.sheetnames[0])

analyzer = ExcelAnalyzer(sheet)
info = analyzer.analyze_columns()
print(info)

history = HistoryManager()
history.save_version("file1", file_path, "before_edit")

editor = ExcelEditor(sheet)
editor.increase_percentage(col_index=2, percent=10)

wb.save(file_path)
