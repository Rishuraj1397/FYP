"""
Test suite for Phase 5: Task 5 - AI Intelligence Generation & Human-in-the-Loop Validation.
Group No. 61 | Rishu Raj | Shaheed Arman Gazi
"""

import tempfile
from pathlib import Path
from datetime import datetime, timezone
import pytest

from src.common.models import (
    DetectedEvent,
    NamedEntity,
    EntityType,
    EventCategory,
    FinancialSentiment,
    SentimentPolarity,
    KnowledgeGraphData,
    KGNode,
    KGEdge,
    EventWindowMetrics
)
from src.intelligence_gen.brief_generator import AIMarketBriefGenerator
from src.intelligence_gen.explainability import ExplainabilityEngine
from src.validation.feedback_store import HumanInTheLoopValidator
from src.ingestion.storage import EventIntelligenceStorage


@pytest.fixture
def sample_event_and_graph():
    event = DetectedEvent(
        event_id="EVT-FOMC-99",
        title="Federal Reserve Cuts Benchmark Rate by 50 bps",
        category=EventCategory.CENTRAL_BANK_POLICY,
        description="The FOMC lowered rates by 50 bps in response to cooling labor inflation.",
        timestamp=datetime.now(timezone.utc),
        entities=[
            NamedEntity(text="Federal Reserve", entity_type=EntityType.ORGANIZATION, ticker=None),
            NamedEntity(text="SPDR S&P 500 ETF", entity_type=EntityType.ASSET, ticker="SPY")
        ],
        primary_assets=["SPY"],
        sentiment=FinancialSentiment(
            polarity=SentimentPolarity.BULLISH,
            polarity_score=0.82,
            hawkish_dovish_score=-0.95,
            uncertainty_score=0.15,
            impact_intensity=0.90
        ),
        cluster_id="cluster-fomc",
        corroboration_count=4,
        credibility_score=0.98,
        source_urls=["https://federalreserve.gov/fomc"],
        source_doc_ids=["doc-fed-1"],
        evidence_excerpts=["Committee decided to lower target range by 50 basis points."]
    )

    graph_data = KnowledgeGraphData(
        nodes=[
            KGNode(id="EVENT_EVT-FOMC-99", label="FOMC Rate Cut", node_type="Event"),
            KGNode(id="ASSET_SPY", label="SPY", node_type="Asset")
        ],
        edges=[
            KGEdge(source="EVENT_EVT-FOMC-99", target="ASSET_SPY", relation="TRANSMITS_TO", weight=0.9)
        ]
    )

    metric = EventWindowMetrics(
        asset_ticker="SPY",
        event_id="EVT-FOMC-99",
        event_date="2024-09-18",
        pre_window_return=0.8,
        event_day_return=1.7,
        post_window_return=2.3,
        abnormal_return=1.5,
        cumulative_abnormal_return=3.8,
        volume_z_score=3.1,
        realized_volatility=2.1,
        baseline_volatility=1.2,
        volatility_shock=0.9,
        affected_sector="Broad Market"
    )

    return event, graph_data, [metric]


def test_brief_generation(sample_event_and_graph):
    event, graph_data, metrics = sample_event_and_graph
    generator = AIMarketBriefGenerator()
    brief = generator.generate_brief(event, metrics, graph_data)

    assert brief.event_id == event.event_id
    assert "Federal Reserve" in brief.what_happened or "Rate" in brief.what_happened
    assert len(brief.key_sources) == 1
    assert brief.key_sources[0]["url"] == "https://federalreserve.gov/fomc"
    assert len(brief.affected_assets) == 1
    assert brief.affected_assets[0]["ticker"] == "SPY"
    assert len(brief.evidence_chain) >= 3
    assert brief.analyst_confidence >= 0.90


def test_explainability_chain(sample_event_and_graph):
    event, graph_data, metrics = sample_event_and_graph
    explainer = ExplainabilityEngine()
    chain = explainer.build_evidence_chain(event, metrics, graph_data)

    assert any("Provenance" in step for step in chain)
    assert any("NLP Extraction" in step for step in chain)
    assert any("Graph Traversal" in step for step in chain)
    assert any("Market Validation" in step for step in chain)


def test_hitl_feedback_loop():
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = EventIntelligenceStorage(db_path=Path(tmpdir) / "hitl.db")
        validator = HumanInTheLoopValidator(storage=storage)

        event = DetectedEvent(
            event_id="EVT-TEST-FB",
            title="CEO Rumor",
            category=EventCategory.UNKNOWN,
            description="Unconfirmed CEO resignation rumor",
            timestamp=datetime.now(timezone.utc),
            entities=[],
            primary_assets=["AAPL"],
            sentiment=FinancialSentiment(
                polarity=SentimentPolarity.NEUTRAL,
                polarity_score=0.0,
                hawkish_dovish_score=0.0,
                uncertainty_score=0.8,
                impact_intensity=0.5
            ),
            cluster_id="c0",
            corroboration_count=1,
            credibility_score=0.5,
            source_urls=[],
            source_doc_ids=[],
            evidence_excerpts=[]
        )
        storage.save_detected_event(event)

        fb = validator.submit_feedback(
            target_id="EVT-TEST-FB",
            target_type="EVENT",
            status="MODIFIED",
            reviewer="Senior Quantitative Analyst",
            reviewer_notes="Confirmed executive departure through 8-K filing",
            verified_category=EventCategory.EXECUTIVE_LEADERSHIP,
            verified_sentiment=SentimentPolarity.BEARISH
        )

        assert fb.status == "MODIFIED"
        
        updated_event = storage.get_event_by_id("EVT-TEST-FB")
        assert updated_event.category == EventCategory.EXECUTIVE_LEADERSHIP
        assert updated_event.sentiment.polarity == SentimentPolarity.BEARISH

