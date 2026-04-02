# Q-shield Evaluation Methodology

이 문서는 Q-shield의 탐지 정확도, 우선순위 로직, AI 신뢰성, 기업 활용 가능성을 어떻게 평가할지 정의한다.

핵심 원칙:
- scanner fact와 AI explanation을 분리해서 평가한다.
- 우선순위는 규칙 기반 planner를 먼저 검증한다.
- AI는 citation coverage, unsupported claim 차단, explanation quality를 중심으로 평가한다.
- `% 보안 향상` 같은 과장 지표는 사용하지 않는다.

## 1. Evaluation Questions

이 문서는 교수 피드백에 직접 대응한다.

### A. 우선순위 알고리즘은 방어 가능한가
- 같은 입력이면 같은 결과가 나오는가
- 우선순위 factor가 문서화되어 있는가
- 공개키, HNDL, interop risk 같은 PQC 핵심 요소가 반영되는가

### B. AI 할루시네이션을 통제하는가
- citation 없는 주장을 줄이는가
- unsupported claim validator가 동작하는가
- benchmark note가 실제 benchmark evidence와 연결되는가

### C. 기업 입장에서 신뢰할 수 있는가
- 결과가 scanner evidence와 연결되는가
- recommendation마다 why, evidence, assumptions, validation checklist가 보이는가
- fallback/mock/error 상태가 UI에서 구분되는가

## 2. System Under Evaluation

평가 대상은 세 계층이다.

1. `Scanner Layer`
- SAST
- SCA
- Config

2. `Planner Layer`
- vulnerability class normalization
- recommendation deduplication
- priority score calculation

3. `AI Guidance Layer`
- grounded recommendation generation
- citation retrieval
- benchmark note linking
- confidence / trust signaling

## 3. Benchmark Sets

Q-shield 평가는 최소 3개의 데이터셋으로 나눠서 진행한다.

### A. Hand-crafted Fixture Set

목적:
- 규칙 기반 검증
- 회귀 테스트
- expected answer가 명확한 케이스 검증

구성:
- RSA key generation
- JWT RS256 / ES256
- TLS_RSA / outdated TLS config
- RSA/ECC certificate
- weak hash
- legacy dependency without PQC support

평가 장점:
- 정답 라벨을 직접 설계 가능
- CI 테스트에 바로 넣기 좋음

### B. Public GitHub Repository Set

목적:
- 실제 코드베이스에서 false negative / false positive 확인
- scanner coverage와 UX 흐름 검증

구성 원칙:
- Python / Node / Java / config repo를 섞음
- JWT/auth, TLS/cert, dependency-heavy repo 포함
- archived legacy crypto repo 포함

평가 장점:
- 실제 사용 환경과 유사
- 발표/데모 시나리오로 활용 가능

### C. NIST Scenario Set

목적:
- 제품 메시지가 NIST transition framing과 맞는지 검증
- PQC migration planning 관점의 신뢰성 평가

구성 원칙:
- NIST IR 8547
- NIST SP 1800-38B
- NIST SP 1800-38C
- FIPS 203/204/205

평가 장점:
- 탐지 그 자체보다 “전환 우선순위 설명”의 정합성을 평가할 수 있음

## 4. Core Metrics

### 4.1 Detection Metrics

#### Detection Precision
- 정의: 탐지한 finding 중 실제로 유효한 finding 비율
- 계산식: `TP / (TP + FP)`

#### Detection Recall
- 정의: 실제 존재하는 finding 중 탐지한 비율
- 계산식: `TP / (TP + FN)`

#### Distinct Class Coverage
- 정의: 실제 존재하는 vulnerability class 중 탐지한 class 비율
- 계산식: `detected_distinct_classes / expected_distinct_classes`

#### Inventory Completeness
- 정의: cryptographic inventory에 포함되어야 할 자산이 누락되지 않았는지 보는 비율
- 측정 단위:
  - algorithm class
  - dependency
  - config/certificate

### 4.2 Recommendation Metrics

#### Recommendation Dedup Reduction
- 정의: raw finding 수 대비 recommendation 수가 얼마나 중복을 줄였는지
- 계산식: `1 - (recommendation_count / related_finding_count)`
- 목적:
  - 같은 class가 recommendation 여러 개로 쪼개지지 않는지 확인

#### Distinct Recommendation Coverage
- 정의: 서로 다른 vulnerability class가 recommendation에 모두 반영되는지
- 계산식: `recommended_distinct_classes / detected_distinct_classes`

#### Priority Explanation Consistency
- 정의: `priorityReason`과 `priorityFactors`가 실제 planner score와 일치하는 비율
- 평가 방식:
  - 샘플 케이스 수동 검토
  - automated snapshot test

#### Ranking Agreement
- 정의: 전문가가 매긴 우선순위와 planner rank의 일치 정도
- 평가 방식:
  - Top-1 agreement
  - Top-3 overlap
  - Spearman rank correlation

### 4.3 AI Trust Metrics

#### Citation Coverage
- 정의: recommendation 중 citation이 하나 이상 붙은 비율
- 계산식: `recommendations_with_citations / total_recommendations`

#### Normative Citation Coverage
- 정의: recommendation 중 normative evidence가 붙은 비율
- 계산식: `recommendations_with_normative_evidence / total_recommendations`

#### Benchmark Linkage Coverage
- 정의: benchmark note가 benchmark citation과 연결된 비율
- 계산식: `linked_benchmark_notes / total_benchmark_notes`

#### Unsupported Claim Rate
- 정의: validator가 제거하거나 경고한 unsupported claim 비율
- 계산식: `flagged_claims / total_claims_checked`

#### Trust Signal Completeness
- 정의: recommendation에 아래 필드가 모두 존재하는 비율
- 대상 필드:
  - `priorityReason`
  - `priorityFactors`
  - `validationChecklist`
  - `assumptions`
  - `confidenceReason`
  - `analysisMode`

### 4.4 Enterprise Usability Metrics

#### Reviewability
- 정의: 사용자가 recommendation을 검토할 때 근거를 추적할 수 있는 정도
- 평가 방식:
  - “근거 문서 확인 가능”
  - “affected file 확인 가능”
  - “validation checklist 확인 가능”
  - “analysis mode 확인 가능”

#### Actionability
- 정의: recommendation이 실제 migration planning에 도움이 되는 정도
- 평가 방식:
  - example code 존재 여부
  - validation checklist 존재 여부
  - benchmark note 존재 여부
  - affected asset scope 표시 여부

## 5. Evaluation Procedure

### Step 1. Scanner Accuracy
- fixture set에 대해 expected findings와 actual findings 비교
- precision / recall / distinct class coverage 계산

### Step 2. Planner Validation
- normalized class grouping 결과 검토
- dedup reduction 계산
- priority factor breakdown이 설계 문서와 일치하는지 확인

### Step 3. AI Grounding Validation
- citation coverage 계산
- normative vs benchmark evidence 분리 여부 확인
- validator가 unsupported claim을 막는지 테스트

### Step 4. Expert Review
- 샘플 repo 3~5개 선정
- recommendation rank와 explanation을 전문가가 검토
- ranking agreement와 actionability를 수집

### Step 5. UI Trust Review
- recommendation 상세에서 아래가 보이는지 체크
  - analysis mode
  - evidence count
  - priority factors
  - benchmark linkage
  - assumptions

## 6. Reporting Format

최종 보고서/발표에는 아래 표를 포함한다.

### A. Detection Summary
- repo name
- expected finding classes
- detected finding classes
- precision
- recall
- inventory completeness

### B. Priority Summary
- top migration target
- planner factors
- priority rank
- expert rank
- agreement 여부

### C. AI Trust Summary
- analysis mode
- citation coverage
- normative evidence count
- benchmark evidence count
- unsupported claim 여부

## 7. Acceptable Claim Boundaries

Q-shield는 아래 주장까지만 허용한다.

- “양자 취약 public-key usage가 발견되었다”
- “이 경로는 PQC migration planning 우선순위가 높다”
- “NIST guidance와 benchmark evidence에 비추어 운영 영향 검토가 필요하다”

Q-shield는 아래 주장을 기본적으로 금지한다.

- “보안이 XX% 향상된다”
- “이 코드가 바로 production-ready 하다”
- “환경과 무관하게 성능이 향상된다”

## 8. Minimal Success Criteria

발표 전 최소 성공 기준은 다음처럼 둔다.

- fixture set distinct class coverage: `>= 0.80`
- recommendation distinct coverage: `1.00`에 가깝게 유지
- citation coverage: `>= 0.70`
- benchmark linkage coverage: `>= 0.70`
- unsupported claim rate: 가능한 `0`에 가깝게 유지
- trust signal completeness: `>= 0.80`

이 수치는 초기 운영 목표이며, 최종 논문/보고서에서는 실험 결과에 따라 조정할 수 있다.

## 9. Linked Documents

- `PQC_PRIORITY_MODEL.md`
- `PQC_PLATFORM_FIX_PLAN.md`
- `SCAN_SCORE_CRITERIA.md`
- `deep-research-report.md`
- `deep-research-report (1).md`
- `deep-research-report (2).md`
