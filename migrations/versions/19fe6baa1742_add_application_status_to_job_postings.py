"""add application_status to job_postings

Revision ID: 19fe6baa1742
Revises: 26cbbcc0576d
Create Date: 2026-09-08 21:02:34.027856

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '19fe6baa1742'
down_revision: Union[str, None] = '26cbbcc0576d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # op.add_column에 sa.Enum(...)을 바로 쓰면 Alembic이 "타입이 이미 있겠지"라고 가정하고
    # CREATE TYPE을 생략해버린다(자동생성의 알려진 한계). 그래서 컬럼을 추가하기 전에
    # enum 타입을 먼저 직접 만들어준다. checkfirst=True: 이미 있으면 에러 없이 건너뜀
    application_status_enum = postgresql.ENUM('NOT_APPLIED', 'APPLIED', name='application_status')
    application_status_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        'job_postings',
        sa.Column(
            'application_status',
            application_status_enum,
            server_default='NOT_APPLIED',
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column('job_postings', 'application_status')
    # 컬럼을 지운 뒤엔 enum 타입도 같이 정리해야 완전히 원상복구됨
    postgresql.ENUM(name='application_status').drop(op.get_bind(), checkfirst=True)