# PyGithub을 이용해 GitHub 저장소의 "원본 데이터"를 수집하는 모듈.

import os
from dataclasses import dataclass
from urllib.parse import urlparse

from github import Github
from github.GithubException import(GithubException, UnknownObjectException, RateLimitExceededException, BadCredentialsException)
from github.Repository import Repository

from app.core.config import get_settings

# github url에서 onwerm repo 문자열 추출
def parse_github_url(url: str | None) -> tuple[str, str]:
    if not url:
        raise ValueError("Github URL이 비어 있습니다.")

    # 스킴(https://) 없는 url 형태 처리
    parsed = urlparse(url if "://" in url else f"https://{url}")

    if "github.com" not in parsed.netloc:
        raise ValueError(f"Github URL이 아닙니다: {url}")

    # 앞/뒤 슬래시 제거
    parts = [p for p in parsed.path.strip("/").split("/") if p]
    if len(parts) < 2:
        raise ValueError(f"URL에서 owner/repo를 찾을 수 없습니다: {url}")

    owner, repo = parts[0], parts[1]
    repo = repo.removesuffix(".git") # "repo.git" -> "repo"

    # "/owner/repo/tree/<branch>" 또는 "/owner/repo/blob/<branch>/..." 형태에서 브랜치 이름 추출
    ref = None
    if len(parts) >= 4 and parts[2] in ("tree", "blob"):
        ref = parts[3]
    return owner, repo, ref

# Github API 클라이언트 생성
def _get_client() -> Github:
    settings = get_settings()
    return Github(settings.github_token) if settings.github_token else Github()

# Repo 접근 가능 여부 확인
def fetch_repository(owner: str, repo: str) -> Repository:
    client = _get_client()
    try:
        return client.get_repo(f"{owner}/{repo}")
    except UnknownObjectException:
        raise ValueError(f"저장소 비공개 or 존재하지 않음: {owner}/{repo}")
    except BadCredentialsException:
        raise ValueError("Github 인증 토큰이 유효하지 않음")
    except RateLimitExceededException:
        raise ValueError("Github API 요청 한도 초과. 잠시 후 시도하세요.")
    except GithubException as e:
        raise ValueError(f"Github 저장소 접근 중 오류 발생: {e}")

# 저장소 커밋 활동량 분석
def fetch_repo_structure(repository: Repository, ref: str | None = None) -> dict:
    try:
        commits = repository.get_commits(sha=ref) if ref else repository.get_commits()
        commit_count = commits.totalCount
    except GithubException:
        commit_count = 0

    return {
        "commit_count": commit_count,
        "default_branch": repository.default_branch,
        "analyze_ref": ref or repository.default_branch,
    }

# README 텍스트 추출
def fetch_readme_text(repository: Repository, ref: str | None = None) -> str | None:
    try:
        readme_file = repository.get_readme(ref=ref) if ref else repository.get_readme()
    except UnknownObjectException:
        return None

    return readme_file.decoded_content.decode("utf-8", errors="ignore")

@dataclass
class RepoFile:
    path: str
    size: int

# 확장자로 언어 매핑
_EXTENSION_LANGUAGE_MAP = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript",
    ".cpp": "C++", ".cc": "C++", ".cxx": "C++", ".h": "C++", ".hpp": "C++",
    ".c": "C", ".cs": "C#", ".java": "Java", ".go": "Go", ".rs": "Rust",
    ".rb": "Ruby", ".php": "PHP", ".swift": "Swift", ".kt": "Kotlin",
    ".html": "HTML", ".css": "CSS", ".sql": "SQL", ".sh": "Shell",
}

# 의존성/패키지 정의 파일
_DEPENDENCY_MANIFEST_FILENAMES = {
    "requirements.txt", "package.json", "pyproject.toml", "cargo.toml",
    "go.mod", "pom.xml", "build.gradle", "gemfile", "podfile",
}

# 제외항목(외부 라이브러리/빌드 산출물)
_VENDOR_DIR_NAMES = {
    "thirdparty", "third_party", "vendor", "vendors", "external", "externals", "extern",
    "sdk", "sdks", "library", "libraries", "libs", "lib", "packages",
    "node_modules", "dist", "build", ".git", "bin", "obj",
}

# 경로 이름으로 걸러지지 않은 제외항목 2차 분류
_LICENSE_HEADER_MARKERS = (
    "permission is hereby granted", "spdx-license-identifier",
)

def _is_vendor_path(path: str) -> bool:
    segments = path.lower().split("/")
    return any(seg in _VENDOR_DIR_NAMES for seg in segments)

def _similar_vendor_code(content: str) -> bool:
    head = content[:500].lower()
    return any(marker in head for marker in _LICENSE_HEADER_MARKERS)

def _get_extension(path: str) -> str:
    return os.path.splitext(path)[1].lower()

# 저장소 경로+크기를 한번에 가져온다.
def fetch_file_tree(repository: Repository, ref: str | None = None) -> list[RepoFile]:
    sha = ref or repository.default_branch
    tree = repository.get_git_tree(sha=sha, recursive=True)
    return [RepoFile(path=el.path, size=el.size or 0) for el in tree.tree if el.type == "blob"]

# 파일트리 기반 언어 비중 계산
def compute_language_breakdown(files: list[RepoFile]) -> list[str]:
    bytes_by_language: dict[str, str] = {}
    for f in files:
        # Unreal 빌드 스크립트는 문법만 C#인 설정 파일이므로 제외.
        if f.path.lower().endswith((".build.cs", ".target.cs")):
            continue
        language = _EXTENSION_LANGUAGE_MAP.get(_get_extension(f.path))
        if language is None:
            continue
        bytes_by_language[language] = bytes_by_language.get(language, 0) + f.size

    return sorted(bytes_by_language, key=bytes_by_language.get, reverse=True)

# 일반 파일 반환
def _fetch_file_content(repository: Repository, path: str, ref: str | None) -> str | None:
    try:
        content_file = repository.get_contents(path, ref=ref) if ref else repository.get_contents(path)
        return content_file.decoded_content.decode("utf-8", errors="ignore")
    except GithubException:
        return None

# 의존성 정의 파일 판단
def _is_dependency_manifest(path: str) -> bool:
    name = path.rsplit("/", 1)[-1].lower()
    if name in _DEPENDENCY_MANIFEST_FILENAMES:
        return True
    if name.endswith((".csproj", ".uproject")):
        # .csproj : C#/.NET 프로젝트 의존성 정의
        # .uproject : Unreal 프로젝트 설정 + 활성화된 플러그인 목록(JSON)
        return True
    if name.endswith((".build.cs", ".target.cs")):
        # <모듈명>.Build.cs : 이 모듈이 실제로 링크하는 엔진 모듈/플러그인 목록
        # <타겟명>.Target.cs : 빌드 타겟(게임/에디터/서버 등) 정의
        return True
    return False

# 의존성 정의 파일 반환
def fetch_dependency_manifests(repository: Repository, files: list[RepoFile], ref: str | None = None, max_files: int = 5) -> dict[str, str]:
    matches = [f for f in files if not _is_vendor_path(f.path) and _is_dependency_manifest(f.path)][:max_files]

    manifests = {}
    for f in matches:
        content = _fetch_file_content(repository, f.path, ref)
        if content is not None:
            manifests[f.path] = content
    return manifests

# 대표 소스파일 내용 반환. 파일크기로 중요도 판단
def fetch_source_snippets(repository: Repository, files: list[RepoFile], ref: str | None = None, max_files: int = 6, max_chars_per_file: int = 3000,) -> dict[str, str]:
    candidates = [f for f in files if _get_extension(f.path) in _EXTENSION_LANGUAGE_MAP and not _is_vendor_path(f.path)]
    candidates.sort(key=lambda f: f.size, reverse=True)

    snippets = {}
    for f in candidates:
        if len(snippets) >= max_files:
            break
        content = _fetch_file_content(repository, f.path, ref)
        if content is None or _similar_vendor_code(content):
            continue
        snippets[f.path] = content[:max_chars_per_file] # 3000자 제한
    return snippets