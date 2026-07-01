"""Input validation for order parameters."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


@dataclass(frozen=True)
class OrderRequest:
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    price: Decimal | None = None


class ValidationError(ValueError):
    """Raised when user input fails validation."""


def _parse_decimal(value: str, field_name: str) -> Decimal:
    try:
        parsed = Decimal(value.strip())
    except (InvalidOperation, AttributeError) as exc:
        raise ValidationError(f"{field_name} must be a valid number, got '{value}'.") from exc

    if parsed <= 0:
        raise ValidationError(f"{field_name} must be greater than zero, got '{value}'.")
    return parsed


def validate_symbol(symbol: str) -> str:
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValidationError("Symbol cannot be empty.")
    if not symbol.isalnum():
        raise ValidationError(
            f"Symbol must contain only letters and numbers, got '{symbol}'."
        )
    if not symbol.endswith("USDT"):
        raise ValidationError(
            f"Symbol should be a USDT-M pair (e.g. BTCUSDT), got '{symbol}'."
        )
    return symbol


def validate_side(side: str) -> OrderSide:
    normalized = side.strip().upper()
    try:
        return OrderSide(normalized)
    except ValueError as exc:
        raise ValidationError(
            f"Side must be BUY or SELL, got '{side}'."
        ) from exc


def validate_order_type(order_type: str) -> OrderType:
    normalized = order_type.strip().upper()
    try:
        return OrderType(normalized)
    except ValueError as exc:
        raise ValidationError(
            f"Order type must be MARKET or LIMIT, got '{order_type}'."
        ) from exc


def validate_order_request(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: str | None = None,
) -> OrderRequest:
    validated_symbol = validate_symbol(symbol)
    validated_side = validate_side(side)
    validated_type = validate_order_type(order_type)
    validated_quantity = _parse_decimal(quantity, "Quantity")

    validated_price: Decimal | None = None
    if validated_type == OrderType.LIMIT:
        if price is None or not str(price).strip():
            raise ValidationError("Price is required for LIMIT orders.")
        validated_price = _parse_decimal(price, "Price")
    elif price is not None and str(price).strip():
        raise ValidationError("Price should not be provided for MARKET orders.")

    return OrderRequest(
        symbol=validated_symbol,
        side=validated_side,
        order_type=validated_type,
        quantity=validated_quantity,
        price=validated_price,
    )
