from core.excel_reader import ExcelReader
from core.excel_analyzer import ExcelAnalyzer
from core.excel_editor import ExcelEditor
from logic.intent_parser import IntentParser
from logic.fake_ai import FakeAI
from logic.blueprint_validator import BlueprintValidator

reader = ExcelReader("storage/uploads/test.xlsx")
wb = reader.load()
sheet = reader.get_sheet("Sheet")

analyzer = ExcelAnalyzer(sheet)
analysis = analyzer.analyze_columns()

ai = FakeAI()
parser = IntentParser(ai)

command = "ستون price رو ۱۰ درصد افزایش بده"
blueprint = parser.parse(command, {
    "sheets": ["Sheet"],
    "columns": analysis
})

validator = BlueprintValidator(analysis)
validator.validate(blueprint)

editor = ExcelEditor(sheet)
editor.execute_blueprint(blueprint, analysis)

wb.save("storage/uploads/test.xlsx")

print("✅ فرمان هوشمند با موفقیت اجرا شد")
