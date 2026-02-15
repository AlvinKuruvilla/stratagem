"""Stratagem CLI entrypoint."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from stratagem.environment.network import NetworkTopology

app = typer.Typer(
    name="stratagem",
    help="Stackelberg security games powered by autonomous LLM agents.",
    no_args_is_help=True,
)
console = Console()

TOPOLOGIES = {
    "small": NetworkTopology.small_enterprise,
    "medium": NetworkTopology.medium_enterprise,
    "large": NetworkTopology.large_enterprise,
}

CONFIGS_DIR = Path(__file__).resolve().parent.parent.parent / "configs" / "topologies"


def _resolve_topology(name: str) -> NetworkTopology:
    """Load a topology by preset name or YAML path."""
    if name in TOPOLOGIES:
        return TOPOLOGIES[name]()
    path = CONFIGS_DIR / f"{name}.yaml"
    if path.exists():
        return NetworkTopology.from_yaml(path)
    path = Path(name)
    if path.exists():
        return NetworkTopology.from_yaml(path)
    console.print(f"[red]Unknown topology: {name}[/red]")
    raise typer.Exit(1)


# Each command below maps to a `stratagem <verb>` invocation. They share
# _resolve_topology to accept either a preset name or a YAML file path.


@app.command()
def run(
    topology: str = typer.Option(
        "small", help="Topology preset (small/medium/large) or YAML path."
    ),
    rounds: int = typer.Option(50, help="Maximum game rounds."),
    budget: float = typer.Option(10.0, help="Defender budget."),
    model: str = typer.Option("got-oss:20b", help="LLM model name."),
    base_url: str = typer.Option(
        "http://localhost:1234/v1", help="OpenAI-compatible API URL."
    ),
    seed: int = typer.Option(42, help="Random seed for reproducibility."),
) -> None:
    """Run a single Stackelberg security game."""
    from stratagem.game.graph import build_game_graph, create_initial_state

    topo = _resolve_topology(topology)
    console.print(f"[bold]{topo.summary()}[/bold]")
    console.print(f"Max rounds: {rounds}, budget: {budget}, seed: {seed}")
    console.print(f"LLM: {model} @ {base_url}\n")

    state = create_initial_state(topo, budget, rounds, seed=seed)
    graph = build_game_graph(model=model, base_url=base_url)
    compiled = graph.compile()

    console.print("[bold green]Starting game...[/bold green]\n")
    final_state = compiled.invoke(state)

    console.print("\n[bold]Game Over![/bold]")
    console.print(f"Winner: [bold cyan]{final_state['winner']}[/bold cyan]")
    console.print(f"Rounds played: {final_state['current_round'] - 1}/{rounds}")

    attacker = final_state["attacker"]
    console.print(f"Attacker exfiltrated: {attacker['exfiltrated_value']:.1f}")
    console.print(f"Attacker detected: {attacker['detected']}")
    console.print(f"Detections: {len(final_state['detections'])}")


@app.command()
def benchmark(
    topology: str = typer.Option("small", help="Topology preset or YAML path."),
    trials: int = typer.Option(100, help="Number of trial runs per strategy."),
) -> None:
    """Benchmark Stackelberg-optimal strategy against baselines."""
    topo = _resolve_topology(topology)
    console.print(f"[bold]Benchmarking on {topo.name} ({trials} trials)[/bold]")
    console.print("[yellow]Benchmark engine not yet implemented — coming in Phase 4.[/yellow]")


@app.command()
def dashboard(
    host: str = typer.Option("127.0.0.1", help="Host to bind to."),
    port: int = typer.Option(8000, help="Port to bind to."),
) -> None:
    """Launch the web dashboard (FastAPI + Vite dev server)."""
    try:
        import uvicorn
    except ImportError:
        console.print("[red]Web dependencies not installed. Run: pip install -e '.[web]'[/red]")
        raise typer.Exit(1)

    console.print(f"[bold green]Starting Stratagem dashboard on http://{host}:{port}[/bold green]")
    console.print("[dim]API docs: http://{host}:{port}/docs[/dim]")
    uvicorn.run("stratagem.web.app:app", host=host, port=port, reload=True)


@app.command(name="topology")
def topology_cmd(
    action: str = typer.Argument("list", help="Action: list or show."),
    name: str = typer.Argument("", help="Topology name (for 'show')."),
) -> None:
    """List available topologies or show details of one."""
    if action == "list":
        table = Table(title="Available Topologies")
        table.add_column("Name", style="cyan")
        table.add_column("Nodes", justify="right")
        table.add_column("Edges", justify="right")
        table.add_column("Entry Points", justify="right")
        table.add_column("High-Value Targets", justify="right")
        for preset_name, factory in TOPOLOGIES.items():
            topo = factory()
            table.add_row(
                preset_name,
                str(topo.node_count),
                str(topo.graph.number_of_edges()),
                str(len(topo.entry_points())),
                str(len(topo.high_value_targets())),
            )
        # Also list YAML files in configs dir.
        if CONFIGS_DIR.exists():
            for yaml_file in sorted(CONFIGS_DIR.glob("*.yaml")):
                topo = NetworkTopology.from_yaml(yaml_file)
                table.add_row(
                    f"{yaml_file.stem} (yaml)",
                    str(topo.node_count),
                    str(topo.graph.number_of_edges()),
                    str(len(topo.entry_points())),
                    str(len(topo.high_value_targets())),
                )
        console.print(table)
    elif action == "show":
        if not name:
            console.print("[red]Provide a topology name: stratagem topology show <name>[/red]")
            raise typer.Exit(1)
        topo = _resolve_topology(name)
        console.print(f"[bold]{topo.summary()}[/bold]\n")
        table = Table(title="Nodes")
        table.add_column("ID", style="cyan")
        table.add_column("Type")
        table.add_column("OS")
        table.add_column("Services")
        table.add_column("Value", justify="right")
        table.add_column("Entry?", justify="center")
        for nid in sorted(topo.nodes):
            attrs = topo.get_attrs(nid)
            table.add_row(
                nid,
                attrs.node_type.value,
                attrs.os.value,
                ", ".join(s.value for s in attrs.services),
                f"{attrs.value:.1f}",
                "yes" if attrs.is_entry_point else "",
            )
        console.print(table)
    else:
        console.print(f"[red]Unknown action: {action}. Use 'list' or 'show'.[/red]")
        raise typer.Exit(1)
