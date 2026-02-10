# core/excel_editor.py

class ExcelEditor:
    def __init__(self, sheet):
        self.sheet = sheet

    def increase_percentage(self, col_index, percent):
        factor = 1 + (percent / 100)

        for row in self.sheet.iter_rows(min_row=2, min_col=col_index, max_col=col_index):
            cell = row[0]
            if isinstance(cell.value, (int, float)):
                cell.value = cell.value * factor
