# Financial data APIs
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from enum import Enum


class MarketType(Enum):
    """Types of financial markets."""

    STOCK = "stock"
    CRYPTO = "crypto"
    FOREX = "forex"
    COMMODITY = "commodity"
    INDEX = "index"


class TimeFrame(Enum):
    """Time frames for historical data."""

    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY = "1d"
    WEEK = "1w"
    MONTH = "1M"


@dataclass
class Quote:
    """Real-time quote data."""

    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int
    timestamp: datetime
    bid: Optional[float] = None
    ask: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    open: Optional[float] = None
    previous_close: Optional[float] = None


@dataclass
class OHLCV:
    """OHLCV candlestick data."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class CompanyInfo:
    """Company information."""

    symbol: str
    name: str
    sector: str
    industry: str
    market_cap: float
    description: str
    website: str
    employees: int
    country: str


class FinancialAPI:
    """Financial data API tool."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._api_keys: Dict[str, str] = {}
        self._default_provider: str = "yahoo"
        self._stats: Dict[str, Any] = {"requests": 0, "errors": 0}
        self._rate_limit_state: Dict[str, Any] = {}

    # ==================== Private Helpers ====================

    def _yahoo_fetch(self, symbol: str, modules: str) -> Dict[str, Any]:
        """Fetch Yahoo Finance quoteSummary for given modules."""
        import httpx
        url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            resp = httpx.get(url, params={"modules": modules}, headers=headers, timeout=15)
            resp.raise_for_status()
            self._stats["requests"] = int(self._stats["requests"]) + 1
            data = resp.json()
            result = data.get("quoteSummary", {}).get("result") or []
            return result[0] if result else {}
        except Exception as exc:
            self._stats["errors"] = int(self._stats["errors"]) + 1
            raise RuntimeError(f"Yahoo Finance request failed: {exc}") from exc

    def _yahoo_chart(
        self,
        symbol: str,
        period: Optional[str] = None,
        start: Optional[date] = None,
        end: Optional[date] = None,
        interval: str = "1d",
    ) -> List[OHLCV]:
        """Fetch OHLCV data from Yahoo Finance v8 chart API."""
        import httpx
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params: Dict[str, Any] = {"interval": interval}
        if period:
            params["range"] = period
        elif start and end:
            import calendar
            params["period1"] = int(datetime.combine(start, datetime.min.time()).timestamp())
            params["period2"] = int(datetime.combine(end, datetime.min.time()).timestamp())
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            resp = httpx.get(url, params=params, headers=headers, timeout=15)
            resp.raise_for_status()
            self._stats["requests"] = int(self._stats["requests"]) + 1
            data = resp.json()
            result = (data.get("chart", {}).get("result") or [None])[0]
            if not result:
                return []
            timestamps = result.get("timestamp", [])
            quotes = result.get("indicators", {}).get("quote", [{}])[0]
            opens = quotes.get("open", [])
            highs = quotes.get("high", [])
            lows = quotes.get("low", [])
            closes = quotes.get("close", [])
            volumes = quotes.get("volume", [])
            candles = []
            for i, ts in enumerate(timestamps):
                try:
                    candles.append(OHLCV(
                        timestamp=datetime.utcfromtimestamp(ts),
                        open=float(opens[i] or 0),
                        high=float(highs[i] or 0),
                        low=float(lows[i] or 0),
                        close=float(closes[i] or 0),
                        volume=int(volumes[i] or 0),
                    ))
                except (IndexError, TypeError):
                    pass
            return candles
        except Exception as exc:
            self._stats["errors"] = int(self._stats["errors"]) + 1
            raise RuntimeError(f"Yahoo chart request failed: {exc}") from exc

    # ==================== Configuration ====================


    def set_api_key(self, provider: str, api_key: str) -> None:
        """Set API key for provider."""
        self._api_keys[provider.lower()] = api_key

    def set_default_provider(self, provider: str) -> None:
        """Set default data provider."""
        self._default_provider = provider.lower()

    def get_available_providers(self) -> List[str]:
        """Get list of available providers."""
        return ["yahoo", "coingecko"]

    # ==================== Real-time Data ====================

    def get_quote(
        self, symbol: str, market_type: MarketType = MarketType.STOCK
    ) -> Quote:
        """Get real-time quote."""
        if market_type == MarketType.CRYPTO:
            return self.get_crypto_quote(symbol)
        if market_type == MarketType.FOREX:
            parts = symbol.replace("/", "").replace("-", "")
            return self.get_forex_quote(parts[:3], parts[3:]) if len(parts) >= 6 else self.get_forex_quote(symbol, "USD")
        data = self._yahoo_fetch(symbol, "price")
        price_data = data.get("price", {})
        return Quote(
            symbol=symbol,
            price=float(price_data.get("regularMarketPrice", {}).get("raw", 0)),
            change=float(price_data.get("regularMarketChange", {}).get("raw", 0)),
            change_percent=float(price_data.get("regularMarketChangePercent", {}).get("raw", 0)),
            volume=int(price_data.get("regularMarketVolume", {}).get("raw", 0)),
            timestamp=datetime.utcnow(),
            bid=float(price_data.get("regularMarketPrice", {}).get("raw", 0)),
            ask=float(price_data.get("regularMarketPrice", {}).get("raw", 0)),
            high=float(price_data.get("regularMarketDayHigh", {}).get("raw", 0)),
            low=float(price_data.get("regularMarketDayLow", {}).get("raw", 0)),
            open=float(price_data.get("regularMarketOpen", {}).get("raw", 0)),
            previous_close=float(price_data.get("regularMarketPreviousClose", {}).get("raw", 0)),
        )

    def get_quotes(
        self, symbols: List[str], market_type: MarketType = MarketType.STOCK
    ) -> List[Quote]:
        """Get multiple quotes."""
        results = []
        for sym in symbols:
            try:
                results.append(self.get_quote(sym, market_type))
            except Exception:
                pass
        return results

    def get_price(self, symbol: str) -> float:
        """Get current price."""
        return self.get_quote(symbol).price

    def get_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get multiple prices."""
        return {sym: self.get_price(sym) for sym in symbols}

    def get_bid_ask(self, symbol: str) -> Dict[str, float]:
        """Get bid/ask spread."""
        q = self.get_quote(symbol)
        return {"bid": q.bid or q.price, "ask": q.ask or q.price}

    # ==================== Historical Data ====================

    def get_historical(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        timeframe: TimeFrame = TimeFrame.DAY,
    ) -> List[OHLCV]:
        """Get historical OHLCV data."""
        interval_map = {
            TimeFrame.MINUTE_1: "1m", TimeFrame.MINUTE_5: "5m",
            TimeFrame.MINUTE_15: "15m", TimeFrame.MINUTE_30: "30m",
            TimeFrame.HOUR_1: "1h", TimeFrame.HOUR_4: "1h",
            TimeFrame.DAY: "1d", TimeFrame.WEEK: "1wk", TimeFrame.MONTH: "1mo",
        }
        return self._yahoo_chart(symbol, start=start_date, end=end_date, interval=interval_map.get(timeframe, "1d"))

    def get_intraday(
        self, symbol: str, timeframe: TimeFrame = TimeFrame.MINUTE_5, days: int = 1
    ) -> List[OHLCV]:
        """Get intraday data."""
        interval_map = {
            TimeFrame.MINUTE_1: "1m", TimeFrame.MINUTE_5: "5m",
            TimeFrame.MINUTE_15: "15m", TimeFrame.MINUTE_30: "30m",
            TimeFrame.HOUR_1: "1h", TimeFrame.HOUR_4: "1h",
        }
        period = f"{days}d"
        return self._yahoo_chart(symbol, period=period, interval=interval_map.get(timeframe, "5m"))

    def get_daily(self, symbol: str, days: int = 30) -> List[OHLCV]:
        """Get daily data for last N days."""
        today = date.today()
        start = today - timedelta(days=days)
        return self._yahoo_chart(symbol, start=start, end=today, interval="1d")

    def get_weekly(self, symbol: str, weeks: int = 52) -> List[OHLCV]:
        """Get weekly data."""
        today = date.today()
        start = today - timedelta(weeks=weeks)
        return self._yahoo_chart(symbol, start=start, end=today, interval="1wk")

    def get_monthly(self, symbol: str, months: int = 12) -> List[OHLCV]:
        """Get monthly data."""
        today = date.today()
        start = today - timedelta(days=months * 31)
        return self._yahoo_chart(symbol, start=start, end=today, interval="1mo")

    # ==================== Company Information ====================

    def get_company_info(self, symbol: str) -> CompanyInfo:
        """Get company information."""
        data = self._yahoo_fetch(symbol, "assetProfile,price")
        profile = data.get("assetProfile", {})
        price = data.get("price", {})
        return CompanyInfo(
            symbol=symbol,
            name=price.get("longName") or price.get("shortName", symbol),
            sector=profile.get("sector", ""),
            industry=profile.get("industry", ""),
            market_cap=float(price.get("marketCap", {}).get("raw", 0)),
            description=profile.get("longBusinessSummary", ""),
            website=profile.get("website", ""),
            employees=int(profile.get("fullTimeEmployees", 0)),
            country=profile.get("country", ""),
        )

    def get_financials(self, symbol: str) -> Dict[str, Any]:
        """Get financial statements."""
        data = self._yahoo_fetch(symbol, "incomeStatementHistory,balanceSheetHistory,cashflowStatementHistory")
        return data

    def get_income_statement(
        self, symbol: str, period: str = "annual"
    ) -> Dict[str, Any]:
        """Get income statement."""
        module = "incomeStatementHistory" if period == "annual" else "incomeStatementHistoryQuarterly"
        data = self._yahoo_fetch(symbol, module)
        return data.get(module, {})

    def get_balance_sheet(self, symbol: str, period: str = "annual") -> Dict[str, Any]:
        """Get balance sheet."""
        module = "balanceSheetHistory" if period == "annual" else "balanceSheetHistoryQuarterly"
        data = self._yahoo_fetch(symbol, module)
        return data.get(module, {})

    def get_cash_flow(self, symbol: str, period: str = "annual") -> Dict[str, Any]:
        """Get cash flow statement."""
        module = "cashflowStatementHistory" if period == "annual" else "cashflowStatementHistoryQuarterly"
        data = self._yahoo_fetch(symbol, module)
        return data.get(module, {})

    def get_earnings(self, symbol: str) -> Dict[str, Any]:
        """Get earnings data."""
        data = self._yahoo_fetch(symbol, "earnings")
        return data.get("earnings", {})

    def get_dividends(self, symbol: str) -> List[Dict[str, Any]]:
        """Get dividend history."""
        candles = self._yahoo_chart(symbol, period="5y", interval="1d")
        # Dividends come via the events in chart API; return empty if not directly parsed
        data = self._yahoo_fetch(symbol, "summaryDetail")
        div_rate = data.get("summaryDetail", {}).get("dividendRate", {}).get("raw")
        return [{"dividendRate": div_rate}] if div_rate else []

    def get_splits(self, symbol: str) -> List[Dict[str, Any]]:
        """Get stock splits history."""
        return []  # Would require events parsing from chart API

    # ==================== Technical Indicators ====================

    def get_sma(
        self, symbol: str, period: int = 20, timeframe: TimeFrame = TimeFrame.DAY
    ) -> List[Dict[str, Any]]:
        """Get Simple Moving Average."""
        import pandas as pd
        candles = self.get_daily(symbol, days=max(period * 3, 90))
        if not candles:
            return []
        df = pd.DataFrame([{"ts": c.timestamp, "close": c.close} for c in candles])
        df["sma"] = df["close"].rolling(window=period).mean()
        return [{"timestamp": str(r["ts"]), "sma": r["sma"]} for _, r in df.dropna().iterrows()]

    def get_ema(
        self, symbol: str, period: int = 20, timeframe: TimeFrame = TimeFrame.DAY
    ) -> List[Dict[str, Any]]:
        """Get Exponential Moving Average."""
        import pandas as pd
        candles = self.get_daily(symbol, days=max(period * 3, 90))
        if not candles:
            return []
        df = pd.DataFrame([{"ts": c.timestamp, "close": c.close} for c in candles])
        df["ema"] = df["close"].ewm(span=period, adjust=False).mean()
        return [{"timestamp": str(r["ts"]), "ema": r["ema"]} for _, r in df.iterrows()]

    def get_rsi(
        self, symbol: str, period: int = 14, timeframe: TimeFrame = TimeFrame.DAY
    ) -> List[Dict[str, Any]]:
        """Get Relative Strength Index."""
        import pandas as pd
        candles = self.get_daily(symbol, days=max(period * 4, 90))
        if not candles:
            return []
        df = pd.DataFrame([{"ts": c.timestamp, "close": c.close} for c in candles])
        delta = df["close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / avg_loss.replace(0, float("inf"))
        df["rsi"] = 100 - (100 / (1 + rs))
        return [{"timestamp": str(r["ts"]), "rsi": r["rsi"]} for _, r in df.dropna().iterrows()]

    def get_macd(
        self, symbol: str, timeframe: TimeFrame = TimeFrame.DAY
    ) -> List[Dict[str, Any]]:
        """Get MACD indicator."""
        import pandas as pd
        candles = self.get_daily(symbol, days=200)
        if not candles:
            return []
        df = pd.DataFrame([{"ts": c.timestamp, "close": c.close} for c in candles])
        ema12 = df["close"].ewm(span=12, adjust=False).mean()
        ema26 = df["close"].ewm(span=26, adjust=False).mean()
        df["macd"] = ema12 - ema26
        df["signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        df["histogram"] = df["macd"] - df["signal"]
        return [
            {"timestamp": str(r["ts"]), "macd": r["macd"], "signal": r["signal"], "histogram": r["histogram"]}
            for _, r in df.dropna().iterrows()
        ]

    def get_bollinger_bands(
        self, symbol: str, period: int = 20, timeframe: TimeFrame = TimeFrame.DAY
    ) -> List[Dict[str, Any]]:
        """Get Bollinger Bands."""
        import pandas as pd
        candles = self.get_daily(symbol, days=max(period * 3, 90))
        if not candles:
            return []
        df = pd.DataFrame([{"ts": c.timestamp, "close": c.close} for c in candles])
        df["sma"] = df["close"].rolling(window=period).mean()
        df["std"] = df["close"].rolling(window=period).std()
        df["upper"] = df["sma"] + 2 * df["std"]
        df["lower"] = df["sma"] - 2 * df["std"]
        return [
            {"timestamp": str(r["ts"]), "upper": r["upper"], "middle": r["sma"], "lower": r["lower"]}
            for _, r in df.dropna().iterrows()
        ]

    def calculate_indicator(
        self, symbol: str, indicator: str, params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Calculate custom technical indicator."""
        indicator_map = {
            "sma": self.get_sma,
            "ema": self.get_ema,
            "rsi": self.get_rsi,
            "macd": self.get_macd,
            "bollinger": self.get_bollinger_bands,
            "bb": self.get_bollinger_bands,
        }
        fn = indicator_map.get(indicator.lower())
        if not fn:
            raise ValueError(f"Unknown indicator: {indicator}. Available: {list(indicator_map.keys())}")
        return fn(symbol, **{k: v for k, v in params.items() if k != "indicator"})

    # ==================== Market Data ====================

    def get_market_status(self, market: str = "US") -> Dict[str, Any]:
        """Get market status (open/closed)."""
        # NYSE/NASDAQ: Mon-Fri 09:30-16:00 ET
        from datetime import timezone
        now_utc = datetime.now(timezone.utc)
        # ET is UTC-5 (EST) or UTC-4 (EDT); approximate with UTC-5
        et_hour = (now_utc.hour - 5) % 24
        weekday = now_utc.weekday()
        is_weekday = weekday < 5
        is_trading_hours = 9 <= et_hour < 16
        is_open = is_weekday and is_trading_hours
        return {
            "market": market,
            "is_open": is_open,
            "status": "open" if is_open else "closed",
            "timestamp": now_utc.isoformat(),
        }

    def get_market_movers(
        self,
        market_type: MarketType = MarketType.STOCK,
        direction: str = "gainers",
        limit: int = 10,
    ) -> List[Quote]:
        """Get top gainers/losers."""
        import httpx
        url = f"https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved"
        screen_id = "day_gainers" if direction == "gainers" else "day_losers"
        try:
            resp = httpx.get(
                url,
                params={"formatted": "true", "lang": "en-US", "region": "US", "scrIds": screen_id, "count": limit},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15,
            )
            resp.raise_for_status()
            results = resp.json().get("finance", {}).get("result", [{}])[0].get("quotes", [])
            quotes = []
            for q in results[:limit]:
                quotes.append(Quote(
                    symbol=q.get("symbol", ""),
                    price=float(q.get("regularMarketPrice", {}).get("raw", 0)),
                    change=float(q.get("regularMarketChange", {}).get("raw", 0)),
                    change_percent=float(q.get("regularMarketChangePercent", {}).get("raw", 0)),
                    volume=int(q.get("regularMarketVolume", {}).get("raw", 0)),
                    timestamp=datetime.utcnow(),
                ))
            return quotes
        except Exception:
            return []

    def get_most_active(
        self, market_type: MarketType = MarketType.STOCK, limit: int = 10
    ) -> List[Quote]:
        """Get most active by volume."""
        return self.get_market_movers(market_type=market_type, direction="most_actives", limit=limit)

    def get_sector_performance(self) -> Dict[str, float]:
        """Get sector performance."""
        sector_etfs = {
            "Technology": "XLK", "Healthcare": "XLV", "Financials": "XLF",
            "Energy": "XLE", "Utilities": "XLU", "Consumer Discretionary": "XLY",
            "Consumer Staples": "XLP", "Industrials": "XLI", "Materials": "XLB",
            "Real Estate": "XLRE", "Communication Services": "XLC",
        }
        result = {}
        for sector, etf in sector_etfs.items():
            try:
                q = self.get_quote(etf)
                result[sector] = q.change_percent
            except Exception:
                result[sector] = 0.0
        return result

    def get_indices(self) -> List[Quote]:
        """Get major indices."""
        indices = ["^GSPC", "^DJI", "^IXIC", "^RUT", "^VIX"]
        return self.get_quotes(indices)

    # ==================== Crypto Specific ====================

    def get_crypto_quote(self, symbol: str, currency: str = "USD") -> Quote:
        """Get cryptocurrency quote."""
        import httpx
        # CoinGecko public API (no key required)
        coin_id = symbol.lower().rstrip("-usd").rstrip("/usd")
        url = "https://api.coingecko.com/api/v3/simple/price"
        try:
            resp = httpx.get(
                url,
                params={"ids": coin_id, "vs_currencies": currency.lower(), "include_24hr_change": "true", "include_24hr_vol": "true"},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json().get(coin_id, {})
            price = float(data.get(currency.lower(), 0))
            change_pct = float(data.get(f"{currency.lower()}_24h_change", 0))
            vol = float(data.get(f"{currency.lower()}_24h_vol", 0))
            self._stats["requests"] = int(self._stats["requests"]) + 1
            return Quote(
                symbol=symbol.upper(),
                price=price,
                change=price * change_pct / 100,
                change_percent=change_pct,
                volume=int(vol),
                timestamp=datetime.utcnow(),
            )
        except Exception as exc:
            self._stats["errors"] = int(self._stats["errors"]) + 1
            raise RuntimeError(f"CoinGecko request failed: {exc}") from exc

    def get_crypto_markets(self, symbol: str) -> List[Dict[str, Any]]:
        """Get available markets for crypto."""
        import httpx
        coin_id = symbol.lower()
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/tickers"
        try:
            resp = httpx.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            resp.raise_for_status()
            tickers = resp.json().get("tickers", [])
            return [{"exchange": t.get("market", {}).get("name"), "pair": t.get("base") + "/" + t.get("target"), "price": t.get("last")} for t in tickers[:20]]
        except Exception:
            return []

    def get_crypto_global_metrics(self) -> Dict[str, Any]:
        """Get global crypto market metrics."""
        import httpx
        try:
            resp = httpx.get("https://api.coingecko.com/api/v3/global", headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            resp.raise_for_status()
            return resp.json().get("data", {})
        except Exception:
            return {}

    # ==================== Forex Specific ====================

    def get_forex_quote(self, base: str, quote: str) -> Quote:
        """Get forex quote."""
        symbol = f"{base}{quote}=X"
        return self.get_quote(symbol, MarketType.STOCK)  # Yahoo Finance handles forex pairs

    def get_exchange_rate(self, base: str, quote: str) -> float:
        """Get exchange rate."""
        return self.get_forex_quote(base, quote).price

    def convert_currency(
        self, amount: float, from_currency: str, to_currency: str
    ) -> float:
        """Convert currency amount."""
        rate = self.get_exchange_rate(from_currency, to_currency)
        return amount * rate

    # ==================== News & Sentiment ====================

    def get_news(
        self, symbol: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get financial news."""
        if not symbol:
            return []
        data = self._yahoo_fetch(symbol, "summaryProfile")
        # Yahoo doesn't expose news via quoteSummary directly; return placeholder
        return [{"source": "yahoo", "symbol": symbol, "note": "Use Yahoo Finance news RSS for full news"}]

    def get_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get market sentiment."""
        data = self._yahoo_fetch(symbol, "upgradeDowngradeHistory")
        history = data.get("upgradeDowngradeHistory", {}).get("history", [])
        upgrades = sum(1 for h in history if h.get("action") in ("up", "init"))
        downgrades = sum(1 for h in history if h.get("action") == "down")
        total = upgrades + downgrades
        return {
            "symbol": symbol,
            "upgrades": upgrades,
            "downgrades": downgrades,
            "sentiment_score": round((upgrades / total) if total else 0.5, 3),
        }

    def get_analyst_ratings(self, symbol: str) -> Dict[str, Any]:
        """Get analyst ratings."""
        data = self._yahoo_fetch(symbol, "recommendationTrend")
        return data.get("recommendationTrend", {})

    # ==================== Search ====================

    def search_symbols(
        self, query: str, market_type: Optional[MarketType] = None
    ) -> List[Dict[str, Any]]:
        """Search for symbols."""
        import httpx
        url = "https://query1.finance.yahoo.com/v1/finance/search"
        try:
            resp = httpx.get(
                url,
                params={"q": query, "lang": "en-US", "region": "US", "quotesCount": 10},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15,
            )
            resp.raise_for_status()
            quotes = resp.json().get("quotes", [])
            return [
                {"symbol": q.get("symbol"), "name": q.get("longname") or q.get("shortname"), "type": q.get("quoteType")}
                for q in quotes
            ]
        except Exception:
            return []

    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get symbol information."""
        data = self._yahoo_fetch(symbol, "price,summaryDetail")
        return data

    # ==================== Statistics ====================

    def get_stats(self) -> Dict[str, Any]:
        """Get API usage statistics."""
        return {
            "total_requests": self._stats["requests"],
            "errors": self._stats["errors"],
            "default_provider": self._default_provider,
            "configured_providers": list(self._api_keys.keys()),
        }

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get rate limit status."""
        return {
            "provider": self._default_provider,
            "rate_limit_state": self._rate_limit_state,
        }
