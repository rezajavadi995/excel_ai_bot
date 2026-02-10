from __future__ import annotations


class BlueprintValidator:
    def __init__(self, excel_analysis):
        self.analysis = excel_analysis

    def validate(self, blueprint):
        required = ["sheet", "action", "target", "operation"]
        for key in required:
            if key not in blueprint:
                raise ValueError(f"کلید {key} در blueprint وجود ندارد")

        col = blueprint["target"].get("column")
        if col not in self.analysis:
            raise ValueError(f"ستون {col} وجود ندارد")

        col_type = self.analysis[col]["type"]
        op_type = blueprint["operation"].get("type")

        if op_type == "percentage_increase":
            if col_type != "numeric":
                raise ValueError("افزایش درصد فقط روی ستون عددی ممکن است")
            if "value" not in blueprint["operation"]:
                raise ValueError("مقدار درصد مشخص نشده است")
        elif op_type == "delete_column":
            return True
        else:
            raise ValueError(f"عملیات {op_type} پشتیبانی نمی‌شود")

        return True
