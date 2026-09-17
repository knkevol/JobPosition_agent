"""add exclude_keyword to user_feedbacks and last_liked_feedback_id to search_keyword_cache

Revision ID: f7c1a9d4b3e2
Revises: b6f2e9a41c3d
Create Date: 2026-09-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f7c1a9d4b3e2'
down_revision: Union[str, None] = 'b6f2e9a41c3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 제외(❌) 피드백에 선택적으로 남기는 사유 키워드.
    op.add_column('user_feedbacks', sa.Column('exclude_keyword', sa.String(length=255), nullable=True))

    # 검색 키워드를 마지막으로 생성했을 때 반영했던 "관심(❤️)" 피드백 중 가장 최신 것의 id.
    op.add_column('search_keyword_cache', sa.Column('last_liked_feedback_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('search_keyword_cache', 'last_liked_feedback_id')
    op.drop_column('user_feedbacks', 'exclude_keyword')