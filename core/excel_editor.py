from __future__ import annotations


class ExcelEditor:
    def __init__(self, sheet):
        self.sheet = sheet

    def increase_percentage(self, col_index: int, percent: float):
        factor = 1 + (percent / 100)
        for row in self.sheet.iter_rows(min_row=2, min_col=col_index, max_col=col_index):
            cell = row[0]
            if isinstance(cell.value, (int, float)):
                cell.value = round(cell.value * factor, 4)

    def delete_column(self, col_index: int):
        self.sheet.delete_cols(col_index, amount=1)

    def execute_blueprint(self, blueprint: dict, column_map: dict):
        action = blueprint["action"]
        operation = blueprint["operation"]

        col_name = blueprint["target"].get("column")
        if not col_name or col_name not in column_map:
            raise ValueError("ستون هدف معتبر نیست")

        col_index = column_map[col_name]["index"]

        if action != "update":
            raise ValueError(f"عملیات action={action} پشتیبانی نمی‌شود")

        op_type = operation.get("type")
        if op_type == "percentage_increase":
            self.increase_percentage(col_index, float(operation.get("value", 0)))
        elif op_type == "delete_column":
            self.delete_column(col_index)
        else:
            raise ValueError(f"نوع عملیات {op_type} پشتیبانی نمی‌شود")
