"""
Test suite for Phase 1: Task 1 - Data Ingestion & Preprocessing.
Group No. 61 | Rishu Raj | Shaheed Arman Gazi
"""

import tempfile
from pathlib import Path
from datetime import datetime, timezone
import pytest

from src.common.models import RawDocument, DataSourceType
from src.ingestion.preprocessor import IngestionPreprocessor
from src.ingestion.storage import EventIntelligenceStorage
from src.ingestion.mock_feed import get_mock_multi_source_feed
from src.ingestion.collector import MarketDataCollector


def test_text_cleaning_and_noise_removal():
    preprocessor = IngestionPreprocessor()
    dirty_text = """
    <div><h1>Breaking Market News</h1>
    <p>The Federal Reserve announced an interest rate cut today. <script>alert(1);</script></p>
    Disclaimer: All rights reserved. Subscribe to our newsletter for more.
    </div>
    """
    cleaned = preprocessor.clean_text(dirty_text)
    assert "The Federal Reserve announced an interest rate cut today." in cleaned
    assert "Disclaimer:" not in cleaned
    assert "alert" not in cleaned


def test_deduplication():
    preprocessor = IngestionPreprocessor(deduplication_threshold=0.8)
    doc1 = RawDocument(
        doc_id="1",
        source_type=DataSourceType.FINANCIAL_NEWS,
        source_name="Reuters",
        title="Fed cuts interest rates by 50 bps",
        content="The Federal Reserve slashed benchmark borrowing costs by 50 basis points.",
        published_at=datetime.now(timezone.utc)
    )
    doc2 = RawDocument(
        doc_id="2",
        source_type=DataSourceType.FINANCIAL_NEWS,
        source_name="Bloomberg",
        title="Fed cuts interest rates by 50 bps",
        content="The Federal Reserve slashed benchmark borrowing costs by 50 basis points.",
        published_at=datetime.now(timezone.utc)
    )
    
    clean1 = preprocessor.process(doc1)
    clean2 = preprocessor.process(doc2, existing_docs=[clean1])
    
    assert clean1.is_duplicate is False
    assert clean2.is_duplicate is True


def test_storage_layer():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_storage.db"
        storage = EventIntelligenceStorage(db_path=db_path)
        
        feed = get_mock_multi_source_feed()
        assert len(feed) > 0
        
        preprocessor = IngestionPreprocessor()
        cleaned_docs = []
        for raw in feed:
            storage.save_raw_document(raw)
            c = preprocessor.process(raw, existing_docs=cleaned_docs)
            cleaned_docs.append(c)
            storage.save_cleaned_document(c)
            
        stored = storage.get_cleaned_documents(limit=10)
        assert len(stored) == len(cleaned_docs)
        assert stored[0].source_credibility > 0


def test_market_data_collector():
    collector = MarketDataCollector()
    df = collector.fetch_historical_prices("NVDA", "2024-01-01", "2024-01-15")
    assert not df.empty
    assert "Close" in df.columns
    assert "Volume" in df.columns

