# Q-shield Scanner (3_scanner)

Q-shield의 스캐너는 GitHub 저장소를 분석해 PQC(양자내성암호) 전환이 필요한 암호 사용 지점을 탐지하는 모듈이다.

FastAPI 기반 HTTP API로 동작하며, 저장소 URL이나 로컬 경로를 받아 스캔 결과를 JSON으로 반환한다.

## 동작 흐름

스캔은 저장소 클론 → 언어 분석 → SAST/SCA/Config 3종 스캔 → 결과 집계 순서로 진행된다.

언어 분석기(`language_detector`)가 확장자를 기준으로 파일을 분류해 각 스캐너가 처리할 대상 목록을 만든다.

## 세 가지 스캐너

SAST 스캐너는 소스코드에서 취약한 암호 함수 호출 패턴을 정규식과 (Python의 경우) AST로 탐지한다.

SCA 스캐너는 의존성 매니페스트(`requirements.txt`, `package.json`, `pom.xml`, `go.mod` 등)를 분석해 PQC 미지원 라이브러리를 탐지한다.

Config 스캐너는 설정 파일과 인증서(`.pem`, `.crt`, `.conf`, `.yaml`, `.xml` 등)에서 취약한 TLS·암호 설정을 진단한다.

## 지원 언어

SAST 분석이 지원하는 언어는 Python, JavaScript/TypeScript, Java, Go다.

각 발견 항목은 `severity`(HIGH/MEDIUM/LOW), `algorithm` 분류, 해당 위치(파일·라인)와 권고(recommendation)를 포함한다.

## 실행 방법

의존성을 설치하려면 `pip install -r requirements.txt`를 실행한다.

서버는 `python main.py`로 기동하며 기본 포트는 8000이다.

스캔을 요청하려면 `POST /api/scan`에 `{"github_url": "<저장소 URL 또는 로컬 경로>"}` 형태의 본문을 보낸다.
