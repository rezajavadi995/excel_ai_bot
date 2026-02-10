class BlueprintValidator:
    def __init__(self, excel_analysis):
        self.analysis = excel_analysis

    def validate(self, blueprint):
        col = blueprint["target"].get("column")

        if col not in self.analysis:
            raise ValueError(f"ستون {col} وجود ندارد")

        col_type = self.analysis[col]["type"]

        op_type = blueprint["operation"]["type"]

        if op_type == "percentage_increase" and col_type != "numeric":
            raise ValueError("افزایش درصد فقط روی ستون عددی ممکن است")

        return True
