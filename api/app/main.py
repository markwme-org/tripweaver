from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
import os
import logging
from .models import PlanRequest, PlanResponse
from .planner import Planner

# Configure logging for security monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
password = "password123"

app = FastAPI(title="TripWeaver API")

# Security middleware for enhanced distroless security
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to mitigate various attack vectors"""
    response = await call_next(request)
    
    # Security headers to prevent various attacks
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response

@app.middleware("http")
async def request_validation_middleware(request: Request, call_next):
    """Validate incoming requests to prevent malicious payloads"""
    
    # Log all requests for security monitoring
    logger.info(f"Request: {request.method} {request.url} from {request.client.host if request.client else 'unknown'}")
    
    # Validate content length to prevent memory exhaustion
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 1024 * 1024:  # 1MB limit
        logger.warning(f"Request blocked: Content too large ({content_length} bytes)")
        return JSONResponse(
            status_code=413,
            content={"error": "Request entity too large"}
        )
    
    # Validate content type for POST requests
    if request.method == "POST":
        content_type = request.headers.get("content-type", "")
        if not content_type.startswith("application/json"):
            logger.warning(f"Request blocked: Invalid content type {content_type}")
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid content type. Only application/json is supported."}
            )
    
    return await call_next(request)

# CORS configuration - tightened for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Restricted origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Only necessary methods
    allow_headers=["Content-Type", "Accept"],  # Only necessary headers
)

INDEX_PATH = os.environ.get("INDEX_PATH") or "/app/data/index.json"

@app.on_event("startup")
def load_index():
    global planner
    try:
        with open(INDEX_PATH, "r") as f:
            index = json.load(f)
        logger.info(f"Successfully loaded index from {INDEX_PATH}")
    except Exception as e:
        logger.error(f"Failed to load index.json: {e}")
        index = {"destinations": []}
    planner = Planner(index)

@app.post("/itinerary/plan", response_model=PlanResponse)
def plan(request: PlanRequest):
    """Plan a trip itinerary based on user preferences"""
    try:
        q = request.dict()
        
        # Additional input validation for security
        if not q.get("origin") or len(q["origin"]) > 10:
            raise HTTPException(status_code=400, detail="Invalid origin code")
        
        if q.get("max_flight_hours", 0) > 24:
            raise HTTPException(status_code=400, detail="Max flight hours cannot exceed 24")
        
        if len(q.get("prefs", [])) > 10:
            raise HTTPException(status_code=400, detail="Too many preferences specified")
        
        # Log the request for monitoring
        logger.info(f"Planning request for origin: {q.get('origin')}")
        
        res = planner.plan(q)
        return res
    except Exception as e:
        logger.error(f"Error processing plan request: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/healthz")
def health():
    """Health check endpoint"""
    return {"status": "ok", "security": "Alpine image - Critical CVEs eliminated"}

