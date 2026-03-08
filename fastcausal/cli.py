"""
CLI entry points for fastcausal.

Provides commands: parse, run, paths, report, analyze.
"""

import click


@click.group()
@click.version_option()
def main():
    """fastcausal - Fast, easy-to-use causal discovery analysis tools."""
    pass


@main.command()
@click.option("--config", required=True, type=click.Path(exists=True), help="Path to config.yaml")
def parse(config):
    """Prepare and preprocess data from a config file."""
    from fastcausal.pipeline.config import load_config
    from fastcausal.pipeline.parse import run_parse

    cfg = load_config(config)
    run_parse(cfg)


@main.command()
@click.option("--config", required=True, type=click.Path(exists=True), help="Path to config.yaml")
@click.option("--start", default=0, help="Start index for case processing")
@click.option("--end", default=-1, help="End index for case processing (-1 = all)")
@click.option("--list", "list_cases", is_flag=True, help="List cases without processing")
def run(config, start, end, list_cases):
    """Run causal discovery analysis."""
    from fastcausal.pipeline.config import load_config
    from fastcausal.pipeline.batch import run_batch

    cfg = load_config(config)
    run_batch(cfg, start=start, end=end, list_cases=list_cases)


@main.command()
@click.option("--config", required=True, type=click.Path(exists=True), help="Path to config.yaml")
def paths(config):
    """Compute path effect sizes and generate heatmaps."""
    from fastcausal.pipeline.config import load_config
    from fastcausal.pipeline.paths import run_paths

    cfg = load_config(config)
    run_paths(cfg)


@main.command()
@click.option("--config", required=True, type=click.Path(exists=True), help="Path to config.yaml")
@click.option("--mode", default="1wide", type=click.Choice(["1wide", "2wide", "3wide"]), help="Report layout mode")
@click.option("--stub", default="_label.png", help="Image filename suffix to include")
def report(config, mode, stub):
    """Generate analysis report document."""
    from fastcausal.pipeline.config import load_config
    from fastcausal.pipeline.report import run_report

    cfg = load_config(config)
    run_report(cfg, mode=mode, stub=stub)


@main.command()
@click.argument("datafile", type=click.Path(exists=True))
@click.option("--algorithm", default="gfci", type=click.Choice(["pc", "fges", "gfci"]), help="Causal discovery algorithm")
@click.option("--alpha", default=0.05, type=float, help="Significance level")
@click.option("--penalty-discount", default=1.0, type=float, help="BIC penalty multiplier")
@click.option("--output", default=".", type=click.Path(), help="Output directory")
def analyze(datafile, algorithm, alpha, penalty_discount, output):
    """Quick single-file causal analysis."""
    import os
    import pandas as pd
    from fastcausal import FastCausal

    fc = FastCausal()
    df = fc.load_csv(datafile)

    kwargs = {}
    if algorithm in ("pc", "gfci"):
        kwargs["alpha"] = alpha
    if algorithm in ("fges", "gfci"):
        kwargs["penalty_discount"] = penalty_discount

    results, dg = fc.run_search(df, algorithm=algorithm, run_sem=False, **kwargs)

    os.makedirs(output, exist_ok=True)
    graph_path = os.path.join(output, os.path.splitext(os.path.basename(datafile))[0])
    if results["edges"]:
        fc.save_graph(dg, graph_path, plot_format="png")
        click.echo(f"Graph saved to: {graph_path}")

    click.echo(f"Edges found: {len(results.get('edges', []))}")
    for edge in results.get("edges", []):
        click.echo(f"  {edge}")
