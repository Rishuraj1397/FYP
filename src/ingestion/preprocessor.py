"""
Data Preprocessing: Cleaning, Noise Removal, Deduplication, and Normalization.
Task 1 Layer of the Event Intelligence Architecture.
Group No. 61 | Rishu Raj | Shaheed Arman Gazi
"""

import re
import hashlib
from typing import List, Tuple, Set, Optional, Any
from datetime import datetime, timezone
import dateutil.parser
from bs4 import BeautifulSoup

from config.settings import settings
from src.common.models import RawDocument, CleanedDocument, DataSourceType


SOURCE_CREDIBILITY_MAP = {
    "Federal Reserve": 0.98,
    "SEC EDGAR": 0.98,
    "European Central Bank": 0.97,
    "Bank of England": 0.97,
    "Reuters": 0.92,
    "Bloomberg": 0.92,
    "Financial Times": 0.90,
    "Wall Street Journal": 0.90,
    "CNBC": 0.82,
    "Yahoo Finance": 0.80,
    "MarketWatch": 0.80,
    "Reddit r/wallstreetbets": 0.52,
    "StockTwits": 0.55,
    "X / Twitter Financial Wire": 0.58,
}

BOILERPLATE_PATTERNS = [
    r"Disclaimer:.*?(?=\n|$)",
    r"All rights reserved\..*?(?=\n|$)",
    r"Subscribe to our newsletter.*?(?=\n|$)",
    r"Sign up for free newsletters.*?(?=\n|$)",
    r"Click here to read more.*?(?=\n|$)",
    r"Copyright ©.*?(?=\n|$)",
    r"Follow us on (Twitter|LinkedIn|Facebook).*?(?=\n|$)",
    r"The views expressed in this article are solely those of the author.*?(?=\n|$)",
]


class IngestionPreprocessor:
    def __init__(self, deduplication_threshold: float = settings.DEDUPLICATION_THRESHOLD):
        self.deduplication_threshold = deduplication_threshold
        self.seen_hashes: Set[str] = set()

    def clean_text(self, text: str) -> str:
        if not text:
            return ""

        if "<" in text and ">" in text:
            soup = BeautifulSoup(text, "html.parser")
            for tag in soup(["script", "style", "noscript", "header", "footer"]):
                tag.decompose()
            text = soup.get_text(separator=" ")

        for pattern in BOILERPLATE_PATTERNS:
            text = re.sub(pattern, " ", text, flags=re.IGNORECASE)

        text = re.sub(r"[\r\n\t]+", " ", text)
        text = re.sub(r"\s{2,}", " ", text)
        return text.strip()

    def compute_content_hash(self, text: str) -> str:
        normalized = re.sub(r"[^a-zA-Z0-9]", "", text.lower())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def extract_shingles(self, text: str, k: int = 3) -> Set[str]:
        words = re.findall(r"\b\w+\b", text.lower())
        if len(words) < k:
            return set(words)
        return {" ".join(words[i:i+k]) for i in range(len(words) - k + 1)}

    def jaccard_similarity(self, set1: Set[str], set2: Set[str]) -> float:
        if not set1 or not set2:
            return 0.0
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0.0

    def normalize_timestamp(self, ts: Any) -> datetime:
        if isinstance(ts, datetime):
            if ts.tzinfo is None:
                return ts.replace(tzinfo=timezone.utc)
            return ts.astimezone(timezone.utc)
        if isinstance(ts, str):
            try:
                dt = dateutil.parser.parse(ts)
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except Exception:
                return datetime.now(timezone.utc)
        return datetime.now(timezone.utc)

    def get_source_credibility(self, source_name: str, source_type: DataSourceType) -> float:
        for key, weight in SOURCE_CREDIBILITY_MAP.items():
            if key.lower() in source_name.lower():
                return weight
        
        if source_type == DataSourceType.OFFICIAL_ANNOUNCEMENT:
            return 0.95
        elif source_type == DataSourceType.FINANCIAL_NEWS:
            return 0.85
        elif source_type == DataSourceType.SOCIAL_MEDIA:
            return 0.55
        return 0.75

    def extract_summary_sentence(self, text: str) -> str:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        for s in sentences:
            s_clean = s.strip()
            if len(s_clean.split()) >= 6:
                return s_clean
        return text[:160] + "..." if len(text) > 160 else text

    def process(self, raw_doc: RawDocument, existing_docs: Optional[List[CleanedDocument]] = None) -> CleanedDocument:
        cleaned_content = self.clean_text(raw_doc.content)
        cleaned_title = self.clean_text(raw_doc.title)
        combined_text = f"{cleaned_title}. {cleaned_content}"

        content_hash = self.compute_content_hash(combined_text)
        published_utc = self.normalize_timestamp(raw_doc.published_at)
        credibility = self.get_source_credibility(raw_doc.source_name, raw_doc.source_type)
        summary = self.extract_summary_sentence(cleaned_content or cleaned_title)

        is_dup = False
        if content_hash in self.seen_hashes:
            is_dup = True
        elif existing_docs:
            new_shingles = self.extract_shingles(combined_text)
            for ex in existing_docs[-50:]:
                ex_text = f"{ex.title}. {ex.cleaned_content}"
                ex_shingles = self.extract_shingles(ex_text)
                sim = self.jaccard_similarity(new_shingles, ex_shingles)
                if sim >= self.deduplication_threshold:
                    is_dup = True
                    break

        if not is_dup:
            self.seen_hashes.add(content_hash)

        return CleanedDocument(
            doc_id=raw_doc.doc_id,
            source_type=raw_doc.source_type,
            source_name=raw_doc.source_name,
            title=cleaned_title,
            cleaned_content=cleaned_content,
            summary_sentence=summary,
            url=raw_doc.url,
            published_at=published_utc,
            content_hash=content_hash,
            source_credibility=credibility,
            char_count=len(cleaned_content),
            is_duplicate=is_dup
        )

