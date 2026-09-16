"""add portfolio_versions table and portfolio_version_id to portfolio_projects

Revision ID: a4c7f0e3d9b2
Revises: e81d923c3ebe
Create Date: 2026-09-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a4c7f0e3d9b2'
down_revision: Union[str, None] = 'e81d923c3ebe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # portfolio_versions: "포트폴리오 업로드 한 번"을 하나의 묶음(버전)으로 표현하는 테이블.
    # 이력서의 is_saved/is_active/label과 똑같은 의미를 버전 단위로 갖는다 —
    # 이 버전에 속한 프로젝트 여러 개가 통째로 저장되거나 활성화된다.
    op.create_table(
        'portfolio_versions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('is_saved', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('label', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # portfolio_projects가 어느 버전에 속하는지 표시할 FK. 기존 행이 있을 수 있어서
    # 일단 nullable로 추가 → 값을 채운 다음 → NOT NULL로 잠근다.
    op.add_column(
        'portfolio_projects',
        sa.Column('portfolio_version_id', sa.Integer(), sa.ForeignKey('portfolio_versions.id', ondelete='CASCADE'), nullable=True),
    )

    # 백필: 이 마이그레이션 이전엔 "재업로드 = 기존 프로젝트 전체 삭제 후 새로 생성"
    # 방식이었으므로, 한 사용자가 지금 갖고 있는 portfolio_projects는 전부 같은
    # 업로드 결과(=하나의 버전)였다고 봐도 무방하다. 그래서 사용자당 미저장
    # (is_saved=false) 버전을 하나씩 만들어서 기존 행들을 그 버전에 묶어준다.
    op.execute(
        """
        INSERT INTO portfolio_versions (user_id, is_saved, is_active, created_at)
        SELECT DISTINCT user_id, false, false, now()
        FROM portfolio_projects
        """
    )
    op.execute(
        """
        UPDATE portfolio_projects AS pp
        SET portfolio_version_id = pv.id
        FROM portfolio_versions AS pv
        WHERE pv.user_id = pp.user_id
          AND pp.portfolio_version_id IS NULL
        """
    )

    op.alter_column('portfolio_projects', 'portfolio_version_id', nullable=False)


def downgrade() -> None:
    op.drop_column('portfolio_projects', 'portfolio_version_id')
    op.drop_table('portfolio_versions')