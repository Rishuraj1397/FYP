"""
Source Corroboration and Credibility Signals.
Evaluates multi-source convergence, rumor vs verified status, and information provenance.
Task 3 Layer of the Event Intelligence Architecture.
Group No. 61 | Rishu Raj | Shaheed Arman Gazi
"""

import math
from typing import List, Dict, Any, Tuple
from src.common.models import CleanedDocument, DataSourceType


class CorroborationEngine:
    """Evaluates cross-source agreement, consensus vs conflict, and credibility weights."""

    def evaluate_corroboration(self, docs: List[CleanedDocument]) -> Dict[str, Any]:
        if not docs:
            return {
                "corroboration_count": 0,
                "credibility_score": 0.5,
                "verification_status": "NO_SOURCES",
                "has_official_source": False,
                "social_volume": 0,
                "mainstream_news_count": 0
            }

        official_count = sum(1 for d in docs if d.source_type == DataSourceType.OFFICIAL_ANNOUNCEMENT)
        news_count = sum(1 for d in docs if d.source_type == DataSourceType.FINANCIAL_NEWS)
        social_count = sum(1 for d in docs if d.source_type == DataSourceType.SOCIAL_MEDIA)

        total_cred = sum(d.source_credibility for d in docs)
        avg_cred = total_cred / len(docs)

        source_count = len(docs)
        diversity_multiplier = math.log2(1 + source_count) / 1.5

        final_cred = round(min(0.99, max(0.40, avg_cred * (0.8 + 0.2 * diversity_multiplier))), 3)

        if official_count >= 1:
            verification_status = "OFFICIALLY_VERIFIED"
        elif news_count >= 2 and final_cred >= 0.80:
            verification_status = "MULTI_SOURCE_CORROBORATED"
        elif news_count == 1 and final_cred >= 0.75:
            verification_status = "SINGLE_SOURCE_NEWS"
        else:
            verification_status = "UNCONFIRMED_SPECULATION"

        return {
            "corroboration_count": source_count,
            "credibility_score": final_cred,
            "verification_status": verification_status,
            "has_official_source": official_count > 0,
            "social_volume": social_count,
            "mainstream_news_count": news_count,
            "official_count": official_count,
        }

