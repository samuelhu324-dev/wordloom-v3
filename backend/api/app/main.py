"""
Wordloom API - Main Application Entry Point
最小化版本 - 用于快速启动

NOTE: Event loop policy should already be set by the launcher script (run_backend.py)
before this module is imported!
"""

import sys
import os

# ---------------------------------------------------------------------------
# Windows async event loop compatibility
# ---------------------------------------------------------------------------
# psycopg async cannot run on ProactorEventLoop. Force Selector policy.
if sys.platform.startswith("win"):
    try:
        import asyncio

        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

# ============================================================================
# NOW safe to do regular imports
# ============================================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response
import logging
from pathlib import Path

from api.app.config.logging_config import setup_logging

# Setup logging first (before any other imports)
setup_logging()

from api.app.middlewares.payload_metrics import PayloadMetricsMiddleware

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

# =========================================================================
# Tracing (OpenTelemetry) - opt-in
# =========================================================================

try:
    from infra.observability.tracing import setup_tracing, instrument_httpx

    _tracing_enabled = setup_tracing(default_service_name="wordloom-api")
    if _tracing_enabled:
        instrument_httpx()
        logger.info({"event": "tracing.enabled", "layer": "startup"})
    else:
        logger.info({"event": "tracing.disabled", "layer": "startup"})
except Exception as _tracing_exc:  # noqa: BLE001
    logger.warning({"event": "tracing.setup_failed", "error": str(_tracing_exc)})

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

try:
    from infra.observability.tracing import instrument_fastapi

    instrument_fastapi(app)
except Exception as _instr_exc:  # noqa: BLE001
    logger.warning({"event": "tracing.fastapi_instrument_failed", "error": str(_instr_exc)})

# =========================================================================
# Observability Middleware
# =========================================================================

app.add_middleware(PayloadMetricsMiddleware)


@app.on_event("startup")
async def _startup_env_guard() -> None:
    # Safety fuse: refuse to start if WORDLOOM_ENV doesn't match the connected DB.
    # This prevents accidental writes to the wrong database (dev vs test).
    try:
        from infra.database.env_guard import assert_expected_database_environment
        from infra.database.session import get_session_factory

        session_factory = await get_session_factory()
        async with session_factory() as session:
            await assert_expected_database_environment(session)
        logger.info("[ENV_GUARD] Database environment check: OK")
    except Exception as exc:  # noqa: BLE001
        logger.error("[ENV_GUARD] Database environment check failed: %s", exc)
        raise

# =========================================================================
# Prometheus Metrics Endpoint
# =========================================================================

@app.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

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
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log schema validation failures (422) in a machine-readable way."""
    correlation_id = getattr(request.state, "correlation_id", None)
    errors = exc.errors()

    logger.info(
        {
            "event": "schema.validation_failed",
            "layer": "exception_handler",
            "correlation_id": correlation_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": 422,
            "error_count": len(errors),
            "errors": errors,
        }
    )

    # Keep FastAPI's default response shape for 422.
    return JSONResponse(status_code=422, content={"detail": errors})

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.exception(f"Unhandled exception: {exc}")

    trace_id = None
    try:
        from opentelemetry import trace as _otel_trace

        _span = _otel_trace.get_current_span()
        _ctx = _span.get_span_context() if _span is not None else None
        if _ctx is not None and getattr(_ctx, "is_valid", False):
            trace_id = f"{_ctx.trace_id:032x}"
    except Exception:
        trace_id = None

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__,
            "trace_id": trace_id,
        },
    )
