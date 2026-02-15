"""Rich terminal dashboard for benchmark results.

Renders three sections:
1. Strategy comparison table — metrics per (strategy, topology)
2. Statistical significance table — Mann-Whitney U pairwise tests
3. Summary panel — headline numbers for SSE vs best baseline
"""

from __future__ import annotations

import math

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from stratagem.evaluation.benchmark import BenchmarkResult
from stratagem.evaluation.metrics import MetricSummary


def _fmt(m: MetricSummary, precision: int = 3, pct: bool = False) -> str:
    """Format a MetricSummary as 'mean +/- std'."""
    if m.n == 0:
        return "-"
    if math.isinf(m.mean):
        return "N/A"
    if pct:
        return f"{m.mean * 100:.1f}% +/- {m.std * 100:.1f}%"
    return f"{m.mean:.{precision}f} +/- {m.std:.{precision}f}"


def render_benchmark_dashboard(
    result: BenchmarkResult,
    console: Console | None = None,
) -> None:
    """Render the benchmark results as Rich tables to the console."""
    if console is None:
        console = Console()

    # ── 1. Strategy comparison table ──────────────────────────────────

    table = Table(
        title="Strategy Comparison",
        title_style="bold",
        border_style="dim",
        header_style="bold cyan",
    )
    table.add_column("Strategy", style="bold")
    table.add_column("Topology")
    table.add_column("Trials", justify="right")
    table.add_column("Det. Rate", justify="right")
    table.add_column("MTTD", justify="right")
    table.add_column("Cost Eff.", justify="right")
    table.add_column("Dwell Time", justify="right")
    table.add_column("Utility", justify="right")
    table.add_column("Exfiltration", justify="right")

    for sm in result.strategy_metrics:
        is_sse = sm.strategy == "sse_optimal"
        style = "bold green" if is_sse else ""

        table.add_row(
            sm.strategy,
            sm.topology,
            str(sm.num_trials),
            _fmt(sm.detection_rate, pct=True),
            _fmt(sm.mean_time_to_detect),
            _fmt(sm.cost_efficiency),
            _fmt(sm.attacker_dwell_time),
            _fmt(sm.defender_utility),
            _fmt(sm.attacker_exfiltration),
            style=style,
        )

    console.print()
    console.print(table)

    # ── 2. Statistical significance table ─────────────────────────────

    if result.comparisons:
        sig_table = Table(
            title="Statistical Significance (Mann-Whitney U)",
            title_style="bold",
            border_style="dim",
            header_style="bold cyan",
        )
        sig_table.add_column("Comparison")
        sig_table.add_column("Metric")
        sig_table.add_column("U-stat", justify="right")
        sig_table.add_column("p-value", justify="right")
        sig_table.add_column("Significant", justify="center")

        for comp in result.comparisons:
            sig_text = (
                Text("YES", style="bold green")
                if comp.significant
                else Text("no", style="dim")
            )
            p_style = "green" if comp.significant else ""

            sig_table.add_row(
                f"{comp.strategy_a} vs {comp.strategy_b}",
                comp.metric,
                f"{comp.u_statistic:.0f}",
                Text(f"{comp.p_value:.4f}", style=p_style),
                sig_text,
            )

        console.print()
        console.print(sig_table)

    # ── 3. Summary panel ──────────────────────────────────────────────

    summary_lines: list[str] = []

    # Group metrics by topology.
    topologies = sorted({sm.topology for sm in result.strategy_metrics})
    for topo in topologies:
        topo_metrics = [sm for sm in result.strategy_metrics if sm.topology == topo]
        sse_m = next((sm for sm in topo_metrics if sm.strategy == "sse_optimal"), None)
        if sse_m is None:
            continue

        baselines = [sm for sm in topo_metrics if sm.strategy != "sse_optimal"]
        if not baselines:
            continue

        best_baseline = max(baselines, key=lambda sm: sm.detection_rate.mean)
        rate_diff = sse_m.detection_rate.mean - best_baseline.detection_rate.mean

        if rate_diff > 0:
            pct_improvement = (rate_diff / max(best_baseline.detection_rate.mean, 1e-8)) * 100
            summary_lines.append(
                f"[bold]{topo}[/bold]: SSE achieves [green]{pct_improvement:.1f}% higher[/green] "
                f"detection rate than best baseline ({best_baseline.strategy})"
            )
        else:
            summary_lines.append(
                f"[bold]{topo}[/bold]: SSE detection rate comparable to {best_baseline.strategy}"
            )

        # MTTD comparison.
        sse_mttd = sse_m.mean_time_to_detect.mean
        baseline_mttds = [
            sm.mean_time_to_detect.mean
            for sm in baselines
            if not math.isinf(sm.mean_time_to_detect.mean)
        ]
        if not math.isinf(sse_mttd) and baseline_mttds:
            best_mttd = min(baseline_mttds)
            if sse_mttd < best_mttd:
                pct_faster = ((best_mttd - sse_mttd) / best_mttd) * 100
                summary_lines.append(
                    f"  MTTD: [green]{pct_faster:.1f}% lower[/green] than best baseline"
                )

    if summary_lines:
        console.print()
        console.print(Panel(
            "\n".join(summary_lines),
            title="Summary",
            border_style="green",
        ))

    # Total trials summary.
    console.print()
    console.print(
        f"[dim]Total trials: {len(result.trial_results)} | "
        f"Strategies: {len(result.config.strategies)} | "
        f"Topologies: {len(result.config.topologies)}[/dim]"
    )
