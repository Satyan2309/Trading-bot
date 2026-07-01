# Binance Futures Testnet Trading Bot

A small Python CLI application that places **MARKET** and **LIMIT** orders on [Binance Futures Testnet (USDT-M)](https://testnet.binancefuture.com) with structured code, file logging, and input validation.

## Features

- Place **MARKET** and **LIMIT** orders (`BUY` / `SELL`)
- CLI via **Typer** (argument mode + interactive prompts)
- Separated layers: client, orders, validators, logging, CLI
- Request/response/error logging to `logs/trading_bot.log`
- Validation for symbol, side, order type, quantity, and price
- Graceful handling of API and network errors

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance REST client (signed requests)
│   ├── orders.py          # Order placement + output formatting
│   ├── validators.py      # Input validation
│   └── logging_config.py  # File + console logging setup
├── cli.py                 # CLI entry point
├── logs/                  # Runtime logs (sample logs included)
├── .env.example
├── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.10+
- A [Binance Futures Testnet](https://testnet.binancefuture.com) account
- Testnet API key and secret ([create keys on testnet](https://testnet.binancefuture.com))

## Setup

1. **Clone or download** this repository.

2. **Create a virtual environment** (recommended):

   ```bash
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   # source .venv/bin/activate   # macOS/Linux
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure credentials**:

   ```bash
   copy .env.example .env          # Windows
   # cp .env.example .env          # macOS/Linux
   ```

   Edit `.env`:

   ```env
   BINANCE_API_KEY=your_testnet_api_key
   BINANCE_API_SECRET=your_testnet_api_secret
   BINANCE_BASE_URL=https://testnet.binancefuture.com
   ```

5. **Verify connectivity**:

   ```bash
   python cli.py ping
   ```

## How to Run

### Interactive mode (default)

Run with no arguments for guided prompts:

```bash
python cli.py
# or
python cli.py interactive
```

### Place a MARKET order

```bash
python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

### Place a LIMIT order

```bash
python cli.py place --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 95000
```

### Short flags

```bash
python cli.py place -s ETHUSDT --side BUY -t LIMIT -q 0.01 -p 3200
```

## Example Output

```
┌────────────────────────────── Request ──────────────────────────────┐
│ Order Request Summary                                               │
│ ----------------------------------------                          │
│ Symbol     : BTCUSDT                                                │
│ Side       : BUY                                                    │
│ Type       : MARKET                                                 │
│ Quantity   : 0.001                                                  │
└─────────────────────────────────────────────────────────────────────┘

┌───────────────────────────── Response ──────────────────────────────┐
│ Order Response Details                                              │
│ ----------------------------------------                          │
│ Order ID      : 123456789                                           │
│ Status        : FILLED                                              │
│ Executed Qty  : 0.001                                               │
│ Avg Price     : 97234.50                                            │
└─────────────────────────────────────────────────────────────────────┘

Order placed successfully.
Log file: logs/trading_bot.log
```

## Logging

All API requests, responses, and errors are written to:

```
logs/trading_bot.log
```

Sample logs from successful orders are included in `logs/`:

- `submission_market_order.log` — real MARKET BUY run (sanitized for submission)
- `submission_limit_order.log` — real LIMIT SELL run (sanitized for submission)
- `sample_market_order.log` / `sample_limit_order.log` — illustrative examples

Re-run the commands above with your credentials to generate fresh logs locally in `logs/trading_bot.log`.

## Submitting to GitHub — security checklist

**Never commit:**

| File | Risk |
|------|------|
| `.env` | Contains your API key and secret — **critical** |
| `.venv/` | Not needed in repo |

**Safe to commit:**

| Item | Notes |
|------|------|
| Source code | No secrets embedded |
| `.env.example` | Placeholder values only |
| `logs/submission_*.log` | Order IDs and trading metadata only — **no API keys** |
| `README.md`, `requirements.txt` | Documentation |

**Log upload risk (low for testnet):**

- Logs contain **order IDs**, **client order IDs**, **symbols**, **quantities**, **prices**, and **timestamps**.
- Logs do **not** contain API keys, secrets, or signatures.
- Because the repo is **public**, anyone can see that you traded on testnet — this is normal for a hiring submission.
- If you reuse the same API key on mainnet later, the log itself does not expose the key, but cancel/delete testnet keys after the interview if you prefer.

**Recommended:** upload `submission_market_order.log` and `submission_limit_order.log` (already sanitized). Keep `trading_bot.log` local only (ignored by git).

## Assumptions

- **USDT-M futures only** — symbols must end with `USDT` (e.g. `BTCUSDT`).
- **Testnet base URL** — `https://testnet.binancefuture.com` (configurable via `.env`).
- **LIMIT orders** use `timeInForce=GTC` (Good Till Cancel).
- **Credentials** are loaded from environment variables via `.env` (never commit real keys).
- **Quantity and price** must be positive decimals; the app does not auto-adjust to exchange lot size filters — use valid step sizes for your symbol on testnet.
- **MARKET orders** may return `avgPrice=0` immediately; the bot optionally re-fetches order details to populate average fill price when available.

## Error Handling

| Scenario              | Behavior                                      |
|-----------------------|-----------------------------------------------|
| Invalid CLI input     | Validation message, exit code 1               |
| Missing API keys      | Clear setup instructions, exit code 1         |
| Binance API error     | API code + message logged and printed         |
| Network timeout/error | User-friendly network message, logged         |

## Bonus: Enhanced CLI UX

- **Interactive mode** with prompts and confirmation
- **Rich** formatted panels for request/response summaries
- **Default to interactive** when no subcommand is provided

## Dependencies

- `httpx` — HTTP client for REST API calls
- `typer` — CLI framework
- `python-dotenv` — load `.env` credentials
- `rich` — terminal formatting

## License

Submitted as a hiring task sample project.
