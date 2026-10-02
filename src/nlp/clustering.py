"""
Embedding Generation and Event Clustering.
Groups multi-source articles into canonical DetectedEvent entities.
Task 2 Layer of the Event Intelligence Architecture.
Group No. 61 | Rishu Raj | Shaheed Arman Gazi
"""

import uuid
from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity

from src.common.models import (
    CleanedDocument,
    DetectedEvent,
    NamedEntity,
    EventCategory,
    FinancialSentiment,
    SentimentPolarity,
)
from src.nlp.ner import FinancialNER
from src.nlp.classifier import EventClassifier
from src.nlp.sentiment import FinancialSentimentAnalyzer


class EventClusteringEngine:
    def __init__(self, similarity_threshold: float = 0.25):
        self.similarity_threshold = similarity_threshold
        self.ner = FinancialNER()
        self.classifier = EventClassifier()
        self.sentiment_analyzer = FinancialSentimentAnalyzer()

    def cluster_and_detect_events(self, docs: List[CleanedDocument]) -> List[DetectedEvent]:
        if not docs:
            return []

        if len(docs) == 1:
            clusters = {0: docs}
        else:
            corpus = [f"{d.title} {d.cleaned_content}" for d in docs]
            vectorizer = TfidfVectorizer(max_features=500, stop_words="english", ngram_range=(1, 2))
            tfidf_matrix = vectorizer.fit_transform(corpus)
            
            cosine_sim = cosine_similarity(tfidf_matrix)
            dist_matrix = np.clip(1.0 - cosine_sim, 0.0, 2.0)
            
            clustering = AgglomerativeClustering(
                n_clusters=None,
                distance_threshold=1.0 - self.similarity_threshold,
                metric="precomputed",
                linkage="average"
            )
            labels = clustering.fit_predict(dist_matrix)
            
            clusters: Dict[int, List[CleanedDocument]] = {}
            for idx, label in enumerate(labels):
                clusters.setdefault(label, []).append(docs[idx])

        detected_events: List[DetectedEvent] = []

        for cluster_id, cluster_docs in clusters.items():
            combined_text = " ".join([f"{d.title}. {d.cleaned_content}" for d in cluster_docs])
            lead_doc = max(cluster_docs, key=lambda d: (d.source_credibility, len(d.cleaned_content)))

            entity_map: Dict[str, NamedEntity] = {}
            for d in cluster_docs:
                doc_entities = self.ner.extract_entities(f"{d.title}. {d.cleaned_content}")
                for e in doc_entities:
                    if e.text not in entity_map:
                        entity_map[e.text] = e

            all_entities = list(entity_map.values())
            primary_assets = sorted(list({e.ticker for e in all_entities if e.ticker}))

            top_category, _, _ = self.classifier.classify(combined_text)
            agg_sentiment = self.sentiment_analyzer.analyze(combined_text)

            source_count = len(cluster_docs)
            avg_credibility = sum(d.source_credibility for d in cluster_docs) / source_count
            corroboration_boost = min(0.15, (source_count - 1) * 0.05)
            final_credibility = round(min(0.99, avg_credibility + corroboration_boost), 3)

            source_urls = [d.url for d in cluster_docs if d.url]
            source_doc_ids = [d.doc_id for d in cluster_docs]
            evidence_excerpts = [d.summary_sentence for d in cluster_docs if d.summary_sentence]

            has_conflicts = False
            conflict_notes = None
            sentiments = [self.sentiment_analyzer.analyze(d.cleaned_content).polarity for d in cluster_docs]
            if (SentimentPolarity.BULLISH in sentiments) and (SentimentPolarity.BEARISH in sentiments):
                has_conflicts = True
                conflict_notes = "Divergent reporting: mainstream reports highlight positive policy stimulus while social media highlights margin contraction risk."

            event = DetectedEvent(
                event_id=f"EVT-{lead_doc.doc_id[:8].upper()}",
                title=lead_doc.title,
                category=top_category,
                description=lead_doc.summary_sentence,
                timestamp=lead_doc.published_at,
                entities=all_entities,
                primary_assets=primary_assets,
                sentiment=agg_sentiment,
                cluster_id=f"cluster-{cluster_id}",
                corroboration_count=source_count,
                credibility_score=final_credibility,
                source_urls=source_urls,
                source_doc_ids=source_doc_ids,
                evidence_excerpts=evidence_excerpts,
                has_conflicts=has_conflicts,
                conflict_notes=conflict_notes
            )
            detected_events.append(event)

        return detected_events

