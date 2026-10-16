import tempfile
import unittest
from pathlib import Path

from doc_qa.evaluator import evaluate, load_jsonl


class DocumentEvaluatorTests(unittest.TestCase):
    def test_sample_fixture_covers_success_and_failure_modes(self):
        root = Path(__file__).resolve().parents[1]
        report = evaluate(load_jsonl(root / "data" / "sample_predictions.jsonl"))
        summary = report["summary"]
        self.assertEqual(summary["document_count"], 4)
        self.assertEqual(summary["strict_passed_documents"], 2)
        self.assertEqual(summary["extra_field_count"], 1)
        self.assertGreater(summary["normalized_field_accuracy"], summary["exact_field_accuracy"])
        self.assertTrue(report["documents"][1]["passed"])
        self.assertFalse(report["documents"][2]["passed"])

    def test_currency_symbol_grouping_and_precision_normalize(self):
        report = evaluate([{
            "expected": {"total": "1240.50"},
            "predicted": {"total": "USD 1,240.500"},
            "field_types": {"total": "currency"},
        }])
        field = report["documents"][0]["fields"][0]
        self.assertFalse(field["exact_match"])
        self.assertTrue(field["normalized_match"])

    def test_extra_prediction_prevents_strict_pass(self):
        report = evaluate([{"expected": {"name": "Acme"}, "predicted": {"name": "Acme", "note": "x"}}])
        self.assertFalse(report["documents"][0]["passed"])
        self.assertEqual(report["summary"]["extra_field_count"], 1)

    def test_empty_expected_fields_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "at least one field"):
            evaluate([{"expected": {}, "predicted": {}}])

    def test_loader_reports_bad_json_line(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "bad.jsonl"
            file.write_text('{"ok": true}\nnope\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "line 2"):
                load_jsonl(file)


if __name__ == "__main__":
    unittest.main()
