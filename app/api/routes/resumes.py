import io
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.services.pdf_extractor import extract_text_from_pdf
from app.services.resume_analyzer import analyze_resume_text
from app.services.user_service import get_or_create_default_user
from app.models.resume_profile import ResumeProfile
from app.schemas.resume import ResumeProfileOut, ResumeProfileUpdate

router = APIRouter(prefix="/resumes", tags=["resumes"])

@router.post("/extract-text")
async def extract_resume_text(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드 할 수 있습니다.")

    contents = await file.read()

    try:
        text = extract_text_from_pdf(io.BytesIO(contents))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return {"filename": file.filename, "extracted_text": text}

@router.post("/analyze")
# b: Session = Depends(get_db) : FastAPI가 요청이 들어올 때마다 자동으로 get_db() 실행해 세션 생성 후 이 함수에 넘겨주고 끝나면 알아서 세션 닫음
async def analyze_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드 할 수 있습니다.")

    contents = await file.read()

    try:
        text = extract_text_from_pdf(io.BytesIO(contents))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    extracted = analyze_resume_text(text)
    user = get_or_create_default_user(db)

    profile = ResumeProfile(
        user_id=user.id,
        skills=extracted.skills,
        experience=[item.model_dump() for item in extracted.experience],
        education=[item.model_dump() for item in extracted.education],
        self_reported_tech=extracted.self_reported_tech,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    return {
        "resume_profile_id": profile.id,
        "extracted": extracted.model_dump(),
    }

# --- 이력서 목록/저장/활성화 ---
class ResumeSaveRequest(BaseModel):
    # 저장할 때 구분용 이름을 붙일 수 있게 한다. Default = None
    label: Optional[str] = None

@router.get("", response_model=list[ResumeProfileOut])
def list_saved_resumes(db: Session = Depends(get_db)):
    user = get_or_create_default_user(db)
    return (
        db.query(ResumeProfile)
        .filter(ResumeProfile.user_id == user.id, ResumeProfile.is_saved.is_(True))
        .order_by(ResumeProfile.created_at.desc())
        .all()
    )

@router.post("/{resume_id}/save", response_model=ResumeProfileOut)
def save_resume(resume_id: int, payload: ResumeSaveRequest, db: Session = Depends(get_db)):
    profile = db.get(ResumeProfile, resume_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="해당 이력서 분석 결과가 없습니다.")

    profile.is_saved = True
    profile.label = payload.label

    # 저장 -> 활성, 활성화된 이력서는 1개
    (
        db.query(ResumeProfile)
        .filter(ResumeProfile.user_id == profile.user_id, ResumeProfile.id != profile.id)
        .update({"is_active": False})
    )
    profile.is_active = True

    db.commit()
    db.refresh(profile)
    return profile

@router.post("/{resume_id}/activate", response_model=ResumeProfileOut)
def activate_resume(resume_id: int, db: Session = Depends(get_db)):
    profile = db.get(ResumeProfile, resume_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="해당 이력서 분석 결과가 없습니다.")
    if not profile.is_saved:
        raise HTTPException(status_code=400, detail="저장되지 않은 이력서는 활성으로 지정할 수 없습니다.")

    (
        db.query(ResumeProfile)
        .filter(ResumeProfile.user_id == profile.user_id, ResumeProfile.id != profile.id)
        .update({"is_active": False})
    )
    profile.is_active = True

    db.commit()
    db.refresh(profile)
    return profile
    
@router.get("/{resume_id}", response_model=ResumeProfileOut)
def get_resume(resume_id: int, db: Session = Depends(get_db)):
    profile = db.get(ResumeProfile, resume_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="해당 이력서 분석 결과가 없습니다.")
    return profile

@router.patch("/{resume_id}", response_model=ResumeProfileOut)
def update_resume(resume_id: int, payload: ResumeProfileUpdate, db: Session = Depends(get_db)):
    profile = db.get(ResumeProfile, resume_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="해당 이력서 분석 결과가 없습니다.")

    # exclude_unset=True : 요청 JSON에 포함된 필드만 dict로 뽑아 나머지가 None이 되지 않게 함
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile