"""
Explainability and Evidence Chain Construction.
Builds an auditable, verifiable reasoning chain connecting raw dispatches to graph paths and market impact.
Task 5 Layer of the Event Intelligence Architecture.
Group No. 61 | Rishu Raj | Shaheed Arman Gazi
"""

from typing import List, Dict, Any
from src.common.models import DetectedEvent, EventWindowMetrics, KnowledgeGraphData


class ExplainabilityEngine:
    """Produces step-by-step reasoning evidence chains for AI Brief transparency."""

    def build_evidence_chain(
        self,
        event: DetectedEvent,
        metrics: List[EventWindowMetrics],
        graph_data: KnowledgeGraphData
    ) -> List[str]:
        chain: List[str] = []

        doc_count = len(event.source_doc_ids)
        sources_str = f"{doc_count} source{'s' if doc_count > 1 else ''} (Credibility: {int(event.credibility_score * 100)}%)"
        excerpt = f'"{event.evidence_excerpts[0]}"' if event.evidence_excerpts else "No excerpt"
        chain.append(f"[Step 1: Provenance] Ingested and verified across {sources_str}. Primary excerpt: {excerpt}")

        entities_str = ", ".join([f"{e.text} ({e.entity_type.value})" for e in event.entities[:4]])
        chain.append(
            f"[Step 2: NLP Extraction] Detected category '{event.category.value}' with {event.sentiment.polarity.value} polarity "
            f"(Score: {event.sentiment.polarity_score:+0.2f}, Uncertainty: {event.sentiment.uncertainty_score:0.2f}). Identified entities: {entities_str}."
        )

        node_count = len(graph_data.nodes)
        edge_count = len(graph_data.edges)
        chain.append(
            f"[Step 3: Graph Traversal] Connected {node_count} nodes via {edge_count} relational edges. "
            f"Mapped event causality to primary assets ({', '.join(event.primary_assets)}) and supply chain spillover nodes."
        )

        if metrics:
            top_m = metrics[0]
            chain.append(
                f"[Step 4: Market Validation] Event window verified for {top_m.asset_ticker}: "
                f"Abnormal Return = {top_m.abnormal_return:+0.2f}%, Volume z-score = {top_m.volume_z_score:+0.2f}, "
                f"Cumulative Abnormal Return (CAR) = {top_m.cumulative_abnormal_return:+0.2f}%, Volatility Shock = {top_m.volatility_shock:+0.2f}%."
            )
        else:
            chain.append("[Step 4: Market Validation] Baseline market study initiated; awaiting subsequent trading close data.")

        return chain

