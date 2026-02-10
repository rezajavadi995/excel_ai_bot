# core/excel_analyzer.py

class ExcelAnalyzer:
    def __init__(self, sheet):
        self.sheet = sheet

    def get_headers(self):
        headers = []
        for cell in self.sheet[1]:
            headers.append(cell.value)
        return headers

    def get_column_values(self, col_index, limit=50):
        values = []
        for row in self.sheet.iter_rows(
            min_row=2,
            max_col=col_index,
            min_col=col_index
        ):
            if row[0].value is not None:
                values.append(row[0].value)
            if len(values) >= limit:
                break
        return values

    def detect_column_type(self, values):
        numeric = 0
        text = 0

        for v in values:
            if isinstance(v, (int, float)):
                numeric += 1
            elif isinstance(v, str):
                text += 1

        if numeric > text:
            return "numeric"
        if text > numeric:
            return "text"
        return "mixed"

    def analyze_columns(self):
        headers = self.get_headers()
        result = {}

        for idx, header in enumerate(headers, start=1):
            values = self.get_column_values(idx)
            col_type = self.detect_column_type(values)

            result[header] = {
                "index": idx,
                "type": col_type,
                "sample": values[:5]
            }

        return result
