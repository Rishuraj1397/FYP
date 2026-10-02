"""
Core Pydantic data schemas for the Event Intelligence & Market Impact system.
Group No. 61 | Rishu Raj | Shaheed Arman Gazi
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class DataSourceType(str, Enum):
    FINANCIAL_NEWS = "FINANCIAL_NEWS"
    OFFICIAL_ANNOUNCEMENT = "OFFICIAL_ANNOUNCEMENT"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    MARKET_DATA = "MARKET_DATA"


class EntityType(str, Enum):
    COMPANY = "COMPANY"
    COUNTRY = "COUNTRY"
    ORGANIZATION = "ORGANIZATION"
    ASSET = "ASSET"
    COMMODITY = "COMMODITY"
    CURRENCY = "CURRENCY"
    SECTOR = "SECTOR"


class EventCategory(str, Enum):
    EARNINGS = "EARNINGS"
    MERGERS_ACQUISITIONS = "MERGERS_ACQUISITIONS"
    CENTRAL_BANK_POLICY = "CENTRAL_BANK_POLICY"
    GEOPOLITICAL_SANCTIONS = "GEOPOLITICAL_SANCTIONS"
    REGULATORY_LEGAL = "REGULATORY_LEGAL"
    MACRO_ECONOMIC = "MACRO_ECONOMIC"
    SUPPLY_CHAIN = "SUPPLY_CHAIN"
    EXECUTIVE_LEADERSHIP = "EXECUTIVE_LEADERSHIP"
    UNKNOWN = "UNKNOWN"


class SentimentPolarity(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class RawDocument(BaseModel):
    doc_id: str
    source_type: DataSourceType
    source_name: str
    title: str
    content: str
    url: Optional[str] = None
    published_at: datetime
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)


class CleanedDocument(BaseModel):
    doc_id: str
    source_type: DataSourceType
    source_name: str
    title: str
    cleaned_content: str
    summary_sentence: str
    url: Optional[str] = None
    published_at: datetime
    content_hash: str
    source_credibility: float = 0.8
    char_count: int
    is_duplicate: bool = False
    canonical_cluster_id: Optional[str] = None


class NamedEntity(BaseModel):
    text: str
    entity_type: EntityType
    ticker: Optional[str] = None
    canonical_name: Optional[str] = None
    sector: Optional[str] = None
    confidence: float = 0.9


class FinancialSentiment(BaseModel):
    polarity: SentimentPolarity
    polarity_score: float = Field(..., ge=-1.0, le=1.0)
    hawkish_dovish_score: float = Field(0.0, ge=-1.0, le=1.0)
    uncertainty_score: float = Field(0.0, ge=0.0, le=1.0)
    impact_intensity: float = Field(0.5, ge=0.0, le=1.0)


class DetectedEvent(BaseModel):
    event_id: str
    title: str
    category: EventCategory
    description: str
    timestamp: datetime
    entities: List[NamedEntity] = Field(default_factory=list)
    primary_assets: List[str] = Field(default_factory=list)
    sentiment: FinancialSentiment
    cluster_id: str
    corroboration_count: int = 1
    credibility_score: float = 0.8
    source_urls: List[str] = Field(default_factory=list)
    source_doc_ids: List[str] = Field(default_factory=list)
    evidence_excerpts: List[str] = Field(default_factory=list)
    has_conflicts: bool = False
    conflict_notes: Optional[str] = None


class KGNode(BaseModel):
    id: str
    label: str
    node_type: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class KGEdge(BaseModel):
    source: str
    target: str
    relation: str
    weight: float = 1.0
    evidence: Optional[str] = None
    source_url: Optional[str] = None
    timestamp: Optional[str] = None


class KnowledgeGraphData(BaseModel):
    nodes: List[KGNode] = Field(default_factory=list)
    edges: List[KGEdge] = Field(default_factory=list)


class EventWindowMetrics(BaseModel):
    asset_ticker: str
    event_id: str
    event_date: str
    pre_window_return: float
    event_day_return: float
    post_window_return: float
    abnormal_return: float
    cumulative_abnormal_return: float
    volume_z_score: float
    realized_volatility: float
    baseline_volatility: float
    volatility_shock: float
    affected_sector: Optional[str] = None


class HistoricalAnalogy(BaseModel):
    past_event_id: str
    past_event_title: str
    past_date: str
    similarity_score: float
    category: EventCategory
    primary_asset: str
    actual_car_3d: float
    actual_car_5d: float
    outcome_summary: str


class InformationCascadeHop(BaseModel):
    step: int
    channel: str
    timestamp: str
    headline_or_action: str
    amplification_score: float
    sentiment: str


class AIMarketBrief(BaseModel):
    brief_id: str
    event_id: str
    headline: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    what_happened: str
    key_sources: List[Dict[str, Any]] = Field(default_factory=list)
    affected_assets: List[Dict[str, Any]] = Field(default_factory=list)
    observed_reaction: str
    expected_spillover: str
    contradictory_unresolved: Optional[str] = None
    evidence_chain: List[str] = Field(default_factory=list)
    analyst_confidence: float = 0.92


class ValidationFeedback(BaseModel):
    feedback_id: str
    target_id: str
    target_type: str
    status: str
    verified_category: Optional[EventCategory] = None
    verified_sentiment: Optional[SentimentPolarity] = None
    reviewer: str = "Analyst"
    reviewer_notes: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)

