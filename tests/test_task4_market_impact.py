"""
Test suite for Phase 4: Task 4 - Market Impact Analysis Engine.
Group No. 61 | Rishu Raj | Shaheed Arman Gazi
"""

from datetime import datetime, timezone
import pytest
import pandas as pd
import numpy as np

from src.common.models import (
    DetectedEvent,
    NamedEntity,
    EntityType,
    EventCategory,
    FinancialSentiment,
    SentimentPolarity
)
from src.market_analysis.event_window import EventWindowAnalyzer
from src.market_analysis.sector_spillover import SectorSpilloverAnalyzer
from src.market_analysis.historical_analogy import HistoricalAnalogyEngine
from src.market_analysis.cascade_timeline import InformationCascadeReconstructor


@pytest.fixture
def sample_event():
    return DetectedEvent(
        event_id="EVT-NVDA-TEST",
        title="Bureau of Industry and Security Tightens AI Chip Export Controls",
        category=EventCategory.GEOPOLITICAL_SANCTIONS,
        description="US curbs exports of AI semiconductors.",
        timestamp=datetime.now(timezone.utc),
        entities=[
            NamedEntity(text="Nvidia", entity_type=EntityType.COMPANY, ticker="NVDA", sector="Semiconductors"),
            NamedEntity(text="TSMC", entity_type=EntityType.COMPANY, ticker="TSM", sector="Semiconductor Foundry")
        ],
        primary_assets=["NVDA", "TSM"],
        sentiment=FinancialSentiment(
            polarity=SentimentPolarity.BEARISH,
            polarity_score=-0.80,
            hawkish_dovish_score=0.0,
            uncertainty_score=0.65,
            impact_intensity=0.90
        ),
        cluster_id="cluster-0",
        corroboration_count=3,
        credibility_score=0.94,
        source_urls=["https://reuters.com/nvda"],
        source_doc_ids=["doc-1"],
        evidence_excerpts=["BIS issues new restrictions."]
    )


def test_event_window_analyzer(sample_event):
    analyzer = EventWindowAnalyzer(pre_window_days=3, post_window_days=3)
    
    dates = pd.date_range("2024-01-01", periods=20, freq="B")
    prices = np.full(20, 100.0)
    prices[10:] = 94.0
    df = pd.DataFrame({
        "Date": dates,
        "Close": prices,
        "Volume": [1e6] * 10 + [4e6] + [1.5e6] * 9
    })
    
    sample_event.timestamp = dates[10].to_pydatetime().replace(tzinfo=timezone.utc)
    metrics = analyzer.analyze_event_impact(df, sample_event, "NVDA")

    assert metrics.asset_ticker == "NVDA"
    assert metrics.abnormal_return < 0
    assert metrics.cumulative_abnormal_return < 0
    assert metrics.volume_z_score > 1.5


def test_sector_spillover_analyzer(sample_event):
    spillover = SectorSpilloverAnalyzer()
    
    analyzer = EventWindowAnalyzer()
    nvda_m = analyzer._default_metrics("NVDA", sample_event)
    tsm_m = analyzer._default_metrics("TSM", sample_event)
    amd_m = analyzer._default_metrics("AMD", sample_event)
    
    res = spillover.analyze_spillover(sample_event, [nvda_m, tsm_m, amd_m])
    assert res["event_id"] == sample_event.event_id
    assert "Semiconductors" in res["sector_summary"] or "General" in res["sector_summary"] or "Technology" in res["sector_summary"]
    assert len(res["losers"]) > 0


def test_historical_analogy_engine(sample_event):
    engine = HistoricalAnalogyEngine()
    analogues = engine.find_analogues(sample_event, top_k=2)
    assert len(analogues) == 2
    assert analogues[0].category == EventCategory.GEOPOLITICAL_SANCTIONS
    assert analogues[0].similarity_score > 0.7


def test_cascade_timeline_reconstructor(sample_event):
    reconstructor = InformationCascadeReconstructor()
    cascade = reconstructor.reconstruct_cascade(sample_event)
    assert len(cascade) == 4
    assert cascade[0].channel == "OFFICIAL_DISCLOSURE"
    assert cascade[-1].channel == "MARKET_ORDERBOOK"
    assert cascade[-1].amplification_score == 1.0

