"""
Momentum Engine - FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import time

from momentum_engine.config import settings
from momentum_engine.database.connection import init_db, close_db
from momentum_engine.shared.exceptions import MomentumEngineException

# Import routers
from momentum_engine.modules.navigator.router import router as navigator_router
from momentum_engine.modules.gamification.router import router as gamification_router
from momentum_engine.modules.analytics.router import router as analytics_router
from momentum_engine.modules.laims.router import router as laims_router
from momentum_engine.modules.pods.router import router as pods_router

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - startup and shutdown events."""
    # Startup
    logger.info("Starting Momentum Engine", env=settings.app_env)
    await init_db()
    logger.info("Database connection established")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Momentum Engine")
    await close_db()
    logger.info("Database connection closed")


# Create FastAPI application
app = FastAPI(
    title="Momentum Engine API",
    description="AI-Powered IELTS Engagement Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS Middleware - Allow all origins for now (frontend on Vercel, backend on Railway)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    """Add request timing and correlation ID."""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time-Ms"] = str(int(process_time))
    
    # Log slow requests
    if process_time > settings.slow_query_threshold_ms:
        logger.warning(
            "Slow request detected",
            path=request.url.path,
            method=request.method,
            duration_ms=process_time
        )
    
    return response


# Exception handlers
@app.exception_handler(MomentumEngineException)
async def momentum_exception_handler(request: Request, exc: MomentumEngineException):
    """Handle custom application exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "code": exc.error_code}
    )


# Health check
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for load balancers."""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint."""
    return {
        "name": "Momentum Engine API",
        "version": "1.0.0",
        "docs": "/docs" if settings.debug else "disabled"
    }


@app.post("/api/seed", tags=["Admin"])
async def seed_database():
    """Seed database with demo data."""
    from momentum_engine.database.connection import async_session_maker
    from momentum_engine.database.models import Track, Task, Competition
    from sqlalchemy import select, func
    from datetime import datetime, timedelta, date
    import uuid
    
    try:
        async with async_session_maker() as session:
            # Check if already seeded
            result = await session.execute(
                select(func.count()).select_from(Track)
            )
            count = result.scalar()
            if count and count > 0:
                return {"message": "Database already seeded", "tracks": count}
            
            # Create demo tracks
            tracks = [
                Track(
                    id=str(uuid.uuid4()),
                    name="Beginner",
                    duration_weeks=8,
                    daily_minutes=30,
                    tasks_per_day=3,
                    focus="Foundation building for first-time test takers",
                    description="Perfect for first-time test takers. Build your foundation with essential skills.",
                    created_at=datetime.utcnow()
                ),
                Track(
                    id=str(uuid.uuid4()),
                    name="Intermediate",
                    duration_weeks=6,
                    daily_minutes=45,
                    tasks_per_day=4,
                    focus="Skill strengthening for Band 6.5-7.0",
                    description="Strengthen your skills and aim for Band 6.5-7.0",
                    created_at=datetime.utcnow()
                ),
                Track(
                    id=str(uuid.uuid4()),
                    name="Advanced",
                    duration_weeks=4,
                    daily_minutes=60,
                    tasks_per_day=5,
                    focus="Master advanced techniques for Band 7.5+",
                    description="Master advanced techniques for high scorers.",
                    created_at=datetime.utcnow()
                ),
            ]
            
            for track in tracks:
                session.add(track)
            
            # Create tasks for each track
            task_templates = [
                {"type": "reading", "title": "Academic Reading Practice", "difficulty": "medium", "duration": 60},
                {"type": "writing", "title": "Task 2 Essay Writing", "difficulty": "medium", "duration": 40},
                {"type": "listening", "title": "Section 1-4 Practice", "difficulty": "easy", "duration": 30},
                {"type": "speaking", "title": "Part 2 Cue Card Practice", "difficulty": "hard", "duration": 15},
            ]
            
            for track in tracks:
                for i, template in enumerate(task_templates):
                    task = Task(
                        id=str(uuid.uuid4()),
                        track_id=track.id,
                        type=template["type"],
                        title=template["title"],
                        description=f"Practice {template['type']} skills with guided exercises",
                        difficulty=template["difficulty"],
                        estimated_minutes=template["duration"],
                        order_in_track=i + 1,
                        created_at=datetime.utcnow()
                    )
                    session.add(task)
            
            # Create demo competition
            competition = Competition(
                id=str(uuid.uuid4()),
                type="L-AIMS",
                name="Weekly L-AIMS Challenge",
                start_date=date.today(),
                end_date=date.today() + timedelta(days=7),
                status="active",
                created_at=datetime.utcnow()
            )
            session.add(competition)
            
            await session.commit()
            
            return {"message": "Database seeded successfully", "tracks": len(tracks), "tasks": len(tracks) * len(task_templates)}
    except Exception as e:
        return {"error": str(e)}


# Register module routers
app.include_router(navigator_router, prefix="/api", tags=["Navigator"])
app.include_router(gamification_router, prefix="/api", tags=["Gamification"])
app.include_router(analytics_router, prefix="/api", tags=["Analytics"])
app.include_router(laims_router, prefix="/api", tags=["L-AIMS"])
app.include_router(pods_router, prefix="/api", tags=["Pods"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "momentum_engine.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
