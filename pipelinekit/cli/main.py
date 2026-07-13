"""Main CLI entry point for PipelineKit."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
import structlog
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from pipelinekit.config import PipelineLoader
from pipelinekit.pipeline import PipelineExecutor

logger = structlog.get_logger()
console = Console()


@click.group()
@click.version_option(version="0.2.0", prog_name="pipelinekit")
@click.pass_context
def cli(ctx):
    """PipelineKit - Modern ETL framework for API ingestion and data transformation."""
    ctx.ensure_object(dict)


@cli.command()
@click.argument("pipeline_name")
@click.option(
    "--config",
    "-c",
    default="config/pipelines.yaml",
    help="Path to pipeline configuration file",
    type=click.Path(exists=True),
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def run(pipeline_name: str, config: str, verbose: bool):
    """Run a specific pipeline by name.

    Example:
        pipelinekit run my_pipeline
        pipelinekit run my_pipeline --config custom/pipelines.yaml
    """
    if verbose:
        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(logging_level=10)
        )

    console.print(
        Panel.fit(
            f"[bold cyan]Running pipeline:[/bold cyan] {pipeline_name}",
            border_style="cyan",
        )
    )

    try:
        pipelines = PipelineLoader.load_from_file(config)
        pipeline = next((p for p in pipelines if p["name"] == pipeline_name), None)

        if not pipeline:
            console.print(f"[bold red]❌ Pipeline '{pipeline_name}' not found[/bold red]")
            available = ", ".join([p["name"] for p in pipelines])
            console.print(f"[yellow]Available pipelines:[/yellow] {available}")
            sys.exit(1)

        executor = PipelineExecutor()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Executing {pipeline_name}...", total=None)
            asyncio.run(executor.execute(pipeline))
            progress.update(task, completed=True)

        console.print(f"[bold green]Pipeline '{pipeline_name}' completed successfully[/bold green]")

    except Exception as e:
        console.print(f"[bold red]❌ Pipeline failed:[/bold red] {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.option(
    "--config",
    "-c",
    default="config/pipelines.yaml",
    help="Path to pipeline configuration file",
    type=click.Path(exists=True),
)
def list(config: str):
    """List all available pipelines.

    Example:
        pipelinekit list
        pipelinekit list --config custom/pipelines.yaml
    """
    try:
        pipelines = PipelineLoader.load_from_file(config)

        if not pipelines:
            console.print("[yellow]No pipelines found[/yellow]")
            return

        table = Table(title="Available Pipelines", show_header=True, header_style="bold cyan")
        table.add_column("Name", style="cyan")
        table.add_column("Enabled", style="green")
        table.add_column("Connector", style="yellow")
        table.add_column("Transformer", style="magenta")
        table.add_column("Sinks", style="blue")

        for pipeline in pipelines:
            enabled = "Yes" if pipeline.get("enabled", True) else "No"
            connector_type = pipeline.get("connector", {}).get("type", "N/A")
            transformer_type = pipeline.get("transformer", {}).get("type", "N/A")
            sinks = ", ".join([s.get("type", "unknown") for s in pipeline.get("sinks", [])])

            table.add_row(
                pipeline["name"],
                enabled,
                connector_type,
                transformer_type,
                sinks or "N/A",
            )

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]❌ Failed to load pipelines:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--config",
    "-c",
    default="config/pipelines.yaml",
    help="Path to pipeline configuration file",
    type=click.Path(exists=True),
)
def validate(config: str):
    """Validate pipeline configuration.

    Example:
        pipelinekit validate
        pipelinekit validate --config custom/pipelines.yaml
    """
    console.print(f"[cyan]Validating configuration:[/cyan] {config}")

    try:
        pipelines = PipelineLoader.load_from_file(config)

        errors = []
        for pipeline in pipelines:
            name = pipeline.get("name")
            if not name:
                errors.append("Pipeline missing 'name' field")
                continue

            if "connector" not in pipeline:
                errors.append(f"Pipeline '{name}': missing 'connector' configuration")

            if "transformer" not in pipeline:
                errors.append(f"Pipeline '{name}': missing 'transformer' configuration")

            if "sinks" not in pipeline or not pipeline["sinks"]:
                errors.append(f"Pipeline '{name}': missing or empty 'sinks' configuration")

        if errors:
            console.print("[bold red]❌ Validation failed:[/bold red]")
            for error in errors:
                console.print(f"  • {error}")
            sys.exit(1)
        else:
            console.print(
                f"[bold green]✅ Configuration is valid ({len(pipelines)} pipelines)[/bold green]"
            )

    except Exception as e:
        console.print(f"[bold red]❌ Validation error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("name")
@click.option(
    "--output",
    "-o",
    default="config/pipelines.yaml",
    help="Output path for the pipeline configuration",
)
def init(name: str, output: str):
    """Initialize a new pipeline configuration template.

    Example:
        pipelinekit init my_pipeline
        pipelinekit init my_pipeline --output custom/pipelines.yaml
    """
    template = f"""pipelines:
  - name: {name}
    enabled: true
    connector:
      type: http
      config:
        url: https://api.example.com/data
        method: GET
        headers:
          Authorization: Bearer YOUR_TOKEN
    transformer:
      type: json_normalizer
      config:
        flatten: true
    sinks:
      - type: file
        config:
          path: data/output/{name}
          format: json
"""

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        console.print(f"[yellow]⚠️  File already exists:[/yellow] {output}")
        if not click.confirm("Append to existing file?"):
            console.print("[red]Cancelled[/red]")
            return

        with output_path.open("a") as f:
            f.write("\n" + template)
    else:
        with output_path.open("w") as f:
            f.write(template)

    console.print(f"[bold green]✅ Pipeline template created:[/bold green] {output}")
    console.print(f"[cyan]Edit the file and run:[/cyan] pipelinekit run {name}")


@cli.command()
@click.argument("pipeline_name")
@click.option(
    "--config",
    "-c",
    default="config/pipelines.yaml",
    help="Path to pipeline configuration file",
    type=click.Path(exists=True),
)
def test(pipeline_name: str, config: str):
    """Test pipeline connections without running full pipeline.

    Example:
        pipelinekit test my_pipeline
    """
    console.print(f"[cyan]Testing pipeline:[/cyan] {pipeline_name}")

    try:
        pipelines = PipelineLoader.load_from_file(config)
        pipeline = next((p for p in pipelines if p["name"] == pipeline_name), None)

        if not pipeline:
            console.print(f"[bold red]❌ Pipeline '{pipeline_name}' not found[/bold red]")
            sys.exit(1)

        # Test connector
        from pipelinekit.sources import HttpConnector, RestConnector

        connector_config = pipeline.get("connector", {})
        connector_type = connector_config.get("type")

        if connector_type == "http":
            connector = HttpConnector(connector_config.get("config", {}))
        elif connector_type == "rest":
            connector = RestConnector(connector_config.get("config", {}))
        else:
            console.print(f"[yellow]⚠️  Unknown connector type:[/yellow] {connector_type}")
            return

        async def test_connection():
            try:
                await connector.fetch()
                console.print("[bold green]✅ Connector test passed[/bold green]")
            except Exception as e:
                console.print(f"[bold red]❌ Connector test failed:[/bold red] {e}")
            finally:
                await connector.close()

        asyncio.run(test_connection())

    except Exception as e:
        console.print(f"[bold red]❌ Test failed:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
