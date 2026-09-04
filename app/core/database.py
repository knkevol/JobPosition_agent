# SQLAlchemy 2.0 기본 DB 연결
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import get_settings

settings = get_settings()

# 실제 DB와의 연결통로 관리. 커넥션 풀도 관리
engine = create_engine(settings.database_url)

# DB와 대화하는 대화창(세션)을 찍어내는 공장. 요청이 들어올 때마다 하나씩 새로 만들어 쓴다.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 모든 테이블이 상속받을 부모 클래스. Base를 상속받은 클래스를 모아 SQLAlchemy가 실제 테이블 구조를 파악한다.
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()