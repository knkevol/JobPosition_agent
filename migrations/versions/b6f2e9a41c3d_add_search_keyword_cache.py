"""add search_keyword_cache table

Revision ID: b6f2e9a41c3d
Revises: a4c7f0e3d9b2
Create Date: 2026-09-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'b6f2e9a41c3d'
down_revision: Union[str, None] = 'a4c7f0e3d9b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 사용자당 1행만 두는 캐시 테이블. 데일리 매칭 에이전트가 검색 키워드를 생성할 때,
    # 마지막으로 키워드를 만들었던 시점의 이력서/포트폴리오 버전과 지금 활성화된 것이
    # 같으면 LLM을 다시 부르지 않고 저장된 키워드를 재사용한다.
    op.create_table(
        'search_keyword_cache',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True),
        sa.Column('resume_id', sa.Integer(), sa.ForeignKey('resume_profiles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('portfolio_version_id', sa.Integer(), sa.ForeignKey('portfolio_versions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('keywords', postgresql.ARRAY(sa.String()), server_default='{}', nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('search_keyword_cache')