"""Palantir analytics CLI — Typer app with subcommand routing."""

import typer

app = typer.Typer(
    name="palantir-analytics",
    help="Palantir ground-segment analytics — export, passes, trends.",
    no_args_is_help=True,
)


@app.command()
def export() -> None:
    """Dump archived telemetry to CSV + plots (PAL-201)."""
    typer.echo("export: not implemented yet")


@app.command()
def passes() -> None:
    """Predict ground-station visibility passes (PAL-202)."""
    typer.echo("passes: not implemented yet")


if __name__ == "__main__":
    app()
