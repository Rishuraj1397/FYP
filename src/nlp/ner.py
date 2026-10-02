"""
Financial Named Entity Recognition (NER) and Entity Typing.
Extracts Company, Country, Organization, Asset/Ticker, Commodity, Currency, Sector.
Task 2 Layer of the Event Intelligence Architecture.
Group No. 61 | Rishu Raj | Shaheed Arman Gazi
"""

import re
from typing import List, Dict, Tuple, Optional, Any
from src.common.models import NamedEntity, EntityType


KNOWN_ENTITIES: List[Dict[str, Any]] = [
    # Tech / Semis
    {"text": "Nvidia", "type": EntityType.COMPANY, "ticker": "NVDA", "sector": "Semiconductors", "aliases": ["Nvidia Corp", "NVIDIA"]},
    {"text": "Advanced Micro Devices", "type": EntityType.COMPANY, "ticker": "AMD", "sector": "Semiconductors", "aliases": ["AMD"]},
    {"text": "Taiwan Semiconductor Manufacturing Co", "type": EntityType.COMPANY, "ticker": "TSM", "sector": "Semiconductors", "aliases": ["TSMC", "Taiwan Semiconductor"]},
    {"text": "ASML", "type": EntityType.COMPANY, "ticker": "ASML", "sector": "Semiconductor Equipment", "aliases": ["ASML Holding"]},
    {"text": "Microsoft", "type": EntityType.COMPANY, "ticker": "MSFT", "sector": "Technology", "aliases": ["Microsoft Corp"]},
    {"text": "Apple", "type": EntityType.COMPANY, "ticker": "AAPL", "sector": "Technology", "aliases": ["Apple Inc"]},
    {"text": "Tesla", "type": EntityType.COMPANY, "ticker": "TSLA", "sector": "Automotive / Clean Energy", "aliases": ["Tesla Inc"]},
    
    # Energy
    {"text": "Exxon Mobil", "type": EntityType.COMPANY, "ticker": "XOM", "sector": "Energy", "aliases": ["Exxon", "ExxonMobil"]},
    {"text": "Chevron", "type": EntityType.COMPANY, "ticker": "CVX", "sector": "Energy", "aliases": ["Chevron Corp"]},
    {"text": "Delta Air Lines", "type": EntityType.COMPANY, "ticker": "DAL", "sector": "Airlines", "aliases": ["Delta"]},

    # Organizations & Central Banks
    {"text": "Federal Reserve", "type": EntityType.ORGANIZATION, "ticker": None, "sector": "Central Banking", "aliases": ["Fed", "FOMC", "Federal Open Market Committee"]},
    {"text": "SEC", "type": EntityType.ORGANIZATION, "ticker": None, "sector": "Regulatory", "aliases": ["Securities and Exchange Commission", "SEC EDGAR"]},
    {"text": "Bureau of Industry and Security", "type": EntityType.ORGANIZATION, "ticker": None, "sector": "Government Agency", "aliases": ["BIS", "Commerce Department", "US Dept of Commerce", "Commerce Dept"]},
    {"text": "OPEC", "type": EntityType.ORGANIZATION, "ticker": None, "sector": "Commodity Cartel", "aliases": ["OPEC+", "OPEC Secretariat"]},
    {"text": "European Central Bank", "type": EntityType.ORGANIZATION, "ticker": None, "sector": "Central Banking", "aliases": ["ECB"]},

    # Countries / Geographies
    {"text": "United States", "type": EntityType.COUNTRY, "ticker": None, "sector": None, "aliases": ["US", "U.S.", "USA", "Washington"]},
    {"text": "China", "type": EntityType.COUNTRY, "ticker": None, "sector": None, "aliases": ["Beijing"]},
    {"text": "Saudi Arabia", "type": EntityType.COUNTRY, "ticker": None, "sector": None, "aliases": ["Riyadh"]},
    {"text": "Taiwan", "type": EntityType.COUNTRY, "ticker": None, "sector": None, "aliases": ["Taipei"]},

    # Commodities
    {"text": "Crude Oil", "type": EntityType.COMMODITY, "ticker": "USO", "sector": "Energy", "aliases": ["Brent crude", "WTI", "Brent", "Oil"]},
    {"text": "Gold", "type": EntityType.COMMODITY, "ticker": "GLD", "sector": "Precious Metals", "aliases": ["Bullion"]},
    {"text": "Natural Gas", "type": EntityType.COMMODITY, "ticker": "UNG", "sector": "Energy", "aliases": ["Nat Gas"]},

    # Currencies
    {"text": "US Dollar", "type": EntityType.CURRENCY, "ticker": "UUP", "sector": "FX", "aliases": ["USD", "Greenback", "Dollar"]},
    {"text": "Euro", "type": EntityType.CURRENCY, "ticker": "FXE", "sector": "FX", "aliases": ["EUR"]},
    {"text": "Japanese Yen", "type": EntityType.CURRENCY, "ticker": "FXY", "sector": "FX", "aliases": ["JPY", "Yen"]},
]


class FinancialNER:
    """Extracts typed financial entities and normalizes them to canonical representations."""

    TICKER_PATTERN = re.compile(r"\b(?:\$|(?<=\())([A-Z]{1,5})(?:\)|\b)")

    def __init__(self):
        self.alias_to_entity: Dict[str, Dict[str, Any]] = {}
        for item in KNOWN_ENTITIES:
            canonical_name = item["text"]
            self.alias_to_entity[canonical_name.lower()] = item
            for alias in item.get("aliases", []):
                self.alias_to_entity[alias.lower()] = item

    def extract_entities(self, text: str) -> List[NamedEntity]:
        found: Dict[str, NamedEntity] = {}

        for match in self.TICKER_PATTERN.finditer(text):
            ticker = match.group(1)
            if ticker in ["A", "I", "AT", "ON", "BE", "US", "IT", "AN", "AM", "PM", "OR", "IF"]:
                continue
            
            matched_item = None
            for item in KNOWN_ENTITIES:
                if item.get("ticker") == ticker:
                    matched_item = item
                    break
            
            entity_type = matched_item["type"] if matched_item else EntityType.ASSET
            canonical_name = matched_item["text"] if matched_item else ticker
            sector = matched_item.get("sector") if matched_item else None

            found[f"TICKER_{ticker}"] = NamedEntity(
                text=ticker,
                entity_type=entity_type,
                ticker=ticker,
                canonical_name=canonical_name,
                sector=sector,
                confidence=0.98
            )

        sorted_aliases = sorted(self.alias_to_entity.keys(), key=len, reverse=True)
        text_lower = f" {text.lower()} "

        for alias in sorted_aliases:
            pattern = r"\b" + re.escape(alias) + r"\b"
            if re.search(pattern, text_lower):
                item = self.alias_to_entity[alias]
                canonical_name = item["text"]
                key = f"{item['type']}_{canonical_name}"
                if key not in found:
                    found[key] = NamedEntity(
                        text=canonical_name,
                        entity_type=item["type"],
                        ticker=item.get("ticker"),
                        canonical_name=canonical_name,
                        sector=item.get("sector"),
                        confidence=0.95
                    )

        return list(found.values())

