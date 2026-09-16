"""add is_saved/is_active/label to resume_profiles

Revision ID: e81d923c3ebe
Revises: 19fe6baa1742
Create Date: 2026-09-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
"""add is_saved/is_active/label to resume_profiles

Revision ID: e81d923c3ebe
Revises: 19fe6baa1742
Create Date: 2026-09-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e81d923c3ebe'
down_revision: Union[str, None] = '19fe6baa1742'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # is_saved: 사용자가 "저장" 버튼을 눌렀는지 여부. False인 행은 분석 시도
    #   기록일 뿐, 저장된 이력서 목록/적합도 계산 대상에서 제외된다.
    # is_active: 저장된 이력서 중 "지금 매칭에 쓸 것"으로 지정된 단 하나.
    #   나중에 만들 자동 매칭 에이전트도 이 값만 보고 동작하게 할 예정이라 지금부터
    #   기준을 통일해둔다.
    # label: 사용자가 붙이는 구분용 이름 (선택 입력, 예: "백엔드용 이력서").
    op.add_column('resume_profiles', sa.Column('is_saved', sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column('resume_profiles', sa.Column('is_active', sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column('resume_profiles', sa.Column('label', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('resume_profiles', 'label')
    op.drop_column('resume_profiles', 'is_active')
    op.drop_column('resume_profiles', 'is_saved')