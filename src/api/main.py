"""
FastAPI Server orchestrating the end-to-end Event Intelligence & Market Impact system.
Phase 6 Layer of the Architecture.
Group No. 61 | Rishu Raj | Shaheed Arman Gazi
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config.settings import settings
from src.common.models import (
    DetectedEvent,
    EventCategory,
    SentimentPolarity,
    KnowledgeGraphData,
    EventWindowMetrics,
    AIMarketBrief,
    ValidationFeedback
)
from src.ingestion.collector import MarketDataCollector
from src.ingestion.preprocessor import IngestionPreprocessor
from src.ingestion.storage import EventIntelligenceStorage
from src.ingestion.mock_feed import get_mock_multi_source_feed
from src.nlp.clustering import EventClusteringEngine
from src.knowledge_graph.graph_builder import EventKnowledgeGraphBuilder
from src.market_analysis.event_window import EventWindowAnalyzer
from src.market_analysis.sector_spillover import SectorSpilloverAnalyzer
from src.market_analysis.historical_analogy import HistoricalAnalogyEngine
from src.market_analysis.cascade_timeline import InformationCascadeReconstructor
from src.intelligence_gen.brief_generator import AIMarketBriefGenerator
from src.validation.feedback_store import HumanInTheLoopValidator


# Initialize core system singletons
storage = EventIntelligenceStorage()
preprocessor = IngestionPreprocessor()
clustering_engine = EventClusteringEngine()
graph_builder = EventKnowledgeGraphBuilder()
market_collector = MarketDataCollector()
event_window_analyzer = EventWindowAnalyzer()
sector_analyzer = SectorSpilloverAnalyzer()
analogy_engine = HistoricalAnalogyEngine()
cascade_reconstructor = InformationCascadeReconstructor()
brief_generator = AIMarketBriefGenerator()
hitl_validator = HumanInTheLoopValidator(storage=storage)


def run_full_pipeline_internal() -> List[DetectedEvent]:
    """Executes Tasks 1 through 5 end-to-end."""
    # Task 1: Ingestion & Preprocessing
    raw_feed = get_mock_multi_source_feed()
    cleaned_docs = []
    for raw in raw_feed:
        storage.save_raw_document(raw)
        cleaned = preprocessor.process(raw, existing_docs=cleaned_docs)
        cleaned_docs.append(cleaned)
        storage.save_cleaned_document(cleaned)

    # Task 2: AI / NLP Event Intelligence
    events = clustering_engine.cluster_and_detect_events(cleaned_docs)

    # Tasks 3, 4, 5 for each detected event
    for evt in events:
        storage.save_detected_event(evt)
        # Task 3: Knowledge Graph
        graph_builder.add_event(evt)
        subgraph = graph_builder.get_event_subgraph(evt.event_id)

        # Task 4: Market Impact Analysis
        metrics_list: List[EventWindowMetrics] = []
        for ticker in evt.primary_assets:
            prices = market_collector.fetch_historical_prices(ticker, "2024-01-01", "2024-10-01")
            m = event_window_analyzer.analyze_event_impact(prices, evt, ticker)
            metrics_list.append(m)
            storage.save_market_metrics(m)

        if not metrics_list:
            m = event_window_analyzer._default_metrics("SPY", evt)
            metrics_list.append(m)
            storage.save_market_metrics(m)

        # Task 5: AI Intelligence Generation
        brief = brief_generator.generate_brief(evt, metrics_list, subgraph)
        storage.save_brief(brief)

    return events


def bootstrap_pipeline():
    existing_events = storage.get_detected_events(limit=5)
    if not existing_events:
        print("[Startup] Database empty. Bootstrapping initial ingestion pipeline...")
        run_full_pipeline_internal()


@asynccontextmanager
async def lifespan(app: FastAPI):
    bootstrap_pipeline()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Powered Multi-Source Event Intelligence & Market Impact Analysis Architecture",
    version=settings.VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
STATIC_DIR = Path(__file__).resolve().parent.parent / "dashboard" / "static"
TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "dashboard" / "templates"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class FeedbackRequest(BaseModel):
    target_id: str
    target_type: str = "EVENT"
    status: str = "APPROVED"
    reviewer: str = "Quantitative Analyst"
    reviewer_notes: str = ""
    verified_category: Optional[EventCategory] = None
    verified_sentiment: Optional[SentimentPolarity] = None


@app.post("/api/pipeline/run")
def trigger_pipeline():
    """Triggers end-to-end ingestion, NLP clustering, KG construction, and impact modeling."""
    events = run_full_pipeline_internal()
    return {
        "status": "success",
        "events_processed": len(events),
        "events": [e.model_dump() for e in events]
    }


@app.get("/api/feed")
def get_event_feed(limit: int = 20):
    """Output 1: Event Intelligence Feed."""
    events = storage.get_detected_events(limit=limit)
    return {
        "count": len(events),
        "events": [e.model_dump() for e in events]
    }


@app.get("/api/events/{event_id}")
def get_event_details(event_id: str):
    """Retrieve full detail for a single event."""
    evt = storage.get_event_by_id(event_id)
    if not evt:
        raise HTTPException(status_code=404, detail="Event not found")
    return evt.model_dump()


@app.get("/api/graph/{event_id}")
def get_event_graph(event_id: str, depth: int = Query(default=2, ge=1, le=4)):
    """Output 2: Event-to-Market Relationship Graph."""
    subgraph = graph_builder.get_event_subgraph(event_id, depth=depth)
    return subgraph.model_dump()


@app.get("/api/market-reaction/{event_id}")
def get_market_reaction(event_id: str):
    """Output 3: Market Reaction Charts and Metrics."""
    metrics = storage.get_market_metrics_for_event(event_id)
    evt = storage.get_event_by_id(event_id)
    if not evt:
        raise HTTPException(status_code=404, detail="Event not found")
    
    spillover = sector_analyzer.analyze_spillover(evt, metrics)
    return {
        "event_id": event_id,
        "metrics": [m.model_dump() for m in metrics],
        "spillover_analysis": spillover
    }


@app.get("/api/brief/{event_id}")
def get_ai_market_brief(event_id: str):
    """Output 4: AI-Generated Market Brief."""
    brief = storage.get_brief_for_event(event_id)
    if not brief:
        evt = storage.get_event_by_id(event_id)
        if not evt:
            raise HTTPException(status_code=404, detail="Event not found")
        metrics = storage.get_market_metrics_for_event(event_id)
        subgraph = graph_builder.get_event_subgraph(event_id)
        brief = brief_generator.generate_brief(evt, metrics, subgraph)
        storage.save_brief(brief)
    return brief.model_dump()


@app.get("/api/analogies/{event_id}")
def get_historical_analogies(event_id: str):
    """Historical Event Comparison analogues."""
    evt = storage.get_event_by_id(event_id)
    if not evt:
        raise HTTPException(status_code=404, detail="Event not found")
    analogues = analogy_engine.find_analogues(evt, top_k=3)
    return {
        "event_id": event_id,
        "analogues": [a.model_dump() for a in analogues]
    }


@app.get("/api/cascade/{event_id}")
def get_information_cascade(event_id: str):
    """Chronological information cascade timeline hops."""
    evt = storage.get_event_by_id(event_id)
    if not evt:
        raise HTTPException(status_code=404, detail="Event not found")
    hops = cascade_reconstructor.reconstruct_cascade(evt)
    return {
        "event_id": event_id,
        "hops": [h.model_dump() for h in hops]
    }


@app.post("/api/validation")
def submit_analyst_validation(req: FeedbackRequest):
    """Human-in-the-Loop Validation feedback endpoint."""
    feedback = hitl_validator.submit_feedback(
        target_id=req.target_id,
        target_type=req.target_type,
        status=req.status,
        reviewer=req.reviewer,
        reviewer_notes=req.reviewer_notes,
        verified_category=req.verified_category,
        verified_sentiment=req.verified_sentiment
    )
    return {"status": "success", "feedback": feedback.model_dump()}


@app.get("/api/validation/history")
def get_validation_history(limit: int = 50):
    """Retrieve Human-in-the-Loop audit history."""
    history = hitl_validator.get_review_history(limit=limit)
    return {"count": len(history), "history": [h.model_dump() for h in history]}


@app.get("/", response_class=HTMLResponse)
def index_page():
    """Serves the interactive dashboard."""
    html_path = TEMPLATE_DIR / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>AI-Powered Event Intelligence Dashboard</h1><p>Template loading...</p>")

