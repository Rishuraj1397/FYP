"""
Test suite for Phase 3: Task 3 - Event Knowledge & Relationship Layer.
Group No. 61 | Rishu Raj | Shaheed Arman Gazi
"""

from datetime import datetime, timezone
import pytest

from src.common.models import (
    DetectedEvent,
    NamedEntity,
    EntityType,
    EventCategory,
    FinancialSentiment,
    SentimentPolarity,
    CleanedDocument,
    DataSourceType
)
from src.knowledge_graph.entity_linker import EntityLinker
from src.knowledge_graph.graph_builder import EventKnowledgeGraphBuilder
from src.knowledge_graph.corroboration import CorroborationEngine


def test_entity_linker():
    linker = EntityLinker()
    entity = NamedEntity(text="Nvidia", entity_type=EntityType.COMPANY, ticker="NVDA")
    resolved = linker.resolve_entity(entity)
    assert resolved["ticker"] == "NVDA"
    assert resolved["sector"] == "Semiconductors"
    assert "TSM" in resolved["suppliers"]
    assert "AMD" in resolved["competitors"]

    spillovers = linker.get_spillover_assets(["NVDA"])
    spillover_tickers = {s["ticker"] for s in spillovers}
    assert "TSM" in spillover_tickers
    assert "AMD" in spillover_tickers
    assert "SMH" in spillover_tickers


def test_knowledge_graph_builder():
    builder = EventKnowledgeGraphBuilder()
    
    event = DetectedEvent(
        event_id="EVT-CHIP-99",
        title="US Restricts AI Chip Exports",
        category=EventCategory.GEOPOLITICAL_SANCTIONS,
        description="Bureau of Industry and Security issues export limits on AI GPUs.",
        timestamp=datetime.now(timezone.utc),
        entities=[
            NamedEntity(text="Nvidia", entity_type=EntityType.COMPANY, ticker="NVDA", sector="Semiconductors"),
            NamedEntity(text="Taiwan Semiconductor", entity_type=EntityType.COMPANY, ticker="TSM", sector="Semiconductor Foundry")
        ],
        primary_assets=["NVDA", "TSM"],
        sentiment=FinancialSentiment(
            polarity=SentimentPolarity.BEARISH,
            polarity_score=-0.75,
            hawkish_dovish_score=0.0,
            uncertainty_score=0.6,
            impact_intensity=0.85
        ),
        cluster_id="cluster-0",
        corroboration_count=3,
        credibility_score=0.92,
        source_urls=["https://reuters.com/chips"],
        source_doc_ids=["doc-1"],
        evidence_excerpts=["Nvidia faces $400M revenue restriction."]
    )

    builder.add_event(event)
    
    assert builder.graph.has_node("EVENT_EVT-CHIP-99")
    assert builder.graph.has_node("ENTITY_NVIDIA_CORPORATION")
    assert builder.graph.has_node("ASSET_NVDA")
    assert builder.graph.has_node("SECTOR_SEMICONDUCTORS")

    assert builder.graph.has_edge("EVENT_EVT-CHIP-99", "ENTITY_NVIDIA_CORPORATION")
    assert builder.graph.has_edge("EVENT_EVT-CHIP-99", "ASSET_NVDA")

    subgraph_data = builder.get_event_subgraph("EVT-CHIP-99", depth=2)
    assert len(subgraph_data.nodes) >= 4
    assert len(subgraph_data.edges) >= 3

    cypher = builder.export_cypher()
    assert "MERGE (n:Event" in cypher
    assert "MERGE (a)-[:" in cypher


def test_corroboration_engine():
    engine = CorroborationEngine()
    
    docs = [
        CleanedDocument(
            doc_id="1",
            source_type=DataSourceType.OFFICIAL_ANNOUNCEMENT,
            source_name="Federal Reserve",
            title="FOMC rate cut",
            cleaned_content="50 bps cut",
            summary_sentence="50 bps cut",
            published_at=datetime.now(timezone.utc),
            content_hash="hash1",
            source_credibility=0.98,
            char_count=50
        ),
        CleanedDocument(
            doc_id="2",
            source_type=DataSourceType.FINANCIAL_NEWS,
            source_name="WSJ",
            title="Fed cuts rates",
            cleaned_content="Aggressive easing",
            summary_sentence="Aggressive easing",
            published_at=datetime.now(timezone.utc),
            content_hash="hash2",
            source_credibility=0.90,
            char_count=60
        )
    ]

    res = engine.evaluate_corroboration(docs)
    assert res["corroboration_count"] == 2
    assert res["credibility_score"] >= 0.90
    assert res["verification_status"] == "OFFICIALLY_VERIFIED"
    assert res["has_official_source"] is True

