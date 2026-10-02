"""
Data Ingestion Collectors:
- Financial News APIs & RSS
- Official Gov / Central Bank Announcements
- Social Media / Web Signals
- Market Data API (yfinance integration)
Group No. 61 | Rishu Raj | Shaheed Arman Gazi
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import feedparser
import pandas as pd
import yfinance as yf

from src.common.models import RawDocument, DataSourceType


class MarketDataCollector:
    """Collects price, volume, and volatility history for assets using yfinance with offline fallback."""
    
    def fetch_historical_prices(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if df is not None and not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                df = df.reset_index()
                return df
        except Exception as e:
            print(f"[MarketDataCollector] Yahoo Finance live fetch failed for {ticker}: {e}. Generating simulated price window.")
        
        return self._generate_synthetic_market_data(ticker, start_date, end_date)

    def _generate_synthetic_market_data(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        import numpy as np
        dates = pd.date_range(start=start_date, end=end_date, freq="B")
        np.random.seed(abs(hash(ticker)) % (2**32))
        
        base_price = 150.0 if ticker in ["AAPL", "NVDA"] else 100.0
        returns = np.random.normal(0.0005, 0.02, size=len(dates))
        prices = base_price * np.exp(np.cumsum(returns))
        volumes = np.random.lognormal(mean=16, sigma=0.5, size=len(dates))

        return pd.DataFrame({
            "Date": dates,
            "Open": prices * 0.995,
            "High": prices * 1.015,
            "Low": prices * 0.985,
            "Close": prices,
            "Adj Close": prices,
            "Volume": volumes
        })


class RSSNewsCollector:
    """Collects live financial news from RSS feeds."""

    DEFAULT_FEEDS = [
        {"name": "Yahoo Finance Top Stories", "url": "https://finance.yahoo.com/news/rssindex"},
        {"name": "CNBC Market News", "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664"},
    ]

    def fetch_feed(self, feed_url: str, source_name: str) -> List[RawDocument]:
        documents: List[RawDocument] = []
        try:
            parsed = feedparser.parse(feed_url)
            for entry in parsed.entries[:15]:
                title = entry.get("title", "")
                summary = entry.get("summary", entry.get("description", ""))
                link = entry.get("link", "")
                published_str = entry.get("published", entry.get("updated", datetime.utcnow().isoformat()))
                
                doc = RawDocument(
                    doc_id=str(uuid.uuid4()),
                    source_type=DataSourceType.FINANCIAL_NEWS,
                    source_name=source_name,
                    title=title,
                    content=summary,
                    url=link,
                    published_at=datetime.utcnow(),
                    raw_metadata={"feed_url": feed_url, "raw_published": published_str}
                )
                documents.append(doc)
        except Exception as e:
            print(f"[RSSNewsCollector] Error reading feed {feed_url}: {e}")
        return documents

