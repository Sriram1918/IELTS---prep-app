"""
Database Connection Management
PostgreSQL async connection with SQLAlchemy 2.0
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.orm import DeclarativeBase
import redis.asyncio as redis
import structlog

from momentum_engine.config import settings

logger = structlog.get_logger()


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""
    pass


# PostgreSQL async engine
engine: AsyncEngine = create_async_engine(
    settings.async_database_url,
    pool_size=settings.postgres_pool_size,
    max_overflow=settings.postgres_max_overflow,
    echo=settings.debug,
    pool_pre_ping=True,  # Verify connections before use
)

# Async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Redis connection pool
redis_pool: redis.ConnectionPool = None
redis_client: redis.Redis = None


async def init_db():
    """Initialize database connections."""
    global redis_pool, redis_client
    
    # Initialize Redis
    redis_pool = redis.ConnectionPool.from_url(
        settings.redis_connection_url,
        decode_responses=True,
        socket_timeout=settings.redis_connection_timeout_ms / 1000,
    )
    redis_client = redis.Redis(connection_pool=redis_pool)
    
    # Test Redis connection
    try:
        await redis_client.ping()
        logger.info("Redis connection established")
    except redis.ConnectionError as e:
        logger.warning("Redis connection failed, will use PostgreSQL fallback", error=str(e))
    
    logger.info("Database initialization complete")


async def close_db():
    """Close database connections."""
    global redis_client, redis_pool
    
    if redis_client:
        await redis_client.close()
    if redis_pool:
        await redis_pool.disconnect()
    
    await engine.dispose()
    logger.info("Database connections closed")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    
    Usage:
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_redis() -> redis.Redis:
    """
    Dependency to get Redis client.
    
    Usage:
        @router.get("/cache")
        async def get_cached(redis: Redis = Depends(get_redis)):
            ...
    """
    if redis_client is None:
        raise RuntimeError("Redis not initialized")
    return redis_client


# Export for Alembic migrations
def get_sync_engine():
    """Get sync engine URL for Alembic."""
    from sqlalchemy import create_engine
    return create_engine(settings.sync_database_url)
