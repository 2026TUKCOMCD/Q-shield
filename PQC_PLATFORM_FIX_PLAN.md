# Q-shield Fix Plan

프로젝트 방향:
Q-shield는 일반 취약점 스캐너가 아니라 `PQC 전환 우선순위 진단 플랫폼`으로 정렬한다.

이 문서는 다음 입력을 반영한다.
- 초기 프로젝트 목표 정의
- 교수 피드백
- `deep-research-report.md`
- `deep-research-report (1).md`
- `deep-research-report (2).md`
- NIST IR 8547
- FIPS 203/204/205
- NIST SP 1800-38B
- NIST SP 1800-38C

핵심 원칙:
- scanner facts와 AI reasoning은 분리한다.
- AI는 recommendation을 발명하지 않고, planner 결과를 설명하고 보강한다.
- `% 보안 향상` 같은 과장 표현은 기본 지표로 사용하지 않는다.
- 우선순위는 severity만이 아니라 노출 범위, 영향 반경, 전환 비용, 운영 영향까지 포함한다.
- 결과물은 finding 목록이 아니라 cryptographic inventory / migration roadmap이어야 한다.

## Guiding Rules

- PQC 효과는 기본적으로 다음 언어로 표현한다.
  - `NIST security category`
  - `quantum-vulnerable exposure reduction`
  - `migration readiness`
  - `interoperability / performance trade-off`
- 퍼센트 기반 지표를 쓸 경우 반드시 정의와 계산식을 함께 제시한다.
- 하이브리드는 최종 상태가 아니라 단계적 전환 수단으로 표현한다.
- 2030/2035 timeline과 HNDL risk를 우선순위 설명에 반영한다.

## Completed

- [x] 프론트/백엔드 scan contract 1차 정렬
- [x] scan 완료 후 AI analysis 자동 enqueue
- [x] recommendation 흐름 단일화
- [x] findings dedup 및 distinct vulnerability class 기반 recommendation 생성
- [x] SCA manifest parsing 확대
- [x] JWT/JOSE 관련 SCA 탐지 보강
- [x] JWT/JOSE 관련 SAST 탐지 보강
- [x] findings 기반 recommendation planner 도입
- [x] `priorityReason`, `evidenceCount`, `affectedFilesCount`, `scannerTypes` 추가
- [x] AI recommendation에 `validationChecklist`, `benchmarkNotes`, `assumptions`, `confidenceReason` 추가
- [x] RAG source metadata 분류
- [x] normative vs benchmark evidence 분리 retrieval
- [x] unsupported claim validator 추가
- [x] 프론트 evidence UI 분리
- [x] structured recommendation DTO (`evidence/guidance/trust`) 도입
- [x] planner score를 factor 모듈로 분리
- [x] HNDL / migration complexity / interop risk 초기 factor 반영
- [x] asset_ref / correlation_ref 기반 cross-layer correlation 초안 도입

## Priority 1

목표:
`발견 -> 정규화 -> inventory -> recommendation`을 제품의 단일 사실 흐름으로 고정한다.

- [ ] findings를 cryptographic inventory / CBOM 성격의 공통 스키마로 정리
- [ ] inventory, findings, recommendation을 asset_ref 기준으로 화면에서 직접 연결
- [ ] scanner 결과를 SARIF 또는 SARIF-유사 구조와 매핑 가능하게 정리
- [ ] 동일 자산에 대한 SAST/SCA/Config correlation layer 강화
- [ ] scan status와 ai-analysis status 완전 분리
- [ ] partial failure 시 transaction/state 정합성 강화

## Priority 2

목표:
교수 피드백에 대응 가능한 우선순위 모델을 고정한다.

- [x] recommendation priority factor를 코드 모듈로 분리
- [x] 우선순위 공식과 factor 정의 문서화
- [x] HNDL risk factor 추가
- [x] migration complexity factor 추가
- [x] performance/interoperability factor를 planner score에 직접 반영
- [ ] HNDL factor를 업무 민감도/데이터 수명 기반으로 고도화
- [ ] migration complexity factor를 dependency graph와 abstraction depth 기반으로 고도화
- [ ] interop risk를 실제 benchmark citation과 직접 연결
- [ ] `priorityReason`을 factor breakdown 기반으로 더 구조화
- [ ] recommendation 1개 = vulnerability class 1개 = 근거 finding N개 구조를 DB/응답에서 더 명확히 연결

## Priority 3

목표:
PQC 전환 플랫폼답게 운영 성능과 상호운용 위험을 같이 진단한다.

주요 근거:
- NIST SP 1800-38C

- [ ] TLS/QUIC 경로에 대한 structured config parsing 강화
- [ ] certificate chain size, handshake-heavy path, keep-alive reuse 관련 signal 추가
- [ ] PKI / certificate / signature path에서 ML-DSA, SLH-DSA migration friction 표시
- [ ] HSM / PKCS#11 / digest-then-sign 경로 탐지 규칙 추가
- [ ] recommendation에 `performance impact risk`와 `interop risk`를 별도 필드로 추가
- [ ] heatmap에서 security risk와 migration friction을 분리 시각화

## Priority 4

목표:
AI 출력의 근거성과 감사 가능성을 강화한다.

- [x] source_type 기반 citation metadata 저장
- [x] normative evidence와 benchmark evidence 분리 노출
- [x] unsupported claim validator 추가
- [ ] citation missing penalty를 더 정교하게 조정
- [ ] benchmark-only evidence가 normative claim에 섞이지 않도록 후처리 강화
- [ ] recommendation마다 scanner evidence id와 citation id 연결
- [ ] fallback mode / real mode / cached mode를 UI에서 명시

## Priority 5

목표:
평가와 발표에 필요한 benchmark / methodology / trust justification을 완성한다.

- [ ] 평가 지표 문서화
  - detection accuracy
  - distinct class coverage
  - duplicate recommendation reduction
  - citation coverage
  - priority explanation consistency
  - expert review acceptance
- [ ] `%` 기반 지표가 필요한 경우 정의와 계산식 문서화
- [ ] authoritative benchmark set 구성
  - NIST 문서 기반 시나리오
  - 공개 GitHub repo 기반 시나리오
  - hand-crafted fixture 기반 시나리오
- [ ] 결과 보고서 템플릿에 다음 섹션 추가
  - 왜 이 항목이 우선인가
  - 근거 문서
  - 운영 영향
  - 검증 체크리스트
  - 전환 로드맵

## Architecture Fixes

- [ ] backend의 `sys.path` 기반 scanner import 제거
- [ ] scanner adapter / service layer 분리
- [ ] recommendation planner와 AI orchestrator 책임 분리 유지
- [ ] stored findings를 single source of truth로 고정
- [ ] frontend mock fallback을 데모 전용으로 제한

## Research Alignment Checklist

- [ ] NIST IR 8547의 transition framing과 충돌하지 않는가
- [ ] FIPS 203/204/205의 algorithm scope 설명과 충돌하지 않는가
- [ ] SP 1800-38B의 discovery-normalization-inventory 흐름을 반영하는가
- [ ] SP 1800-38C의 interoperability/performance lesson을 반영하는가
- [ ] security + performance + interoperability를 함께 설명하는가
- [ ] 퍼센트 지표를 사용할 때 정의와 한계를 함께 보여주는가

## Current Next Steps

1. prioritization factor를 AI summary와 recommendation 상세에 더 구조적으로 노출
2. findings/inventory/heatmap 화면에도 trust/evidence 표시 확대
3. benchmark-aware citation linking 강화
4. evaluation methodology 문서 추가
5. scanner correlation과 CBOM 스키마 정리
