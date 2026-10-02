"""
Knowledge Graph Construction Layer: Event -> Entity -> Sector -> Asset.
Maintains multi-relational graph with NetworkX and Neo4j Cypher export.
Task 3 Layer of the Event Intelligence Architecture.
Group No. 61 | Rishu Raj | Shaheed Arman Gazi
"""

import json
from typing import Dict, List, Any, Optional, Set
import networkx as nx

from src.common.models import (
    DetectedEvent,
    NamedEntity,
    KGNode,
    KGEdge,
    KnowledgeGraphData,
    EventCategory
)
from src.knowledge_graph.entity_linker import EntityLinker


class EventKnowledgeGraphBuilder:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.linker = EntityLinker()

    def add_event(self, event: DetectedEvent):
        event_node_id = f"EVENT_{event.event_id}"
        
        self.graph.add_node(
            event_node_id,
            id=event_node_id,
            label=event.title[:40] + ("..." if len(event.title) > 40 else ""),
            node_type="Event",
            category=event.category.value,
            sentiment=event.sentiment.polarity.value,
            credibility=event.credibility_score,
            timestamp=event.timestamp.isoformat(),
            description=event.description
        )

        evidence_str = event.evidence_excerpts[0] if event.evidence_excerpts else event.description
        source_url = event.source_urls[0] if event.source_urls else None
        ts_str = event.timestamp.isoformat()

        for entity in event.entities:
            resolved = self.linker.resolve_entity(entity)
            entity_node_id = f"ENTITY_{resolved['name'].replace(' ', '_').upper()}"
            
            self.graph.add_node(
                entity_node_id,
                id=entity_node_id,
                label=resolved["name"],
                node_type="Entity",
                entity_type=entity.entity_type.value,
                sector=resolved.get("sector")
            )

            self.graph.add_edge(
                event_node_id,
                entity_node_id,
                relation="IMPACTS",
                weight=event.credibility_score,
                evidence=evidence_str,
                source_url=source_url,
                timestamp=ts_str
            )

            if resolved.get("sector"):
                sector_id = f"SECTOR_{resolved['sector'].replace(' ', '_').upper()}"
                self.graph.add_node(
                    sector_id,
                    id=sector_id,
                    label=resolved["sector"],
                    node_type="Sector"
                )
                self.graph.add_edge(
                    entity_node_id,
                    sector_id,
                    relation="OPERATES_IN",
                    weight=1.0,
                    evidence=None,
                    source_url=None,
                    timestamp=None
                )

            if resolved.get("ticker"):
                ticker = resolved["ticker"]
                asset_id = f"ASSET_{ticker}"
                self.graph.add_node(
                    asset_id,
                    id=asset_id,
                    label=ticker,
                    node_type="Asset",
                    ticker=ticker,
                    sector=resolved.get("sector")
                )
                self.graph.add_edge(
                    entity_node_id,
                    asset_id,
                    relation="TRADES_AS",
                    weight=1.0,
                    evidence=None,
                    source_url=None,
                    timestamp=None
                )
                self.graph.add_edge(
                    event_node_id,
                    asset_id,
                    relation="TRANSMITS_TO",
                    weight=event.sentiment.impact_intensity,
                    evidence=evidence_str,
                    source_url=source_url,
                    timestamp=ts_str
                )

        spillovers = self.linker.get_spillover_assets(event.primary_assets)
        for sp in spillovers:
            ticker = sp["ticker"]
            asset_id = f"ASSET_{ticker}"
            src_asset_id = f"ASSET_{sp['source_asset']}"

            if not self.graph.has_node(asset_id):
                self.graph.add_node(
                    asset_id,
                    id=asset_id,
                    label=ticker,
                    node_type="Asset",
                    ticker=ticker
                )
            
            if self.graph.has_node(src_asset_id):
                self.graph.add_edge(
                    src_asset_id,
                    asset_id,
                    relation=sp["relation"],
                    weight=0.8,
                    evidence=f"Spillover transmission via {sp['relation']}",
                    source_url=source_url,
                    timestamp=ts_str
                )

    def get_event_subgraph(self, event_id: str, depth: int = 2) -> KnowledgeGraphData:
        target_node = f"EVENT_{event_id}"
        if not self.graph.has_node(target_node):
            return KnowledgeGraphData(nodes=[], edges=[])

        sub_nodes: Set[str] = {target_node}
        current_layer: Set[str] = {target_node}
        for _ in range(depth):
            next_layer: Set[str] = set()
            for n in current_layer:
                next_layer.update(self.graph.successors(n))
                next_layer.update(self.graph.predecessors(n))
            sub_nodes.update(next_layer)
            current_layer = next_layer

        subgraph = self.graph.subgraph(sub_nodes)
        
        nodes: List[KGNode] = []
        for n, data in subgraph.nodes(data=True):
            props = {k: v for k, v in data.items() if k not in ["id", "label", "node_type"]}
            nodes.append(KGNode(
                id=str(n),
                label=data.get("label", str(n)),
                node_type=data.get("node_type", "Unknown"),
                properties=props
            ))

        edges: List[KGEdge] = []
        for u, v, data in subgraph.edges(data=True):
            edges.append(KGEdge(
                source=str(u),
                target=str(v),
                relation=data.get("relation", "RELATED"),
                weight=data.get("weight", 1.0),
                evidence=data.get("evidence"),
                source_url=data.get("source_url"),
                timestamp=data.get("timestamp")
            ))

        return KnowledgeGraphData(nodes=nodes, edges=edges)

    def export_cypher(self) -> str:
        statements = []
        for n, data in self.graph.nodes(data=True):
            node_type = data.get("node_type", "Entity")
            lbl = data.get("label", str(n)).replace("'", "\\'")
            statements.append(f"MERGE (n:{node_type} {{id: '{n}'}}) SET n.label = '{lbl}';")

        for u, v, data in self.graph.edges(data=True):
            rel = data.get("relation", "RELATED")
            statements.append(f"MATCH (a {{id: '{u}'}}), (b {{id: '{v}'}}) MERGE (a)-[:{rel}]->(b);")

        return "\n".join(statements)

