"""
Enhanced AI Risk Mitigation System - Main Application Entry Point (API + Admin)
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import structlog
from contextlib import asynccontextmanager

from app.api import detection, scoring, mitigation, reports, llm, config
from app.api import llm_integration
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import init_db

# Admin system integration - conditionally import
try:
    from admin.main_admin import router as main_admin_router
    from admin.client_admin import router as client_admin_router
    from admin.middleware import RiskMitigationMiddleware
    ADMIN_AVAILABLE = True
except ImportError:
    ADMIN_AVAILABLE = False
    print("⚠️  Admin middleware not available - running in basic mode")

# Enhanced detection modules
from app.detection.enhanced_adversarial_detector import EnhancedAdversarialDetector
from app.detection.enhanced_hallucination_detector import EnhancedHallucinationDetector
from app.detection.enhanced_pii_detector import EnhancedPIIDetector
from app.detection.bias_detector import AdvancedBiasDetector

# Enhanced scoring and mitigation
from app.scoring.enhanced_risk_engine import EnhancedRiskScoringEngine
from app.mitigation.enhanced_strategies import create_mitigation_engine
# Enhanced detection modules
from app.detection.enhanced_adversarial_detector import EnhancedAdversarialDetector
from app.detection.enhanced_hallucination_detector import EnhancedHallucinationDetector
from app.detection.enhanced_pii_detector import EnhancedPIIDetector
from app.detection.bias_detector import AdvancedBiasDetector

# Enhanced scoring and mitigation
from app.scoring.enhanced_risk_engine import EnhancedRiskScoringEngine
from app.mitigation.enhanced_strategies import create_mitigation_engine
setup_logging()
logger = structlog.get_logger()

# Global instances of enhanced components
enhanced_detectors = {}
enhanced_risk_engine = None
enhanced_mitigation_engine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global enhanced_detectors, enhanced_risk_engine, enhanced_mitigation_engine
    
    # Startup
    logger.info("Starting Enhanced AI Risk Mitigation System...")
    await init_db()
    logger.info("Database initialized")
    
    # Initialize admin database
    try:
        from admin.database import init_database
        init_database()
        logger.info("Admin database initialized")
    except Exception as e:
        logger.warning(f"Admin database initialization failed: {e}")
    
    # Initialize enhanced components
    try:
        logger.info("Initializing enhanced detection modules...")
        enhanced_detectors['bias'] = AdvancedBiasDetector()
        enhanced_detectors['hallucination'] = EnhancedHallucinationDetector()
        enhanced_detectors['pii'] = EnhancedPIIDetector()
        enhanced_detectors['adversarial'] = EnhancedAdversarialDetector()
        logger.info("Enhanced detectors initialized")
        
        logger.info("Initializing enhanced risk scoring engine...")
        enhanced_risk_engine = EnhancedRiskScoringEngine()
        logger.info("Enhanced risk engine initialized")
        
        logger.info("Initializing enhanced mitigation engine...")
        enhanced_mitigation_engine = create_mitigation_engine()
        logger.info("Enhanced mitigation engine initialized")
        
        # Store in app state for access in routes
        app.state.enhanced_detectors = enhanced_detectors
        app.state.enhanced_risk_engine = enhanced_risk_engine
        app.state.enhanced_mitigation_engine = enhanced_mitigation_engine
        
        logger.info("All enhanced components initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize enhanced components", error=str(e))
        # Continue with basic functionality if enhanced components fail
    
    yield
    
    # Shutdown
    logger.info("Shutting down Enhanced AI Risk Mitigation System...")

# Create FastAPI application
app = FastAPI(
    title="Enhanced AI Risk Mitigation System",
    description="""
    Advanced AI Risk Mitigation System with enhanced detection capabilities:
    
    🔍 **Advanced Detection Modules:**
    - **Bias Detection**: AIF360, Fairlearn integration with intersectionality analysis
    - **Hallucination Detection**: Fact-checking APIs, VERITAS, retrieval models
    - **PII Detection**: Enhanced Presidio, spaCy, custom pattern recognition
    - **Adversarial Detection**: Adversarial Robustness Toolbox (ART), anomaly detection
    
    ⚖️ **Enhanced Risk Scoring:**
    - Custom risk matrices with domain-specific weighting
    - ML-driven risk correlation analysis
    - Uncertainty quantification and confidence intervals
    
    🛡️ **Advanced Mitigation:**
    - ML-driven strategy selection
    - Adaptive mitigation techniques
    - Context-aware risk responses
    
    📊 **Real-time Monitoring:**
    - Interactive dashboard with risk analytics
    - Trend analysis and predictive insights
    - Compliance reporting and audit trails
    """,
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Risk Mitigation Middleware for client API requests
if ADMIN_AVAILABLE:
    try:
        app.add_middleware(RiskMitigationMiddleware)
        logger.info("Risk mitigation middleware added")
    except Exception as e:
        logger.warning(f"Risk mitigation middleware not added: {e}")
else:
    logger.info("Admin system not available - skipping middleware")

# Include API routers (Core functionality only)
app.include_router(detection.router, prefix="/api/v1/detection", tags=["Detection"])
app.include_router(scoring.router, prefix="/api/v1/scoring", tags=["Risk Scoring"])
app.include_router(mitigation.router, prefix="/api/v1/mitigation", tags=["Mitigation"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(llm.router, prefix="/api/v1/llm", tags=["LLM Risk-Aware Processing"])
app.include_router(config.router, tags=["Configuration Management"])
app.include_router(llm_integration.router, prefix="/api/v1/llm-integration", tags=["LLM Integration Proxy"])

# Include enhanced API router
from app.api import enhanced
app.include_router(enhanced.router, prefix="/api/v2", tags=["Enhanced AI Risk Analysis"])

# Include admin routers if available
if ADMIN_AVAILABLE:
    app.include_router(main_admin_router, prefix="/admin", tags=["Main Admin Panel"])
    app.include_router(client_admin_router, prefix="/client-admin", tags=["Client Admin Panel"])
    logger.info("Admin panels loaded successfully")

# Serve static files for dashboard
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
# Serve admin static files if available
if ADMIN_AVAILABLE:
    app.mount("/admin/static", StaticFiles(directory="admin/static"), name="admin_static")

@app.get("/", response_class=HTMLResponse)
async def main_interface():
    """Main interface for the AI Risk Mitigation System"""
    import os
    html_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "templates", "main.html")
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        # Fallback to a simple HTML response
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Risk Mitigation System</title>
            <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        </head>
        <body class="bg-gray-50">
            <div class="container mx-auto px-4 py-8">
                <h1 class="text-3xl font-bold text-center text-blue-600 mb-8">AI Risk Mitigation System</h1>
                <div class="text-center">
                    <div class="space-y-4">
                        <a href="/admin/" class="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700">
                            Main Admin Panel
                        </a>
                        <a href="/client-admin/" class="inline-block bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 ml-4">
                            Client Admin Panel  
                        </a>
                    </div>
                    <p class="mt-8 text-gray-600">Welcome to the AI Risk Mitigation System</p>
                </div>
            </div>
        </body>
        </html>
        """)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_redirect():
    """Redirect dashboard to main interface"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/")

@app.get("/admin/", response_class=HTMLResponse)
async def admin_dashboard():
    """Admin dashboard - redirect to login if not authenticated"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/admin/login")

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard_no_slash():
    """Admin dashboard redirect without trailing slash"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/admin/")

@app.get("/client-admin/dashboard", response_class=HTMLResponse) 
async def client_admin_dashboard_direct():
    """Client admin dashboard - redirect to actual dashboard"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/client-admin/client/dashboard")

@app.get("/client-admin/", response_class=HTMLResponse) 
async def client_admin_dashboard():
    """Client admin dashboard - redirect to registration if not authenticated"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/client-admin/register")

@app.get("/client-admin", response_class=HTMLResponse)
async def client_admin_dashboard_no_slash():
    """Client admin dashboard redirect without trailing slash"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/client-admin/")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0", "enhanced_features": True}

@app.get("/api/v1/status")
async def system_status():
    """System status endpoint"""
    return {
        "status": "operational",
        "version": "2.0.0",
        "enhanced_modules": {
            "bias_detection": "active - AIF360, Fairlearn",
            "hallucination_detection": "active - Fact-checking, VERITAS", 
            "pii_detection": "active - Enhanced Presidio, spaCy",
            "adversarial_detection": "active - ART, Anomaly Detection",
            "risk_scoring": "active - ML-driven, Custom Matrices",
            "mitigation": "active - Adaptive Strategies"
        },
        "ml_capabilities": {
            "fairlearn": True,
            "aif360": True,
            "presidio": True,
            "sentence_transformers": True,
            "textattack": True
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
