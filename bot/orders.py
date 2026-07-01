"""Order placement logic and response formatting."""

import logging
from dataclasses import asdict
from decimal import Decimal
from typing import Any

from bot.client import BinanceAPIError, BinanceFuturesClient, BinanceNetworkError
from bot.validators import OrderRequest, OrderType

logger = logging.getLogger("trading_bot.orders")


def format_request_summary(request: OrderRequest) -> str:
    lines = [
        "Order Request Summary",
        "-" * 40,
        f"Symbol     : {request.symbol}",
        f"Side       : {request.side.value}",
        f"Type       : {request.order_type.value}",
        f"Quantity   : {request.quantity}",
    ]
    if request.price is not None:
        lines.append(f"Price      : {request.price}")
    return "\n".join(lines)


def format_order_response(response: dict[str, Any]) -> str:
    fields = [
        ("orderId", "Order ID"),
        ("status", "Status"),
        ("executedQty", "Executed Qty"),
        ("avgPrice", "Avg Price"),
        ("origQty", "Original Qty"),
        ("price", "Price"),
        ("type", "Type"),
        ("side", "Side"),
        ("symbol", "Symbol"),
        ("updateTime", "Update Time"),
    ]

    lines = ["Order Response Details", "-" * 40]
    for key, label in fields:
        if key in response and response[key] not in (None, "", "0", "0.00", "0.00000000"):
            lines.append(f"{label:<14}: {response[key]}")
        elif key in response:
            lines.append(f"{label:<14}: {response[key]}")

    return "\n".join(lines)


def _decimal_to_str(value: Decimal) -> str:
    normalized = value.normalize()
    return format(normalized, "f")


def place_order(client: BinanceFuturesClient, request: OrderRequest) -> dict[str, Any]:
    """Place an order on Binance Futures Testnet."""
    logger.info("Placing order: %s", asdict(request))

    price_str = _decimal_to_str(request.price) if request.price is not None else None
    quantity_str = _decimal_to_str(request.quantity)

    response = client.place_order(
        symbol=request.symbol,
        side=request.side.value,
        order_type=request.order_type.value,
        quantity=quantity_str,
        price=price_str,
    )

    logger.info(
        "Order placed successfully: orderId=%s status=%s executedQty=%s avgPrice=%s",
        response.get("orderId"),
        response.get("status"),
        response.get("executedQty"),
        response.get("avgPrice"),
    )
    return response


def enrich_market_order_response(
    client: BinanceFuturesClient,
    request: OrderRequest,
    response: dict[str, Any],
) -> dict[str, Any]:
    """Fetch full order details when avgPrice is missing from the initial response."""
    if request.order_type != OrderType.MARKET:
        return response

    avg_price = response.get("avgPrice")
    if avg_price and str(avg_price) not in {"0", "0.00", "0.00000000"}:
        return response

    order_id = response.get("orderId")
    if order_id is None:
        return response

    try:
        details = client.get_order(request.symbol, int(order_id))
        response = {**response, **details}
        logger.info("Enriched MARKET order response via GET /fapi/v1/order")
    except (BinanceAPIError, BinanceNetworkError) as exc:
        logger.warning("Could not enrich MARKET order response: %s", exc)

    return response
