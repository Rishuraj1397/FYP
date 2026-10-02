"""
Main Application Launcher for:
AI-Powered Multi-Source Event Intelligence & Market Impact Analysis
Group No. 61 | Rishu Raj | Shaheed Arman Gazi
"""

import sys
import uvicorn
from config.settings import settings


def main():
    print("=" * 75)
    print("AI-POWERED MULTI-SOURCE EVENT INTELLIGENCE & MARKET IMPACT ANALYSIS")
    print(f"{settings.GROUP_INFO}")
    print("=" * 75)
    print(f"[*] Starting server on http://{settings.API_HOST}:{settings.API_PORT}")
    print(f"[*] API Documentation available at http://{settings.API_HOST}:{settings.API_PORT}/docs")
    print(f"[*] Interactive Intelligence Dashboard available at http://{settings.API_HOST}:{settings.API_PORT}/")
    print("=" * 75)

    uvicorn.run(
        "src.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()

