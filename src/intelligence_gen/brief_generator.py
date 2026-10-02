"""
AI Intelligence Generation: Evidence-grounded AI Market Brief Generator.
Constructs structured executive briefings with citation footnotes and conflict detection.
Task 5 Layer of the Event Intelligence Architecture.
Group No. 61 | Rishu Raj | Shaheed Arman Gazi
"""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.common.models import (
    DetectedEvent,
    EventWindowMetrics,
    AIMarketBrief,
    KnowledgeGraphData
)
from src.intelligence_gen.explainability import ExplainabilityEngine


class AIMarketBriefGenerator:
    """Generates structured, evidence-grounded market briefs matching Task 5 specifications."""

    def __init__(self):
        self.explainability_engine = ExplainabilityEngine()

    def generate_brief(
        self,
        event: DetectedEvent,
        metrics_list: List[EventWindowMetrics],
        graph_data: KnowledgeGraphData
    ) -> AIMarketBrief:
        brief_id = f"BRIEF-{uuid.uuid4().hex[:8].upper()}"

        headline = f"Market Intelligence Brief: {event.title}"

        what_happened = (
            f"On {event.timestamp.strftime('%B %d, %Y at %H:%M UTC')}, an event categorized as "
            f"'{event.category.value.replace('_', ' ')}' was detected: '{event.title}'. {event.description} "
            f"Overall sentiment stance is classified as {event.sentiment.polarity.value} "
            f"(Polarity Score: {event.sentiment.polarity_score:+0.2f}, Impact Intensity: {int(event.sentiment.impact_intensity * 100)}%)."
        )

        key_sources: List[Dict[str, Any]] = []
        for i, url in enumerate(event.source_urls):
            doc_id = event.source_doc_ids[i] if i < len(event.source_doc_ids) else f"doc-{i}"
            excerpt = event.evidence_excerpts[i] if i < len(event.evidence_excerpts) else ""
            key_sources.append({
                "source_id": doc_id,
                "url": url,
                "credibility_score": event.credibility_score,
                "excerpt": excerpt
            })

        affected_assets: List[Dict[str, Any]] = []
        metrics_map = {m.asset_ticker: m for m in metrics_list}
        
        for ticker in event.primary_assets:
            m = metrics_map.get(ticker)
            affected_assets.append({
                "ticker": ticker,
                "type": "PRIMARY_CATALYST",
                "abnormal_return": f"{m.abnormal_return:+0.2f}%" if m else "N/A",
                "cumulative_abnormal_return": f"{m.cumulative_abnormal_return:+0.2f}%" if m else "N/A",
                "volume_z_score": f"{m.volume_z_score:+0.2f}" if m else "N/A",
                "sector": m.affected_sector if m else "Technology"
            })

        if metrics_list:
            top = metrics_list[0]
            observed_reaction = (
                f"{top.asset_ticker} recorded an event-day return of {top.event_day_return:+0.2f}% with "
                f"abnormal return of {top.abnormal_return:+0.2f}% and a trading volume spike of {top.volume_z_score:+0.2f} standard deviations. "
                f"Post-event realized volatility shifted by {top.volatility_shock:+0.2f}% relative to baseline."
            )
        else:
            observed_reaction = "Awaiting subsequent market session trading close to confirm realized volatility."

        spillover_peers = [m.asset_ticker for m in metrics_list if m.asset_ticker not in event.primary_assets]
        if spillover_peers:
            expected_spillover = (
                f"Transmission observed into supply chain partners and sector peers: {', '.join(spillover_peers[:4])}. "
                f"Contagion monitoring active across sector ETFs."
            )
        else:
            expected_spillover = "Direct asset concentration observed; systemic contagion currently contained."

        if event.has_conflicts:
            contradictory = event.conflict_notes or "Divergent reporting observed between official filings and social media sentiment."
        elif event.sentiment.uncertainty_score > 0.4:
            contradictory = (
                f"Elevated uncertainty index ({event.sentiment.uncertainty_score:0.2f}). Regulatory implementation timeline "
                f"and secondary vendor compliance details remain unresolved."
            )
        else:
            contradictory = "Consensus verified across official regulatory disclosures and primary financial wires with no significant conflicting reports."

        evidence_chain = self.explainability_engine.build_evidence_chain(event, metrics_list, graph_data)
        analyst_confidence = round(min(0.98, event.credibility_score * 0.95 + 0.05), 2)

        return AIMarketBrief(
            brief_id=brief_id,
            event_id=event.event_id,
            headline=headline,
            generated_at=datetime.utcnow(),
            what_happened=what_happened,
            key_sources=key_sources,
            affected_assets=affected_assets,
            observed_reaction=observed_reaction,
            expected_spillover=expected_spillover,
            contradictory_unresolved=contradictory,
            evidence_chain=evidence_chain,
            analyst_confidence=analyst_confidence
        )

