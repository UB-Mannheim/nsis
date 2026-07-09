# -*- coding: utf-8 -*-
# =============================================================================
# main.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
FastAPI application for nsis - natürlichsprachige Suche im StabiKat
"""

# =============================================================================
# IMPORTS
# =============================================================================

# Standard library imports
import logging
import uuid
import time
import traceback
from datetime import datetime
from typing import Any, Optional
from pathlib import Path
from contextlib import asynccontextmanager

# Third-party imports
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, Response
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded
from starlette.middleware.trustedhost import TrustedHostMiddleware

# Local imports
from app.config import settings
from app.api.v1.router import router as v1_router
from app.dependencies import initialize_services, shutdown_services, get_milvus_service, get_vufind_service, get_transformation_service
from app.utils.logging import setup_logging, setup_api_calls_logger, log_api_call
from core.usage_stats_logging import setup_usage_stats_loggers, usage_stats_logger
from app.rate_limit import limiter
from app.ip_blocklist import blocklist
from app.ip_tracker import tracker, initialize_tracker, shutdown_tracker


# =============================================================================
# LOGGING SETUP
# =============================================================================

setup_logging(settings.log_level, settings.log_dir)
# init logger for API calls
setup_api_calls_logger(settings.log_dir)
# init usage statistics loggers (basic, business, performance metrics)
setup_usage_stats_loggers(settings.log_dir)
# init logger for FastAPI server
logger = logging.getLogger(settings.logger_name)


# =============================================================================
# LIFESPAN CONTEXT MANAGER
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for application startup and shutdown."""
    # Startup: Initialize services
    logger.info(f"Starting {settings.api_title}...")
    await initialize_services()
    await initialize_tracker()
    logger.info(f"{settings.api_title} started successfully.")

    yield

    # Shutdown: Clean up services
    logger.info(f"Shutting down {settings.api_title}...")
    await shutdown_tracker()
    await shutdown_services()
    logger.info(f"{settings.api_title} shut down successfully.")


# =============================================================================
# APP INITIALIZATION
# =============================================================================

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    root_path=settings.root_path,
    lifespan=lifespan,
)

# Rate limiting setup
app.state.limiter = limiter


# =============================================================================
# RATE LIMIT EXCEEDED HANDLER
# =============================================================================

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Handle rate limit exceeded - track violation and return error."""
    client_ip = request.client.host if request.client else None
    if client_ip:
        tracker.record_rate_violation(client_ip)

    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": str(exc.detail) if hasattr(exc, 'detail') else "Rate limit exceeded. Please try again later."
            }
        }
    )


# =============================================================================
# MIDDLEWARE
# =============================================================================

# IP blocking middleware
@app.middleware("http")
async def ip_blocking_middleware(request: Request, call_next):
    """Block requests from configured IP addresses, except for localhost."""
    client_ip = request.client.host if request.client else None

    # Skip IP blocking for localhost / 127.0.0.1
    if client_ip and client_ip in ("127.0.0.1", "::1", "localhost"):
        return await call_next(request)

    if client_ip and blocklist.is_blocked(client_ip):
        logger.warning(f"Blocked IP attempted access: {client_ip}")
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": {
                    "code": "IP_BLOCKED",
                    "message": "Access denied for your IP address."
                }
            }
        )

    return await call_next(request)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to all requests for tracking and debugging."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# JSON decode error catching middleware
@app.middleware("http")
async def catch_json_decode_errors(request: Request, call_next):
    """Catch JSON decode errors and return 422 instead of 500."""
    try:
        return await call_next(request)
    except Exception as exc:
        logger.error(f"Exception caught in catch_json_decode_errors: type={type(exc).__name__}, message={str(exc)}")

        if "JSONDecodeError" in type(exc).__name__ or "Expecting value" in str(exc):
            logger.error(f"JSON decode error: {exc}")
            request_id = getattr(request.state, 'request_id', None)
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=_create_error_response(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    error_code="INVALID_JSON",
                    message="Invalid JSON format in request body",
                    request_id=request_id,
                    suggestion="Please ensure your request body contains valid JSON"
                ),
            )

        raise


# API request logging middleware
@app.middleware("http")
async def log_api_requests(request: Request, call_next):
    """Log all API requests and responses."""
    # Get client IP
    client_ip = request.client.host if request.client else None

    # Get user agent
    user_agent = request.headers.get("user-agent")

    # Get query parameters
    query_params = str(request.url.query) if request.url.query else None

    # Get request body for POST/PUT/PATCH requests
    body = None
    request_size = 0
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body_bytes = await request.body()
            if body_bytes:
                request_size = len(body_bytes)
                body = body_bytes.decode('utf-8', errors='replace')
        except Exception as e:
            logger.error(f"Error reading request body in log_api_requests: type={type(e).__name__}, message={str(e)}")

    # Record start time
    start_time = time.time()

    try:
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Get response size
        response_size = int(response.headers.get("content-length", 0))

        # Log the API call (legacy format)
        log_api_call(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            client_ip=client_ip,
            query_params=query_params,
            body=body,
            duration_ms=duration_ms
        )

        # Log basic metrics to usage stats (JSON format)
        request_id = getattr(request.state, 'request_id', None)
        usage_stats_logger.log_basic(
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code,
            client_ip=client_ip,
            latency_ms=duration_ms,
            request_size_bytes=request_size,
            response_size_bytes=response_size,
            request_id=request_id,
            user_agent=user_agent
        )

        # Track error responses for bot detection
        if client_ip and 400 <= response.status_code < 600:
            tracker.record_error(client_ip)

        return response

    except Exception:

        # Calculate duration even for exceptions
        duration_ms = (time.time() - start_time) * 1000

        # Log the failed API call (legacy format)
        log_api_call(
            method=request.method,
            path=request.url.path,
            status_code=500,
            client_ip=client_ip,
            query_params=query_params,
            body=body,
            duration_ms=duration_ms
        )

        # Log basic metrics for failed request (JSON format)
        request_id = getattr(request.state, 'request_id', None)
        usage_stats_logger.log_basic(
            endpoint=request.url.path,
            method=request.method,
            status_code=500,
            client_ip=client_ip,
            latency_ms=duration_ms,
            request_size_bytes=request_size,
            response_size_bytes=0,
            request_id=request_id,
            user_agent=user_agent
        )

        raise


# =============================================================================
# CORS CONFIGURATION
# =============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# TRUSTED HOST CONFIGURATION
# =============================================================================

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[settings.domain, "localhost", "127.0.0.1"],
)


# =============================================================================
# API ROUTERS
# =============================================================================

app.include_router(v1_router, prefix=f"{settings.api_prefix}/v1", tags=["v1"])

# Future versions can be added here:
#
# from app.api.v2.router import router as v2_router
# app.include_router(v2_router, prefix=f"{settings.api_prefix}/v2", tags=["v2"])


# =============================================================================
# ERROR RESPONSE HELPERS
# =============================================================================

def _make_json_serializable(obj: Any) -> Any:
    """Recursively convert bytes and other non-serializable objects to strings."""
    if isinstance(obj, bytes):
        return obj.decode('utf-8', errors='replace')
    elif isinstance(obj, dict):
        return {k: _make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_make_json_serializable(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(_make_json_serializable(item) for item in obj)
    else:
        return obj


def _create_error_response(
    status_code: int,
    error_code: str,
    message: str,
    field: Optional[str] = None,
    suggestion: Optional[str] = None,
    request_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """Create a structured error response for frontend-friendly error handling."""
    error_response: dict[str, Any] = {
        "error": {
            "code": error_code,
            "message": message,
        }
    }

    if field:
        error_response["error"]["field"] = field
    if suggestion:
        error_response["error"]["suggestion"] = suggestion
    if request_id:
        error_response["requestId"] = request_id
    if details:
        error_response["error"]["details"] = details

    return error_response


# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation errors with structured error responses."""
    request_id = getattr(request.state, 'request_id', None)
    logger.error(f"Validation error: {exc.errors()}")

    # Handle bytes body (from invalid JSON) by converting to string
    body = exc.body
    if isinstance(body, bytes):
        body = body.decode('utf-8', errors='replace')

    # Convert error details to JSON-serializable format
    errors = _make_json_serializable(exc.errors())

    # Build structured error response
    error_details: list[dict[str, Any]] = []
    for error in errors:
        error_detail: dict[str, Any] = {
            "field": ".".join(str(loc) for loc in error.get("loc", [])),
            "message": error.get("msg", ""),
            "type": error.get("type", "")
        }

        # Add suggestions for common validation errors
        suggestion: Optional[str] = None
        if error.get("type") == "string_too_short":
            suggestion = f"Field must be at least {error.get('ctx', {}).get('min_length', 1)} character(s) long"
        elif error.get("type") == "string_too_long":
            suggestion = f"Field must be at most {error.get('ctx', {}).get('max_length', 255)} character(s) long"
        elif error.get("type") == "missing":
            suggestion = "This field is required"
        elif error.get("type") == "value_error.missing":
            suggestion = "This field is required"

        if suggestion:
            error_detail["suggestion"] = suggestion

        error_details.append(error_detail)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            request_id=request_id,
            details={"errors": error_details, "body": body}
        ),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions with structured error responses."""
    request_id = getattr(request.state, 'request_id', None)
    logger.error(f"General exception at {request.url}: {type(exc).__name__}: {exc}")
    logger.error(traceback.format_exc())

    # Determine error code and suggestion based on exception type
    error_code = "INTERNAL_SERVER_ERROR"
    suggestion = "Please try again later or contact support if the problem persists"

    # Add specific handling for common exceptions
    if "ConnectionError" in type(exc).__name__ or "TimeoutError" in type(exc).__name__:
        error_code = "SERVICE_UNAVAILABLE"
        suggestion = "External service is temporarily unavailable. Please try again later"
    elif "ValidationError" in type(exc).__name__:
        error_code = "VALIDATION_ERROR"
        suggestion = "Please check your request parameters"

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code,
            message=str(exc) if str(exc) else "An unexpected error occurred",
            request_id=request_id,
            suggestion=suggestion,
            details={"type": type(exc).__name__}
        ),
    )


# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the Recherche-Kompass HTML interface at root."""
    # Load the HTML file
    html_file = Path(__file__).parent / "static" / "research-compass.html"
    html_content = html_file.read_text(encoding="utf-8")

    # Inject CSP meta tag after <head> opening tag
    csp_meta_tag = settings.csp_meta_tag
    html_content = html_content.replace("<head>", f"<head>\n    {csp_meta_tag}", 1)

    return HTMLResponse(content=html_content)


@app.get("/api", include_in_schema=False)
async def api_info():
    """API information endpoint."""
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "api_prefix": settings.api_prefix,
        "supported_versions": settings.supported_versions
    }


@app.get("/api/config", include_in_schema=False)
async def get_config():
    """Frontend configuration endpoint for instance-specific settings."""
    return {
        "vufind_base_url": settings.vufind_base_url,
        "csp_vufind_domain": settings.csp_vufind_domain,
        "csp_institution_domain": settings.csp_institution_domain,
        "api_prefix": settings.api_prefix,
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and frontend integration.

    Returns the overall status of the API and individual service health.
    """
    # Get current service instances using getter functions
    current_milvus_service = get_milvus_service()
    current_vufind_service = get_vufind_service()
    current_transformation_service = get_transformation_service()

    # Check individual service health
    services: dict[str, dict[str, str]] = {}
    overall_status = "healthy"

    # Check Milvus service
    if current_milvus_service is not None:
        try:
            # Milvus service is initialized and ready
            services["milvus"] = {
                "status": "ok",
                "message": "Milvus vector database service is operational"
            }
        except Exception as e:
            services["milvus"] = {
                "status": "error",
                "message": f"Milvus service error: {str(e)}"
            }
            overall_status = "degraded"
    else:
        services["milvus"] = {
            "status": "not_initialized",
            "message": "Milvus service not initialized"
        }
        overall_status = "degraded"

    # Check VuFind service
    if current_vufind_service is not None:
        try:
            # VuFind service is initialized
            services["vufind"] = {
                "status": "ok",
                "message": "VuFind integration service is operational"
            }
        except Exception as e:
            services["vufind"] = {
                "status": "error",
                "message": f"VuFind service error: {str(e)}"
            }
            overall_status = "degraded"
    else:
        services["vufind"] = {
            "status": "not_initialized",
            "message": "VuFind service not initialized"
        }
        overall_status = "degraded"

    # Check Transformation service
    if current_transformation_service is not None:
        try:
            # Transformation service is initialized
            services["transformation"] = {
                "status": "ok",
                "message": "Query Transformation service is operational"
            }
        except Exception as e:
            services["transformation"] = {
                "status": "error",
                "message": f"Query Transformation service error: {str(e)}"
            }
            overall_status = "degraded"
    else:
        services["transformation"] = {
            "status": "not_initialized",
            "message": "Query Transformation service not initialized"
        }
        overall_status = "degraded"

    return {
        "status": overall_status,
        "version": settings.api_version,
        "supported_versions": settings.supported_versions,
        "services": services,
        "timestamp": datetime.now().isoformat()
    }


# =============================================================================
# RESEARCH COMPASS ENDPOINTS
# =============================================================================

@app.get("/research-compass")
async def serve_research_compass():
    """Redirect to root for backward compatibility."""
    from fastapi.responses import RedirectResponse
    redirect_url = settings.root_path
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)


@app.get("/static/{filepath:path}", include_in_schema=False)
async def serve_static_file(filepath: str):
    """Serve any static file from the static directory."""
    static_dir = Path(__file__).parent / "static"
    file_path = static_dir / filepath

    # Security: prevent directory traversal - ensure file is within static directory
    try:
        file_path.resolve().relative_to(static_dir.resolve())
    except ValueError:
        return Response(content="Access denied", status_code=403)

    if not file_path.exists() or not file_path.is_file():
        return Response(content="File not found", status_code=404)

    # Determine media type
    media_types = {
        '.svg': 'image/svg+xml',
        '.png': 'image/png',
        '.ico': 'image/x-icon',
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.html': 'text/html',
    }
    media_type = media_types.get(file_path.suffix, 'application/octet-stream')

    return Response(content=file_path.read_bytes(), media_type=media_type)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        root_path=settings.root_path,
    )
