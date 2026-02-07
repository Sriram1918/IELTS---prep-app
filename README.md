# Momentum Engine

AI-Powered IELTS Engagement Platform

## Quick Start

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Edit .env with your API keys
# ANTHROPIC_API_KEY=your-key

# 3. Start services
docker-compose up -d

# 4. Run migrations
docker-compose exec backend alembic upgrade head

# 5. Seed database
docker-compose exec backend python scripts/seed_database.py

# 6. Access API
# http://localhost:8000/docs
```

## Project Structure

```
momentum_engine/
├── main.py                 # FastAPI entry point
├── config.py               # Pydantic settings
├── database/
│   ├── connection.py       # PostgreSQL + Redis
│   └── models.py           # SQLAlchemy ORM
├── modules/
│   ├── navigator/          # Track assignment, daily planning
│   ├── gamification/       # Streaks, cohorts, leaderboards
│   ├── analytics/          # LVS, MACR, progress
│   └── laims/              # Mock tests, competitions
└── workers/
    └── tasks/              # Celery background jobs
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/onboarding/diagnostic` | Complete diagnostic, assign track |
| `GET /api/dashboard/{user_id}` | Daily dashboard |
| `GET /api/streaks/{user_id}` | Streak info |
| `GET /api/cohorts/{user_id}/ghost-data` | Peer comparisons |
| `GET /api/analytics/{user_id}/metrics` | LVS, MACR |
| `POST /api/laims/competitions/{id}/submit` | Submit mock test |

## Architecture

- **Backend**: FastAPI + SQLAlchemy 2.0
- **Database**: PostgreSQL 15+
- **Cache**: Redis 7+
- **Workers**: Celery + Redis
- **AI**: Claude (Haiku T2, Sonnet T3)

## Documentation

- [Implementation Plan](docs/implementation_plan.md)
- [Track Definitions](docs/tracks_definition.md)
- [Cohort Matching](docs/cohort_matching.md)
- [AI Integration](docs/ai_integration_specification.md)
