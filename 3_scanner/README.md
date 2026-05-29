# Q-shield Scanner (3_scanner)

Q-shield의 스캐너는 GitHub 저장소를 분석해 PQC(양자내성암호) 전환이 필요한 암호 사용 지점을 탐지하는 모듈이다.

FastAPI 기반 HTTP API로 동작하며, 저장소 URL이나 로컬 경로를 받아 스캔 결과를 JSON으로 반환한다.

## 동작 흐름

스캔은 저장소 클론 → 언어 분석 → SAST/SCA/Config 3종 스캔 → 결과 집계 순서로 진행된다.

언어 분석기(`language_detector`)가 확장자를 기준으로 파일을 분류해 각 스캐너가 처리할 대상 목록을 만든다.
