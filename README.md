# TW-Pulse-CLI

<div align="center">

![TW-Pulse-CLI](https://img.shields.io/badge/TW-Pulse--CLI-58a6ff?style=for-the-badge&logo=python&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Beta-yellow?style=for-the-badge)

**AI-Powered Taiwan Stock Market Analysis CLI**

*台灣股市分析工具 (基於 AI 的終端介面)*

[Features](#features) • [Installation](#installation) • [Usage](#usage) • [Commands](#commands) • [SAPTA Engine](#sapta-engine) • [Configuration](#configuration) • [Documentation](docs/)

[![GitHub](https://img.shields.io/badge/GitHub-alingowangxr%2FTW--Pulse--CLI-181717?style=flat-square&logo=github)](https://github.com/alingowangxr/TW-Pulse-CLI)

</div>

---

## Overview

**TW-Pulse-CLI** 是一個強大的終端使用者介面 (TUI) 應用程式，用於台灣股市分析。它整合了：

- **即時數據** 來自 FinMind (主要), Yahoo Finance (備用)
- **技術分析** (RSI, MACD, 布林通道, 支撐/壓力)
- **基本面分析** (本益比, 股價淨值比, 股東權益報酬率, 股利殖利率)
- **AI/LLM 整合** 支援多家 LLM (Groq/Gemini/Claude/GPT)
- **SAPTA 引擎** - 基於機器學習的盤前預漲偵測系統
- **交易計畫生成器** 包含停利/停損/風險報酬計算
- **法人動向分析** 來自 FinMind 數據

---

## Features

### Core Features

| Feature | Description |
|---------|-------------|
| **Smart Agent** | AI 代理會在分析前獲取真實數據 |
| **Natural Language** | 支援繁體中文或英文提問 |
| **Stock Screening** | 使用多種條件篩選台灣股票 |
| **Technical Analysis** | 15+ 種技術指標自動分析 |
| **Trading Plan** | 生成包含停利/停損/風險報酬的交易計畫 |
| **SAPTA Detection** | 使用機器學習偵測預漲階段 |
| **Price Forecast** | 價格預測含信賴區間 |
| **Chart Generation** | 匯出圖表為 PNG 格式 |

### Supported Analysis

```
Technical Indicators        Fundamental Metrics       SAPTA Modules
─────────────────────      ──────────────────────    ─────────────────────
• RSI (14)                 • P/E Ratio               • Supply Absorption
• MACD + Signal + Hist     • P/B Ratio               • Compression
• SMA (20, 50, 200)        • ROE / ROA               • BB Squeeze
• EMA (9, 21, 55)          • Net Profit Margin       • Elliott Wave
• Bollinger Bands          • Debt to Equity          • Time Projection
• Stochastic K/D           • Dividend Yield          • Anti-Distribution
• ATR (14)                 • Revenue Growth
• Support/Resistance       • Earnings Growth
• Volume Analysis          • Market Cap
```

---

## Installation

### Prerequisites

- **Python 3.11+** (required)
- **pip** or **uv** package manager
- **Git** (for cloning)

### Quick Install

```bash
# Clone repository
git clone https://github.com/alingowangxr/TW-Pulse-CLI.git
cd TW-Pulse-CLI

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# Install package
pip install -e .

# Install Playwright browsers (optional - for legacy Stockbit integration)
playwright install chromium
```

### Install with Development Dependencies

```bash
pip install -e ".[dev]"
```

### Using uv (Faster)

```bash
# Install uv if not installed
pip install uv

# Install with uv
uv pip install -e .
```

### Verify Installation

```bash
# Check if pulse is installed
pulse --help

# Or run directly
python -m pulse.cli.app
```

---

## Usage

### Starting Pulse CLI

```bash
# Simply run
pulse
```

You'll see the TUI interface:

```
┌─────────────────────────────────────────────────────────────────┐
│ Pulse - Type /help for commands                                 │
│                                                                 │
│                                                                 │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ > Message Pulse...                                              │
│                                                           pulse │
└─────────────────────────────────────────────────────────────────┘
```

### Basic Interactions

#### Natural Language (Traditional Chinese / 繁體中文)

```
> 分析 2330
> 台灣股市今天狀況如何?
> 比較 2330 和 2317
> 找出超賣的股票
> 幫 2454 建立交易計畫
> 檢查 2303 的潛在買點
```

#### Natural Language (English)

```
> analyze 2330
> what's the technical outlook for 2317?
> compare tech stocks 2330 2454 2303
> find undervalued stocks
> generate trading plan for 2881
```

#### Slash Commands

```
> /analyze 2330
> /technical 2317
> /fundamental 2454
> /chart 2330 6mo
> /forecast 2454 14
> /plan 2317
> /sapta 2303
> /screen oversold
```

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Submit message/command |
| `Ctrl+C` | Quit application |
| `Ctrl+L` | Clear chat history |
| `Escape` | Close command palette |
| `Tab` | Navigate command palette |
| `↑` `↓` | Navigate options |

---

## Commands

### Quick Reference

| Command | Aliases | Description |
|---------|---------|-------------|
| `/help` | `/h`, `/?` | Show available commands |
| `/analyze` | `/a`, `/stock` | Complete stock analysis |
| `/technical` | `/ta`, `/tech` | Technical analysis only |
| `/fundamental` | `/fa`, `/fund` | Fundamental analysis only |
| `/institutional` | `/inst`, `/flow` | Institutional investor flow analysis |
| `/chart` | `/c` | Generate price chart |
| `/forecast` | `/fc` | Price prediction |
| `/screen` | `/s`, `/filter` | Stock screening |
| `/sector` | `/sec` | Sector analysis |
| `/compare` | `/cmp`, `/vs` | Compare multiple stocks |
| `/plan` | `/tp`, `/sl` | Trading plan generator |
| `/sapta` | `/premarkup` | SAPTA pre-markup detection |
| `/index` | `/market` | Market index status |
| `/models` | `/model`, `/m` | Switch AI model |
| `/clear` | `/cls` | Clear chat history |

### Command Details

#### `/analyze <TICKER>` - Complete Analysis

完整分析包括價格、技術面和 AI 洞察。

```
/analyze 2330
```

Output:
```
2330 - 台積電 (Taiwan Semiconductor Manufacturing Company)

Price: NT$ 820 (+5, +0.61%)
Volume: 15,234,500 (Avg: 12,456,000)
Range: 815 - 825
52W: 500 - 850

Technical:
  RSI(14): 58.3 - Neutral
  MACD: Bullish crossover
  Trend: Bullish
  Signal: Buy

AI Insight:
台積電顯示出積極的動能，RSI 位於中性區間...
```

#### `/technical <TICKER>` - Technical Analysis

```
/technical 2317
```

Output:
```
Technical Analysis: 2317

  RSI(14): 45.2 (Neutral)
  MACD: -12.5 (Signal: -15.3) - Bullish
  SMA20: 5,425 | SMA50: 5,380
  Bollinger: 5,200 - 5,400 - 5,600
  Stochastic: K=35.2, D=38.5
  Support: 5,200 | Resistance: 5,600
  Trend: Sideways | Signal: Neutral
```

#### `/chart <TICKER> [period]` - Price Chart

生成並儲存圖表為 PNG。

```
/chart 2330 3mo
/chart 2317 1y
```

Periods: `1mo`, `3mo`, `6mo`, `1y`, `2y`

#### `/forecast <TICKER> [days]` - Price Forecast

```
/forecast 2454 14
```

Output:
```
Forecast: 2454 (14 days)

Current: NT$ 750
Target: NT$ 770 (+2.67%)
Trend: UP
Support: NT$ 730
Resistance: NT$ 780
Confidence: 72%

Chart saved: charts/2454_forecast_20240115.png
```

#### `/screen <criteria>` - Stock Screening

**Preset Screeners:**

```
/screen oversold      # RSI < 30
/screen overbought    # RSI > 70
/screen bullish       # MACD bullish + price > SMA20
/screen bearish       # MACD bearish + price < SMA20
/screen breakout      # Near resistance + volume spike
/screen momentum      # RSI 50-70 + MACD bullish
/screen undervalued   # PE < 15 + ROE > 10%
```

**Flexible Criteria:**

```
/screen rsi<30
/screen pe<15
/screen rsi>70 and pe<20
```

**Universe Options:**

```
/screen oversold --universe=all       # All Taiwan stocks
```

**Export to CSV:**

```
/screen oversold --export             # Export to data/reports/screen_YYYYMMDD_HHMMSS.csv
/screen rsi<30 --export=my_results.csv  # Export with custom filename
```

The CSV export includes 18 columns: ticker, name, sector, price, change_percent, volume, rsi_14, macd, sma_20, sma_50, pe_ratio, pb_ratio, roe, dividend_yield, market_cap, score, signals.

#### `/plan <TICKER> [account_size]` - Trading Plan

```
/plan 2330
/plan 2317 5000000
```

Output:
```
TRADING PLAN: 2330
Generated: 2024-01-15 14:30

=== ENTRY ===
Price: NT$ 820 (current)
Type: Market
Trend: Bullish | Signal: Buy

=== TAKE PROFIT ===
TP1: NT$ 840 (+2.44%) - Conservative
TP2: NT$ 860 (+4.88%) - Moderate
TP3: NT$ 880 (+7.32%) - Aggressive

=== STOP LOSS ===
SL: NT$ 800 (-2.44%)
Method: Hybrid

=== RISK/REWARD ===
Risk: NT$ 20 per share (2.44%)
Reward (TP1): NT$ 20 (2.44%)
R:R to TP1: 1:1.0 [FAIR]
R:R to TP2: 1:2.0 [GOOD]

Trade Quality: FAIR
Confidence: 65%

=== POSITION SIZING (2% Risk) ===
Account: NT$ 10,000,000
Max Risk: NT$ 200,000
Suggested: 10 units (10,000 shares)
Position Value: NT$ 8,200,000 (82.0% of account)

=== EXECUTION STRATEGY ===
1. Entry: Buy at market or limit NT$ 820
2. Set stop loss immediately at NT$ 800
3. TP1: Sell 50% position at NT$ 840
4. After TP1 hit: Move SL to breakeven
5. TP2: Sell remaining 50% at NT$ 860
```

#### `/compare <TICKER1> <TICKER2> ...` - Compare Stocks

```
/compare 2330 2317 2454
```

Output:
```
Stock Comparison

Ticker   Price        Change      Volume
------------------------------------------------
2330       820        +0.61%      15,234,500
2317       120        +1.23%      45,678,900
2454       750        +0.65%      23,456,700
```

#### `/institutional <TICKER>` - Institutional Investor Flow Analysis

```
/institutional 2330
```

Output:
```
═══ 機構法人動向: 2330 (2024-01-01 至 2024-01-15) ═══

總體訊號: BUY (評分: 70/100)

─── 機構法人淨買賣超 ───
總計淨流量: NT$ 500,000,000
外資淨流量: NT$ 300,000,000
投信淨流量: NT$ 150,000,000
自營商淨流量: NT$ 50,000,000

─── 洞察報告 ───
🟢 機構法人總計淨買超 NT$ 500,000,000 (過去 20 個交易日)
🟢 外資淨買超 NT$ 300,000,000
🟢 投信淨買超 NT$ 150,000,000
🟢 自營商淨買超 NT$ 50,000,000
```

#### `/auth` - Stockbit Authentication (Deprecated)

⚠️ **Note**: Stockbit is an Indonesian platform. This feature is deprecated for Taiwan market.
For Taiwan institutional flow analysis, use `/institutional` command instead.

```
# Legacy Stockbit auth commands (not recommended for Taiwan market)
/auth                              # Check auth status
/auth status                       # Detailed token info
/auth set-token <JWT_TOKEN>        # Set token manually
```



---

## SAPTA Engine

### Overview

**SAPTA** (System for Analyzing Pre-markup Technical Accumulation) 是基於機器學習的引擎，用於偵測股票是否處於 **預漲階段** - 即價格突破前的吸籌階段。

### How It Works

SAPTA 使用 6 個分析模組:

| Module | Weight | Description |
|--------|--------|-------------|
| **Supply Absorption** | 25% | 透過成交量和價格行為偵測主力吸籌 |
| **Compression** | 20% | 波動收縮 - 價格區間縮窄 |
| **BB Squeeze** | 15% | 布林通道擠壓偵測 |
| **Elliott Wave** | 15% | 波浪位置和費波那契回撤 |
| **Time Projection** | 15% | 費波那契時間窗口 + 行星相位 |
| **Anti-Distribution** | 10% | 過濾出貨階段 |

### Status Levels

| Status | Score | Meaning |
|--------|-------|---------|
| **PRE-MARKUP** | >= 47 | 準備在短期內突破 |
| **SIAP** | >= 35 | 接近就緒，需密切監控 |
| **WATCHLIST** | >= 24 | 仍處於早期吸籌階段 |
| **SKIP** | < 24 | 尚未顯示預漲訊號 |

### Usage

**Single Stock Analysis:**

```
/sapta 2330
/sapta 2454 --detailed
```

**Scan Multiple Stocks:**

```
/sapta scan              # Scan TW50 (default)
/sapta scan tw50         # 50 stocks
/sapta scan midcap       # 100 stocks
/sapta scan popular      # Popular stocks
/sapta scan all          # All stocks
```

**Natural Language:**

```
> 找預漲股票
> 找準備突破的股票
> 掃描全市場預漲股
```

### Example Output

```
SAPTA Analysis: 2330
========================================
Status: [PRE-MARKUP]
Score: 68.5/100
Confidence: HIGH
ML Probability: 78%
Wave Phase: Wave 3 (Impulse)
Fib Retracement: 61.8%
Projected Window: 5-8 days
Days to Window: 3

Module Breakdown
------------------------------
  [+] Absorption: 22.5/25
  [+] Compression: 18.0/20
  [+] BB Squeeze: 12.0/15
  [+] Elliott: 10.5/15
  [-] Time Projection: 5.5/15
  [+] Anti-Distribution: 0.0/10

Signals
------------------------------
  - High volume accumulation detected
  - Volatility compression 15 days
  - Bollinger squeeze active
  - Wave 3 position confirmed
  - Near Fibonacci time cluster
```

---

## Configuration

### Environment Variables

Create `.env` file in project root:

```env
# AI API Key (選擇一個即可)
GROQ_API_KEY=your_groq_key              # Groq (免費，推薦)
# GEMINI_API_KEY=your_gemini_key        # Google Gemini
# ANTHROPIC_API_KEY=your_anthropic_key  # Anthropic Claude
# OPENAI_API_KEY=your_openai_key        # OpenAI GPT

# 預設 AI 模型 (可選)
PULSE_AI__DEFAULT_MODEL=groq/llama-3.3-70b-versatile

# FinMind API (用於法人動向，可選)
FINMIND_TOKEN=your_finmind_token

# Debug
PULSE_DEBUG=false
```

**取得免費 API Key:**
- **Groq** (推薦): https://console.groq.com/keys
- **Google**: https://aistudio.google.com/apikey
- **FinMind**: https://finmindtrade.com/



### Configuration File

Edit `config/pulse.yaml`:

```yaml
# AI Settings (LiteLLM - 支援多家 LLM)
ai:
  default_model: "groq/llama-3.3-70b-versatile"
  temperature: 0.7
  max_tokens: 4096
  timeout: 120

# Data Settings
data:
  cache_ttl: 3600  # 1 hour
  default_period: "3mo"

# Analysis Settings
analysis:
  rsi_period: 14
  rsi_oversold: 30
  rsi_overbought: 70
  macd_fast: 12
  macd_slow: 26
  macd_signal: 9

# UI Settings
ui:
  theme: "dark"
  chart_width: 60
  chart_height: 15
  max_results: 50
```

### Available AI Models

| Model ID | Provider | 備註 |
|----------|----------|------|
| `groq/llama-3.3-70b-versatile` | Groq | 免費，推薦 |
| `groq/llama-3.1-8b-instant` | Groq | 免費，快速 |
| `gemini/gemini-2.0-flash` | Google | 免費額度有限 |
| `gemini/gemini-2.5-flash-preview-05-20` | Google | 免費額度有限 |
| `anthropic/claude-sonnet-4-20250514` | Anthropic | 付費 |
| `anthropic/claude-haiku-4-20250514` | Anthropic | 付費 |
| `openai/gpt-4o` | OpenAI | 付費 |
| `openai/gpt-4o-mini` | OpenAI | 付費 |

Switch model:
```
/models              # Open model selector
```

---

## Stock Universe

### Preset Universes

| Universe | Count | Description |
|----------|-------|-------------|
| `ALL` | All | All Taiwan listed stocks (from FinMind) |

### Data Source

股票數據主要從 [FinMind](https://finmindtrade.com/) 獲取，輔以 Yahoo Finance 作為備用。

Supported indices:
- **TAIEX** (^TWII) - Taiwan Weighted Index

---

## Project Structure

```
tw-pulse-cli/
├── pulse/
│   ├── __init__.py
│   ├── cli/                      # TUI Application
│   │   ├── __init__.py
│   │   ├── app.py                # Main Textual app
│   │   └── commands/             # Command handlers (refactored)
│   │       ├── __init__.py
│   │       ├── registry.py       # Lightweight dispatcher
│   │       ├── analysis.py       # Analysis commands
│   │       ├── charts.py         # Chart commands
│   │       ├── screening.py      # Screening commands
│   │       └── advanced.py       # Advanced commands
│   │
│   ├── core/                     # Core Business Logic
│   │   ├── __init__.py
│   │   ├── config.py             # Settings (Pydantic)
│   │   ├── models.py             # Data models
│   │   ├── smart_agent.py        # Agentic AI orchestrator
│   │   ├── screener.py           # Stock screening
│   │   ├── trading_plan.py       # TP/SL generator
│   │   ├── chart_generator.py    # PNG charts
│   │   ├── forecasting.py        # Price prediction
│   │   │
│   │   ├── data/                 # Data Layer
│   │   │   ├── __init__.py
│   │   │   ├── yfinance.py       # Yahoo Finance fetcher
│   │   │   ├── finmind_data.py   # FinMind API integration
│   │   │   ├── fugle.py          # Fugle API integration
│   │   │   └── cache.py          # Disk cache
│   │   │
│   │   ├── analysis/             # Analysis Modules
│   │   │   ├── __init__.py
│   │   │   ├── technical.py      # Technical indicators
│   │   │   ├── fundamental.py    # Fundamental analysis
│   │   │   ├── broker_flow.py    # Broker flow
│   │   │   └── sector.py         # Sector analysis
│   │   │
│   │   └── sapta/                # SAPTA Engine
│   │       ├── __init__.py
│   │       ├── engine.py         # Main orchestrator
│   │       ├── models.py         # SAPTA models
│   │       ├── modules/          # 6 Analysis modules
│   │       │   ├── __init__.py
│   │       │   ├── base.py
│   │       │   ├── absorption.py
│   │       │   ├── compression.py
│   │       │   ├── bb_squeeze.py
│   │       │   ├── elliott.py
│   │       │   ├── time_projection.py
│   │       │   └── anti_distribution.py
│   │       ├── ml/               # Machine Learning
│   │       │   ├── __init__.py
│   │       │   ├── trainer.py
│   │       │   ├── features.py
│   │       │   ├── labeling.py
│   │       │   └── data_loader.py
│   │       └── data/             # Trained models
│   │           ├── sapta_model.pkl
│   │           └── thresholds.json
│   │
│   ├── ai/                       # AI Integration
│   │   ├── __init__.py
│   │   ├── client.py             # LiteLLM client
│   │   └── prompts.py            # System prompts
│   │
│   └── utils/                    # Utilities
│       ├── __init__.py
│       ├── logger.py
│       ├── formatters.py
│       ├── validators.py
│       ├── constants.py
│       ├── retry.py              # Retry utilities
│       └── error_handler.py      # Exception classes
│
├── config/
│   └── pulse.yaml                # Configuration file
│
├── data/
│   ├── tw_tickers.json           # Taiwan stock tickers (5,868 stocks)
│   ├── twse_tickers.json         # TWSE listed stocks
│   ├── otc_tickers.json          # OTC stocks
│   ├── cache/                    # Disk cache
│   ├── logs/                     # Log files
│   └── reports/                  # Export reports (CSV)
│
├── docs/                         # Documentation
│   ├── SAPTA_ALGORITHM.md        # SAPTA algorithm details
│   ├── training_guide.md         # ML model training guide
│   └── architecture.md           # System architecture
│
├── tests/                        # Test suite
│   └── ...
│
├── pyproject.toml                # Project config & dependencies
├── README.md                     # This file
├── .env.example                  # Environment template
└── .gitignore
```

---

## Development

### Setup Development Environment

```bash
# Clone and install
git clone https://github.com/alingowangxr/TW-Pulse-CLI.git
cd TW-Pulse-CLI

# Create venv
python -m venv .venv
source .venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (optional)
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pulse --cov-report=html

# Run specific test
pytest tests/test_core/test_screener.py -v
```

### Code Quality

```bash
# Linting with ruff
ruff check pulse/

# Type checking with mypy
mypy pulse/

# Format code
ruff format pulse/
```

### Training SAPTA Model

```bash
# Train new model with historical data
python -m pulse.core.sapta.ml.train_model

# This will:
# 1. Load historical price data
# 2. Generate features from 6 modules
# 3. Label data based on forward returns
# 4. Train XGBoost classifier
# 5. Save model to pulse/core/sapta/data/
```

---

## Troubleshooting

### Common Issues

**1. "No data found for XXXX"**

```
Cause: Ticker 無效或 FinMind/Yahoo Finance 無資料
Solution: 請確認股票代號正確
```

**2. "AI request failed"**

```
Cause: AI API key 未設定或無效
Solution:
  - 確認已設定 API key (GROQ_API_KEY, GEMINI_API_KEY 等)
  - 檢查 API key 是否正確
  - 嘗試切換到其他 Provider
```

**3. "Insufficient data for SAPTA"**

```
Cause: Newly listed stock or historical data < 100 days
Solution: SAPTA requires at least 100 days of historical data
```

**4. "Stockbit not authenticated" (Legacy)**

```
Cause: Stockbit is an Indonesian platform, not applicable for Taiwan market
Solution: 
  - For Taiwan market, use /institutional command instead
  - Stockbit features are deprecated for Taiwan stocks
```

### Debug Mode

Enable debug logging:

```bash
PULSE_DEBUG=true pulse
```

Or in `.env`:
```env
PULSE_DEBUG=true
```

---

## Roadmap

- [ ] **v0.2.0** - Watchlist & Portfolio tracking
- [ ] **v0.2.1** - Alert notifications
- [ ] **v0.3.0** - Backtesting framework
- [ ] **v0.4.0** - Strategy builder
- [ ] **v0.5.0** - Multi-market support (US, Crypto)
- [ ] **v1.0.0** - Stable release

---

## Contributing

Contributions are welcome! Please read our contributing guidelines first.

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## Disclaimer

**IMPORTANT:** Pulse CLI is for **educational and informational purposes only**. 

- Not financial advice
- Past performance doesn't guarantee future results
- Always do your own research (DYOR)
- Invest responsibly

The developers are not responsible for any financial losses incurred from using this tool.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [Textual](https://github.com/Textualize/textual) - Amazing TUI framework
- [yfinance](https://github.com/ranaroussi/yfinance) - Yahoo Finance API wrapper
- [TA-Lib](https://github.com/bukosabino/ta) - Technical analysis library
- [Rich](https://github.com/Textualize/rich) - Beautiful terminal formatting
- [FinMind](https://github.com/FinMind/FinMind) - Taiwan Financial Data Source

---

## Documentation

### Core Documentation

| Document | Description |
|----------|-------------|
| [README](README.md) | Main project documentation |
| [SAPTA Algorithm](docs/SAPTA_ALGORITHM.md) | SAPTA algorithm details and modules |
| [Training Guide](docs/training_guide.md) | ML model training documentation |
| [Architecture](docs/architecture.md) | System architecture and design |

### Key Topics

- **SAPTA Engine**: [Algorithm](docs/SAPTA_ALGORITHM.md) | [Training](docs/training_guide.md)
- **System Architecture**: [Overview](docs/architecture.md)
- **API Integration**: [LiteLLM](https://docs.litellm.io/) | [Groq](https://console.groq.com/)
- **Data Sources**: [FinMind](https://finmindtrade.com/) | [yfinance](https://github.com/ranaroussi/yfinance)

---

<div align="center">

**Made with :heart: for Taiwan Stock Market**

[Report Bug](https://github.com/alingowangxr/TW-Pulse-CLI/issues) • [Request Feature](https://github.com/alingowangxr/TW-Pulse-CLI/issues)

</div>
