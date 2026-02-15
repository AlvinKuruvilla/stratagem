"""Evaluation and benchmarking for defender strategies."""

from stratagem.evaluation.benchmark import (
    BenchmarkConfig,
    BenchmarkResult,
    export_results_csv,
    export_results_json,
    run_benchmark,
    run_game_sync,
)
from stratagem.evaluation.metrics import (
    MetricSummary,
    PairwiseComparison,
    StrategyMetrics,
    TrialResult,
    compare_all_pairs,
    compare_strategies,
    compute_metrics,
    extract_trial_result,
)

__all__ = [
    "BenchmarkConfig",
    "BenchmarkResult",
    "MetricSummary",
    "PairwiseComparison",
    "StrategyMetrics",
    "TrialResult",
    "compare_all_pairs",
    "compare_strategies",
    "compute_metrics",
    "export_results_csv",
    "export_results_json",
    "extract_trial_result",
    "run_benchmark",
    "run_game_sync",
]
