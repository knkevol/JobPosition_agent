import io

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.pdf_extractor import extract_text_from_pdf
from app.services.portfolio_analyzer import analyze_portfolio_text
from app.services.user_service import get_or_create_default_user
from app.models.portfolio_project import PortfolioProject

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

    db.query(PortfolioProject).filter(PortfolioProject.user_id == user.id).delete()

    saved_projects = []
    for item in extracted.projects:
        project = PortfolioProject(
            user_id=user.id,
            title=item.title,
            description=item.description,
            tech_stack=item.tech_stack,
            github_url=item.github_url,
        )
        db.add(project)
        saved_projects.append(project)

    db.commit()
    for project in saved_projects:
        db.refresh(project)

    return {
        "portfolio_project_ids": [p.id for p in saved_projects],
        "extracted": extracted.model_dump(),
    }