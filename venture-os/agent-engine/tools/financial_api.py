# Financial data APIs
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, date
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

    # ==================== Configuration ====================

    def set_api_key(self, provider: str, api_key: str) -> None:
        """Set API key for provider."""
        pass

    def set_default_provider(self, provider: str) -> None:
        """Set default data provider."""
        pass

    def get_available_providers(self) -> List[str]:
        """Get list of available providers."""
        pass

    # ==================== Real-time Data ====================

    def get_quote(
        self, symbol: str, market_type: MarketType = MarketType.STOCK
    ) -> Quote:
        """Get real-time quote."""
        pass

    def get_quotes(
        self, symbols: List[str], market_type: MarketType = MarketType.STOCK
    ) -> List[Quote]:
        """Get multiple quotes."""
        pass

    def get_price(self, symbol: str) -> float:
        """Get current price."""
        pass

    def get_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get multiple prices."""
        pass

    def get_bid_ask(self, symbol: str) -> Dict[str, float]:
        """Get bid/ask spread."""
        pass

    # ==================== Historical Data ====================

    def get_historical(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        timeframe: TimeFrame = TimeFrame.DAY,
    ) -> List[OHLCV]:
        """Get historical OHLCV data."""
        pass

    def get_intraday(
        self, symbol: str, timeframe: TimeFrame = TimeFrame.MINUTE_5, days: int = 1
    ) -> List[OHLCV]:
        """Get intraday data."""
        pass

    def get_daily(self, symbol: str, days: int = 30) -> List[OHLCV]:
        """Get daily data for last N days."""
        pass

    def get_weekly(self, symbol: str, weeks: int = 52) -> List[OHLCV]:
        """Get weekly data."""
        pass

    def get_monthly(self, symbol: str, months: int = 12) -> List[OHLCV]:
        """Get monthly data."""
        pass

    # ==================== Company Information ====================

    def get_company_info(self, symbol: str) -> CompanyInfo:
        """Get company information."""
        pass

    def get_financials(self, symbol: str) -> Dict[str, Any]:
        """Get financial statements."""
        pass

    def get_income_statement(
        self, symbol: str, period: str = "annual"
    ) -> Dict[str, Any]:
        """Get income statement."""
        pass

    def get_balance_sheet(self, symbol: str, period: str = "annual") -> Dict[str, Any]:
        """Get balance sheet."""
        pass

    def get_cash_flow(self, symbol: str, period: str = "annual") -> Dict[str, Any]:
        """Get cash flow statement."""
        pass

    def get_earnings(self, symbol: str) -> Dict[str, Any]:
        """Get earnings data."""
        pass

    def get_dividends(self, symbol: str) -> List[Dict[str, Any]]:
        """Get dividend history."""
        pass

    def get_splits(self, symbol: str) -> List[Dict[str, Any]]:
        """Get stock splits history."""
        pass

    # ==================== Technical Indicators ====================

    def get_sma(
        self, symbol: str, period: int = 20, timeframe: TimeFrame = TimeFrame.DAY
    ) -> List[Dict[str, Any]]:
        """Get Simple Moving Average."""
        pass

    def get_ema(
        self, symbol: str, period: int = 20, timeframe: TimeFrame = TimeFrame.DAY
    ) -> List[Dict[str, Any]]:
        """Get Exponential Moving Average."""
        pass

    def get_rsi(
        self, symbol: str, period: int = 14, timeframe: TimeFrame = TimeFrame.DAY
    ) -> List[Dict[str, Any]]:
        """Get Relative Strength Index."""
        pass

    def get_macd(
        self, symbol: str, timeframe: TimeFrame = TimeFrame.DAY
    ) -> List[Dict[str, Any]]:
        """Get MACD indicator."""
        pass

    def get_bollinger_bands(
        self, symbol: str, period: int = 20, timeframe: TimeFrame = TimeFrame.DAY
    ) -> List[Dict[str, Any]]:
        """Get Bollinger Bands."""
        pass

    def calculate_indicator(
        self, symbol: str, indicator: str, params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Calculate custom technical indicator."""
        pass

    # ==================== Market Data ====================

    def get_market_status(self, market: str = "US") -> Dict[str, Any]:
        """Get market status (open/closed)."""
        pass

    def get_market_movers(
        self,
        market_type: MarketType = MarketType.STOCK,
        direction: str = "gainers",
        limit: int = 10,
    ) -> List[Quote]:
        """Get top gainers/losers."""
        pass

    def get_most_active(
        self, market_type: MarketType = MarketType.STOCK, limit: int = 10
    ) -> List[Quote]:
        """Get most active by volume."""
        pass

    def get_sector_performance(self) -> Dict[str, float]:
        """Get sector performance."""
        pass

    def get_indices(self) -> List[Quote]:
        """Get major indices."""
        pass

    # ==================== Crypto Specific ====================

    def get_crypto_quote(self, symbol: str, currency: str = "USD") -> Quote:
        """Get cryptocurrency quote."""
        pass

    def get_crypto_markets(self, symbol: str) -> List[Dict[str, Any]]:
        """Get available markets for crypto."""
        pass

    def get_crypto_global_metrics(self) -> Dict[str, Any]:
        """Get global crypto market metrics."""
        pass

    # ==================== Forex Specific ====================

    def get_forex_quote(self, base: str, quote: str) -> Quote:
        """Get forex quote."""
        pass

    def get_exchange_rate(self, base: str, quote: str) -> float:
        """Get exchange rate."""
        pass

    def convert_currency(
        self, amount: float, from_currency: str, to_currency: str
    ) -> float:
        """Convert currency amount."""
        pass

    # ==================== News & Sentiment ====================

    def get_news(
        self, symbol: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get financial news."""
        pass

    def get_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get market sentiment."""
        pass

    def get_analyst_ratings(self, symbol: str) -> Dict[str, Any]:
        """Get analyst ratings."""
        pass

    # ==================== Search ====================

    def search_symbols(
        self, query: str, market_type: Optional[MarketType] = None
    ) -> List[Dict[str, Any]]:
        """Search for symbols."""
        pass

    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get symbol information."""
        pass

    # ==================== Statistics ====================

    def get_stats(self) -> Dict[str, Any]:
        """Get API usage statistics."""
        pass

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get rate limit status."""
        pass
