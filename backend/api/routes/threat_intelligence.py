"""
Dark Web Threat Intelligence API Routes

Endpoints for querying and analyzing dark web threat intelligence.
Integrates with ThreatIntelligenceFusionEngine and DarkWebScraper.

Endpoints:
  POST   /api/threat-intelligence/analyze         - Analyze raw text for threats
  POST   /api/threat-intelligence/marketplace     - Process marketplace listing
  POST   /api/threat-intelligence/leak-dump       - Process leak dump data
  GET    /api/threat-intelligence/threats         - Get all threats
  GET    /api/threat-intelligence/threats/{id}    - Get specific threat
  GET    /api/threat-intelligence/search          - Search threats by keyword
  GET    /api/threat-intelligence/summary         - Get threat summary
  GET    /api/threat-intelligence/correlations    - Get threat correlations
  POST   /api/threat-intelligence/correlate       - Find correlations between threats
  GET    /api/threat-intelligence/top             - Get top threats by severity
  POST   /api/threat-intelligence/alert           - Generate keyword alert
  GET    /api/threat-intelligence/indicators      - Get known indicators
  POST   /api/threat-intelligence/scrape          - Scrape and analyze dark web
  GET    /api/threat-intelligence/health          - Service health check
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/threat-intelligence",
    tags=["threat-intelligence"],
    responses={404: {"description": "Not found"}},
)

# Global threat intelligence engine (lazy loaded)
_threat_engine = None


def get_threat_engine():
    """Lazy load threat intelligence engine"""
    global _threat_engine
    if _threat_engine is None:
        try:
            from backend.core.deception.threat_intelligence_fusion import (
                ThreatIntelligenceFusionEngine,
            )
            _threat_engine = ThreatIntelligenceFusionEngine()
            logger.info("Threat Intelligence Fusion Engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize threat engine: {e}")
            raise
    return _threat_engine


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class ThreatAnalysisRequest(BaseModel):
    """Request to analyze text for threats"""
    text: str = Field(..., min_length=10, description="Text to analyze for threats")
    source_url: Optional[str] = Field(None, description="Source URL if from dark web")
    marketplace: Optional[str] = Field(None, description="Marketplace name")


class MarketplaceListingRequest(BaseModel):
    """Request to process marketplace listing"""
    title: str = Field(..., description="Listing title")
    description: str = Field(..., description="Listing description")
    marketplace: str = Field(..., description="Marketplace name (darkfox, versus, etc.)")
    price: Optional[float] = Field(None, description="Listing price")
    vendor: Optional[str] = Field(None, description="Vendor name")


class LeakDumpRequest(BaseModel):
    """Request to process leak dump"""
    dump_name: str = Field(..., description="Name of leak dump")
    entries_sample: str = Field(..., min_length=20, description="Sample of leak entries")


class KeywordAlertRequest(BaseModel):
    """Request to generate keyword alert"""
    keyword: str = Field(..., min_length=3, description="Keyword to search for")


class CorrelationRequest(BaseModel):
    """Request to find correlations between two threats"""
    signal_id_1: str = Field(..., description="First threat signal ID")
    signal_id_2: str = Field(..., description="Second threat signal ID")


class ScrapeAndAnalyzeRequest(BaseModel):
    """Request to scrape dark web content and analyze"""
    urls: List[str] = Field(..., min_items=1, max_items=10, description="URLs to scrape")
    marketplace: Optional[str] = Field(None, description="Marketplace name")


class ThreatIndicatorResponse(BaseModel):
    """Response model for threat indicator"""
    ioc_type: str
    ioc_value: str
    confidence: float
    source_text: Optional[str] = None
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None


class ThreatSignalResponse(BaseModel):
    """Response model for threat signal"""
    signal_id: str
    title: str
    description: str
    threat_type: str
    severity: str
    confidence_score: float
    indicators: List[Dict[str, Any]]
    threat_actors: List[str]
    affected_products: List[str]
    extraction_method: str
    source_url: Optional[str] = None
    marketplace: Optional[str] = None
    created_at: str
    updated_at: str


class ThreatSummaryResponse(BaseModel):
    """Response model for threat summary"""
    total_threats: int
    total_correlations: int
    threats_by_severity: Dict[str, int]
    threats_by_type: Dict[str, int]
    known_indicators: Dict[str, int]


class KeywordAlertResponse(BaseModel):
    """Response model for keyword alert"""
    keyword: str
    matched_signals: int
    signals: List[ThreatSignalResponse]


class CorrelationResponse(BaseModel):
    """Response model for threat correlation"""
    correlation_id: str
    signal_ids: List[str]
    correlation_score: float
    correlation_type: str
    description: str
    created_at: str


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    engine: str
    threats_tracked: int
    correlations_tracked: int
    timestamp: str


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("/analyze", response_model=ThreatSignalResponse)
async def analyze_threat_text(request: ThreatAnalysisRequest):
    """
    Analyze raw text for threat indicators and classifications.
    
    Returns a threat signal with:
    - Extracted indicators (CVEs, IPs, malware names, etc.)
    - Threat classification (type and severity)
    - Confidence score
    - Correlations with known threats
    """
    try:
        engine = get_threat_engine()
        signal = engine.process_dark_web_text(
            text=request.text,
            source_url=request.source_url,
            marketplace=request.marketplace,
        )
        return signal.to_dict()
    except Exception as e:
        logger.error(f"Error analyzing threat text: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/marketplace", response_model=ThreatSignalResponse)
async def analyze_marketplace_listing(request: MarketplaceListingRequest):
    """
    Process dark web marketplace listing as threat signal.
    
    Extracts threat indicators and classifies the listing.
    """
    try:
        engine = get_threat_engine()
        signal = engine.process_marketplace_listing(
            listing_title=request.title,
            listing_description=request.description,
            marketplace=request.marketplace,
            price=request.price or 0.0,
            vendor=request.vendor,
        )
        return signal.to_dict()
    except Exception as e:
        logger.error(f"Error processing marketplace listing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/leak-dump", response_model=ThreatSignalResponse)
async def analyze_leak_dump(request: LeakDumpRequest):
    """
    Process leak dump data as threat signal.
    
    Classifies leaked data by type and extracts exposed indicators.
    """
    try:
        engine = get_threat_engine()
        signal = engine.process_leak_dump(
            dump_name=request.dump_name,
            entries_sample=request.entries_sample,
        )
        return signal.to_dict()
    except Exception as e:
        logger.error(f"Error processing leak dump: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/threats", response_model=List[ThreatSignalResponse])
async def get_all_threats(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100)):
    """
    Get all tracked threat signals.
    
    Supports pagination with skip and limit.
    """
    try:
        engine = get_threat_engine()
        signals = list(engine.threat_signals.values())
        signals = sorted(signals, key=lambda s: s.created_at, reverse=True)
        return [s.to_dict() for s in signals[skip : skip + limit]]
    except Exception as e:
        logger.error(f"Error retrieving threats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/threats/{signal_id}", response_model=ThreatSignalResponse)
async def get_threat(signal_id: str):
    """
    Get specific threat signal by ID.
    """
    try:
        engine = get_threat_engine()
        if signal_id not in engine.threat_signals:
            raise HTTPException(status_code=404, detail="Threat signal not found")
        signal = engine.threat_signals[signal_id]
        return signal.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving threat {signal_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=List[ThreatSignalResponse])
async def search_threats(keyword: str = Query(..., min_length=1), limit: int = Query(20, le=100)):
    """
    Search threat signals by keyword.
    
    Searches in title, description, and threat actors.
    """
    try:
        engine = get_threat_engine()
        keyword_lower = keyword.lower()
        matching = []
        
        for signal in engine.threat_signals.values():
            if (keyword_lower in signal.title.lower() or
                keyword_lower in signal.description.lower() or
                any(keyword_lower in actor.lower() for actor in signal.threat_actors)):
                matching.append(signal)
        
        matching = sorted(matching, key=lambda s: s.confidence_score, reverse=True)
        return [s.to_dict() for s in matching[:limit]]
    except Exception as e:
        logger.error(f"Error searching threats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", response_model=ThreatSummaryResponse)
async def get_threat_summary():
    """
    Get overall threat intelligence summary.
    
    Returns:
    - Total threats tracked
    - Breakdown by severity and type
    - Known indicators by category
    """
    try:
        engine = get_threat_engine()
        return engine.get_threat_summary()
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/correlations", response_model=List[CorrelationResponse])
async def get_correlations(limit: int = Query(20, le=100)):
    """
    Get all tracked threat correlations.
    
    Shows relationships between threat signals.
    """
    try:
        engine = get_threat_engine()
        correlations = list(engine.correlations.values())
        correlations = sorted(correlations, key=lambda c: c.correlation_score, reverse=True)
        return [c.to_dict() for c in correlations[:limit]]
    except Exception as e:
        logger.error(f"Error retrieving correlations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/correlate", response_model=Optional[CorrelationResponse])
async def find_correlation(request: CorrelationRequest):
    """
    Find or create correlation between two threat signals.
    """
    try:
        engine = get_threat_engine()
        correlation = engine.create_correlation(request.signal_id_1, request.signal_id_2)
        if correlation is None:
            raise HTTPException(status_code=404, detail="One or both threat signals not found")
        return correlation.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating correlation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top", response_model=List[ThreatSignalResponse])
async def get_top_threats(limit: int = Query(10, ge=1, le=50)):
    """
    Get top threats by confidence score.
    
    Highest confidence threats first.
    """
    try:
        engine = get_threat_engine()
        return engine.get_top_threats(limit)
    except Exception as e:
        logger.error(f"Error retrieving top threats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alert", response_model=KeywordAlertResponse)
async def generate_keyword_alert(request: KeywordAlertRequest):
    """
    Generate alert for high-priority keyword.
    
    Returns all threat signals matching the keyword.
    """
    try:
        engine = get_threat_engine()
        result = engine.generate_keyword_alert(request.keyword)
        return result
    except Exception as e:
        logger.error(f"Error generating keyword alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indicators", response_model=Dict[str, Dict[str, Any]])
async def get_known_indicators():
    """
    Get all known indicators by category.
    
    Returns CVEs, malware names, threat actors, domains detected.
    """
    try:
        engine = get_threat_engine()
        return {
            "cves": list(engine.known_indicators["cve"]),
            "malware": list(engine.known_indicators["malware"]),
            "threat_actors": list(engine.known_indicators["threat_actor"]),
            "domains": list(engine.known_indicators["domain"]),
            "total": sum(len(v) for v in engine.known_indicators.values()),
        }
    except Exception as e:
        logger.error(f"Error retrieving indicators: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scrape")
async def scrape_and_analyze(request: ScrapeAndAnalyzeRequest):
    """
    Scrape dark web URLs and analyze for threats.
    
    Integrates with DarkWebScraper for OSINT collection.
    """
    try:
        engine = get_threat_engine()
        from backend.core.deception.darkweb_scraper import DarkWebScraper
        
        scraper = DarkWebScraper()
        results = []
        
        for url in request.urls:
            try:
                content = scraper.fetch(url)
                if content:
                    signal = engine.process_dark_web_text(
                        text=content,
                        source_url=url,
                        marketplace=request.marketplace,
                    )
                    results.append({
                        "url": url,
                        "status": "success",
                        "signal": signal.to_dict(),
                    })
            except Exception as url_error:
                results.append({
                    "url": url,
                    "status": "error",
                    "error": str(url_error),
                })
        
        return {
            "total_urls": len(request.urls),
            "successful": sum(1 for r in results if r["status"] == "success"),
            "results": results,
        }
    except Exception as e:
        logger.error(f"Error scraping and analyzing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check for threat intelligence service.
    """
    try:
        engine = get_threat_engine()
        return {
            "status": "healthy",
            "engine": "MindSpore NLP" if engine._nlp_model == "mindspore" else "sklearn" if engine._nlp_model == "sklearn" else "regex",
            "threats_tracked": len(engine.threat_signals),
            "correlations_tracked": len(engine.correlations),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "engine": "error",
            "threats_tracked": 0,
            "correlations_tracked": 0,
            "timestamp": datetime.utcnow().isoformat(),
        }


__all__ = ["router"]
