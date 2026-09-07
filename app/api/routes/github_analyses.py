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
    )
from app.services.github_repo_analyzer import analyze_github_repository
from app.models.portfolio_project import PortfolioProject
from app.models.github_repo_analysis import GithubRepoAnalysis
from app.schemas.github_analysis import GithubRepoAnalysisOut

router = APIRouter(prefix="/github=analyses", tags=["github-analyses"])

# 포트폴리오 프로젝트 1개를 분석해서 GithubRepoAnalysis에 upsert(있으면 갱신/없으면 생성)
def _analyze_and_save(db: Session, project: PortfolioProject) -> GithubRepoAnalysis:
    owner, repo, ref = parse_github_url(project.github_url)
    repository = fetch_repository(owner, repo) # 접근 가능 여부

    fetch_readme_text(repository, ref)
    readme_text = fetch_readme_text(repository, ref)
    files = fetch_file_tree(repository, ref)
    languages = compute_language_breakdown(files)
    manifests = fetch_dependency_manifests(repository, files, ref)
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