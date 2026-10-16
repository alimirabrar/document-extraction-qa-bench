"""Evaluate extracted JSON fields against synthetic ground truth."""
from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable

_CURRENCY_MARKS = re.compile(r"[$€£₹]|\b(?:USD|EUR|GBP|INR)\b", re.IGNORECASE)
_SPACE = re.compile(r"\s+")


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as stream:
        for line_number, raw in enumerate(stream, start=1):
            if not raw.strip():
                continue
            try:
                item = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}: {exc.msg}") from exc
            if not isinstance(item, dict):
                raise ValueError(f"Line {line_number} must contain a JSON object")
            records.append(item)
    return records


def _normalize(value: Any, field_type: str) -> Any:
    if value is None:
        return None
    if field_type == "currency":
        text = _CURRENCY_MARKS.sub("", str(value)).replace(",", "").strip()
        try:
            return Decimal(text).normalize()
        except InvalidOperation:
            return ("invalid-currency", text.casefold())
    text = _SPACE.sub(" ", str(value)).strip()
    return text.casefold() if field_type in {"text", "date", "identifier"} else text


def evaluate(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Compute exact/normalized field accuracy, coverage, and strict pass rate."""
    per_document: list[dict[str, Any]] = []
    expected_total = exact_total = normalized_total = present_total = 0
    extra_total = 0

    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise ValueError(f"Document {index} must be an object")
        document_id = str(record.get("document_id", f"document-{index}"))
        expected = record.get("expected")
        predicted = record.get("predicted")
        field_types = record.get("field_types", {})
        if not isinstance(expected, dict) or not isinstance(predicted, dict) or not isinstance(field_types, dict):
            raise ValueError(f"Document {document_id}: expected, predicted, and field_types must be objects")
        if not expected:
            raise ValueError(f"Document {document_id}: expected must contain at least one field")

        fields: list[dict[str, Any]] = []
        doc_exact = doc_normalized = doc_present = 0
        for name, expected_value in expected.items():
            present = name in predicted and predicted[name] is not None
            predicted_value = predicted.get(name)
            exact = present and type(predicted_value) is type(expected_value) and predicted_value == expected_value
            kind = str(field_types.get(name, "text"))
            normalized = present and _normalize(predicted_value, kind) == _normalize(expected_value, kind)
            doc_present += int(present)
            doc_exact += int(exact)
            doc_normalized += int(normalized)
            fields.append({
                "field": name,
                "present": present,
                "exact_match": bool(exact),
                "normalized_match": bool(normalized),
            })

        extras = sorted(set(predicted) - set(expected))
        strict_pass = doc_normalized == len(expected) and not extras
        expected_total += len(expected)
        present_total += doc_present
        exact_total += doc_exact
        normalized_total += doc_normalized
        extra_total += len(extras)
        per_document.append({
            "document_id": document_id,
            "passed": strict_pass,
            "expected_field_count": len(expected),
            "present_field_count": doc_present,
            "exact_matches": doc_exact,
            "normalized_matches": doc_normalized,
            "extra_fields": extras,
            "fields": fields,
        })

    document_count = len(per_document)
    return {
        "summary": {
            "document_count": document_count,
            "strict_passed_documents": sum(doc["passed"] for doc in per_document),
            "strict_document_pass_rate": (sum(doc["passed"] for doc in per_document) / document_count) if document_count else 0.0,
            "expected_fields": expected_total,
            "present_field_coverage": (present_total / expected_total) if expected_total else 0.0,
            "exact_field_accuracy": (exact_total / expected_total) if expected_total else 0.0,
            "normalized_field_accuracy": (normalized_total / expected_total) if expected_total else 0.0,
            "extra_field_count": extra_total,
        },
        "documents": per_document,
    }
