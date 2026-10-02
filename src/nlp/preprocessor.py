"""
Financial NLP Preprocessor: tokenization, financial symbol preservation, sentence segmentation.
Task 2 Layer of the Event Intelligence Architecture.
Group No. 61 | Rishu Raj | Shaheed Arman Gazi
"""

import re
from typing import List


class FinancialNLPPreprocessor:
    """Specialized tokenization and sentence splitting preserving financial figures (e.g. 50bps, $400M, 4.8%)."""

    ABBREVIATIONS = {"inc", "corp", "ltd", "co", "u.s", "gov", "mr", "ms", "dr"}

    def segment_sentences(self, text: str) -> List[str]:
        if not text:
            return []
        raw_chunks = re.split(r'([.!?]+\s+)', text.strip())
        sentences = []
        current = ""
        for i in range(0, len(raw_chunks), 2):
            part = raw_chunks[i]
            delim = raw_chunks[i+1] if i+1 < len(raw_chunks) else ""
            current += part + delim
            
            words = part.strip().split()
            last_word = words[-1].lower().rstrip(".") if words else ""
            if last_word in self.ABBREVIATIONS:
                continue
            
            if current.strip():
                sentences.append(current.strip())
                current = ""
        if current.strip():
            sentences.append(current.strip())
        return sentences

    def tokenize(self, text: str) -> List[str]:
        pattern = r"\$?[A-Z]{1,5}\b|\b\d+(?:\.\d+)?(?:%|bps|M|B|T)?\b|[a-zA-Z]+"
        return re.findall(pattern, text)

