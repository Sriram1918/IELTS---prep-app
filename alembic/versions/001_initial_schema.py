"""Initial schema - all tables

Revision ID: 001_initial_schema
Revises: 
Create Date: 2024-02-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === Core Tables ===
    
    # Tracks table
    op.create_table(
        'tracks',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('name', sa.String(50), unique=True, nullable=False),
        sa.Column('duration_weeks', sa.Integer, nullable=False),
        sa.Column('daily_minutes', sa.Integer, nullable=False),
        sa.Column('tasks_per_day', sa.Integer, nullable=False),
        sa.Column('focus', sa.Text, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    
    # Cohorts table
    op.create_table(
        'cohorts',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('cohort_key', sa.String(100), unique=True, nullable=False),
        sa.Column('skill_tier', sa.Numeric(2, 1), nullable=False),
        sa.Column('velocity_tier', sa.String(20), nullable=False),
        sa.Column('member_count', sa.Integer, default=0),
        sa.Column('active_member_count', sa.Integer, default=0),
        sa.Column('avg_tasks_per_week', sa.Numeric(5, 2)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )
    
    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('diagnostic_score', sa.Numeric(2, 1), nullable=False),
        sa.Column('current_track', sa.String(50), nullable=False),
        sa.Column('exam_date', sa.Date, nullable=False),
        sa.Column('tasks_completed', sa.Integer, default=0),
        sa.Column('total_practice_time', sa.Integer, default=0),
        sa.Column('current_streak', sa.Integer, default=0),
        sa.Column('longest_streak', sa.Integer, default=0),
        sa.Column('predicted_band', sa.Numeric(2, 1)),
        sa.Column('cohort_id', postgresql.UUID(as_uuid=False), sa.ForeignKey('cohorts.id')),
        sa.Column('rank', sa.Integer),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('idx_users_cohort', 'users', ['cohort_id'])
    op.create_index('idx_users_rank', 'users', ['rank'], postgresql_where=sa.text('rank IS NOT NULL'))
    
    # Tasks table
    op.create_table(
        'tasks',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('track_id', postgresql.UUID(as_uuid=False), sa.ForeignKey('tracks.id')),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('difficulty', sa.String(20), nullable=False),
        sa.Column('estimated_minutes', sa.Integer, nullable=False),
        sa.Column('order_in_track', sa.Integer, nullable=False),
        sa.Column('content_url', sa.Text),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    
    # User Progress table
    op.create_table(
        'user_progress',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=False), sa.ForeignKey('tasks.id')),
        sa.Column('completed_at', sa.DateTime, nullable=False),
        sa.Column('accuracy_score', sa.Integer),
        sa.Column('time_spent_minutes', sa.Integer),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('idx_user_progress_user', 'user_progress', ['user_id', 'completed_at'])
    
    # Streaks table
    op.create_table(
        'streaks',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('current_streak', sa.Integer, default=0),
        sa.Column('longest_streak', sa.Integer, default=0),
        sa.Column('last_activity_date', sa.Date),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )
    
    # === Competitions & Leaderboards ===
    
    # Competitions table
    op.create_table(
        'competitions',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date, nullable=False),
        sa.Column('status', sa.String(20), default='upcoming'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    
    # Leaderboard Entries table
    op.create_table(
        'leaderboard_entries',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('competition_id', postgresql.UUID(as_uuid=False), sa.ForeignKey('competitions.id')),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), sa.ForeignKey('users.id')),
        sa.Column('score', sa.Numeric(3, 1), nullable=False),
        sa.Column('rank', sa.Integer),
        sa.Column('module_scores', postgresql.JSONB),
        sa.Column('submitted_at', sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('competition_id', 'user_id'),
    )
    op.create_index('idx_leaderboard_competition', 'leaderboard_entries', ['competition_id', 'rank'])
    
    # === Analytics & Metrics ===
    
    # User Metrics table
    op.create_table(
        'user_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.Date, nullable=False),
        sa.Column('lvs', sa.Numeric(5, 3)),
        sa.Column('macr', sa.Numeric(5, 2)),
        sa.Column('crc', sa.Numeric(5, 3)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('user_id', 'date'),
    )
    
    # === Ghost Data ===
    
    # Ghost Benchmarks (historical)
    op.create_table(
        'ghost_benchmarks',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('target_band', sa.Numeric(2, 1), nullable=False),
        sa.Column('starting_skill', sa.Numeric(2, 1), nullable=False),
        sa.Column('day_number', sa.Integer, nullable=False),
        sa.Column('avg_tasks_completed', sa.Integer),
        sa.Column('avg_practice_minutes', sa.Integer),
        sa.Column('avg_speaking_tasks', sa.Integer),
        sa.Column('avg_writing_tasks', sa.Integer),
        sa.Column('avg_reading_tasks', sa.Integer),
        sa.Column('avg_listening_tasks', sa.Integer),
        sa.Column('success_percentile', sa.Integer),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    
    # Cohort Ghost Data (real-time)
    op.create_table(
        'cohort_ghost_data',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('cohort_id', postgresql.UUID(as_uuid=False), sa.ForeignKey('cohorts.id')),
        sa.Column('snapshot_date', sa.Date, nullable=False),
        sa.Column('avg_tasks_completed', sa.Numeric(5, 2)),
        sa.Column('avg_practice_minutes', sa.Numeric(7, 2)),
        sa.Column('median_streak', sa.Integer),
        sa.Column('active_member_count', sa.Integer),
        sa.Column('top_10_percent_tasks', sa.Integer),
        sa.Column('top_25_percent_tasks', sa.Integer),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('cohort_id', 'snapshot_date'),
    )
    op.create_index('idx_cohort_ghost_date', 'cohort_ghost_data', ['cohort_id', 'snapshot_date'])
    
    # === AI Cost Tracking ===
    
    # AI Usage Logs
    op.create_table(
        'ai_usage_logs',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('tier', sa.Integer, nullable=False),
        sa.Column('operation', sa.String(50), nullable=False),
        sa.Column('model', sa.String(50)),
        sa.Column('tokens_input', sa.Integer),
        sa.Column('tokens_output', sa.Integer),
        sa.Column('tokens_total', sa.Integer),
        sa.Column('cost_usd', sa.Numeric(10, 6)),
        sa.Column('latency_ms', sa.Integer),
        sa.Column('success', sa.Boolean, default=True),
        sa.Column('error_message', sa.Text),
        sa.Column('timestamp', sa.DateTime, server_default=sa.func.now()),
        sa.CheckConstraint('tier IN (2, 3)', name='check_ai_tier'),
    )
    op.create_index('idx_ai_cost_user_date', 'ai_usage_logs', ['user_id', 'timestamp'])
    op.create_index('idx_ai_cost_tier', 'ai_usage_logs', ['tier', 'timestamp'])
    
    # User AI Budgets
    op.create_table(
        'user_ai_budgets',
        sa.Column('user_id', postgresql.UUID(as_uuid=False), sa.ForeignKey('users.id'), primary_key=True),
        sa.Column('monthly_budget_usd', sa.Numeric(6, 2), default=0.50),
        sa.Column('current_month_spend', sa.Numeric(6, 2), default=0.00),
        sa.Column('total_lifetime_spend', sa.Numeric(10, 2), default=0.00),
        sa.Column('tier3_calls_this_week', sa.Integer, default=0),
        sa.Column('last_tier3_call', sa.DateTime),
        sa.Column('budget_exceeded', sa.Boolean, default=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_table('user_ai_budgets')
    op.drop_table('ai_usage_logs')
    op.drop_table('cohort_ghost_data')
    op.drop_table('ghost_benchmarks')
    op.drop_table('user_metrics')
    op.drop_table('leaderboard_entries')
    op.drop_table('competitions')
    op.drop_table('streaks')
    op.drop_table('user_progress')
    op.drop_table('tasks')
    op.drop_table('users')
    op.drop_table('cohorts')
    op.drop_table('tracks')
