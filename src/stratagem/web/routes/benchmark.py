"""POST /api/benchmark — run strategy benchmark and return metrics."""

from __future__ import annotations

import math

from fastapi import APIRouter

from stratagem.evaluation.benchmark import BenchmarkConfig, run_benchmark
from stratagem.evaluation.metrics import MetricSummary
from stratagem.web.schemas import (
    BenchmarkRequest,
    BenchmarkResponse,
    MetricSummaryResponse,
    PairwiseComparisonResponse,
    StrategyMetricsResponse,
)

router = APIRouter(prefix="/api", tags=["benchmark"])


def _metric_to_response(m: MetricSummary) -> MetricSummaryResponse:
    """Convert a MetricSummary dataclass to its Pydantic response model."""
    return MetricSummaryResponse(
        mean=m.mean if not math.isinf(m.mean) else -1.0,
        std=m.std if not math.isinf(m.std) else 0.0,
        ci_lower=m.ci_lower if not math.isinf(m.ci_lower) else -1.0,
        ci_upper=m.ci_upper if not math.isinf(m.ci_upper) else -1.0,
        n=m.n,
    )


@router.post("/benchmark", response_model=BenchmarkResponse)
def run_benchmark_endpoint(req: BenchmarkRequest) -> BenchmarkResponse:
    config = BenchmarkConfig(
        topologies=req.topologies,
        strategies=req.strategies,
        num_trials=req.num_trials,
        max_rounds=req.max_rounds,
        budget=req.budget,
        base_seed=req.base_seed,
    )

    result = run_benchmark(config)

    strategy_metrics = [
        StrategyMetricsResponse(
            strategy=sm.strategy,
            topology=sm.topology,
            num_trials=sm.num_trials,
            detection_rate=_metric_to_response(sm.detection_rate),
            mean_time_to_detect=_metric_to_response(sm.mean_time_to_detect),
            cost_efficiency=_metric_to_response(sm.cost_efficiency),
            attacker_dwell_time=_metric_to_response(sm.attacker_dwell_time),
            defender_utility=_metric_to_response(sm.defender_utility),
            attacker_exfiltration=_metric_to_response(sm.attacker_exfiltration),
        )
        for sm in result.strategy_metrics
    ]

    comparisons = [
        PairwiseComparisonResponse(
            strategy_a=c.strategy_a,
            strategy_b=c.strategy_b,
            metric=c.metric,
            u_statistic=c.u_statistic,
            p_value=c.p_value,
            significant=c.significant,
        )
        for c in result.comparisons
    ]

    return BenchmarkResponse(
        strategy_metrics=strategy_metrics,
        comparisons=comparisons,
        num_trials=len(result.trial_results),
        topologies=config.topologies,
        strategies=config.strategies,
    )
