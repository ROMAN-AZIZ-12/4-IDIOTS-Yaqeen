"""Gemini explanation with number-check fallback to a template report."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from app.config import Settings, get_settings

try:
    from google import genai
    from google.genai import types
except Exception:  # pragma: no cover
    genai = None  # type: ignore
    types = None  # type: ignore


PROMPTS_DIR = Path(__file__).resolve().parents[3] / "prompts"


class Explanation(BaseModel):
    summary: str
    factor_notes: list[str]


def _load_prompt(version: str) -> str:
    return (PROMPTS_DIR / version).read_text(encoding="utf-8")


def _allowed_numbers(features: dict[str, Any], factors: dict[str, Any]) -> set[float]:
    """Numbers that may legitimately appear in the explanation text."""
    values: set[float] = set()
    for key, value in features.items():
        if isinstance(value, (int, float)):
            values.add(round(float(value), 1))
    for data in factors.values():
        if isinstance(data, dict):
            pts = data.get("points")
            if isinstance(pts, (int, float)):
                values.add(round(float(pts), 1))
    # Also allow score total if present.
    if "score_total" in factors:
        values.add(round(float(factors["score_total"]), 1))
    return values


def _numbers_in_text(text: str) -> set[float]:
    found = set()
    for match in re.finditer(r"-?\d+(?:\.\d+)?", text):
        try:
            found.add(round(float(match.group()), 1))
        except ValueError:
            continue
    return found


def _numbers_ok(report: dict[str, Any], features: dict[str, Any], factors: dict[str, Any]) -> bool:
    allowed = _allowed_numbers(features, factors)
    text = " ".join([report.get("summary", "")] + report.get("factor_notes", []))
    found = _numbers_in_text(text)
    return found.issubset(allowed)


def _template_report(features: dict[str, Any], factors: dict[str, Any]) -> dict[str, Any]:
    cv = features.get("credit_cv")
    seasonality = " Seasonal income may be present." if cv is not None and cv > 0.5 else ""
    summary = (
        f"The file scored {factors['score_total']} out of 100 "
        f"({factors['suggestion'].replace('_', ' ')}).{seasonality}"
    )
    notes = [
        f"Income consistency ({factors['factors']['income_consistency']['points']}): {factors['factors']['income_consistency']['evidence']}",
        f"Bill payment ({factors['factors']['bill_payment']['points']}): {factors['factors']['bill_payment']['evidence']}",
        f"Transaction regularity ({factors['factors']['transaction_regularity']['points']}): {factors['factors']['transaction_regularity']['evidence']}",
        f"Document quality ({factors['factors']['document_quality']['points']}): {factors['factors']['document_quality']['evidence']}",
    ]
    return {"summary": summary, "factor_notes": notes}


def explain(
    features: dict[str, Any],
    factors: dict[str, Any],
    settings: Settings | None = None,
) -> tuple[dict[str, Any], str]:
    """Return (report_json, report_source)."""
    if settings is None:
        settings = get_settings()
    prompt_text = _load_prompt("explain.v1")
    payload = json.dumps({"features": features, "factors": factors}, default=str)
    try:
        if genai is None:
            raise RuntimeError("google-genai package is not installed")
        client = genai.Client(api_key=settings.GEMINI_API_KEY.get_secret_value())
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=Explanation,
            temperature=0,
        )
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[types.Part.from_text(text=prompt_text + "\n\nInput:\n" + payload)],
            config=config,
        )
        raw = response.text or "{}"
        report = json.loads(raw)
        validated = Explanation.model_validate(report)
        report_json = validated.model_dump(mode="json")
        if _numbers_ok(report_json, features, factors):
            return report_json, "model"
    except (Exception, ValidationError):
        pass
    return _template_report(factors, factors), "template"


# Avoid shadowing the module name for callers.
run_explain = explain
