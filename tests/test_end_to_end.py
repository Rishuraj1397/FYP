"""
End-to-End Integration Tests for the complete system.
Tests Task 1 through Task 5 and Phase 6 API endpoints.
Group No. 61 | Rishu Raj | Shaheed Arman Gazi
"""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_pipeline_trigger_and_feed(client):
    resp = client.post("/api/pipeline/run")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["events_processed"] >= 2
    
    first_event = data["events"][0]
    event_id = first_event["event_id"]

    feed_resp = client.get("/api/feed")
    assert feed_resp.status_code == 200
    feed_data = feed_resp.json()
    assert feed_data["count"] >= 2

    graph_resp = client.get(f"/api/graph/{event_id}")
    assert graph_resp.status_code == 200
    g_data = graph_resp.json()
    assert len(g_data["nodes"]) > 0
    assert len(g_data["edges"]) > 0

    market_resp = client.get(f"/api/market-reaction/{event_id}")
    assert market_resp.status_code == 200
    m_data = market_resp.json()
    assert len(m_data["metrics"]) > 0
    assert "spillover_analysis" in m_data

    brief_resp = client.get(f"/api/brief/{event_id}")
    assert brief_resp.status_code == 200
    b_data = brief_resp.json()
    assert "what_happened" in b_data
    assert "evidence_chain" in b_data
    assert len(b_data["evidence_chain"]) >= 3

    cascade_resp = client.get(f"/api/cascade/{event_id}")
    assert cascade_resp.status_code == 200
    c_data = cascade_resp.json()
    assert len(c_data["hops"]) == 4

    analogy_resp = client.get(f"/api/analogies/{event_id}")
    assert analogy_resp.status_code == 200
    a_data = analogy_resp.json()
    assert len(a_data["analogues"]) > 0

    val_resp = client.post("/api/validation", json={
        "target_id": event_id,
        "target_type": "EVENT",
        "status": "APPROVED",
        "reviewer": "Shaheed Arman Gazi & Rishu Raj",
        "reviewer_notes": "Validated end-to-end pipeline output"
    })
    assert val_resp.status_code == 200
    v_data = val_resp.json()
    assert v_data["status"] == "success"

    hist_resp = client.get("/api/validation/history")
    assert hist_resp.status_code == 200
    h_data = hist_resp.json()
    assert h_data["count"] >= 1


def test_index_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "AI-Powered Multi-Source Event Intelligence" in resp.text
    assert "Group No. 61" in resp.text

