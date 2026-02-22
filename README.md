# Investment Agent (Google ADK)

Portfolio-aware investment analysis agent implemented with Google ADK.

## Features

- Google ADK `root_agent` with custom tool functions
- yfinance market data retrieval with local TTL cache and stale fallback
- Technical indicator engine covering trend, momentum, volatility, volume, and structure signals
- TA chart generation to PNG for multimodal evidence
- LLM-centric recommendation flow with structured JSON contract and guardrails
- Tests for cache behavior, indicator outputs, and recommendation schema validation

## Setup

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `.env`:

```env
GOOGLE_API_KEY="YOUR_API_KEY"
INVESTMENT_AGENT_MODEL="gemini-2.0-flash"
PORTFOLIO_PATH="data/portfolio.json"
```

## Run

From the repository parent directory:

```bash
adk run investment_agent
```

Or start the dev web UI:

```bash
adk web --port 8000
```

## Test

```bash
pytest -q
```
# Investment Agent

Python investment analysis agent that:
- pulls market data from `yfinance`,
- caches historical data locally,
- computes common technical indicators,
- uses Google ADK tools + LLM for final portfolio-aware recommendations.

## Quickstart

1. Create virtual environment and install:
   - `pip install -e .`
2. Run analysis:
   - `investment-agent analyze --symbol NVDA --portfolio examples/portfolio.json`
3. Set model credentials, for example:
   - `GOOGLE_API_KEY=<your_api_key>`

## Notes

- The final recommendation is generated through ADK `Agent` + function tools.
- Tool functions are in `src/investment_agent/adk_tools.py` and are exposed directly to the LLM.
- `src/investment_agent/agent.py` exports `root_agent` for ADK runtimes.
