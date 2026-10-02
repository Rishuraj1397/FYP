"""
Financial Sentiment and Context Analysis:
- Financial Polarity (Bullish / Bearish / Neutral)
- Hawkish vs Dovish Monetary Stance Score (-1.0 to +1.0)
- Market Uncertainty Score (0.0 to 1.0)
- Impact Intensity Score (0.0 to 1.0)
Task 2 Layer of the Event Intelligence Architecture.
Group No. 61 | Rishu Raj | Shaheed Arman Gazi
"""

import re
from typing import Dict, List, Tuple
from src.common.models import FinancialSentiment, SentimentPolarity


BULLISH_WORDS = {
    "rally", "rallied", "rallies", "surge", "surged", "surges", "gain", "gains", "jump", "jumped",
    "soar", "soared", "skyrocket", "skyrocketing", "record high", "outperform", "outperformed",
    "beat", "beats", "exceeded", "strong", "bullish", "upgrade", "upgraded", "easing", "rate cut",
    "growth", "expansion", "profit", "profitable", "optimistic", "stimulus"
}

BEARISH_WORDS = {
    "plunge", "plunged", "slide", "slides", "tumble", "tumbled", "slump", "slumped", "drop",
    "dropped", "fall", "fell", "bleeding", "dump", "dumping", "selloff", "crush", "crushed",
    "loss", "losses", "miss", "missed", "weak", "bearish", "downgrade", "downgraded", "curbs",
    "ban", "sanction", "sanctions", "panic", "restriction", "restrictions", "headwinds", "decline"
}

HAWKISH_WORDS = {
    "rate hike", "hike", "tightening", "curb inflation", "restrictive", "higher for longer",
    "hawkish", "raise rates", "cool economy", "upside inflation risk"
}

DOVISH_WORDS = {
    "rate cut", "slashes", "lowered", "easing", "support employment", "dovish", "cut rates",
    "cooling labor", "subside", "reduce benchmark", "stimulative"
}

UNCERTAINTY_WORDS = {
    "uncertain", "uncertainty", "speculative", "volatile", "volatility", "risk", "risks",
    "unclear", "unresolved", "headwinds", "panic", "ambiguous", "pending", "scrutiny"
}


class FinancialSentimentAnalyzer:
    """Calculates finance-specific polarity, hawkish/dovish stance, uncertainty, and expected volatility."""

    def analyze(self, text: str) -> FinancialSentiment:
        words = re.findall(r"\b[a-zA-Z\-]+\b", text.lower())
        word_count = max(len(words), 1)

        bullish_hits = sum(1 for w in words if w in BULLISH_WORDS)
        bearish_hits = sum(1 for w in words if w in BEARISH_WORDS)
        hawkish_hits = sum(1 for w in words if w in HAWKISH_WORDS)
        dovish_hits = sum(1 for w in words if w in DOVISH_WORDS)
        uncertainty_hits = sum(1 for w in words if w in UNCERTAINTY_WORDS)

        net_polarity = bullish_hits - bearish_hits
        denom = max(bullish_hits + bearish_hits, 1)
        raw_polarity_score = net_polarity / denom
        polarity_score = round(max(-1.0, min(1.0, raw_polarity_score)), 3)

        if polarity_score > 0.15:
            polarity = SentimentPolarity.BULLISH
        elif polarity_score < -0.15:
            polarity = SentimentPolarity.BEARISH
        else:
            polarity = SentimentPolarity.NEUTRAL

        net_monetary = hawkish_hits - dovish_hits
        monetary_denom = max(hawkish_hits + dovish_hits, 1)
        hawk_dove_score = round(net_monetary / monetary_denom, 3) if (hawkish_hits + dovish_hits) > 0 else 0.0

        uncertainty_score = round(min(1.0, (uncertainty_hits / (word_count * 0.05 + 1e-6))), 3)

        impact_hits = bullish_hits + bearish_hits + uncertainty_hits + hawkish_hits + dovish_hits
        impact_intensity = round(min(1.0, max(0.3, impact_hits / 8.0)), 3)

        return FinancialSentiment(
            polarity=polarity,
            polarity_score=polarity_score,
            hawkish_dovish_score=hawk_dove_score,
            uncertainty_score=uncertainty_score,
            impact_intensity=impact_intensity
        )

