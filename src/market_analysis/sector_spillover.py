"""
Sector and Multi-Asset Spillover Matrix.
Measures cross-asset contagion, winners vs losers, and sector ETF responses.
Task 4 Layer of the Event Intelligence Architecture.
Group No. 61 | Rishu Raj | Shaheed Arman Gazi
"""

from typing import Dict, List, Any
from src.common.models import DetectedEvent, EventWindowMetrics
from src.knowledge_graph.entity_linker import RELATIONSHIP_KB, EntityLinker


class SectorSpilloverAnalyzer:
    def __init__(self):
        self.linker = EntityLinker()

    def analyze_spillover(
        self,
        event: DetectedEvent,
        metrics_list: List[EventWindowMetrics]
    ) -> Dict[str, Any]:
        primary_tickers = set(event.primary_assets)
        spillover_targets = self.linker.get_spillover_assets(event.primary_assets)

        metrics_map = {m.asset_ticker: m for m in metrics_list}
        
        sector_breakdown: Dict[str, List[float]] = {}
        winners: List[Dict[str, Any]] = []
        losers: List[Dict[str, Any]] = []

        for m in metrics_list:
            sec = m.affected_sector or "General"
            sector_breakdown.setdefault(sec, []).append(m.abnormal_return)
            
            entry = {
                "ticker": m.asset_ticker,
                "sector": sec,
                "abnormal_return": m.abnormal_return,
                "cumulative_return": m.cumulative_abnormal_return,
                "volume_z": m.volume_z_score,
                "is_primary": m.asset_ticker in primary_tickers
            }
            if m.abnormal_return > 0:
                winners.append(entry)
            else:
                losers.append(entry)

        winners.sort(key=lambda x: x["abnormal_return"], reverse=True)
        losers.sort(key=lambda x: x["abnormal_return"])

        sector_summary = {}
        for sec, rets in sector_breakdown.items():
            avg_ret = sum(rets) / len(rets) if rets else 0.0
            sector_summary[sec] = {
                "average_abnormal_return": round(avg_ret, 2),
                "asset_count": len(rets),
                "sentiment_alignment": "BULLISH" if avg_ret > 0 else "BEARISH"
            }

        significant_peers = sum(
            1 for m in metrics_list
            if m.asset_ticker not in primary_tickers and (abs(m.abnormal_return) > 1.5 or abs(m.volume_z_score) > 2.0)
        )
        total_peers = max(1, len(metrics_list) - len(primary_tickers))
        contagion_score = round(min(1.0, significant_peers / total_peers), 2)

        return {
            "event_id": event.event_id,
            "category": event.category.value,
            "sector_summary": sector_summary,
            "contagion_index": contagion_score,
            "winners": winners,
            "losers": losers,
            "spillover_relationships": spillover_targets
        }

