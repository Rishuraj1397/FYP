"""
Entity Linking and Entity Resolution.
Links detected text entities to canonical asset symbols, sectors, and supply chains.
Task 3 Layer of the Event Intelligence Architecture.
Group No. 61 | Rishu Raj | Shaheed Arman Gazi
"""

from typing import Dict, List, Optional, Any
from src.common.models import NamedEntity, EntityType


RELATIONSHIP_KB: Dict[str, Dict[str, Any]] = {
    "NVDA": {
        "name": "Nvidia Corporation",
        "sector": "Semiconductors",
        "suppliers": ["TSM", "ASML"],
        "competitors": ["AMD", "INTC"],
        "customers": ["MSFT", "GOOGL", "AMZN", "META"],
        "etfs": ["SMH", "SOXX", "QQQ"],
        "macro_sensitivities": ["US-China Trade", "AI Capex"]
    },
    "AMD": {
        "name": "Advanced Micro Devices",
        "sector": "Semiconductors",
        "suppliers": ["TSM"],
        "competitors": ["NVDA", "INTC"],
        "etfs": ["SMH", "SOXX", "QQQ"],
        "macro_sensitivities": ["US-China Trade", "PC Demand"]
    },
    "TSM": {
        "name": "Taiwan Semiconductor Manufacturing Co",
        "sector": "Semiconductor Foundry",
        "suppliers": ["ASML"],
        "customers": ["NVDA", "AAPL", "AMD"],
        "etfs": ["SMH", "EWT"],
        "macro_sensitivities": ["Taiwan Geopolitics", "Export Controls"]
    },
    "ASML": {
        "name": "ASML Holding NV",
        "sector": "Semiconductor Equipment",
        "customers": ["TSM", "INTC", "Samsung"],
        "etfs": ["SMH"],
        "macro_sensitivities": ["Export Regulations", "Lithography Capex"]
    },
    "MSFT": {
        "name": "Microsoft Corporation",
        "sector": "Enterprise Software / Cloud",
        "suppliers": ["NVDA"],
        "competitors": ["GOOGL", "AMZN", "AAPL"],
        "etfs": ["XLK", "QQQ", "SPY"],
        "macro_sensitivities": ["Enterprise IT Spend", "AI Demand"]
    },
    "XOM": {
        "name": "Exxon Mobil Corp",
        "sector": "Energy / Oil & Gas",
        "peers": ["CVX", "BP", "SHEL"],
        "correlated_commodities": ["USO", "BRENT"],
        "etfs": ["XLE"],
        "macro_sensitivities": ["OPEC Quotas", "Crude Inventory"]
    },
    "CVX": {
        "name": "Chevron Corp",
        "sector": "Energy / Oil & Gas",
        "peers": ["XOM", "COP"],
        "correlated_commodities": ["USO", "BRENT"],
        "etfs": ["XLE"],
        "macro_sensitivities": ["OPEC Quotas", "Crude Inventory"]
    },
    "DAL": {
        "name": "Delta Air Lines",
        "sector": "Airlines / Transportation",
        "inverse_correlated_commodities": ["USO", "JET_FUEL"],
        "etfs": ["JETS"],
        "macro_sensitivities": ["Fuel Costs", "Consumer Travel"]
    },
    "SPY": {
        "name": "SPDR S&P 500 ETF Trust",
        "sector": "Broad Market",
        "macro_sensitivities": ["Federal Reserve Interest Rates", "GDP", "Inflation"]
    },
    "QQQ": {
        "name": "Invesco QQQ Trust",
        "sector": "Tech / Nasdaq 100",
        "macro_sensitivities": ["Interest Rates", "Tech Multiples"]
    },
    "TLT": {
        "name": "iShares 20+ Year Treasury Bond ETF",
        "sector": "Fixed Income / US Treasuries",
        "macro_sensitivities": ["FOMC Rate Decisions", "Inflation Expectations"]
    },
    "USO": {
        "name": "United States Oil Fund",
        "sector": "Commodity / Crude Oil",
        "macro_sensitivities": ["OPEC Decisions", "Geopolitical Supply Disruptions"]
    }
}


class EntityLinker:
    """Links named entities to standardized tickers, sectors, and supply chain networks."""

    def resolve_entity(self, entity: NamedEntity) -> Dict[str, Any]:
        ticker = entity.ticker
        if ticker and ticker in RELATIONSHIP_KB:
            data = RELATIONSHIP_KB[ticker].copy()
            data["ticker"] = ticker
            return data

        text_lower = entity.text.lower()
        for t, info in RELATIONSHIP_KB.items():
            if t.lower() == text_lower or info["name"].lower() in text_lower or text_lower in info["name"].lower():
                data = info.copy()
                data["ticker"] = t
                return data

        return {
            "ticker": ticker or entity.text.upper(),
            "name": entity.canonical_name or entity.text,
            "sector": entity.sector or "General",
            "suppliers": [],
            "competitors": [],
            "customers": [],
            "etfs": []
        }

    def get_spillover_assets(self, primary_tickers: List[str]) -> List[Dict[str, str]]:
        spillovers: List[Dict[str, str]] = []
        seen = set(primary_tickers)

        for ticker in primary_tickers:
            if ticker in RELATIONSHIP_KB:
                info = RELATIONSHIP_KB[ticker]
                for s in info.get("suppliers", []):
                    if s not in seen:
                        spillovers.append({"ticker": s, "relation": "SUPPLIER_TO", "source_asset": ticker})
                        seen.add(s)
                for c in info.get("competitors", []):
                    if c not in seen:
                        spillovers.append({"ticker": c, "relation": "COMPETITOR_OF", "source_asset": ticker})
                        seen.add(c)
                for cust in info.get("customers", []):
                    if cust not in seen:
                        spillovers.append({"ticker": cust, "relation": "CUSTOMER_OF", "source_asset": ticker})
                        seen.add(cust)
                for etf in info.get("etfs", []):
                    if etf not in seen:
                        spillovers.append({"ticker": etf, "relation": "INDEX_BASKET", "source_asset": ticker})
                        seen.add(etf)
        return spillovers

