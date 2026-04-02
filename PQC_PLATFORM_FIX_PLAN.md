# Q-shield Fix Plan

프로젝트 방향: Q-shield는 일반 취약점 스캐너가 아니라 `PQC 전환 우선순위 진단 플랫폼`으로 정렬한다.

이 계획은 다음 문서의 핵심 요구를 반영한다.
- `deep-research-report.md`
- `deep-research-report (1).md`
- `deep-research-report (2).md`

핵심 반영 사항:
- NIST IR 8547, FIPS 203/204/205, NIST SP 1800-38B/38C에 맞는 표현과 평가 체계를 사용한다.
- `보안이 몇 % 향상된다`는 식의 과장 표현은 기본 지표로 쓰지 않는다.
- 우선순위는 severity만이 아니라 `발견 범위`, `외부 노출`, `전환 비용`, `상호운용성`, `운영 성능 영향`까지 포함한다.
- 스캐너 결과는 단순 finding 목록이 아니라 `정규화된 cryptographic inventory / CBOM 성격의 데이터`로 수렴해야 한다.
- AI는 근거를 요약하고 설명하는 계층이지, scanner 사실을 대체하는 계층이 아니다.

## Guiding Rules

- PQC 효과는 기본적으로 `NIST security category`, `quantum-vulnerable exposure reduction`, `attack-cost/risk reduction`, `migration readiness`로 표현한다.
- `%` 지표가 필요하면 반드시 정의를 명시한다.
  - 예: `양자 취약 노출 감소율`
  - 예: `가정 기반 위험 감소율`
- `%`를 쓰더라도 `NIST가 직접 제공한 수치`처럼 보이게 표현하지 않는다.
- 하이브리드 구성은 임시 전환 수단으로 본다.
- 2030/2035 전환 타임라인과 HNDL 위험을 고려한 우선순위 설명이 가능해야 한다.

## Completed

- [x] 스캔 API 계약 불일치 1차 축소
- [x] AI 분석 자동 enqueue
- [x] recommendation 흐름 1차 통합
- [x] recommendation 중복 제거 및 distinct class 저장
- [x] SCA manifest 파싱 범위 확장
- [x] JWT/JOSE 관련 SCA 탐지 보강
- [x] JWT/JOSE 관련 SAST 탐지 보강
- [x] findings 기반 recommendation planner 도입
- [x] vulnerability class 단위 정규화
- [x] recommendation에 `priorityReason`, `evidenceCount`, `affectedFilesCount` 계산

## Priority 1

목표: `발견 -> 정규화 -> 우선순위화`를 제품 핵심 가치로 고정한다.

- [ ] findings를 `cryptographic inventory / CBOM 성격의 공통 스키마`로 정리
- [ ] scanner 결과를 SARIF 또는 SARIF-유사 구조로 내보낼 수 있게 설계
- [ ] 동일 자산을 SAST/SCA/Config에서 교차 상관하는 correlation layer 강화
- [ ] recommendation 화면에서 `normalizedClass`, `priorityReason`, `evidenceCount`, `affectedFilePaths`, `scannerTypes` 노출
- [ ] scan status와 ai-analysis status 분리
  - `SCAN_PENDING`, `SCAN_RUNNING`, `SCAN_COMPLETED`
  - `AI_PENDING`, `AI_READY`, `AI_FAILED`
- [ ] transaction 실패 시 partial state 정리 강화

## Priority 2

목표: 교수 피드백에 답할 수 있는 `방어 가능한 prioritization model`을 만든다.

- [ ] 우선순위 점수 공식을 명시 문서화
  - severity
  - public-key 여부
  - auth/tls/pki/token 노출 여부
  - affected files / blast radius
  - scanner source 다양성
  - migration cost
  - operational compatibility risk
- [ ] `priorityReason`을 규칙 기반 문장으로 고정
- [ ] recommendation 1개 = vulnerability class 1개 = 근거 finding N개 구조를 명확화
- [ ] findings, inventory, recommendations 간 ID 연결 강화
- [ ] `HNDL risk`, `external exposure`, `time-to-migrate`를 별도 신호로 관리

## Priority 3

목표: PQC 전환 플랫폼답게 `운영 성능 / 상호운용성 리스크`를 함께 진단한다.

문서 반영 근거:
- NIST SP 1800-38C
- 운영 성능 리서치 문서들

- [ ] TLS/QUIC 설정에서 PQC 적용 시 성능 병목 가능성 규칙 추가
  - certificate chain 크기
  - QUIC amplification / initcwnd / initial RTT 민감도
  - keep-alive / connection reuse 여부
  - handshake-heavy API 경로
- [ ] PKI/인증서/서명 경로에서 `ML-DSA`, `SLH-DSA` 적용 시 크기 증가 리스크 표기
- [ ] HSM / PKCS#11 / digest-then-sign 경로 탐지 규칙 추가
- [ ] 추천 결과에 `성능 영향 가능성`과 `상호운용성 영향 가능성` 필드 추가
- [ ] heatmap에서 security risk와 migration friction을 분리해서 볼 수 있게 설계

## Priority 4

목표: AI 신뢰성과 근거성을 강화한다.

- [ ] recommendation마다 scanner evidence와 NIST citation 연결
- [ ] fallback/real mode를 API와 UI에서 명확히 구분
- [ ] citation 부족 시 confidence 하향 규칙 명시
- [ ] AI 출력에 다음 필드 추가
  - `priority_reason`
  - `confidence_reason`
  - `evidence_count`
  - `citations_count`
  - `nist_reference`
  - `assumptions`
- [ ] AI가 unsupported metric을 만들지 못하게 prompt / validator 강화

## Priority 5

목표: 평가와 발표에 필요한 `benchmark / methodology / trust justification`을 완성한다.

- [ ] 평가 지표 문서화
  - 탐지 정확도
  - distinct class coverage
  - 중복 recommendation 감소율
  - inventory completeness
  - priority explanation consistency
- [ ] `%` 기반 대체 지표 정의
  - `양자 취약 노출 감소율`
  - `가정 기반 위험 감소율`
  - 정의와 계산식, 한계를 함께 표기
- [ ] authoritative benchmark set 구성
  - NIST 문서 기반 시나리오
  - 공개 GitHub 레포 기반 시나리오
  - hand-crafted fixture 기반 회귀 테스트
- [ ] 결과 보고서 템플릿에 다음 섹션 추가
  - `왜 이 항목이 우선인가`
  - `근거 문서`
  - `운영 영향`
  - `전환 난이도`
  - `권장 단계적 로드맵`

## Architecture Fixes

- [ ] backend에서 `sys.path` 기반 scanner import 제거
- [ ] scanner adapter / service layer 분리
- [ ] recommendation planner와 ai orchestrator 책임 분리
- [ ] stored findings를 single source of truth로 고정
- [ ] frontend mock fallback을 데모 전용으로 제한

## Research Alignment Checklist

- [ ] NIST IR 8547의 category/timeline 언어와 충돌하지 않는가
- [ ] FIPS 203/204/205의 알고리즘/크기/카테고리 설명을 왜곡하지 않는가
- [ ] SP 1800-38B의 discovery-normalization-inventory 흐름을 반영하는가
- [ ] SP 1800-38C의 interoperability/performance lesson을 반영하는가
- [ ] `security + performance + interoperability`를 함께 설명하는가
- [ ] `% 향상` 수치가 있으면 정의와 한계를 같이 보여주는가

## Current Next Step

1. 프론트 recommendation 화면에 구조화 필드 표시
2. scan / ai-analysis 상태 분리
3. inventory를 CBOM 성격의 공통 스키마로 정리
4. TLS/QUIC/HSM 성능 리스크 규칙 추가
5. 평가 지표와 보고서 템플릿 문서화
