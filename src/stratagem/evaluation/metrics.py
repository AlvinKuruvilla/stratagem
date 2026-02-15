"""Evaluation metrics for benchmarking defender strategies.

This module defines the data structures and computation functions that turn
raw game outcomes into statistical summaries.  The pipeline is:

    final_state  -->  extract_trial_result()  -->  TrialResult
                                                       |
    [TrialResult, ...]  -->  compute_metrics()  -->  StrategyMetrics
                                                       |
    {strategy: [TrialResult]}  -->  compare_all_pairs()  -->  [PairwiseComparison]

Each function is pure (no side effects) so the benchmark runner can
parallelise or serialise freely.

Metrics computed per-strategy:

- **Detection rate** — fraction of trials where the defender detected the
  attacker before the game ended.  Higher is better for the defender.
- **Mean time to detect (MTTD)** — average round at which first detection
  occurred, across detected trials only.  Lower is better.
- **Cost efficiency** — detection rate / total spent.  Measures how
  effectively the defender converts budget into detections.
- **Attacker dwell time** — rounds the attacker was active before detection
  or game end.  Lower is better for the defender.
- **Defender utility** — a composite score: +value for detections, -value
  for exfiltration.  Mirrors the solver's utility model.
- **Attacker exfiltration** — total value exfiltrated.  Lower is better
  for the defender.

Statistical comparison uses the Mann-Whitney U test (non-parametric) since
game outcomes are not guaranteed to be normally distributed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from scipy.stats import mannwhitneyu

# ── Per-trial result ──────────────────────────────────────────────────


@dataclass
class TrialResult:
    """Outcome of a single game trial."""

    strategy: str
    topology: str
    seed: int
    winner: str
    rounds_played: int
    max_rounds: int
    detected: bool
    detection_round: int | None
    num_detections: int
    attacker_dwell_time: int
    exfiltrated_value: float
    nodes_compromised: int
    defender_budget: float
    defender_spent: float


def extract_trial_result(
    final_state: dict,
    strategy: str,
    topology: str,
    seed: int,
) -> TrialResult:
    """Extract a TrialResult from the final game state dict.

    This is a pure function — it reads the state and produces a value
    without mutation.
    """
    attacker = final_state["attacker"]
    defender = final_state["defender"]
    detections = final_state.get("detections", [])

    detected = bool(attacker.get("detected", False))
    detection_round: int | None = None
    if detected and detections:
        detection_round = min(d["round"] for d in detections)

    rounds_played = final_state["current_round"] - 1
    dwell_time = detection_round if detection_round is not None else rounds_played

    return TrialResult(
        strategy=strategy,
        topology=topology,
        seed=seed,
        winner=final_state.get("winner", ""),
        rounds_played=rounds_played,
        max_rounds=final_state["max_rounds"],
        detected=detected,
        detection_round=detection_round,
        num_detections=len(detections),
        attacker_dwell_time=dwell_time,
        exfiltrated_value=float(attacker.get("exfiltrated_value", 0.0)),
        nodes_compromised=len(attacker.get("compromised_nodes", [])),
        defender_budget=float(defender.get("budget", 0.0)),
        defender_spent=float(defender.get("total_spent", 0.0)),
    )


# ── Aggregate metrics ─────────────────────────────────────────────────


@dataclass
class MetricSummary:
    """Descriptive statistics for a single metric across trials."""

    mean: float
    std: float
    ci_lower: float
    ci_upper: float
    n: int


@dataclass
class StrategyMetrics:
    """Aggregated metrics for one (strategy, topology) combination."""

    strategy: str
    topology: str
    num_trials: int
    detection_rate: MetricSummary
    mean_time_to_detect: MetricSummary
    cost_efficiency: MetricSummary
    attacker_dwell_time: MetricSummary
    defender_utility: MetricSummary
    attacker_exfiltration: MetricSummary


def _summarise(values: list[float]) -> MetricSummary:
    """Compute mean, std, and 95% CI for a list of values."""
    n = len(values)
    if n == 0:
        return MetricSummary(mean=0.0, std=0.0, ci_lower=0.0, ci_upper=0.0, n=0)
    mean = sum(values) / n
    if n == 1:
        return MetricSummary(mean=mean, std=0.0, ci_lower=mean, ci_upper=mean, n=1)
    variance = sum((x - mean) ** 2 for x in values) / (n - 1)
    std = math.sqrt(variance)
    margin = 1.96 * std / math.sqrt(n)
    return MetricSummary(
        mean=mean,
        std=std,
        ci_lower=mean - margin,
        ci_upper=mean + margin,
        n=n,
    )


def _binomial_ci(successes: int, n: int) -> MetricSummary:
    """Compute detection rate with Wilson score 95% CI."""
    if n == 0:
        return MetricSummary(mean=0.0, std=0.0, ci_lower=0.0, ci_upper=0.0, n=0)
    p = successes / n
    std = math.sqrt(p * (1 - p) / n) if n > 0 else 0.0
    # Wilson score interval.
    z = 1.96
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    spread = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return MetricSummary(
        mean=p,
        std=std,
        ci_lower=max(0.0, centre - spread),
        ci_upper=min(1.0, centre + spread),
        n=n,
    )


def compute_metrics(
    trials: list[TrialResult],
    strategy: str,
    topology: str,
) -> StrategyMetrics:
    """Aggregate a list of TrialResults into StrategyMetrics."""
    n = len(trials)
    detected_count = sum(1 for t in trials if t.detected)
    detection_rate = _binomial_ci(detected_count, n)

    # MTTD: only across trials where detection occurred.
    mttd_values = [
        float(t.detection_round) for t in trials if t.detection_round is not None
    ]
    mttd = _summarise(mttd_values) if mttd_values else MetricSummary(
        mean=float("inf"), std=0.0, ci_lower=float("inf"), ci_upper=float("inf"), n=0,
    )

    # Cost efficiency: detection rate / spent (per trial).
    cost_values = [
        (1.0 if t.detected else 0.0) / max(t.defender_spent, 1e-8)
        for t in trials
    ]
    cost_efficiency = _summarise(cost_values)

    # Dwell time.
    dwell_values = [float(t.attacker_dwell_time) for t in trials]
    dwell = _summarise(dwell_values)

    # Defender utility: +exfil if detected, -exfil if not (simplified).
    utility_values = [
        t.exfiltrated_value if t.detected else -t.exfiltrated_value
        for t in trials
    ]
    # Actually, use: detected → positive reward, not detected → negative penalty.
    # Simpler: defender wins = +1 per detection, loses = -exfiltrated_value.
    utility_values = []
    for t in trials:
        if t.detected:
            utility_values.append(1.0 + t.num_detections * 0.1)
        else:
            utility_values.append(-t.exfiltrated_value)
    defender_utility = _summarise(utility_values)

    # Attacker exfiltration.
    exfil_values = [t.exfiltrated_value for t in trials]
    exfil = _summarise(exfil_values)

    return StrategyMetrics(
        strategy=strategy,
        topology=topology,
        num_trials=n,
        detection_rate=detection_rate,
        mean_time_to_detect=mttd,
        cost_efficiency=cost_efficiency,
        attacker_dwell_time=dwell,
        defender_utility=defender_utility,
        attacker_exfiltration=exfil,
    )


# ── Statistical comparison ────────────────────────────────────────────


@dataclass
class PairwiseComparison:
    """Result of a Mann-Whitney U test between two strategy samples."""

    strategy_a: str
    strategy_b: str
    metric: str
    u_statistic: float
    p_value: float
    significant: bool


def compare_strategies(
    results_a: list[float],
    results_b: list[float],
    strategy_a: str,
    strategy_b: str,
    metric_name: str,
) -> PairwiseComparison:
    """Run a Mann-Whitney U test comparing two strategy samples."""
    if len(results_a) < 2 or len(results_b) < 2:
        return PairwiseComparison(
            strategy_a=strategy_a,
            strategy_b=strategy_b,
            metric=metric_name,
            u_statistic=0.0,
            p_value=1.0,
            significant=False,
        )

    try:
        stat, pval = mannwhitneyu(results_a, results_b, alternative="two-sided")
    except ValueError:
        stat, pval = 0.0, 1.0

    return PairwiseComparison(
        strategy_a=strategy_a,
        strategy_b=strategy_b,
        metric=metric_name,
        u_statistic=float(stat),
        p_value=float(pval),
        significant=bool(pval < 0.05),
    )


def compare_all_pairs(
    all_trials: dict[str, list[TrialResult]],
) -> list[PairwiseComparison]:
    """Compare sse_optimal against each baseline on key metrics."""
    comparisons: list[PairwiseComparison] = []

    sse_trials = all_trials.get("sse_optimal", [])
    if not sse_trials:
        return comparisons

    baselines = ["uniform", "static", "heuristic"]
    metrics = {
        "detection_rate": lambda t: 1.0 if t.detected else 0.0,
        "dwell_time": lambda t: float(t.attacker_dwell_time),
        "exfiltrated_value": lambda t: t.exfiltrated_value,
    }

    sse_values: dict[str, list[float]] = {
        name: [fn(t) for t in sse_trials] for name, fn in metrics.items()
    }

    for baseline in baselines:
        baseline_trials = all_trials.get(baseline, [])
        if not baseline_trials:
            continue

        baseline_values: dict[str, list[float]] = {
            name: [fn(t) for t in baseline_trials] for name, fn in metrics.items()
        }

        for metric_name in metrics:
            comparisons.append(
                compare_strategies(
                    sse_values[metric_name],
                    baseline_values[metric_name],
                    "sse_optimal",
                    baseline,
                    metric_name,
                )
            )

    return comparisons
