"""
Human-in-the-Loop (HITL) Validation and Feedback Loops.
Allows financial analysts to verify, adjust, or reject events, relationships, and briefs.
Feeds corrections back into Task 2 (NLP) and Task 3 (Knowledge Graph).
Group No. 61 | Rishu Raj | Shaheed Arman Gazi
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.common.models import (
    ValidationFeedback,
    DetectedEvent,
    EventCategory,
    SentimentPolarity
)
from src.ingestion.storage import EventIntelligenceStorage


class HumanInTheLoopValidator:
    def __init__(self, storage: Optional[EventIntelligenceStorage] = None):
        self.storage = storage or EventIntelligenceStorage()

    def submit_feedback(
        self,
        target_id: str,
        target_type: str,
        status: str,
        reviewer: str = "Lead Analyst",
        reviewer_notes: str = "",
        verified_category: Optional[EventCategory] = None,
        verified_sentiment: Optional[SentimentPolarity] = None
    ) -> ValidationFeedback:
        feedback = ValidationFeedback(
            feedback_id=f"FB-{uuid.uuid4().hex[:8].upper()}",
            target_id=target_id,
            target_type=target_type,
            status=status,
            verified_category=verified_category,
            verified_sentiment=verified_sentiment,
            reviewer=reviewer,
            reviewer_notes=reviewer_notes,
            timestamp=datetime.utcnow()
        )
        self.storage.save_feedback(feedback)

        if target_type == "EVENT" and status == "MODIFIED":
            event = self.storage.get_event_by_id(target_id)
            if event:
                if verified_category:
                    event.category = verified_category
                if verified_sentiment:
                    event.sentiment.polarity = verified_sentiment
                self.storage.save_detected_event(event)

        return feedback

    def get_review_history(self, limit: int = 50) -> List[ValidationFeedback]:
        return self.storage.get_feedback_list(limit=limit)

