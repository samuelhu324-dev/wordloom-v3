"""
Wordloom API - Main Application Entry Point
最小化版本 - 用于快速启动

NOTE: Event loop policy should already be set by the launcher script (run_backend.py)
before this module is imported!
"""

import sys
import os

# ============================================================================
# NOW safe to do regular imports
# ============================================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from pathlib import Path

# Setup logging first (before any other imports)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

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

# ---------------------------------------------------------------------------
# Database URL Resolution (WSL2-safe)
# ---------------------------------------------------------------------------
# Avoid hardcoding ephemeral WSL2 IP (e.g., 172.31.x.x). Prefer precedence:
# 1. Existing env DATABASE_URL (e.g. from .env or process manager)
# 2. .env file inside api/ folder (backend/api/.env) if present
# 3. Fallback to localhost (works for Windows ↔ WSL2 since 2022 update)
# This prevents connection failures when WSL IP changes after restart.

def _resolve_database_url() -> str:
    # 1. Direct environment override
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        return env_url

    # 2. Try loading backend/api/.env manually (simple parse) to avoid extra deps
    env_path = Path(__file__).parent.parent / ".env"  # backend/api/.env
    if env_path.exists():
        try:
            for line in env_path.read_text().splitlines():
                if line.startswith("DATABASE_URL="):
                    return line.split("=", 1)[1].strip().strip('"')
        except Exception as e:
            logger.warning(f"Failed reading .env for DATABASE_URL: {e}")

    # 3. Fallback to localhost (assuming postgres listening on 0.0.0.0:5432)
    return "postgresql://postgres:pgpass@localhost:5432/wordloom"

os.environ["DATABASE_URL"] = _resolve_database_url()
logger.info(f"Using DATABASE_URL: {os.environ.get('DATABASE_URL')}")

# Import settings (will now use the environment variable)
from api.app.config.setting import get_settings

# Get settings to verify it's using correct database
settings = get_settings()
logger.info(f"Settings loaded with database: {settings.database_url}")

# ============================================================================
# Try to import infrastructure modules
# ============================================================================

_event_bus = None
_infra_available = False

try:
    from infra.event_bus import EventHandlerRegistry
    logger.info("EventHandlerRegistry imported successfully")
    try:
        import infra.event_bus.handlers  # noqa: F401 ensures decorator registration
        logger.info("Event handler modules imported successfully")
    except ImportError as handler_error:
        logger.warning(f"Event handler modules not fully available: {handler_error}")
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
        _routers.append((tag_router, "/api/v1/tags", ["Tags"]))
    except ImportError as e:
        logger.warning(f"Tag router not available: {e}")

    try:
        from api.app.modules.media.routers.media_router import router as media_router
        _routers.append((media_router, "/api/v1/media", ["Media"]))
    except ImportError as e:
        logger.warning(f"Media router not available: {e}")

    try:
        from api.app.modules.bookshelf.routers.bookshelf_router import router as bookshelf_router
        _routers.append((bookshelf_router, "/api/v1/bookshelves", ["Bookshelves"]))
    except ImportError as e:
        logger.warning(f"Bookshelf router not available: {e}")

    try:
        from api.app.modules.book.routers.book_router import router as book_router
        _routers.append((book_router, "/api/v1/books", ["Books"]))
    except ImportError as e:
        logger.warning(f"Book router not available: {e}")

    try:
        from api.app.modules.maturity.routers.maturity_router import router as maturity_router
        _routers.append((maturity_router, "/api/v1", ["Maturity"]))
    except ImportError as e:
        logger.warning(f"Maturity router not available: {e}")

    try:
        from api.app.modules.block.routers.block_router import router as block_router
        _routers.append((block_router, "/api/v1/blocks", ["Blocks"]))
    except ImportError as e:
        logger.warning(f"Block router not available: {e}")

    # Phase 0 minimal block router (分页 V2 + 基础 CRUD)
    try:
        from api.app.modules.block.routers.phase0_block_router import router as phase0_block_router
        _routers.append((phase0_block_router, "/api/v1", ["Blocks-Phase0"]))
    except ImportError as e:
        logger.warning(f"Phase0 block router not available: {e}")

    try:
        from api.app.modules.basement.routers.basement_router import router as basement_router
        _routers.append((basement_router, "/api/v1", ["Basement"]))
    except ImportError as e:
        logger.warning(f"Basement router not available: {e}")

    try:
        from api.app.modules.library.routers.library_router import router as library_router
        _routers.append((library_router, "/api/v1/libraries", ["Libraries"]))
    except ImportError as e:
        logger.warning(f"Library router not available: {e}")

    try:
        from api.app.modules.search.routers.search_router import router as search_router
        _routers.append((search_router, "/api/v1/search", ["Search"]))
    except ImportError as e:
        logger.warning(f"Search router not available: {e}")

    try:
        from api.app.modules.chronicle.routers.chronicle_router import router as chronicle_router
        _routers.append((chronicle_router, "/api/v1/chronicle", ["Chronicle"]))
    except ImportError as e:
        logger.warning(f"Chronicle router not available: {e}")

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

# CORS: Allow frontend to access backend API
# Both frontend and backend run on WSL2, so use localhost
# Also allow 172.31.150.143 (WSL2 IP) for cross-network access if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",        # Next.js dev default
        "http://localhost:5173",        # Vite dev default (WSL2)
        "http://127.0.0.1:3000",        # Localhost IPv4
        "http://127.0.0.1:5173",        # Localhost IPv4
        "http://172.31.150.143:3000",   # WSL2 IP access from Windows
        "http://172.31.150.143:5173",   # WSL2 IP access from Windows
        "http://localhost:30001",        # If frontend is served on 30001 (same host)
        "http://172.31.150.143:30001",  # Windows browser accessing backend via WSL2 IP
        "http://localhost:30002",        # Frontend served on 30002
        "http://127.0.0.1:30002",       # Frontend served on 30002 (IPv4)
        "http://localhost:31002",      # 新增
        "http://127.0.0.1:31002",      # 建议也加
        "http://localhost:30000",      # frontend dev alt port
        "http://127.0.0.1:30000",
        "http://localhost:31000",
        "http://127.0.0.1:31000",
    ],
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

@app.get("/api/v1/health", tags=["Health"], summary="Health check")
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

    # Run database migrations (using the shared application engine)
    try:
        logger.info("Checking database migrations...")
        from infra.database.session import get_engine
        from pathlib import Path

        # Get the application's shared engine (ensures consistency)
        engine = await get_engine()

        migration_dir = Path(__file__).parent.parent / "migrations"
        migration_files = sorted(migration_dir.glob("*.sql"))
        logger.info(f"Found {len(migration_files)} migration files")

        if migration_files:
            for mf in migration_files:
                try:
                    sql = mf.read_text(encoding="utf-8")
                    if sql.strip():
                        async with engine.begin() as conn:
                            await conn.exec_driver_sql(sql)
                        logger.info(f"✓ {mf.name}")
                except Exception as e:
                    # Ignore "already exists" errors - it's safe
                    error_str = str(e).lower()
                    if any(x in error_str for x in ["already exists", "duplicate", "not null violation"]):
                        logger.debug(f"⊘ {mf.name}: {type(e).__name__} (safe to skip)")
                    else:
                        logger.warning(f"✗ {mf.name}: {type(e).__name__}")

            logger.info("Database migration check complete")
    except Exception as e:
        logger.error(f"Error during migration: {type(e).__name__}: {e}", exc_info=True)

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
    # Cleanup database engine
    from api.app.config.database import shutdown_db
    await shutdown_db()

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
