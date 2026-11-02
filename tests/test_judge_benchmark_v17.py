"""Benchmark itself must remain a reproducible non-model safety proof."""
from scripts.judge_benchmark import evaluate


def test_judge_benchmark_passes_all_synthetic_checks():
    result=evaluate()
    assert result["result"]=="PASS"
    assert result["checks_passed"]==result["checks_total"]
    assert result["checks_total"]>=12
    assert all(result["checks"].values())
    assert result["meta_inference_used"] is False
    assert result["external_systems_modified"] is False
    assert result["claims_excluded"]
