import asyncio
import json
import os

from main import scan_repository, ScanRequest

async def run():
    # Get the absolute path to test_vulnerable_repo
    # We're in 3_scanner/, so test_vulnerable_repo is at ../test_vulnerable_repo
    test_repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'test_vulnerable_repo'))
    
    req = ScanRequest(github_url=test_repo_path)
    res = await scan_repository(req)
    # scan_repository returns ScanResponse; print result dict if present
    print(json.dumps(res.result, indent=2, default=str))

if __name__ == '__main__':
    asyncio.run(run())
