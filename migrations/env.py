import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# alembic 명령을 어느 위치에서 실행하든 app 패키지를 확실히 찾을 수 있도록,
# 현재 작업 폴더(프로젝트 루트)를 파이썬이 모듈을 찾는 경로에 추가
sys.path.insert(0, os.getcwd())

from app.core.config import get_settings
from app.core.database import Base
# app.models의 모든 모델을 import해서 Base.metadata에 등록시킴 (autogenerate가 인식하려면 필요)
from app.models import *  # noqa: F401,F403

config = context.config

# alembic.ini에 적힌 접속정보 대신, 우리 .env에서 읽은 실제 DATABASE_URL로 덮어씀
config.set_main_option("sqlalchemy.url", get_settings().database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# autogenerate가 "코드의 모델 구조"와 "실제 DB 구조"를 비교할 때 기준이 되는 정보
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    # DB에 직접 연결하지 않고 SQL 문자열만 출력하는 모드 (우리는 안 씀, 표준 템플릿이라 남겨둠)
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # 실제 DB에 연결해서 마이그레이션을 적용하는, 우리가 실제로 쓰는 모드
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()