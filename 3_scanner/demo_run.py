import asyncio
import json
import os
import sys

from main import scan_repository, ScanRequest

async def run():
    # Get test_vulnerable_repo path based on current working directory
    # In GitHub Actions, cwd is 3_scanner, so test_vulnerable_repo is at ../test_vulnerable_repo
    cwd = os.getcwd()
    
    # Try multiple possible locations
    possible_paths = [
        os.path.join(cwd, '..', 'test_vulnerable_repo'),  # If cwd is 3_scanner
        os.path.join(cwd, 'test_vulnerable_repo'),         # If cwd is root
        os.path.join(os.path.dirname(cwd), 'test_vulnerable_repo'),  # Parent directory
    ]
    
    test_repo_path = None
    for path in possible_paths:
        abs_path = os.path.abspath(path)
        if os.path.isdir(abs_path):
            test_repo_path = abs_path
            print(f"✅ Found test_vulnerable_repo at: {test_repo_path}")
            break
    
    if not test_repo_path:
        print(f"❌ Could not find test_vulnerable_repo")
        print(f"   Current working directory: {cwd}")
        print(f"   Tried paths:")
        for path in possible_paths:
            print(f"     - {os.path.abspath(path)}")
        sys.exit(1)
    
    print(f"\n🚀 Starting scan of test_vulnerable_repo...\n")
    
    req = ScanRequest(github_url=test_repo_path)
    res = await scan_repository(req)
    
    # Print result
    if res.result:
        print(json.dumps(res.result, indent=2, default=str))
    else:
        print(f"Status: {res.status}")
        print(f"Message: {res.message}")

if __name__ == '__main__':
    asyncio.run(run())
