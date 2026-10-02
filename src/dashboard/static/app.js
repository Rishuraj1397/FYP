/**
 * Event Intelligence & Market Impact Analysis Dashboard
 * Group No. 61 | Rishu Raj | Shaheed Arman Gazi
 */

let selectedEventId = null;
let graphData = { nodes: [], edges: [] };

document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    initRunPipeline();
    initHITLForm();
    loadEventFeed();
    loadHITLHistory();
});

function initTabs() {
    const tabBtns = document.querySelectorAll(".tab-btn");
    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            tabBtns.forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
            
            btn.classList.add("active");
            const targetId = btn.dataset.tab;
            const targetPane = document.getElementById(targetId);
            if (targetPane) targetPane.classList.add("active");

            if (targetId === "tab-graph") {
                renderKnowledgeGraph();
            }
        });
    });
}

function initRunPipeline() {
    const btn = document.getElementById("runPipelineBtn");
    const status = document.getElementById("pipelineStatus");
    btn.addEventListener("click", async () => {
        btn.disabled = true;
        btn.innerHTML = `<span class="icon">⏳</span> Processing Ingestion &amp; Tasks 1-5...`;
        status.textContent = "Pipeline Running";
        status.className = "status-badge";
        status.style.background = "rgba(59, 130, 246, 0.2)";
        status.style.color = "#60a5fa";

        try {
            const resp = await fetch("/api/pipeline/run", { method: "POST" });
            const data = await resp.json();
            status.textContent = `Completed (${data.events_processed} Events)`;
            status.className = "status-badge status-ready";
            await loadEventFeed();
        } catch (e) {
            console.error(e);
            status.textContent = "Execution Error";
        } finally {
            btn.disabled = false;
            btn.innerHTML = `<span class="icon">⚡</span> Run Full Pipeline Ingestion`;
        }
    });
}

async function loadEventFeed() {
    const feedContainer = document.getElementById("eventsList");
    const badge = document.getElementById("eventCountBadge");
    
    try {
        const res = await fetch("/api/feed");
        const data = await res.json();
        const events = data.events || [];
        badge.textContent = `${events.length} Events`;

        if (events.length === 0) {
            feedContainer.innerHTML = `<div class="empty-state">No events detected yet. Click 'Run Full Pipeline Ingestion' above.</div>`;
            return;
        }

        feedContainer.innerHTML = "";
        events.forEach((evt, idx) => {
            const card = document.createElement("div");
            card.className = `event-card ${evt.event_id === selectedEventId || (!selectedEventId && idx === 0) ? "selected" : ""}`;
            card.dataset.eventId = evt.event_id;

            const sentimentClass = evt.sentiment.polarity === "BULLISH" ? "sentiment-bullish" :
                                 (evt.sentiment.polarity === "BEARISH" ? "sentiment-bearish" : "sentiment-neutral");

            const entityChipsHtml = evt.entities.slice(0, 4).map(e => 
                `<span class="entity-chip">${e.text}${e.ticker ? ` (${e.ticker})` : ""}</span>`
            ).join("");

            card.innerHTML = `
                <div class="event-card-header">
                    <span class="category-tag">${evt.category.replace(/_/g, ' ')}</span>
                    <span class="sentiment-badge ${sentimentClass}">${evt.sentiment.polarity}</span>
                </div>
                <div class="event-card-title">${evt.title}</div>
                <div class="event-card-meta">
                    <span class="credibility-pill">Credibility: ${Math.round(evt.credibility_score * 100)}%</span>
                    <span>${evt.corroboration_count} sources</span>
                </div>
                <div class="entity-chips">${entityChipsHtml}</div>
            `;

            card.addEventListener("click", () => selectEvent(evt.event_id));
            feedContainer.appendChild(card);
        });

        if (!selectedEventId && events.length > 0) {
            selectEvent(events[0].event_id);
        }
    } catch (e) {
        console.error("Error loading feed:", e);
        feedContainer.innerHTML = `<div class="empty-state">Failed to connect to backend feed API.</div>`;
    }
}

async function selectEvent(eventId) {
    selectedEventId = eventId;
    document.querySelectorAll(".event-card").forEach(c => {
        c.classList.toggle("selected", c.dataset.eventId === eventId);
    });

    document.getElementById("hitlTargetId").value = eventId;
    document.getElementById("hitlEventDisplay").value = eventId;

    loadBrief(eventId);
    loadGraph(eventId);
    loadMarketImpact(eventId);
    loadCascade(eventId);
    loadAnalogies(eventId);
}

async function loadBrief(eventId) {
    const container = document.getElementById("briefContainer");
    try {
        const res = await fetch(`/api/brief/${eventId}`);
        if (!res.ok) throw new Error("Brief not found");
        const brief = await res.json();

        const sourcesHtml = (brief.key_sources || []).map(s => `
            <div class="source-item">
                <strong>Source:</strong> ${s.source_id} &bull; 
                <span style="color:var(--accent-cyan)">Credibility: ${Math.round(s.credibility_score * 100)}%</span><br>
                <em>${s.excerpt || "Official citation"}</em>
            </div>
        `).join("");

        const assetsHtml = (brief.affected_assets || []).map(a => `
            <div class="source-item">
                <strong>${a.ticker}</strong> (${a.sector || 'Equities'}): Return ${a.abnormal_return}, CAR ${a.cumulative_abnormal_return}, Volume z ${a.volume_z_score}
            </div>
        `).join("");

        const evidenceStepsHtml = (brief.evidence_chain || []).map(step => `
            <div class="evidence-step">${step}</div>
        `).join("");

        container.innerHTML = `
            <div class="brief-card">
                <div class="brief-header">
                    <div class="brief-tagline">AI-Generated Market Brief &bull; Grounded Evidence Model</div>
                    <h2 class="brief-headline">${brief.headline}</h2>
                    <div style="font-size:0.75rem; color:var(--text-muted); margin-top:6px;">
                        Generated: ${new Date(brief.generated_at).toUTCString()} &bull; Analyst Confidence: ${Math.round(brief.analyst_confidence * 100)}%
                    </div>
                </div>

                <div class="brief-section">
                    <h4>1. What Happened</h4>
                    <p class="brief-text">${brief.what_happened}</p>
                </div>

                <div class="brief-section">
                    <h4>2. Key Sources &amp; Attribution</h4>
                    <div class="source-badges">${sourcesHtml || '<p class="brief-text">Ingested wire feeds</p>'}</div>
                </div>

                <div class="brief-section">
                    <h4>3. Affected Assets &amp; Sectors</h4>
                    <div class="source-badges">${assetsHtml || '<p class="brief-text">Broad market indices</p>'}</div>
                </div>

                <div class="brief-section">
                    <h4>4. Observed Reaction &amp; Expected Spillover</h4>
                    <p class="brief-text">${brief.observed_reaction}</p>
                    <p class="brief-text" style="margin-top:6px; color:#93c5fd;">${brief.expected_spillover}</p>
                </div>

                <div class="brief-section">
                    <h4>5. Contradictory or Unresolved Information</h4>
                    <p class="brief-text" style="color:#fdba74;">${brief.contradictory_unresolved || 'No material reporting contradictions identified.'}</p>
                </div>

                <div class="brief-section">
                    <h4>6. Explainability &amp; Evidence Chain</h4>
                    <div class="evidence-chain-list">${evidenceStepsHtml}</div>
                </div>
            </div>
        `;
    } catch (e) {
        console.error("Error loading brief:", e);
        container.innerHTML = `<div class="empty-state">Unable to load AI Brief for this event.</div>`;
    }
}

async function loadGraph(eventId) {
    try {
        const res = await fetch(`/api/graph/${eventId}?depth=2`);
        graphData = await res.json();
        document.getElementById("graphNodeCount").textContent = graphData.nodes.length;
        document.getElementById("graphEdgeCount").textContent = graphData.edges.length;
        renderKnowledgeGraph();
    } catch (e) {
        console.error("Error loading graph:", e);
    }
}

function renderKnowledgeGraph() {
    const canvas = document.getElementById("kgCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const width = canvas.width;
    const height = canvas.height;

    ctx.clearRect(0, 0, width, height);

    if (!graphData.nodes || graphData.nodes.length === 0) {
        ctx.fillStyle = "#64748b";
        ctx.font = "14px Inter";
        ctx.textAlign = "center";
        ctx.fillText("No graph relationships recorded for this event.", width / 2, height / 2);
        return;
    }

    const nodes = graphData.nodes;
    const nodeMap = {};
    const centerX = width / 2;
    const centerY = height / 2;

    nodes.forEach((n, idx) => {
        let x, y;
        if (n.node_type === "Event") {
            x = centerX;
            y = centerY;
        } else {
            const angle = (idx / (nodes.length - 1 || 1)) * 2 * Math.PI;
            const radius = n.node_type === "Entity" ? 140 : (n.node_type === "Sector" ? 220 : 200);
            x = centerX + Math.cos(angle) * radius;
            y = centerY + Math.sin(angle) * radius;
        }
        nodeMap[n.id] = { ...n, x, y };
    });

    (graphData.edges || []).forEach(e => {
        const src = nodeMap[e.source];
        const tgt = nodeMap[e.target];
        if (src && tgt) {
            ctx.beginPath();
            ctx.moveTo(src.x, src.y);
            ctx.lineTo(tgt.x, tgt.y);
            ctx.strokeStyle = "rgba(100, 116, 139, 0.4)";
            ctx.lineWidth = 1.5;
            ctx.stroke();

            const midX = (src.x + tgt.x) / 2;
            const midY = (src.y + tgt.y) / 2;
            ctx.fillStyle = "#94a3b8";
            ctx.font = "9px 'JetBrains Mono'";
            ctx.textAlign = "center";
            ctx.fillText(e.relation, midX, midY - 3);
        }
    });

    Object.values(nodeMap).forEach(n => {
        ctx.beginPath();
        const r = n.node_type === "Event" ? 22 : (n.node_type === "Entity" ? 16 : 14);
        ctx.arc(n.x, n.y, r, 0, 2 * Math.PI);

        if (n.node_type === "Event") ctx.fillStyle = "#8b5cf6";
        else if (n.node_type === "Entity") ctx.fillStyle = "#3b82f6";
        else if (n.node_type === "Sector") ctx.fillStyle = "#f59e0b";
        else ctx.fillStyle = "#10b981";

        ctx.fill();
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.fillStyle = "#f8fafc";
        ctx.font = "11px Inter";
        ctx.textAlign = "center";
        ctx.fillText(n.label, n.x, n.y + r + 14);
    });
}

async function loadMarketImpact(eventId) {
    const grid = document.getElementById("marketMetricsGrid");
    const spilloverEl = document.getElementById("spilloverContent");
    try {
        const res = await fetch(`/api/market-reaction/${eventId}`);
        const data = await res.json();
        const metrics = data.metrics || [];

        if (metrics.length === 0) {
            grid.innerHTML = `<div class="empty-state">No market return data calculated.</div>`;
            return;
        }

        const top = metrics[0];
        const isBullish = top.abnormal_return >= 0;
        const sign = isBullish ? "+" : "";

        grid.innerHTML = `
            <div class="metric-card">
                <div class="metric-label">Event-Day Return</div>
                <div class="metric-val ${isBullish ? 'bullish' : 'bearish'}">${sign}${top.event_day_return}%</div>
                <div class="metric-sub">${top.asset_ticker} direct movement</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Cumulative Abnormal Return (CAR)</div>
                <div class="metric-val ${top.cumulative_abnormal_return >= 0 ? 'bullish' : 'bearish'}">${top.cumulative_abnormal_return > 0 ? '+' : ''}${top.cumulative_abnormal_return}%</div>
                <div class="metric-sub">Full event window [0, +5d]</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Abnormal Volume Spike</div>
                <div class="metric-val bullish">+${top.volume_z_score}&sigma;</div>
                <div class="metric-sub">Standard deviation z-score</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Realized Volatility Shock</div>
                <div class="metric-val ${top.volatility_shock > 0 ? 'bearish' : 'bullish'}">${top.volatility_shock > 0 ? '+' : ''}${top.volatility_shock}%</div>
                <div class="metric-sub">Baseline: ${top.baseline_volatility}% &bull; Realized: ${top.realized_volatility}%</div>
            </div>
        `;

        const sp = data.spillover_analysis || {};
        const winners = (sp.winners || []).map(w => `<span class="badge-pill" style="color:var(--bullish-green)">${w.ticker}: +${w.abnormal_return}%</span>`).join(" ");
        const losers = (sp.losers || []).map(l => `<span class="badge-pill" style="color:var(--bearish-red)">${l.ticker}: ${l.abnormal_return}%</span>`).join(" ");

        spilloverEl.innerHTML = `
            <p style="font-size:0.85rem; margin-bottom:10px;">
                <strong>Contagion Index:</strong> <span style="color:var(--accent-cyan)">${Math.round((sp.contagion_index || 0.5) * 100)}%</span>
            </p>
            <div style="margin-bottom:8px;"><strong>Spillover Winners:</strong> ${winners || 'None'}</div>
            <div><strong>Spillover Losers:</strong> ${losers || 'None'}</div>
        `;
    } catch (e) {
        console.error("Error loading market impact:", e);
    }
}

async function loadCascade(eventId) {
    const el = document.getElementById("cascadeTimeline");
    try {
        const res = await fetch(`/api/cascade/${eventId}`);
        const data = await res.json();
        const hops = data.hops || [];

        el.innerHTML = hops.map(h => `
            <div class="timeline-step">
                <div class="timeline-channel">${h.channel.replace(/_/g, ' ')} &bull; Amplification: ${Math.round(h.amplification_score * 100)}%</div>
                <div class="timeline-headline">${h.headline_or_action}</div>
                <div style="font-size:0.75rem; color:var(--text-muted);">${h.timestamp}</div>
            </div>
        `).join("");
    } catch (e) {
        console.error(e);
    }
}

async function loadAnalogies(eventId) {
    const el = document.getElementById("analogiesContent");
    try {
        const res = await fetch(`/api/analogies/${eventId}`);
        const data = await res.json();
        const analogues = data.analogues || [];

        el.innerHTML = analogues.map(a => `
            <div style="padding:10px; background:rgba(255,255,255,0.02); border:1px solid var(--border-color); border-radius:6px; margin-bottom:8px;">
                <div style="display:flex; justify-content:space-between; font-size:0.8rem; font-weight:700;">
                    <span>${a.past_event_title}</span>
                    <span style="color:var(--accent-cyan)">Match: ${Math.round(a.similarity_score * 100)}%</span>
                </div>
                <div style="font-size:0.75rem; color:var(--text-secondary); margin:4px 0;">
                    Date: ${a.past_date} &bull; Observed 3D CAR: <strong>${a.actual_car_3d > 0 ? '+' : ''}${a.actual_car_3d}%</strong> &bull; 5D CAR: <strong>${a.actual_car_5d > 0 ? '+' : ''}${a.actual_car_5d}%</strong>
                </div>
                <div style="font-size:0.75rem; color:#cbd5e1;">${a.outcome_summary}</div>
            </div>
        `).join("");
    } catch (e) {
        console.error(e);
    }
}

function initHITLForm() {
    const form = document.getElementById("hitlForm");
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const targetId = document.getElementById("hitlTargetId").value;
        if (!targetId) {
            alert("Please select an event to review.");
            return;
        }

        const payload = {
            target_id: targetId,
            target_type: "EVENT",
            status: document.getElementById("hitlStatus").value,
            reviewer: document.getElementById("hitlReviewer").value,
            reviewer_notes: document.getElementById("hitlNotes").value,
            verified_category: document.getElementById("hitlCategory").value || null,
            verified_sentiment: document.getElementById("hitlSentiment").value || null,
        };

        try {
            const res = await fetch("/api/validation", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            alert(`Validation submitted successfully! Feedback ID: ${data.feedback.feedback_id}`);
            loadHITLHistory();
            loadEventFeed();
        } catch (err) {
            console.error(err);
            alert("Error submitting validation feedback.");
        }
    });
}

async function loadHITLHistory() {
    const el = document.getElementById("hitlHistoryList");
    try {
        const res = await fetch("/api/validation/history");
        const data = await res.json();
        const list = data.history || [];

        if (list.length === 0) {
            el.innerHTML = `<div style="font-size:0.78rem; color:var(--text-muted);">No validation reviews recorded yet.</div>`;
            return;
        }

        el.innerHTML = list.map(item => `
            <div class="history-item">
                <strong>[${item.status}]</strong> ${item.target_id} reviewed by <em>${item.reviewer}</em>: "${item.reviewer_notes || 'Approved'}"
                <div style="color:var(--text-muted); font-size:0.7rem;">${new Date(item.timestamp).toLocaleString()}</div>
            </div>
        `).join("");
    } catch (e) {
        console.error(e);
    }
}

