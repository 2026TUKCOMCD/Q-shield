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
    # 로컬 디렉토리인 경우 처리
    if os.path.isdir(github_url):
        return os.path.abspath(github_url)
    
        print(f"[DEBUG] github_url={github_url}")
        print(f"[DEBUG] isdir={os.path.isdir(github_url)}")
        print(f"[DEBUG] exists={os.path.exists(github_url)}")
    
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
