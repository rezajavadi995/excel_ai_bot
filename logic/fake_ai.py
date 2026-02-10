class FakeAI:
    def complete(self, prompt: str) -> str:
        # فقط برای تست فاز ۲
        return """
{
  "sheet": "Sheet",
  "action": "update",
  "target": {
    "column": "price"
  },
  "condition": null,
  "operation": {
    "type": "percentage_increase",
    "value": 10
  }
}
"""
