"""
High-fidelity simulated multi-source feeds representing real-world financial events.
Ensures zero-dependency standalone demonstrations, unit testing, and historical replay.
Group No. 61 | Rishu Raj | Shaheed Arman Gazi
"""

import uuid
from typing import List
from datetime import datetime, timezone, timedelta
from src.common.models import RawDocument, DataSourceType


def get_mock_multi_source_feed() -> List[RawDocument]:
    """Returns realistic multi-source documents covering major financial events."""
    base_time = datetime.now(timezone.utc) - timedelta(hours=6)
    
    docs = [
        # EVENT 1: US Commerce Dept Imposes AI Chip Export Restrictions
        RawDocument(
            doc_id="doc-gov-chip-01",
            source_type=DataSourceType.OFFICIAL_ANNOUNCEMENT,
            source_name="SEC EDGAR / US Dept of Commerce",
            title="Bureau of Industry and Security Updates Export Controls on Advanced Computing Semiconductors",
            content="""The Bureau of Industry and Security (BIS) today released interim final rules restricting exports of high-performance artificial intelligence semiconductors and advanced wafer fabrication equipment to selected overseas jurisdictions. The revised threshold specifically restricts export licenses for GPUs with interconnect bandwidth exceeding 600 GB/s, affecting high-density data center hardware produced by leading American semiconductor designers including Nvidia Corp (NVDA) and Advanced Micro Devices (AMD).""",
            url="https://bis.doc.gov/index.php/regulations/export-controls-advanced-ai-chips",
            published_at=base_time - timedelta(minutes=180),
            raw_metadata={"category": "GOVERNMENT_RULE", "jurisdiction": "USA"}
        ),
        RawDocument(
            doc_id="doc-news-chip-02",
            source_type=DataSourceType.FINANCIAL_NEWS,
            source_name="Reuters",
            title="Nvidia and AMD face new export restrictions on advanced AI hardware; TSMC supply chain impacted",
            content="""Washington tightens restrictions on high-performance artificial intelligence chips to foreign data centers. Semiconductor giant Nvidia (NVDA) stated in a regulatory disclosure that the rules could restrict approximately $400 million in quarterly revenue. Taiwan Semiconductor Manufacturing Co (TSM) and equipment supplier ASML also face revised compliance requirements for leading-edge lithography tools.""",
            url="https://reuters.com/technology/nvidia-amd-face-new-export-rules",
            published_at=base_time - timedelta(minutes=165),
            raw_metadata={"author": "Financial Technology Desk"}
        ),
        RawDocument(
            doc_id="doc-news-chip-03",
            source_type=DataSourceType.FINANCIAL_NEWS,
            source_name="Bloomberg",
            title="Chip Stocks Slide as Commerce Dept Broadens AI Processor Curbs on Nvidia and Peers",
            content="""Shares of Nvidia Corp dropped over 4.8% in early trading following newly issued semiconductor restrictions from the US Commerce Department. The Philadelphia Semiconductor Index (SOX) declined 3.1%, dragging major supplier TSMC and competing chipmaker AMD into negative territory. Analysts at Morgan Stanley noted potential long-term headwinds for data-center hardware revenue.""",
            url="https://bloomberg.com/news/articles/chip-stocks-slide-on-export-curbs",
            published_at=base_time - timedelta(minutes=150),
            raw_metadata={"ticker_tags": ["NVDA", "AMD", "TSM", "SMH"]}
        ),
        RawDocument(
            doc_id="doc-social-chip-04",
            source_type=DataSourceType.SOCIAL_MEDIA,
            source_name="Reddit r/wallstreetbets",
            title="NVDA down 5% on export ban panic - buying the dip or is datacenter revenue cooked?",
            content="""Huge red candle on NVDA right at market open after the new Commerce Dept rules leaked. Everyone dumping semiconductor calls. TSM and AMD bleeding too. Is this an overreaction or will enterprise AI revenue genuinely stall this quarter? Discussion thread.""",
            url="https://reddit.com/r/wallstreetbets/comments/nvda_export_controls_dip",
            published_at=base_time - timedelta(minutes=135),
            raw_metadata={"upvotes": 1420, "sentiment_tone": "PANIC_UNCERTAINTY"}
        ),

        # EVENT 2: Federal Reserve FOMC Unexpected Dovish 50 bps Rate Cut
        RawDocument(
            doc_id="doc-gov-fed-01",
            source_type=DataSourceType.OFFICIAL_ANNOUNCEMENT,
            source_name="Federal Reserve",
            title="Federal Open Market Committee Announces 50 Basis Point Cut to Federal Funds Target Range",
            content="""In light of progress on inflation and the balance of risks to employment, the Federal Open Market Committee decided to lower the target range for the federal funds rate by 50 basis points to 4.75 to 5.00 percent. The Committee is strongly committed to supporting maximum employment and returning inflation to its 2 percent objective, while adjusting policy stance in response to cooling labor market metrics.""",
            url="https://federalreserve.gov/newsevents/pressreleases/monetary20240918a.htm",
            published_at=base_time - timedelta(minutes=90),
            raw_metadata={"type": "FOMC_POLICY_STATEMENT", "hawkish_dovish": "DOVISH"}
        ),
        RawDocument(
            doc_id="doc-news-fed-02",
            source_type=DataSourceType.FINANCIAL_NEWS,
            source_name="Wall Street Journal",
            title="Fed Slashes Benchmark Interest Rate by Half-Point in Aggressive Policy Shift",
            content="""The Federal Reserve commenced its monetary easing cycle with an outsized 50-basis-point interest rate reduction on Wednesday. Chairman Jerome Powell emphasized the central bank's determination to preserve low unemployment even as price pressures subside. Benchmark Treasury yields plunged, while US stock indexes rallied sharply led by rate-sensitive technology and real estate equities.""",
            url="https://wsj.com/economy/central-banking/fed-interest-rate-cut-decision",
            published_at=base_time - timedelta(minutes=75),
            raw_metadata={"sector_impact": "FINANCIALS_TECH_REALESTATE"}
        ),
        RawDocument(
            doc_id="doc-social-fed-03",
            source_type=DataSourceType.SOCIAL_MEDIA,
            source_name="StockTwits",
            title="FOMC fires the bazooka with 50bps cut! SPY and QQQ skyrocketing into the close",
            content="""50 bps! Powell went bold. Bond yields collapsing, Dollar tumbling against EUR and Yen. Tech stocks popping. SPY green candle to new highs. Bears getting destroyed.""",
            url="https://stocktwits.com/symbol/SPY/streams/fomc-50bps-rally",
            published_at=base_time - timedelta(minutes=65),
            raw_metadata={"sentiment_score": 0.95}
        ),

        # EVENT 3: OPEC+ Surprise 1.5M BPD Oil Production Quota Cut
        RawDocument(
            doc_id="doc-gov-opec-01",
            source_type=DataSourceType.OFFICIAL_ANNOUNCEMENT,
            source_name="OPEC Secretariat",
            title="OPEC and non-OPEC Ministerial Meeting Agrees on Additional 1.5 Million BPD Crude Production Adjustments",
            content="""In accordance with the decision taken at the 38th OPEC and non-OPEC Ministerial Meeting, member countries have decided to extend voluntary production adjustments of 1.5 million barrels per day through the end of the calendar year to maintain global crude market stability and counter speculative supply volatility.""",
            url="https://opec.org/opec_web/en/press_room/production_cut_notice.htm",
            published_at=base_time - timedelta(minutes=45),
            raw_metadata={"commodity": "CRUDE_OIL"}
        ),
        RawDocument(
            doc_id="doc-news-opec-02",
            source_type=DataSourceType.FINANCIAL_NEWS,
            source_name="Financial Times",
            title="Oil Surges 4% After OPEC+ Delivers Unexpected 1.5 Million Barrels Production Cut",
            content="""Brent crude and West Texas Intermediate (WTI) leaped more than 4.2% after OPEC+ producers led by Saudi Arabia unveiled an unexpected supply curb. Major energy producers Exxon Mobil (XOM) and Chevron (CVX) gained in pre-market trading, whereas transportation and airline stocks like Delta (DAL) faced immediate margin compression concerns over rising jet fuel costs.""",
            url="https://ft.com/content/opec-surprise-production-curbs-crude-surge",
            published_at=base_time - timedelta(minutes=35),
            raw_metadata={"assets": ["USO", "XOM", "CVX", "DAL"]}
        ),
    ]
    return docs

