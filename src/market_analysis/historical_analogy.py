"""
Historical Event Comparison Layer.
Matches current detected events against a curated historical event archive to benchmark post-event CAR trajectories.
Task 4 Layer of the Event Intelligence Architecture.
Group No. 61 | Rishu Raj | Shaheed Arman Gazi
"""

from typing import List, Dict, Any
from src.common.models import DetectedEvent, HistoricalAnalogy, EventCategory


HISTORICAL_EVENT_ARCHIVE: List[Dict[str, Any]] = [
    {
        "past_event_id": "HIST-2022-BIS-01",
        "past_event_title": "US Bureau of Industry and Security Introduces Initial AI Chip Restrictions",
        "past_date": "2022-10-07",
        "category": EventCategory.GEOPOLITICAL_SANCTIONS,
        "primary_asset": "NVDA",
        "actual_car_3d": -6.4,
        "actual_car_5d": -9.2,
        "outcome_summary": "Immediate steep selloff across NVDA, AMD, and ASML with elevated volume z-scores (+3.8). Rebound commenced after 3 weeks as firms redesigned compliant GPUs."
    },
    {
        "past_event_id": "HIST-2023-FOMC-02",
        "past_event_title": "FOMC Signals Peak Fed Funds Rate and Begins Dovish Pivot Discussion",
        "past_date": "2023-12-13",
        "category": EventCategory.CENTRAL_BANK_POLICY,
        "primary_asset": "SPY",
        "actual_car_3d": +3.1,
        "actual_car_5d": +4.6,
        "outcome_summary": "Broad equity rally across SPY and QQQ with 10-year Treasury yields dropping 28 bps over 5 trading sessions. Small-cap equities (IWM) strongly outperformed."
    },
    {
        "past_event_id": "HIST-2023-OPEC-03",
        "past_event_title": "OPEC+ Announces Surprise 1.16 Million BPD Voluntary Output Cuts",
        "past_date": "2023-04-02",
        "category": EventCategory.SUPPLY_CHAIN,
        "primary_asset": "USO",
        "actual_car_3d": +6.8,
        "actual_car_5d": +5.4,
        "outcome_summary": "WTI crude gapped up 6.3% on market open. Energy sector ETF XLE outperformed broad market by 4.2% while airline stocks dropped 3.1% due to fuel margin compression."
    },
    {
        "past_event_id": "HIST-2023-MSFT-AI",
        "past_event_title": "Microsoft Expands Multi-Billion OpenAI Partnership & Cloud Infrastructure",
        "past_date": "2023-01-23",
        "category": EventCategory.EARNINGS,
        "primary_asset": "MSFT",
        "actual_car_3d": +4.2,
        "actual_car_5d": +7.1,
        "outcome_summary": "Sustained upward price trend driven by enterprise AI hype, catalyzing subsequent hardware capex spending into Nvidia."
    }
]


class HistoricalAnalogyEngine:
    """Finds closest historical analogues for current event to project probable market reaction."""

    def find_analogues(self, event: DetectedEvent, top_k: int = 3) -> List[HistoricalAnalogy]:
        matches: List[HistoricalAnalogy] = []

        for hist in HISTORICAL_EVENT_ARCHIVE:
            cat_score = 1.0 if hist["category"] == event.category else 0.2
            
            asset_match = 0.0
            if hist["primary_asset"] in event.primary_assets:
                asset_match = 1.0
            elif any(e.ticker == hist["primary_asset"] for e in event.entities):
                asset_match = 0.8
            else:
                asset_match = 0.3

            expected_dir = 1.0 if event.sentiment.polarity_score > 0 else -1.0
            hist_dir = 1.0 if hist["actual_car_3d"] > 0 else -1.0
            sentiment_match = 1.0 if expected_dir == hist_dir else 0.4

            similarity = round(cat_score * 0.45 + asset_match * 0.35 + sentiment_match * 0.20, 3)

            matches.append(HistoricalAnalogy(
                past_event_id=hist["past_event_id"],
                past_event_title=hist["past_event_title"],
                past_date=hist["past_date"],
                similarity_score=similarity,
                category=hist["category"],
                primary_asset=hist["primary_asset"],
                actual_car_3d=hist["actual_car_3d"],
                actual_car_5d=hist["actual_car_5d"],
                outcome_summary=hist["outcome_summary"]
            ))

        matches.sort(key=lambda x: x.similarity_score, reverse=True)
        return matches[:top_k]

