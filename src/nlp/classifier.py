"""
Event Detection and Multi-Category Classification.
Task 2 Layer of the Event Intelligence Architecture.
Group No. 61 | Rishu Raj | Shaheed Arman Gazi
"""

import re
from typing import Dict, List, Tuple
from src.common.models import EventCategory


CATEGORY_KEYWORDS: Dict[EventCategory, List[str]] = {
    EventCategory.CENTRAL_BANK_POLICY: [
        "federal reserve", "fomc", "interest rate", "basis points", "rate cut", "rate hike",
        "monetary policy", "central bank", "federal funds", "powell", "inflation target",
        "benchmark borrowing", "easing cycle", "dovish", "hawkish"
    ],
    EventCategory.GEOPOLITICAL_SANCTIONS: [
        "export controls", "sanctions", "tariffs", "bureau of industry and security", "bis",
        "national security", "trade curbs", "embargo", "export restrictions", "overseas jurisdictions"
    ],
    EventCategory.SUPPLY_CHAIN: [
        "production cut", "supply chain", "opec", "crude production", "wafer fabrication",
        "semiconductor equipment", "lithography", "shortage", "logistics bottleneck", "output reduction"
    ],
    EventCategory.EARNINGS: [
        "earnings", "quarterly revenue", "eps", "profit margin", "q1", "q2", "q3", "q4",
        "beats estimates", "missed estimates", "guidance", "net income", "fiscal quarter"
    ],
    EventCategory.MERGERS_ACQUISITIONS: [
        "acquisition", "merger", "buyout", "takeover", "agrees to acquire", "tender offer",
        "deal value", "cash and stock", "regulatory approval for merger"
    ],
    EventCategory.REGULATORY_LEGAL: [
        "antitrust", "sec investigation", "doj", "lawsuit", "subpoena", "regulatory compliance",
        "fine", "injunction", "patent infringement"
    ],
    EventCategory.MACRO_ECONOMIC: [
        "cpi", "consumer price index", "inflation", "gdp", "unemployment rate", "jobs report",
        "non-farm payrolls", "recession", "economic growth"
    ],
    EventCategory.EXECUTIVE_LEADERSHIP: [
        "appointed ceo", "ceo steps down", "chief executive", "board of directors", "resignation",
        "leadership transition", "cfo resignation"
    ]
}


class EventClassifier:
    """Classifies financial news and announcements into discrete event taxonomy categories."""

    def classify(self, text: str) -> Tuple[EventCategory, float, Dict[EventCategory, float]]:
        text_lower = text.lower()
        scores: Dict[EventCategory, float] = {}

        for category, keywords in CATEGORY_KEYWORDS.items():
            score = 0.0
            for kw in keywords:
                matches = len(re.findall(r"\b" + re.escape(kw) + r"\b", text_lower))
                if matches > 0:
                    score += 1.0 + (matches - 1) * 0.5
            scores[category] = score

        max_score = max(scores.values()) if scores else 0.0
        if max_score == 0.0:
            return EventCategory.UNKNOWN, 0.5, scores

        top_cat = max(scores, key=scores.get)
        confidence = min(0.98, 0.60 + (max_score / (sum(scores.values()) + 1e-6)) * 0.38)
        return top_cat, confidence, scores

