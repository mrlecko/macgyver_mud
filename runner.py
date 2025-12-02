#!/usr/bin/env python3
"""
MacGyver Active Inference Demo - Runner
Entry point for executing agent episodes
"""
import argparse
import sys
from neo4j import GraphDatabase
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
import numpy as np

import config
from agent_runtime import AgentRuntime
from agent_runtime_robust import AgentRuntimeRobust
from agent_runtime_active import ActiveInferenceRuntime, build_model_from_graph, load_model_from_graph, save_model_to_graph
from graph_model import get_episode_stats


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="MacGyver Active Inference Demo - Locked Room Escape",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python runner.py --door-state unlocked
  python runner.py --door-state locked --max-steps 10
  python runner.py --door-state unlocked --verbose
  python runner.py --door-state locked --use-memory
  python runner.py --door-state unlocked --use-memory --adaptive --verbose-memory
  python runner.py --door-state locked --skill-mode crisp
  python runner.py --door-state unlocked --skill-mode balanced
  python runner.py --door-state locked --skill-mode hybrid --verbose
        """
    )

    parser.add_argument(
        "--door-state",
        choices=["locked", "unlocked"],
        required=True,
        help="Ground truth door state"
    )

    parser.add_argument(
        "--max-steps",
        type=int,
        default=config.MAX_STEPS,
        help=f"Maximum steps before giving up (default: {config.MAX_STEPS})"
    )

    parser.add_argument(
        "--initial-belief",
        type=float,
        default=config.INITIAL_BELIEF,
        help=f"Initial belief p(unlocked) (default: {config.INITIAL_BELIEF})"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed scoring information"
    )

    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Minimal output (just result)"
    )

    parser.add_argument(
        "--use-memory",
        action="store_true",
        help="Enable procedural memory (agent learns from past episodes)"
    )

    parser.add_argument(
        "--adaptive",
        action="store_true",
        help="Enable adaptive meta-parameters (adjusts exploration/exploitation)"
    )

    parser.add_argument(
        "--verbose-memory",
        action="store_true",
        help="Show memory reasoning in decision-making (requires --use-memory)"
    )

    parser.add_argument(
        "--reward-mode",
        choices=["naive", "strategic"],
        default="strategic",
        help="Reward mode: 'naive' (shows metric gaming) or 'strategic' (encourages smart play)"
    )

    parser.add_argument(
        "--skill-mode",
        choices=["crisp", "balanced", "hybrid"],
        default="hybrid",
        help="Skill selection mode: 'crisp' (base skills only), 'balanced' (multi-objective skills), or 'hybrid' (all skills)"
    )

    parser.add_argument(
        "--runtime",
        choices=["heuristic", "active"],
        default=config.AGENT_RUNTIME_MODE,
        help="Choose the agent runtime: 'heuristic' (current bandit) or 'active' (Active Inference beta)"
    )

    return parser.parse_args()


def print_header(console: Console, args):
    """Print episode header"""
    memory_status = ""
    if args.use_memory or args.adaptive:
        features = []
        if args.use_memory:
            features.append("Procedural Memory")
        if args.adaptive:
            features.append("Adaptive Params")
        memory_status = f"\n  [bold]Memory:[/bold] [green]{', '.join(features)} enabled[/green]"

    # Show reward mode (highlight if naive to indicate it's the "problematic" version)
    reward_mode_display = f"[yellow]{args.reward_mode}[/yellow]" if args.reward_mode == "naive" else f"[green]{args.reward_mode}[/green]"

    # Show skill mode with appropriate color
    skill_mode_colors = {"crisp": "cyan", "balanced": "magenta", "hybrid": "green"}
    skill_mode_display = f"[{skill_mode_colors.get(args.skill_mode, 'white')}]{args.skill_mode}[/]"

    header_text = f"""
[bold cyan]MacGyver Active Inference Demo[/bold cyan]
[dim]Locked Room Escape Scenario[/dim]

[bold]Configuration:[/bold]
  Ground Truth: Door is [bold {'green' if args.door_state == 'unlocked' else 'red'}]{args.door_state}[/]
  Initial Belief: p(unlocked) = {args.initial_belief:.2f}
  Max Steps: {args.max_steps}
  Reward Mode: {reward_mode_display}
  Skill Mode: {skill_mode_display}{memory_status}
    """
    console.print(Panel(header_text.strip(), box=box.ROUNDED))


def print_trace(console: Console, runtime: AgentRuntime, verbose: bool = False):
    """Print episode trace as a table"""
    trace = runtime.get_trace()

    if not trace:
        console.print("[yellow]No steps recorded[/yellow]")
        return

    # Create table
    table = Table(
        title="Episode Trace",
        box=box.SIMPLE,
        show_header=True,
        header_style="bold cyan"
    )

    table.add_column("Step", justify="center", style="dim")
    table.add_column("Skill", style="cyan")
    table.add_column("Observation", style="yellow")
    table.add_column("p(unlocked)", justify="right")
    table.add_column("Δp", justify="right", style="dim")

    for step in trace:
        step_idx = str(step["step_index"])
        skill = step["skill"]
        obs = step["observation"]
        p_before = step["p_before"]
        p_after = step["p_after"]
        delta = p_after - p_before

        # Format observation with color
        obs_display = obs.replace("obs_", "")
        if "locked" in obs or "stuck" in obs:
            obs_display = f"[red]{obs_display}[/red]"
        elif "unlocked" in obs or "opened" in obs or "escape" in obs:
            obs_display = f"[green]{obs_display}[/green]"

        # Format belief change
        belief_str = f"{p_before:.2f} → {p_after:.2f}"
        delta_str = f"{delta:+.2f}" if delta != 0 else "—"

        table.add_row(step_idx, skill, obs_display, belief_str, delta_str)

    console.print(table)


def print_trace_active(console: Console, trace: list):
    """Print episode trace for Active Inference runtime."""
    if not trace:
        console.print("[yellow]No steps recorded[/yellow]")
        return

    table = Table(
        title="Active Inference Episode Trace",
        box=box.SIMPLE,
        show_header=True,
        header_style="bold cyan"
    )
    table.add_column("Step", justify="center", style="dim")
    table.add_column("Action", style="cyan")
    table.add_column("Observation", style="yellow")
    table.add_column("p(unlocked)", justify="right")
    table.add_column("EFE", justify="right")

    for step in trace:
        belief_str = f"{step['p_before']:.2f} → {step['p_after']:.2f}"
        table.add_row(
            str(step["step_index"]),
            step["action"],
            step["observation"],
            belief_str,
            f"{step.get('efe', 0.0):.3f}",
        )

    console.print(table)


def print_decision_log(console: Console, runtime: AgentRuntime):
    """Print memory-influenced decision log"""
    if not runtime.decision_log:
        return

    console.print("\n[bold cyan]Decision Log (Memory Reasoning):[/bold cyan]")

    for decision in runtime.decision_log:
        step = decision["step"]
        belief = decision["belief"]
        selected = decision["selected"]
        score = decision["score"]
        explanation = decision.get("explanation")

        console.print(f"\n[bold]Step {step}:[/bold] belief={belief:.2f} → selected [cyan]{selected}[/cyan] (score={score:.2f})")

        if explanation and "reasoning" in explanation:
            console.print(f"  [dim]{explanation['reasoning']}[/dim]")

        # Show all scores for comparison
        if decision.get("all_scores"):
            console.print("  [dim]All skill scores:[/dim]")
            for skill_name, skill_score in decision["all_scores"]:
                prefix = "  →" if skill_name == selected else "   "
                console.print(f"    {prefix} {skill_name:15s}: {skill_score:6.2f}")


def print_summary(console: Console, runtime: AgentRuntime, door_state: str):
    """Print episode summary"""
    # Determine outcome
    if runtime.escaped:
        # Check how escaped
        trace = runtime.get_trace()
        last_obs = trace[-1]["observation"] if trace else "unknown"

        if "door" in last_obs:
            outcome = "[bold green]✓ ESCAPED VIA DOOR[/bold green]"
            method = "door"
        elif "window" in last_obs:
            outcome = "[bold green]✓ ESCAPED VIA WINDOW[/bold green]"
            method = "window"
        else:
            outcome = "[bold green]✓ ESCAPED[/bold green]"
            method = "unknown"
    else:
        outcome = "[bold red]✗ FAILED TO ESCAPE[/bold red]"
        method = "none"

    # Determine if strategy was optimal
    optimal = False
    if door_state == "unlocked" and method == "door":
        optimal = True
        strategy = "[green]Optimal[/green]"
    elif door_state == "locked" and method == "window":
        optimal = True
        strategy = "[green]Optimal[/green]"
    elif runtime.escaped:
        strategy = "[yellow]Suboptimal but escaped[/yellow]"
    else:
        strategy = "[red]Failed[/red]"

    summary_text = f"""
{outcome}

[bold]Summary:[/bold]
  Steps Taken: {runtime.step_count}
  Final Belief: p(unlocked) = {runtime.p_unlocked:.2f}
  Strategy: {strategy}
    """

    console.print(Panel(summary_text.strip(), box=box.ROUNDED, border_style="green" if optimal else "yellow"))


def main():
    """Main entry point"""
    args = parse_args()
    console = Console()

    # Set reward mode environment variable so config picks it up
    import os
    os.environ["REWARD_MODE"] = args.reward_mode

    # Reload config to pick up the new reward mode
    import importlib
    importlib.reload(config)

    # Print header (unless quiet)
    if not args.quiet:
        print_header(console, args)
        console.print()

    # Connect to Neo4j
    try:
        driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
    except Exception as e:
        console.print(f"[bold red]Error connecting to Neo4j:[/bold red] {e}", file=sys.stderr)
        console.print(f"[dim]URI: {config.NEO4J_URI}[/dim]", file=sys.stderr)
        sys.exit(1)

    try:
        with driver.session(database="neo4j") as session:
            if args.runtime == "heuristic":
                if not args.quiet:
                    console.print("[dim]Initializing heuristic agent...[/dim]")

                runtime_cls = AgentRuntimeRobust if config.ENABLE_ROBUST_SCENARIO else AgentRuntime
                runtime = runtime_cls(
                    session,
                    door_state=args.door_state,
                    initial_belief=args.initial_belief,
                    use_procedural_memory=args.use_memory,
                    adaptive_params=args.adaptive,
                    verbose_memory=args.verbose_memory,
                    skill_mode=args.skill_mode
                )

                if not args.quiet:
                    console.print("[dim]Running episode...[/dim]")
                    console.print()

                episode_id = runtime.run_episode(max_steps=args.max_steps)

                if not args.quiet:
                    print_trace(console, runtime, verbose=args.verbose)
                    console.print()

                if args.verbose_memory and not args.quiet:
                    print_decision_log(console, runtime)

                if args.quiet:
                    console.print("ESCAPED" if runtime.escaped else "FAILED")
                else:
                    print_summary(console, runtime, args.door_state)

                if args.verbose and not args.quiet:
                    console.print("\n[dim]Episode Stats from Graph:[/dim]")
                    stats = get_episode_stats(session, episode_id)
                    console.print(f"  Episode ID: {stats.get('id', 'N/A')}")
                    console.print(f"  Steps in Graph: {stats.get('step_count', 0)}")

            else:
                if not args.quiet:
                    console.print("[dim]Initializing Active Inference agent (beta)...[/dim]")

                model = load_model_from_graph(session) or build_model_from_graph(session)
                initial_belief_vec = np.array([1 - args.initial_belief, args.initial_belief], dtype=float)
                runtime_ai = ActiveInferenceRuntime(model=model, temperature=1.0, session=session)

                if not args.quiet:
                    console.print("[dim]Running episode...[/dim]")
                    console.print()

                episode_id = runtime_ai.run_episode(
                    door_state=args.door_state,
                    max_steps=args.max_steps,
                    initial_belief=initial_belief_vec,
                    policy_depth=2,
                )
                # Persist any learned parameters
                save_model_to_graph(session, runtime_ai.model)

                if not args.quiet:
                    print_trace_active(console, runtime_ai.get_trace())
                    console.print()

                if args.quiet:
                    console.print("ESCAPED" if runtime_ai.escaped else "FAILED")
                else:
                    outcome = "[bold green]✓ ESCAPED[/bold green]" if runtime_ai.escaped else "[bold red]✗ FAILED[/bold red]"
                    steps = len(runtime_ai.get_trace())
                    final_belief = runtime_ai.get_trace()[-1]["p_after"] if runtime_ai.get_trace() else args.initial_belief
                    summary_text = f"""
{outcome}

[bold]Summary (Active Inference):[/bold]
  Steps Taken: {steps}
  Final Belief: p(unlocked) = {final_belief:.2f}
"""
                    console.print(Panel(summary_text.strip(), box=box.ROUNDED, border_style="green" if runtime_ai.escaped else "yellow"))

    except Exception as e:
        console.print(f"[bold red]Error during execution:[/bold red] {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            console.print(traceback.format_exc(), file=sys.stderr)
        sys.exit(1)

    finally:
        driver.close()

    # Exit with success
    sys.exit(0 if runtime.escaped else 1)


if __name__ == "__main__":
    main()
