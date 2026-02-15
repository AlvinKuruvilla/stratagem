"""Tests for the evaluation metrics engine."""

import math

import pytest

from stratagem.evaluation.metrics import (
    TrialResult,
    compare_all_pairs,
    compare_strategies,
    compute_metrics,
    extract_trial_result,
)

# ── Helpers ───────────────────────────────────────────────────────────


def _make_trial(
    detected: bool = True,
    detection_round: int | None = 2,
    rounds_played: int = 5,
    exfiltrated: float = 0.0,
    spent: float = 5.0,
    strategy: str = "sse_optimal",
    seed: int = 42,
) -> TrialResult:
    return TrialResult(
        strategy=strategy,
        topology="small",
        seed=seed,
        winner="defender" if detected else "attacker",
        rounds_played=rounds_played,
        max_rounds=10,
        detected=detected,
        detection_round=detection_round if detected else None,
        num_detections=1 if detected else 0,
        attacker_dwell_time=detection_round if detected and detection_round else rounds_played,
        exfiltrated_value=exfiltrated,
        nodes_compromised=2,
        defender_budget=10.0,
        defender_spent=spent,
    )


def _make_final_state(
    detected: bool = True,
    detection_round: int = 2,
    rounds_played: int = 5,
    exfiltrated: float = 0.0,
) -> dict:
    detections = []
    if detected:
        detections = [
            {
                "round": detection_round,
                "node_id": "ws-1",
                "asset_type": "honeypot",
                "technique_id": "T1059",
            },
        ]
    return {
        "attacker": {
            "position": "ws-1",
            "detected": detected,
            "exfiltrated_value": exfiltrated,
            "compromised_nodes": ["fw-ext", "ws-1"],
            "path": ["fw-ext", "ws-1"],
            "access_levels": {},
        },
        "defender": {
            "budget": 10.0,
            "total_spent": 6.0,
            "deployed_assets": [],
            "remaining_budget": 4.0,
        },
        "detections": detections,
        "current_round": rounds_played + 1,
        "max_rounds": 10,
        "game_over": True,
        "winner": "defender" if detected else "attacker",
    }


# ── TestTrialResultExtraction ────────────────────────────────────────


class TestTrialResultExtraction:
    def test_detected_game(self):
        state = _make_final_state(detected=True, detection_round=3, rounds_played=3)
        trial = extract_trial_result(state, "sse_optimal", "small", 42)
        assert trial.detected is True
        assert trial.detection_round == 3
        assert trial.winner == "defender"
        assert trial.rounds_played == 3

    def test_undetected_game(self):
        state = _make_final_state(detected=False, rounds_played=10, exfiltrated=5.0)
        trial = extract_trial_result(state, "uniform", "medium", 99)
        assert trial.detected is False
        assert trial.detection_round is None
        assert trial.winner == "attacker"
        assert trial.exfiltrated_value == 5.0

    def test_dwell_time_detected(self):
        state = _make_final_state(detected=True, detection_round=4, rounds_played=4)
        trial = extract_trial_result(state, "sse_optimal", "small", 42)
        assert trial.attacker_dwell_time == 4

    def test_dwell_time_undetected(self):
        state = _make_final_state(detected=False, rounds_played=10)
        trial = extract_trial_result(state, "sse_optimal", "small", 42)
        assert trial.attacker_dwell_time == 10

    def test_multiple_detections(self):
        state = _make_final_state(detected=True, detection_round=3)
        state["detections"].append(
            {"round": 5, "node_id": "ws-2", "asset_type": "honeytoken", "technique_id": "T1041"},
        )
        trial = extract_trial_result(state, "sse_optimal", "small", 42)
        assert trial.num_detections == 2
        assert trial.detection_round == 3  # min round

    def test_defender_budget_extracted(self):
        state = _make_final_state()
        trial = extract_trial_result(state, "sse_optimal", "small", 42)
        assert trial.defender_budget == 10.0
        assert trial.defender_spent == 6.0

    def test_nodes_compromised(self):
        state = _make_final_state()
        trial = extract_trial_result(state, "sse_optimal", "small", 42)
        assert trial.nodes_compromised == 2


# ── TestMetricComputation ────────────────────────────────────────────


class TestMetricComputation:
    def test_100_percent_detection(self):
        trials = [_make_trial(detected=True, detection_round=i + 1) for i in range(10)]
        metrics = compute_metrics(trials, "sse_optimal", "small")
        assert metrics.detection_rate.mean == pytest.approx(1.0)
        assert metrics.detection_rate.n == 10

    def test_0_percent_detection(self):
        trials = [_make_trial(detected=False, exfiltrated=3.0) for _ in range(10)]
        metrics = compute_metrics(trials, "uniform", "small")
        assert metrics.detection_rate.mean == pytest.approx(0.0)

    def test_partial_detection(self):
        trials = (
            [_make_trial(detected=True, detection_round=2) for _ in range(7)]
            + [_make_trial(detected=False, exfiltrated=2.0) for _ in range(3)]
        )
        metrics = compute_metrics(trials, "static", "small")
        assert metrics.detection_rate.mean == pytest.approx(0.7)

    def test_ci_bounds(self):
        trials = [_make_trial(detected=True, detection_round=3) for _ in range(100)]
        metrics = compute_metrics(trials, "sse_optimal", "small")
        assert metrics.detection_rate.ci_lower <= metrics.detection_rate.mean + 1e-9
        assert metrics.detection_rate.ci_upper >= metrics.detection_rate.mean - 1e-9

    def test_mttd_with_no_detections(self):
        trials = [_make_trial(detected=False) for _ in range(10)]
        metrics = compute_metrics(trials, "uniform", "small")
        assert math.isinf(metrics.mean_time_to_detect.mean)

    def test_mttd_with_detections(self):
        trials = [_make_trial(detected=True, detection_round=3) for _ in range(10)]
        metrics = compute_metrics(trials, "sse_optimal", "small")
        assert metrics.mean_time_to_detect.mean == pytest.approx(3.0)

    def test_cost_efficiency(self):
        trials = [_make_trial(detected=True, spent=5.0) for _ in range(10)]
        metrics = compute_metrics(trials, "sse_optimal", "small")
        assert metrics.cost_efficiency.mean == pytest.approx(1.0 / 5.0)

    def test_empty_trials(self):
        metrics = compute_metrics([], "sse_optimal", "small")
        assert metrics.num_trials == 0
        assert metrics.detection_rate.n == 0


# ── TestStatisticalComparison ────────────────────────────────────────


class TestStatisticalComparison:
    def test_identical_distributions_not_significant(self):
        values = [1.0] * 50
        comp = compare_strategies(values, values, "a", "b", "test_metric")
        # p-value should be high (not significant).
        assert comp.significant is False or comp.p_value >= 0.05

    def test_clearly_different_distributions_significant(self):
        a = [1.0] * 50
        b = [0.0] * 50
        comp = compare_strategies(a, b, "sse_optimal", "uniform", "detection")
        assert comp.significant is True
        assert comp.p_value < 0.05

    def test_too_few_samples(self):
        comp = compare_strategies([1.0], [0.0], "a", "b", "metric")
        assert comp.significant is False
        assert comp.p_value == 1.0

    def test_compare_all_pairs_returns_comparisons(self):
        sse_trials = [_make_trial(detected=True, strategy="sse_optimal") for _ in range(20)]
        uniform_trials = [_make_trial(detected=False, strategy="uniform") for _ in range(20)]

        all_trials = {
            "sse_optimal": sse_trials,
            "uniform": uniform_trials,
        }

        comparisons = compare_all_pairs(all_trials)
        assert len(comparisons) == 3  # 3 metrics x 1 baseline

    def test_compare_all_pairs_empty_sse(self):
        comparisons = compare_all_pairs({"uniform": [_make_trial()]})
        assert comparisons == []
