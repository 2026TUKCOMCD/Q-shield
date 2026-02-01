import asyncio
import json

from main import scan_repository, ScanRequest

async def run():
    req = ScanRequest(github_url='./test_vulnerable_repo')
    res = await scan_repository(req)
    # scan_repository returns ScanResponse; print result dict if present
    print(json.dumps(res.result, indent=2, default=str))

if __name__ == '__main__':
    asyncio.run(run())
