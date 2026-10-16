# Document Extraction QA Bench

A lightweight, dependency-free benchmark for checking **structured extraction outputs against ground truth**. It reports exact and normalized field accuracy, field coverage, unexpected fields, and a strict per-document pass rate.

This is a personal demo/evaluation utility—not an OCR engine, document-processing service, or claim of production use. It accepts JSONL records containing expected and predicted fields; it does not read PDFs or call an LLM. All included examples are synthetic and contain no real customer or bank data.

## Quick start

Requires Python 3.11 or newer. No runtime dependencies.

```bash
python -m doc_qa.cli data/sample_predictions.jsonl
```

Write a JSON report:

```bash
python -m doc_qa.cli data/sample_predictions.jsonl --out report.json
```

Run tests:

```bash
python -m unittest discover -s tests -v
```

## Input format

Each non-empty JSONL line describes one document. `field_types` is optional; supported kinds are `text`, `identifier`, `date`, and `currency`. Text-like values compare case-insensitively after whitespace normalization. Currency values ignore common symbols/codes and grouping commas before decimal comparison. Exact match remains available alongside normalized match.

```json
{
  "document_id": "synthetic-invoice-001",
  "field_types": {"invoice_number": "identifier", "total": "currency"},
  "expected": {"invoice_number": "INV-001", "total": "1240.50"},
  "predicted": {"invoice_number": "INV-001", "total": "$1,240.50"}
}
```

## Metrics

- **Exact field accuracy:** raw JSON value equality with matching value types.
- **Normalized field accuracy:** matches after the field-type normalization above.
- **Present field coverage:** non-null predicted expected fields divided by expected fields.
- **Extra field count:** predicted keys absent from ground truth.
- **Strict document pass rate:** every expected field matches after normalization and no extra fields are present.

The benchmark does not measure OCR quality, semantic correctness beyond these rules, confidence calibration, or downstream business impact. Extend normalization carefully for your own schema, and keep test data synthetic or properly authorized.

## Project status

Personal demo MVP. Useful next steps include schema-aware validation, per-field error breakdowns, confidence calibration, and adapters for OCR/LLM output formats.
