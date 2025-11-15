"""
Wordloom API - Main Application Entry Point
最小化版本 - 用于快速启动
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# ============================================================================
# Setup Python path for imports
# ============================================================================

# Add backend root and api root to path
backend_root = Path(__file__).parent.parent.parent  # backend/
api_root = Path(__file__).parent.parent  # api/
app_root = Path(__file__).parent  # app/

sys.path.insert(0, str(backend_root))  # For infra imports
sys.path.insert(0, str(api_root))  # For app imports
sys.path.insert(0, str(app_root))  # For modules imports

# ============================================================================
# Import hook for backward compatibility: redirect 'modules' to 'api.app.modules'
# ============================================================================

import importlib.abc
import importlib.machinery

class ModulesRedirectFinder(importlib.abc.MetaPathFinder):
    """Redirect 'from modules.xxx' to 'from api.app.modules.xxx'"""

    def find_spec(self, fullname, path, target=None):
        if fullname.startswith('modules.'):
            # Redirect: modules.xxx -> api.app.modules.xxx
            new_name = fullname.replace('modules.', 'api.app.modules.', 1)
            try:
                return importlib.util.find_spec(new_name)
            except (ImportError, ModuleNotFoundError, ValueError):
                pass
        return None

# Install the import hook
sys.meta_path.insert(0, ModulesRedirectFinder())

import importlib.util

# Set environment DATABASE_URL if not already set
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "postgresql+psycopg://postgres:pgpass@127.0.0.1:5433/wordloom"

# ============================================================================
# Try to import infrastructure modules
# ============================================================================

_event_bus = None
_infra_available = False

try:
    from infra.event_bus import EventHandlerRegistry
    logger.info("EventHandlerRegistry imported successfully")
    _infra_available = True
except ImportError as e:
    logger.warning(f"Infrastructure modules not available: {e}")
    _infra_available = False

# ============================================================================
# Try to import routers
# ============================================================================

_routers = []

if _infra_available:
    try:
        from api.app.modules.tag.routers.tag_router import router as tag_router
        _routers.append((tag_router, "/api/tags", ["Tags"]))
    except ImportError as e:
        logger.warning(f"Tag router not available: {e}")

    try:
        from api.app.modules.media.routers.media_router import router as media_router
        _routers.append((media_router, "/api/media", ["Media"]))
    except ImportError as e:
        logger.warning(f"Media router not available: {e}")

    try:
        from api.app.modules.bookshelf.routers.bookshelf_router import router as bookshelf_router
        _routers.append((bookshelf_router, "/api/bookshelves", ["Bookshelves"]))
    except ImportError as e:
        logger.warning(f"Bookshelf router not available: {e}")

    try:
        from api.app.modules.book.routers.book_router import router as book_router
        _routers.append((book_router, "/api/books", ["Books"]))
    except ImportError as e:
        logger.warning(f"Book router not available: {e}")

    try:
        from api.app.modules.block.routers.block_router import router as block_router
        _routers.append((block_router, "/api/blocks", ["Blocks"]))
    except ImportError as e:
        logger.warning(f"Block router not available: {e}")

    try:
        from api.app.modules.library.routers.library_router import router as library_router
        _routers.append((library_router, "/api/libraries", ["Libraries"]))
    except ImportError as e:
        logger.warning(f"Library router not available: {e}")

    try:
        from api.app.modules.search.routers.search_router import router as search_router
        _routers.append((search_router, "/api/search", ["Search"]))
    except ImportError as e:
        logger.warning(f"Search router not available: {e}")

# ============================================================================
# Create FastAPI Application
# ============================================================================

app = FastAPI(
    title="Wordloom API",
    description="Book Management System with Hexagonal Architecture",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ============================================================================
# CORS Middleware
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Register Routers
# ============================================================================

for router, prefix, tags in _routers:
    app.include_router(
        router,
        prefix=prefix,
        tags=tags,
    )

# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.get("/health", tags=["Health"], summary="Health check")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "infrastructure_available": _infra_available,
        "routers_loaded": len(_routers),
    }

# ============================================================================
# Root Endpoint
# ============================================================================

@app.get("/", tags=["Root"], summary="API root")
async def root():
    """API root endpoint"""
    return {
        "message": "Welcome to Wordloom API",
        "docs": "/docs",
        "version": "1.0.0",
    }

# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup():
    """Startup event"""
    logger.info("Wordloom API startup")
    if _infra_available:
        try:
            from infra.event_bus import EventHandlerRegistry
            EventHandlerRegistry.bootstrap()
            logger.info("EventBus handlers bootstrap complete")
        except Exception as e:
            logger.error(f"Failed to bootstrap EventBus: {e}")
    else:
        logger.warning("API running in minimal mode - no infrastructure")

@app.on_event("shutdown")
async def shutdown():
    """Shutdown event"""
    logger.info("Wordloom API shutdown")

# ============================================================================
# Exception Handler
# ============================================================================

from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__,
        },
    )
