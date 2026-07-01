"""CLI entry point for the Binance Futures Testnet trading bot."""

import os
import sys
from typing import Optional

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from bot.client import BinanceAPIError, BinanceFuturesClient, BinanceNetworkError
from bot.logging_config import LOG_FILE, setup_logging
from bot.orders import (
    enrich_market_order_response,
    format_order_response,
    format_request_summary,
    place_order,
)
from bot.validators import ValidationError, validate_order_request

app = typer.Typer(
    help="Place MARKET and LIMIT orders on Binance Futures Testnet (USDT-M).",
    add_completion=False,
)
console = Console()
logger = setup_logging()


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""


def _load_client() -> BinanceFuturesClient:
    load_dotenv()

    api_key = os.getenv("BINANCE_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_API_SECRET", "").strip()
    base_url = os.getenv("BINANCE_BASE_URL", "https://testnet.binancefuture.com").strip()

    if not api_key or not api_secret:
        console.print(
            "[red]Missing API credentials.[/red] Copy [.env.example](.env.example) to [.env](.env) "
            "and set BINANCE_API_KEY and BINANCE_API_SECRET."
        )
        raise ConfigurationError("Missing API credentials")

    try:
        return BinanceFuturesClient(api_key=api_key, api_secret=api_secret, base_url=base_url)
    except ValueError as exc:
        console.print(f"[red]Configuration error:[/red] {exc}")
        raise ConfigurationError(str(exc)) from exc


def _execute_order(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str] = None,
) -> None:
    try:
        request = validate_order_request(symbol, side, order_type, quantity, price)
    except ValidationError as exc:
        logger.error("Validation failed: %s", exc)
        console.print(f"[red]Validation error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(Panel(format_request_summary(request), title="Request", border_style="cyan"))

    try:
        client = _load_client()
    except ConfigurationError:
        raise typer.Exit(code=1)

    try:
        with client:
            response = place_order(client, request)
            response = enrich_market_order_response(client, request, response)
    except ValidationError as exc:
        logger.error("Validation failed: %s", exc)
        console.print(f"[red]Validation error:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    except BinanceAPIError as exc:
        logger.error("Binance API error: %s", exc)
        console.print(f"[red]Order failed:[/red] {exc.message}")
        raise typer.Exit(code=1) from exc
    except BinanceNetworkError as exc:
        logger.error("Network error: %s", exc)
        console.print(f"[red]Network error:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        logger.exception("Unexpected error while placing order")
        console.print(f"[red]Unexpected error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(Panel(format_order_response(response), title="Response", border_style="green"))
    console.print("[bold green]Order placed successfully.[/bold green]")
    console.print(f"Log file: {LOG_FILE}")


@app.command("place")
def place_command(
    symbol: str = typer.Option(..., "--symbol", "-s", help="Trading pair, e.g. BTCUSDT"),
    side: str = typer.Option(..., "--side", help="BUY or SELL"),
    order_type: str = typer.Option(..., "--type", "-t", help="MARKET or LIMIT"),
    quantity: str = typer.Option(..., "--quantity", "-q", help="Order quantity"),
    price: Optional[str] = typer.Option(None, "--price", "-p", help="Limit price (required for LIMIT)"),
) -> None:
    """Place a single order using command-line arguments."""
    _execute_order(symbol, side, order_type, quantity, price)


@app.command("interactive")
def interactive_command() -> None:
    """Place an order using guided prompts."""
    console.print(Panel.fit("Binance Futures Testnet — Interactive Order", style="bold blue"))

    symbol = Prompt.ask("Symbol", default="BTCUSDT")
    side = Prompt.ask("Side", choices=["BUY", "SELL"], default="BUY")
    order_type = Prompt.ask("Order type", choices=["MARKET", "LIMIT"], default="MARKET")
    quantity = Prompt.ask("Quantity")

    price: Optional[str] = None
    if order_type == "LIMIT":
        price = Prompt.ask("Limit price")

    if not Confirm.ask("Submit this order?", default=True):
        console.print("[yellow]Order cancelled.[/yellow]")
        raise typer.Exit()

    _execute_order(symbol, side, order_type, quantity, price)


@app.command("ping")
def ping_command() -> None:
    """Verify connectivity to the Binance Futures Testnet API."""
    try:
        client = _load_client()
    except ConfigurationError:
        raise typer.Exit(code=1)

    try:
        with client:
            client.ping()
    except BinanceAPIError as exc:
        console.print(f"[red]Ping failed:[/red] {exc.message}")
        raise typer.Exit(code=1) from exc
    except BinanceNetworkError as exc:
        console.print(f"[red]Network error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print("[green]Connected to Binance Futures Testnet successfully.[/green]")


def main() -> None:
    if len(sys.argv) == 1:
        interactive_command()
    else:
        app()


if __name__ == "__main__":
    main()
