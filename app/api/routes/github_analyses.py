from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from github.GithubException import GithubException

from app.core.database import get_db
from app.services.user_service import get_or_create_default_user
from app.services.github_repo_fetcher import ( 
    parse_github_url,
    fetch_repository,
    fetch_repo_structure,
    fetch_readme_text,
    fetch_file_tree,
    compute_language_breakdown,
    fetch_dependency_manifests,
    fetch_source_snippets,
    _fetch_file_content,
    _is_vendor_path,
    _similar_vendor_code,
    )
from app.services.github_repo_analyzer import (
    analyze_github_repository,
    select_relevant_file_paths,
    select_paths_from_readme,
    verify_user_claim,
)
from app.models.portfolio_project import PortfolioProject
from app.models.github_repo_analysis import GithubRepoAnalysis
from app.schemas.github_analysis import GithubRepoAnalysisOut, ClaimVerificationRequest

router = APIRouter(prefix="/github-analyses", tags=["github-analyses"])

# 포트폴리오 프로젝트 1개를 분석해서 GithubRepoAnalysis에 upsert(있으면 갱신/없으면 생성)
def _analyze_and_save(db: Session, project: PortfolioProject) -> GithubRepoAnalysis:
    owner, repo, ref = parse_github_url(project.github_url)
    repository = fetch_repository(owner, repo) # 접근 가능 여부

    readme_text = fetch_readme_text(repository, ref)
    files = fetch_file_tree(repository, ref)
    languages = compute_language_breakdown(files)
    manifests = fetch_dependency_manifests(repository, files, ref)

    snippets = {}
    if readme_text:
        all_paths = [f.path for f in files if not _is_vendor_path(f.path)]
        selected_paths = select_paths_from_readme(readme_text, all_paths)
        for path in selected_paths:
            content = _fetch_file_content(repository, path, ref)
            if content is not None and not _similar_vendor_code(content):
                snippets[path] = content[:3000]

    if not snippets:
        snippets = fetch_source_snippets(repository, files, ref)

    llm_result = analyze_github_repository(readme_text, manifests, snippets)

    analysis = (db.query(GithubRepoAnalysis).filter(GithubRepoAnalysis.portfolio_project_id == project.id).first())
    if analysis is None:
        analysis = GithubRepoAnalysis(portfolio_project_id=project.id)
        db.add(analysis)

    analysis.repo_url = project.github_url
    analysis.languages = languages
    analysis.readme_summary = llm_result.readme_summary
    analysis.verified_tech = llm_result.verified_tech
    analysis.analyzed_at = func.now()

    db.commit()
    db.refresh(analysis)
    return analysis

@router.post("/analyze")
def analyze_all(db: Session = Depends(get_db)):
    user = get_or_create_default_user(db)

    # isnot(None): SQL의 "IS NOT NULL" 대비
    projects = (db.query(PortfolioProject).filter(PortfolioProject.user_id == user.id, PortfolioProject.github_url.isnot(None)).all())
    if not projects:
        raise HTTPException(status_code=422, detail="Github URL이 있는 포트폴리오 프로젝트가 없습니다.")

    results = []
    for project in projects:
        try:
            analysis = _analyze_and_save(db, project)
            results.append({
                "portfolio_project_id": project.id,
                "title": project.title,
                "status": "ok",
                "verified_tech": analysis.verified_tech,
            })
        except (ValueError, GithubException) as e:
            db.rollback()
            results.append({
                "portfolio_project_id": project.id,
                "title": project.title,
                "status": "failed",
                "detail": str(e),
            })

    return {"results": results}

@router.get("/{portfolio_project_id}", response_model=GithubRepoAnalysisOut)
def get_github_analysis(portfolio_project_id: int, db: Session = Depends(get_db)):
    analysis = (db.query(GithubRepoAnalysis).filter(GithubRepoAnalysis.portfolio_project_id == portfolio_project_id).first())
    if analysis is None:
        raise HTTPException(status_code=404, detail="해당 프로젝트의 Github 분석 결과가 없습니다.")
    return analysis

# 수동 기능 추가에 대한 분석
@router.post("/{portfolio_project_id}/verify-claim")
def verify_claim(portfolio_project_id: int, payload: ClaimVerificationRequest, db: Session = Depends(get_db)):
    project = db.query(PortfolioProject).filter(PortfolioProject.id == portfolio_project_id).first()
    if project is None or not project.github_url:
        raise HTTPException(status_code=404, detail="Github URL이 있는 포트폴리오 프로젝트를 찾을 수 없습니다.")

    owner, repo, ref = parse_github_url(project.github_url)
    try:
        repository = fetch_repository(owner, repo)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    files = fetch_file_tree(repository, ref)
    candidate_paths = [f.path for f in files if not _is_vendor_path(f.path)]

    relevant_paths = select_relevant_file_paths(payload.claim, candidate_paths)

    if not relevant_paths:
        return {
            "claim": payload.claim,
            "checked_files": [],
            "found": False,
            "tech_label": None,
            "evidence": [],
            "explanation": "기능과 관련 있어 보이는 파일을 찾지 못했습니다.",
        }

    file_contents = {}
    for path in relevant_paths:
        content = _fetch_file_content(repository, path, ref)
        if content is not None:
            file_contents[path] = content[:3000]

    result = verify_user_claim(payload.claim, file_contents)

    if result.found and result.tech_label:
        analysis = (db.query(GithubRepoAnalysis).filter(GithubRepoAnalysis.portfolio_project_id == project.id).first())
        if analysis is not None and result.tech_label not in analysis.verified_tech:
            analysis.verified_tech = analysis.verified_tech + [result.tech_label]
            db.commit()

    return {
        "claim": payload.claim,
        "checked_files": list(file_contents.keys()),
        "found": result.found,
        "tech_label": result.tech_label,
        "evidence": [e.model_dump() for e in result.evidence],
        "explanation": result.explanation,
    }