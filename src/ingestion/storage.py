"""
Storage layer for structured metadata, raw documents, events, and metrics.
Supports SQLite out of the box with PostgreSQL schema compatibility.
Group No. 61 | Rishu Raj | Shaheed Arman Gazi
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from config.settings import settings
from src.common.models import (
    RawDocument,
    CleanedDocument,
    DetectedEvent,
    ValidationFeedback,
    EventWindowMetrics,
    AIMarketBrief
)


class EventIntelligenceStorage:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS raw_documents (
                    doc_id TEXT PRIMARY KEY,
                    source_type TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    url TEXT,
                    published_at TEXT NOT NULL,
                    fetched_at TEXT NOT NULL,
                    raw_metadata TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cleaned_documents (
                    doc_id TEXT PRIMARY KEY,
                    source_type TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    title TEXT NOT NULL,
                    cleaned_content TEXT NOT NULL,
                    summary_sentence TEXT NOT NULL,
                    url TEXT,
                    published_at TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    source_credibility REAL NOT NULL,
                    char_count INTEGER NOT NULL,
                    is_duplicate INTEGER NOT NULL DEFAULT 0,
                    canonical_cluster_id TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detected_events (
                    event_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    entities_json TEXT NOT NULL,
                    primary_assets_json TEXT NOT NULL,
                    sentiment_json TEXT NOT NULL,
                    cluster_id TEXT NOT NULL,
                    corroboration_count INTEGER NOT NULL,
                    credibility_score REAL NOT NULL,
                    source_urls_json TEXT NOT NULL,
                    source_doc_ids_json TEXT NOT NULL,
                    evidence_excerpts_json TEXT NOT NULL,
                    has_conflicts INTEGER NOT NULL DEFAULT 0,
                    conflict_notes TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_impact_metrics (
                    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_ticker TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    event_date TEXT NOT NULL,
                    pre_window_return REAL NOT NULL,
                    event_day_return REAL NOT NULL,
                    post_window_return REAL NOT NULL,
                    abnormal_return REAL NOT NULL,
                    cumulative_abnormal_return REAL NOT NULL,
                    volume_z_score REAL NOT NULL,
                    realized_volatility REAL NOT NULL,
                    baseline_volatility REAL NOT NULL,
                    volatility_shock REAL NOT NULL,
                    affected_sector TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_market_briefs (
                    brief_id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL,
                    headline TEXT NOT NULL,
                    generated_at TEXT NOT NULL,
                    what_happened TEXT NOT NULL,
                    key_sources_json TEXT NOT NULL,
                    affected_assets_json TEXT NOT NULL,
                    observed_reaction TEXT NOT NULL,
                    expected_spillover TEXT NOT NULL,
                    contradictory_unresolved TEXT,
                    evidence_chain_json TEXT NOT NULL,
                    analyst_confidence REAL NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS validation_feedback (
                    feedback_id TEXT PRIMARY KEY,
                    target_id TEXT NOT NULL,
                    target_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    verified_category TEXT,
                    verified_sentiment TEXT,
                    reviewer TEXT NOT NULL,
                    reviewer_notes TEXT,
                    timestamp TEXT NOT NULL
                )
            """)
            conn.commit()

    def save_raw_document(self, doc: RawDocument):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO raw_documents (
                    doc_id, source_type, source_name, title, content, url,
                    published_at, fetched_at, raw_metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc.doc_id,
                doc.source_type.value,
                doc.source_name,
                doc.title,
                doc.content,
                doc.url,
                doc.published_at.isoformat(),
                doc.fetched_at.isoformat(),
                json.dumps(doc.raw_metadata)
            ))
            conn.commit()

    def save_cleaned_document(self, doc: CleanedDocument):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO cleaned_documents (
                    doc_id, source_type, source_name, title, cleaned_content,
                    summary_sentence, url, published_at, content_hash,
                    source_credibility, char_count, is_duplicate, canonical_cluster_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc.doc_id,
                doc.source_type.value,
                doc.source_name,
                doc.title,
                doc.cleaned_content,
                doc.summary_sentence,
                doc.url,
                doc.published_at.isoformat(),
                doc.content_hash,
                doc.source_credibility,
                doc.char_count,
                1 if doc.is_duplicate else 0,
                doc.canonical_cluster_id
            ))
            conn.commit()

    def get_cleaned_documents(self, limit: int = 100, include_duplicates: bool = False) -> List[CleanedDocument]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM cleaned_documents"
            params = []
            if not include_duplicates:
                query += " WHERE is_duplicate = 0"
            query += " ORDER BY published_at DESC LIMIT ?"
            params.append(limit)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            docs = []
            for r in rows:
                docs.append(CleanedDocument(
                    doc_id=r["doc_id"],
                    source_type=r["source_type"],
                    source_name=r["source_name"],
                    title=r["title"],
                    cleaned_content=r["cleaned_content"],
                    summary_sentence=r["summary_sentence"],
                    url=r["url"],
                    published_at=datetime.fromisoformat(r["published_at"]),
                    content_hash=r["content_hash"],
                    source_credibility=r["source_credibility"],
                    char_count=r["char_count"],
                    is_duplicate=bool(r["is_duplicate"]),
                    canonical_cluster_id=r["canonical_cluster_id"]
                ))
            return docs

    def save_detected_event(self, event: DetectedEvent):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO detected_events (
                    event_id, title, category, description, timestamp,
                    entities_json, primary_assets_json, sentiment_json, cluster_id,
                    corroboration_count, credibility_score, source_urls_json,
                    source_doc_ids_json, evidence_excerpts_json, has_conflicts, conflict_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id,
                event.title,
                event.category.value,
                event.description,
                event.timestamp.isoformat(),
                json.dumps([e.model_dump() for e in event.entities]),
                json.dumps(event.primary_assets),
                json.dumps(event.sentiment.model_dump()),
                event.cluster_id,
                event.corroboration_count,
                event.credibility_score,
                json.dumps(event.source_urls),
                json.dumps(event.source_doc_ids),
                json.dumps(event.evidence_excerpts),
                1 if event.has_conflicts else 0,
                event.conflict_notes
            ))
            conn.commit()

    def get_detected_events(self, limit: int = 50) -> List[DetectedEvent]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM detected_events ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            events = []
            for r in rows:
                events.append(DetectedEvent(
                    event_id=r["event_id"],
                    title=r["title"],
                    category=r["category"],
                    description=r["description"],
                    timestamp=datetime.fromisoformat(r["timestamp"]),
                    entities=json.loads(r["entities_json"]),
                    primary_assets=json.loads(r["primary_assets_json"]),
                    sentiment=json.loads(r["sentiment_json"]),
                    cluster_id=r["cluster_id"],
                    corroboration_count=r["corroboration_count"],
                    credibility_score=r["credibility_score"],
                    source_urls=json.loads(r["source_urls_json"]),
                    source_doc_ids=json.loads(r["source_doc_ids_json"]),
                    evidence_excerpts=json.loads(r["evidence_excerpts_json"]),
                    has_conflicts=bool(r["has_conflicts"]),
                    conflict_notes=r["conflict_notes"]
                ))
            return events

    def get_event_by_id(self, event_id: str) -> Optional[DetectedEvent]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM detected_events WHERE event_id = ?", (event_id,))
            r = cursor.fetchone()
            if not r:
                return None
            return DetectedEvent(
                event_id=r["event_id"],
                title=r["title"],
                category=r["category"],
                description=r["description"],
                timestamp=datetime.fromisoformat(r["timestamp"]),
                entities=json.loads(r["entities_json"]),
                primary_assets=json.loads(r["primary_assets_json"]),
                sentiment=json.loads(r["sentiment_json"]),
                cluster_id=r["cluster_id"],
                corroboration_count=r["corroboration_count"],
                credibility_score=r["credibility_score"],
                source_urls=json.loads(r["source_urls_json"]),
                source_doc_ids=json.loads(r["source_doc_ids_json"]),
                evidence_excerpts=json.loads(r["evidence_excerpts_json"]),
                has_conflicts=bool(r["has_conflicts"]),
                conflict_notes=r["conflict_notes"]
            )

    def save_market_metrics(self, m: EventWindowMetrics):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO market_impact_metrics (
                    asset_ticker, event_id, event_date, pre_window_return, event_day_return,
                    post_window_return, abnormal_return, cumulative_abnormal_return,
                    volume_z_score, realized_volatility, baseline_volatility,
                    volatility_shock, affected_sector, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                m.asset_ticker,
                m.event_id,
                m.event_date,
                m.pre_window_return,
                m.event_day_return,
                m.post_window_return,
                m.abnormal_return,
                m.cumulative_abnormal_return,
                m.volume_z_score,
                m.realized_volatility,
                m.baseline_volatility,
                m.volatility_shock,
                m.affected_sector,
                datetime.utcnow().isoformat()
            ))
            conn.commit()

    def get_market_metrics_for_event(self, event_id: str) -> List[EventWindowMetrics]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM market_impact_metrics WHERE event_id = ?", (event_id,))
            rows = cursor.fetchall()
            return [
                EventWindowMetrics(
                    asset_ticker=r["asset_ticker"],
                    event_id=r["event_id"],
                    event_date=r["event_date"],
                    pre_window_return=r["pre_window_return"],
                    event_day_return=r["event_day_return"],
                    post_window_return=r["post_window_return"],
                    abnormal_return=r["abnormal_return"],
                    cumulative_abnormal_return=r["cumulative_abnormal_return"],
                    volume_z_score=r["volume_z_score"],
                    realized_volatility=r["realized_volatility"],
                    baseline_volatility=r["baseline_volatility"],
                    volatility_shock=r["volatility_shock"],
                    affected_sector=r["affected_sector"]
                )
                for r in rows
            ]

    def save_brief(self, brief: AIMarketBrief):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO ai_market_briefs (
                    brief_id, event_id, headline, generated_at, what_happened,
                    key_sources_json, affected_assets_json, observed_reaction,
                    expected_spillover, contradictory_unresolved, evidence_chain_json,
                    analyst_confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                brief.brief_id,
                brief.event_id,
                brief.headline,
                brief.generated_at.isoformat(),
                brief.what_happened,
                json.dumps(brief.key_sources),
                json.dumps(brief.affected_assets),
                brief.observed_reaction,
                brief.expected_spillover,
                brief.contradictory_unresolved,
                json.dumps(brief.evidence_chain),
                brief.analyst_confidence
            ))
            conn.commit()

    def get_brief_for_event(self, event_id: str) -> Optional[AIMarketBrief]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ai_market_briefs WHERE event_id = ? ORDER BY generated_at DESC LIMIT 1", (event_id,))
            r = cursor.fetchone()
            if not r:
                return None
            return AIMarketBrief(
                brief_id=r["brief_id"],
                event_id=r["event_id"],
                headline=r["headline"],
                generated_at=datetime.fromisoformat(r["generated_at"]),
                what_happened=r["what_happened"],
                key_sources=json.loads(r["key_sources_json"]),
                affected_assets=json.loads(r["affected_assets_json"]),
                observed_reaction=r["observed_reaction"],
                expected_spillover=r["expected_spillover"],
                contradictory_unresolved=r["contradictory_unresolved"],
                evidence_chain=json.loads(r["evidence_chain_json"]),
                analyst_confidence=r["analyst_confidence"]
            )

    def save_feedback(self, feedback: ValidationFeedback):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO validation_feedback (
                    feedback_id, target_id, target_type, status,
                    verified_category, verified_sentiment, reviewer,
                    reviewer_notes, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                feedback.feedback_id,
                feedback.target_id,
                feedback.target_type,
                feedback.status,
                feedback.verified_category.value if feedback.verified_category else None,
                feedback.verified_sentiment.value if feedback.verified_sentiment else None,
                feedback.reviewer,
                feedback.reviewer_notes,
                feedback.timestamp.isoformat()
            ))
            conn.commit()

    def get_feedback_list(self, limit: int = 50) -> List[ValidationFeedback]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM validation_feedback ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [
                ValidationFeedback(
                    feedback_id=r["feedback_id"],
                    target_id=r["target_id"],
                    target_type=r["target_type"],
                    status=r["status"],
                    verified_category=r["verified_category"],
                    verified_sentiment=r["verified_sentiment"],
                    reviewer=r["reviewer"],
                    reviewer_notes=r["reviewer_notes"],
                    timestamp=datetime.fromisoformat(r["timestamp"])
                )
                for r in rows
            ]

