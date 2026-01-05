import os
import shutil
import subprocess
import sys
from pathlib import Path

import click
from typing_extensions import Annotated

from .analyzer import Analyzer
from .gatherer import GnewsGatherer, GnewsQuery
from .generator import GnewsGenerator
from .logs import log
from .orchestrator import Orchestrator
from .visualizer import Visualizer

orchestrator = Orchestrator()


@click.group()
def cli():
    """looksatwords CLI - Gather, generate, analyze, and visualize language data."""
    pass


@cli.command()
@click.option(
    "--keywords", "-k", multiple=True, default=["test"], help="Keywords to search for"
)
@click.option("--table", "-t", default="io", help="Table to save to")
@click.option("--num_gen", "-f", default=3, help="Number of articles to generate")
@click.option("--num_gath", "-g", default=3, help="Number of articles to gather")
@click.option(
    "--analysis_level",
    "-a",
    default="default",
    help="Analysis level, either leave blank for none, or 'default' for default analysis",
)
@click.option(
    "--visuals_out",
    "-v",
    multiple=True,
    default=["sentiment", "wordcount", "grammar"],
    help="Visuals to output, blank for none any of 'sentiment', 'wordcount', 'grammar'",
)
def run(keywords, table, num_gen, num_gath, analysis_level, visuals_out):
    """Orchestrates the gathering, generating, analyzing, and visualizing of articles."""
    # Create query with top news (keywords parameter not used in current GnewsQuery API)
    query = GnewsQuery(top=True)
    
    orchestrator.add_gatherer(
        GnewsGatherer(
            table_name=table,
            q=query,
            n=num_gath,
        )
    )
    orchestrator.gather()
    orchestrator.save()

    if analysis_level == "default":
        orchestrator.analyze()
    if len(visuals_out) > 0:
        orchestrator.visualize()


@cli.command()
@click.option("--cov", is_flag=True, help="Run with coverage report")
@click.option("--html", is_flag=True, help="Generate HTML coverage report")
@click.option("--parallel", "-n", is_flag=True, help="Run tests in parallel")
@click.option("--timeout", type=int, default=None, help="Test timeout in seconds")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--file", "-f", help="Run specific test file")
def test(cov, html, parallel, timeout, verbose, file):
    """Run pytest tests with various options.

    Examples:
        looksatwords test                      # Run all tests
        looksatwords test --cov               # With coverage
        looksatwords test --html --cov        # With HTML coverage report
        looksatwords test -n                  # Parallel execution
        looksatwords test -f test_analyzer    # Specific test file
        looksatwords test -v                  # Verbose
        looksatwords test --timeout 60        # With 60 second timeout
    """
    click.echo("Running tests...\n")

    cmd = [sys.executable, "-m", "pytest"]

    # Add test path or specific file
    if file:
        cmd.append(
            f"looksatwords/tests/test_{file}.py"
            if not file.startswith("test_")
            else f"looksatwords/tests/{file}.py"
        )
    else:
        cmd.append("looksatwords/tests/")

    # Verbosity
    if verbose:
        cmd.append("-vv")
    else:
        cmd.append("-v")

    # Coverage
    if cov:
        cmd.extend(["--cov=looksatwords", "--cov-report=term-missing"])
        if html:
            cmd.append("--cov-report=html")
            click.echo("HTML coverage report will be saved to htmlcov/index.html\n")

    # Parallel execution
    if parallel:
        cmd.extend(["-n", "auto"])

    # Timeout
    if timeout is not None:
        cmd.append(f"--timeout={timeout}")

    result = subprocess.run(cmd)

    if result.returncode == 0:
        click.echo("\nAll tests passed!")
    else:
        click.echo("\nSome tests failed.")

    sys.exit(result.returncode)


@cli.command("test-api")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--timeout", type=int, default=30, help="Test timeout in seconds")
def test_api(verbose, timeout):
    """Run API integration tests.
    
    Examples:
        looksatwords test-api                # Run API tests
        looksatwords test-api -v             # Verbose output
        looksatwords test-api --timeout 60   # Custom timeout
    """
    click.echo("Running API integration tests...\n")

    cmd = [sys.executable, "-m", "pytest", "looksatwords/tests/", "-k", "api"]

    if verbose:
        cmd.append("-vv")
    else:
        cmd.append("-v")

    if timeout:
        cmd.append(f"--timeout={timeout}")

    result = subprocess.run(cmd)

    if result.returncode == 0:
        click.echo("\nAll API tests passed!")
    else:
        click.echo("\nSome API tests failed.")

    sys.exit(result.returncode)


@cli.command("test-e2e")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--browser", default="chromium", help="Browser to use (chromium, firefox, webkit)")
@click.option("--headed", is_flag=True, help="Run in headed mode (show browser window)")
def test_e2e(verbose, browser, headed):
    """Run end-to-end tests with playwright.
    
    Examples:
        looksatwords test-e2e                           # Run E2E tests
        looksatwords test-e2e -v                        # Verbose output
        looksatwords test-e2e --browser firefox         # Use Firefox
        looksatwords test-e2e --headed                  # Show browser window
    """
    click.echo(f"Running end-to-end tests with {browser}...\n")

    cmd = [sys.executable, "-m", "pytest", "looksatwords/tests/", "-k", "e2e or playwright"]

    if verbose:
        cmd.append("-vv")
    else:
        cmd.append("-v")

    # Set browser environment variable for playwright
    env = os.environ.copy()
    env["BROWSER"] = browser
    if headed:
        env["PLAYWRIGHT_HEADED"] = "1"

    result = subprocess.run(cmd, env=env)

    if result.returncode == 0:
        click.echo(f"\nAll E2E tests passed!")
    else:
        click.echo("\nSome E2E tests failed.")

    sys.exit(result.returncode)


@cli.command()
def lint():
    """Run linters (ruff check)."""
    click.echo("Running linters...")
    result = subprocess.run([sys.executable, "-m", "ruff", "check", "looksatwords/"])
    sys.exit(result.returncode)


@cli.command("format-code")
def format_code():
    """Format code with ruff."""
    click.echo("Formatting code with ruff...")
    result = subprocess.run([sys.executable, "-m", "ruff", "format", "looksatwords/"])
    sys.exit(result.returncode)


@cli.command()
def clean():
    """Clean up generated files and caches."""
    click.echo("Cleaning up...")

    paths_to_clean = [
        Path(".pytest_cache"),
        Path("__pycache__"),
        Path(".ruff_cache"),
        Path(".coverage"),
        Path("htmlcov"),
    ]

    for path in paths_to_clean:
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
                click.echo(f"  [OK] Removed {path}")
            else:
                path.unlink()
                click.echo(f"  [OK] Removed {path}")

    # Clean nested __pycache__ directories
    for root, dirs, files in os.walk("looksatwords"):
        if "__pycache__" in dirs:
            pycache_path = os.path.join(root, "__pycache__")
            shutil.rmtree(pycache_path)
            click.echo(f"  [OK] Removed {pycache_path}")

    click.echo("\nCleanup complete!")


@cli.command("install-dev")
def install_dev():
    """Install development dependencies (via uv sync) and Playwright browsers."""
    click.echo("Syncing development environment...")
    result = subprocess.run(["uv", "sync"])
    if result.returncode != 0:
        sys.exit(result.returncode)
    
    # Install Playwright browsers for E2E tests
    click.echo("\nInstalling Playwright browsers for E2E tests...")
    pw_result = subprocess.run(["uv", "run", "playwright", "install", "chromium"])
    if pw_result.returncode != 0:
        click.echo("Warning: Playwright browser installation failed. E2E tests may be skipped.")
    else:
        click.echo("Playwright browsers installed successfully!")
    
    sys.exit(0)


def _run_server(host, port, reload, open_browser):
    """Internal function to run the FastAPI server."""
    import threading
    import webbrowser
    import uvicorn
    
    url = f"http://{host}:{port}"
    click.echo(f"Starting server on {url}")
    click.echo(f"API docs available at {url}/docs")
    click.echo("Press Ctrl+C to stop\n")
    
    if open_browser:
        # Open browser in a separate thread to not block server
        threading.Timer(1, lambda: webbrowser.open(url)).start()
    
    uvicorn.run(
        "looksatwords.app.main:app",
        host=host,
        port=port,
        reload=reload
    )


@cli.command()
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", "-p", default=8000, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
@click.option("--no-open", is_flag=True, help="Don't open browser automatically")
def serve(host, port, reload, no_open):
    """Start the application server (API + frontend).
    
    Examples:
        looksatwords serve                   # Serve on localhost:8000
        looksatwords serve -p 8080          # Serve on port 8080
        looksatwords serve --reload          # With auto-reload for development
        looksatwords serve --host 0.0.0.0    # Listen on all interfaces
        looksatwords serve --no-open         # Don't open browser
    """
    _run_server(host, port, reload, open_browser=not no_open)


# Alias for backward compatibility
@cli.command("run-server", hidden=True)
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", "-p", default=8000, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def run_server(host, port, reload):
    """Run the FastAPI backend server (deprecated, use 'serve' instead)."""
    click.echo("Note: 'run-server' is deprecated, use 'serve' instead.\n")
    _run_server(host, port, reload, open_browser=False)


@cli.command()
def doctor():
    """Check environment health and dependencies."""
    click.echo("\nChecking environment health...\n")

    # Python version
    version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    click.echo(f"  [OK] Python {version}")

    # Check key packages
    packages = [
        "click",
        "pandas",
        "nltk",
        "pytest",
        "ollama",
        "gnews",
    ]

    missing = []
    for pkg in packages:
        try:
            __import__(pkg)
            click.echo(f"  [OK] {pkg}")
        except ImportError:
            click.echo(f"  [MISSING] {pkg}")
            missing.append(pkg)

    if missing:
        click.echo(f"\nMissing packages: {', '.join(missing)}")
        click.echo("\nRun: uv sync")
    else:
        click.echo(f"\nAll systems nominal!")


if __name__ == "__main__":
    cli()
