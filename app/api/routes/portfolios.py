import io
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.services.pdf_extractor import extract_text_from_pdf
from app.services.portfolio_analyzer import analyze_portfolio_text
from app.services.user_service import get_or_create_default_user
from app.models.portfolio_project import PortfolioProject
from app.models.portfolio_version import PortfolioVersion
from app.schemas.portfolio import PortfolioVersionOut

router = APIRouter(prefix="/portfolios", tags=["portfolios"])

@router.post("/analyze")
async def analyze_portfolio(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드 할 수 있습니다.")

    contents = await file.read()

    try:
        text = extract_text_from_pdf(io.BytesIO(contents))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    extracted = analyze_portfolio_text(text)
    user = get_or_create_default_user(db)

    # 업로드할 때마다 기존 프로젝트를 지우던 방식(delete)을 버리고, 이번 업로드
    # 결과를 새 버전(PortfolioVersion) 하나로 묶어서 쌓아간다. is_saved/is_active는
    # 컬럼 기본값(false)이라, "저장하기"를 눌러야만 재사용 목록/매칭 대상이 된다.
    version = PortfolioVersion(user_id=user.id)
    db.add(version)
    db.flush()  # 아직 커밋 전이지만, 아래 프로젝트들이 참조할 version.id를 미리 받아온다.

    saved_projects = []
    for item in extracted.projects:
        project = PortfolioProject(
            user_id=user.id,
            portfolio_version_id=version.id,
            title=item.title,
            description=item.description,
            tech_stack=item.tech_stack,
            github_url=item.github_url,
        )
        db.add(project)
        saved_projects.append(project)

    db.commit()
    db.refresh(version)
    for project in saved_projects:
        db.refresh(project)

    return {
        "portfolio_version_id": version.id,
        "portfolio_project_ids": [p.id for p in saved_projects],
        "extracted": extracted.model_dump(),
    }

# --- 포트폴리오 버전 목록/저장/활성화  ---

class PortfolioVersionSaveRequest(BaseModel):
    label: Optional[str] = None

@router.get("/versions", response_model=list[PortfolioVersionOut])
def list_saved_portfolio_versions(db: Session = Depends(get_db)):
    user = get_or_create_default_user(db)
    return (
        db.query(PortfolioVersion)
        .filter(PortfolioVersion.user_id == user.id, PortfolioVersion.is_saved.is_(True))
        .order_by(PortfolioVersion.created_at.desc())
        .all()
    )

@router.get("/versions/{version_id}", response_model=PortfolioVersionOut)
def get_portfolio_version(version_id: int, db: Session = Depends(get_db)):
    version = db.get(PortfolioVersion, version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="해당 포트폴리오 버전이 없습니다.")
    return version

@router.post("/versions/{version_id}/save", response_model=PortfolioVersionOut)
def save_portfolio_version(version_id: int, payload: PortfolioVersionSaveRequest, db: Session = Depends(get_db)):
    version = db.get(PortfolioVersion, version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="해당 포트폴리오 버전이 없습니다.")

    version.is_saved = True
    version.label = payload.label

    # 이력서와 동일한 규칙
    (
        db.query(PortfolioVersion)
        .filter(PortfolioVersion.user_id == version.user_id, PortfolioVersion.id != version.id)
        .update({"is_active": False})
    )
    version.is_active = True

    db.commit()
    db.refresh(version)
    return version

@router.post("/versions/{version_id}/activate", response_model=PortfolioVersionOut)
def activate_portfolio_version(version_id: int, db: Session = Depends(get_db)):
    version = db.get(PortfolioVersion, version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="해당 포트폴리오 버전이 없습니다.")
    if not version.is_saved:
        raise HTTPException(status_code=400, detail="저장되지 않은 버전은 활성으로 지정할 수 없습니다.")

    (
        db.query(PortfolioVersion)
        .filter(PortfolioVersion.user_id == version.user_id, PortfolioVersion.id != version.id)
        .update({"is_active": False})
    )
    version.is_active = True

    db.commit()
    db.refresh(version)
    return version