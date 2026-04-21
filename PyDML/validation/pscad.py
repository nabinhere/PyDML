"""PSCAD comparison helpers."""

from __future__ import annotations

from typing import Any

from PyDML.types import ScenarioResults, ValidationReport


def compare_to_pscad(results: ScenarioResults, reference_case: dict[str, Any]) -> ValidationReport:
    """Compare scenario outputs to PSCAD reference metrics.

    Expected `reference_case` format:
    {
        "metrics": {"v_pcc_pu": 0.98, "f_pcc_hz": 59.9, ...},
        "tolerance": 0.1
    }
    """

    target_metrics = dict(reference_case.get("metrics", {}))
    tolerance = float(reference_case.get("tolerance", 0.1))
    if not target_metrics:
        return ValidationReport(
            passed=False,
            score=0.0,
            metric_errors={"_global": 1.0},
            details={"reason": "No reference metrics supplied."},
        )

    last = results.records[-1] if results.records else {}
    errors: dict[str, float] = {}
    for key, target in target_metrics.items():
        observed = last.get(key)
        if observed is None:
            errors[key] = 1.0
            continue
        denom = max(abs(float(target)), 1e-6)
        errors[key] = abs(float(observed) - float(target)) / denom

    mean_err = sum(errors.values()) / max(len(errors), 1)
    score = max(0.0, 1.0 - mean_err)
    passed = all(err <= tolerance for err in errors.values())
    return ValidationReport(
        passed=passed,
        score=score,
        metric_errors=errors,
        details={"reference_case_keys": sorted(target_metrics.keys())},
    )
