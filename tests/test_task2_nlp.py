"""
Test suite for Phase 2: Task 2 - AI / NLP Event Intelligence Engine.
Group No. 61 | Rishu Raj | Shaheed Arman Gazi
"""

import pytest
from src.nlp.preprocessor import FinancialNLPPreprocessor
from src.nlp.ner import FinancialNER
from src.nlp.classifier import EventClassifier
from src.nlp.sentiment import FinancialSentimentAnalyzer
from src.nlp.clustering import EventClusteringEngine
from src.ingestion.mock_feed import get_mock_multi_source_feed
from src.ingestion.preprocessor import IngestionPreprocessor
from src.common.models import EventCategory, SentimentPolarity, EntityType


def test_financial_nlp_preprocessor():
    nlp_prep = FinancialNLPPreprocessor()
    text = "Nvidia Corp. saw GPU sales surge 45.2% to $18.1B. Meanwhile, the U.S. Federal Reserve cut rates by 50bps."
    sentences = nlp_prep.segment_sentences(text)
    assert len(sentences) == 2
    tokens = nlp_prep.tokenize(sentences[0])
    assert "45.2%" in tokens or "45.2" in tokens
    assert "$18.1B" in tokens or "18.1B" in tokens


def test_financial_ner():
    ner = FinancialNER()
    sample = "The Federal Reserve lowered rates. TSMC and Nvidia (NVDA) face export restrictions to China."
    entities = ner.extract_entities(sample)
    
    types = {e.entity_type for e in entities}
    assert EntityType.ORGANIZATION in types
    assert EntityType.COMPANY in types or EntityType.ASSET in types
    assert EntityType.COUNTRY in types

    nvda = next((e for e in entities if e.ticker == "NVDA"), None)
    assert nvda is not None
    assert nvda.sector == "Semiconductors"


def test_event_classifier():
    classifier = EventClassifier()
    
    cat1, conf1, _ = classifier.classify("Federal Reserve cuts target rate by 50 basis points at FOMC meeting.")
    assert cat1 == EventCategory.CENTRAL_BANK_POLICY
    assert conf1 > 0.7

    cat2, conf2, _ = classifier.classify("Bureau of Industry and Security issues export controls on advanced AI chips.")
    assert cat2 == EventCategory.GEOPOLITICAL_SANCTIONS
    assert conf2 > 0.7

    cat3, conf3, _ = classifier.classify("OPEC+ announces 1.5 million bpd crude oil production cut.")
    assert cat3 == EventCategory.SUPPLY_CHAIN
    assert conf3 > 0.7


def test_financial_sentiment():
    analyzer = FinancialSentimentAnalyzer()
    
    res_dovish = analyzer.analyze("Fed slashes rates by 50 basis points to support cooling employment. Stocks rally sharply.")
    assert res_dovish.polarity == SentimentPolarity.BULLISH
    assert res_dovish.hawkish_dovish_score < 0
    assert res_dovish.polarity_score > 0

    res_bearish = analyzer.analyze("Severe panic selloff as chip stocks slide under sweeping export ban. Uncertain long-term revenue risks.")
    assert res_bearish.polarity == SentimentPolarity.BEARISH
    assert res_bearish.uncertainty_score > 0.1


def test_event_clustering():
    raw_feed = get_mock_multi_source_feed()
    prep = IngestionPreprocessor()
    cleaned = [prep.process(r) for r in raw_feed]
    
    clustering_engine = EventClusteringEngine()
    events = clustering_engine.cluster_and_detect_events(cleaned)

    assert len(events) >= 2
    categories = {e.category for e in events}
    assert (EventCategory.GEOPOLITICAL_SANCTIONS in categories) or (EventCategory.CENTRAL_BANK_POLICY in categories)
    
    chip_event = next((e for e in events if "NVDA" in e.primary_assets or "chip" in e.title.lower()), None)
    if chip_event:
        assert chip_event.corroboration_count >= 1
        assert len(chip_event.evidence_excerpts) >= 1

