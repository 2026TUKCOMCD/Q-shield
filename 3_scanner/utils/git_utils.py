# utils/git_utils.py
import subprocess
import tempfile
import os
from urllib.parse import urlparse

def clone_repository(github_url: str) -> str:
    """
    GitHub Repository 클론 또는 로컬 경로 반환
    
    Returns:
        str: 클론된 Repository 경로 또는 로컬 경로
    """
    # 디버그 출력
    print(f"[DEBUG] clone_repository input: {github_url}")

    # file:// URI 처리
    try:
        parsed = urlparse(github_url)
    except Exception:
        parsed = None

    # 로컬 경로 후보들
    local_candidates = []
    if parsed and parsed.scheme == 'file':
        # file:///absolute/path -> parsed.path
        local_candidates.append(parsed.path)
    # 원시 문자열이 로컬 경로일 수 있음
    local_candidates.append(github_url)

    for candidate in local_candidates:
        if candidate and os.path.isdir(candidate):
            abs_path = os.path.abspath(candidate)
            print(f"[DEBUG] using local directory: {abs_path}")
            return abs_path

    print(f"[DEBUG] not a local directory; will attempt git clone")
    
    # 임시 디렉토리 생성
    temp_dir = tempfile.mkdtemp(prefix="pqc_scan_")
    
    # Repository 이름 추출
    parsed_url = urlparse(github_url)
    repo_name = os.path.basename(parsed_url.path).replace('.git', '')
    
    clone_path = os.path.join(temp_dir, repo_name)
    
    try:
        # git clone 실행
        result = subprocess.run(
            ['git', 'clone', '--depth', '1', github_url, clone_path],
            capture_output=True,
            text=True,
            timeout=300  # 5분 타임아웃
        )
        
        if result.returncode != 0:
            raise Exception(f"Git clone failed: {result.stderr}")
        
        return clone_path
    
    except subprocess.TimeoutExpired:
        raise Exception("Git clone timeout (5 minutes)")
    except Exception as e:
        # 실패 시 임시 디렉토리 정리
        if os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)
        raise e
