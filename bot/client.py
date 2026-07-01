"""Binance Futures Testnet REST API client."""

import hashlib
import hmac
import logging
import time
from typing import Any
from urllib.parse import urlencode

import httpx

logger = logging.getLogger("trading_bot.client")

DEFAULT_BASE_URL = "https://testnet.binancefuture.com"
DEFAULT_TIMEOUT = 30.0
DEFAULT_RECV_WINDOW = 5000

ALLOWED_BASE_URLS = frozenset(
    {
        "https://testnet.binancefuture.com",
        "https://demo-fapi.binance.com",
    }
)


def validate_base_url(base_url: str) -> str:
    """Ensure API requests only go to known Binance Futures endpoints."""
    normalized = base_url.strip().rstrip("/")
    if normalized not in ALLOWED_BASE_URLS:
        allowed = ", ".join(sorted(ALLOWED_BASE_URLS))
        raise ValueError(
            f"Unsupported BINANCE_BASE_URL '{base_url}'. Allowed values: {allowed}"
        )
    return normalized


class BinanceAPIError(Exception):
    """Raised when the Binance API returns an error response."""

    def __init__(self, status_code: int, code: int | None, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(f"Binance API error [{code}]: {message} (HTTP {status_code})")


class BinanceNetworkError(Exception):
    """Raised when a network-level failure occurs."""


class BinanceFuturesClient:
    """Thin wrapper around Binance USDT-M Futures REST endpoints."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        if not api_key or not api_secret:
            raise ValueError("API key and secret are required.")

        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = validate_base_url(base_url)
        self.timeout = timeout
        self._client = httpx.Client(base_url=self.base_url, timeout=self.timeout)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "BinanceFuturesClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _sign(self, params: dict[str, Any]) -> str:
        query_string = urlencode(params, doseq=True)
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        signed: bool = False,
    ) -> dict[str, Any]:
        params = dict(params or {})

        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["recvWindow"] = DEFAULT_RECV_WINDOW
            params["signature"] = self._sign(params)

        headers = {"X-MBX-APIKEY": self.api_key} if signed else {}
        url = path

        logger.info("API request: %s %s params=%s", method, url, self._sanitize_params(params))

        try:
            response = self._client.request(method, url, params=params, headers=headers)
        except httpx.TimeoutException as exc:
            logger.error("Network timeout for %s %s", method, path)
            raise BinanceNetworkError("Request timed out. Check your connection.") from exc
        except httpx.RequestError as exc:
            logger.error("Network error for %s %s: %s", method, path, exc)
            raise BinanceNetworkError(f"Network failure: {exc}") from exc

        try:
            payload = response.json()
        except ValueError:
            payload = {"raw": response.text}

        logger.info(
            "API response: status=%s body=%s",
            response.status_code,
            payload,
        )

        if response.status_code >= 400:
            code = payload.get("code") if isinstance(payload, dict) else None
            message = payload.get("msg", response.text) if isinstance(payload, dict) else response.text
            logger.error("API error: status=%s code=%s message=%s", response.status_code, code, message)
            raise BinanceAPIError(response.status_code, code, message)

        if not isinstance(payload, dict):
            raise BinanceAPIError(response.status_code, None, "Unexpected non-JSON response.")
        return payload

    @staticmethod
    def _sanitize_params(params: dict[str, Any]) -> dict[str, Any]:
        sanitized = dict(params)
        sanitized.pop("signature", None)
        return sanitized

    def ping(self) -> dict[str, Any]:
        return self._request("GET", "/fapi/v1/ping")

    def get_exchange_info(self, symbol: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if symbol:
            params["symbol"] = symbol
        return self._request("GET", "/fapi/v1/exchangeInfo", params=params)

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: str,
        price: str | None = None,
        time_in_force: str = "GTC",
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }

        if order_type == "LIMIT":
            if price is None:
                raise ValueError("Price is required for LIMIT orders.")
            params["price"] = price
            params["timeInForce"] = time_in_force

        return self._request("POST", "/fapi/v1/order", params=params, signed=True)

    def get_order(self, symbol: str, order_id: int) -> dict[str, Any]:
        params = {"symbol": symbol, "orderId": order_id}
        return self._request("GET", "/fapi/v1/order", params=params, signed=True)
