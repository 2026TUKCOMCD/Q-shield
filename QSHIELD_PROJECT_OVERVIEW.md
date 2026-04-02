# Q-shield 프로젝트 개요

## 1. 프로젝트 정체성

Q-shield는 일반적인 취약점 스캐너가 아니다.

이 프로젝트는 **PQC 전환 우선순위 진단 및 계획 수립 플랫폼**으로, 조직이 다음 질문에 답할 수 있도록 설계되어 있다.

- 양자 취약 암호가 어디에서 사용되고 있는가?
- 무엇을 먼저 전환해야 하는가?
- 왜 그 항목이 더 높은 우선순위를 가지는가?
- 전환 비용과 난이도는 어느 정도인가?
- 이 판단을 뒷받침하는 근거는 무엇인가?

즉 Q-shield는 다음에 더 가깝다.

- PQC 전환 계획 수립 도구
- 암호 자산 인벤토리 및 전환 우선순위화 도구
- AI 보강형 전환 가이드 플랫폼
- 개발자와 의사결정자를 함께 지원하는 대시보드형 진단 시스템

반대로 다음을 목표로 하지는 않는다.

- 전체 애플리케이션의 완전 자동 전환
- 범용 DevSecOps 대체 제품
- 원클릭 코드 수정기

## 2. 핵심 목적

Q-shield의 핵심 목적은 스캐너가 발견한 암호 관련 사실 데이터를, 실제로 활용 가능한 **PQC 전환 로드맵**으로 바꾸는 것이다.

의도한 흐름은 다음과 같다.

1. 코드, 의존성, 설정에서 암호 사용 흔적을 발견한다.
2. findings를 정규화하고 distinct migration target 단위로 묶는다.
3. 설명 가능한 규칙 기반 점수로 우선순위를 계산한다.
4. RAG 기반 AI로 전환 가이드와 설명을 보강한다.
5. 신뢰 근거와 함께 대시보드로 보여준다.

## 3. 핵심 기능

### 3.1 Repository Heatmap

목적:
- 저장소 내에서 PQC 전환 리스크가 집중된 위치를 빠르게 파악한다.

포함 요소:
- 위험한 파일 및 폴더
- 집계된 위험도 시각화
- 경계 정보와 trust cue
- 보안 및 전환 hot spot

### 3.2 Crypto Inventory

목적:
- 실제로 사용 중인 암호 자산을 구조화된 목록으로 정리한다.

포함 요소:
- 알고리즘 클래스
- 파일 경로와 라인 정보
- 위험 점수
- 알고리즘 패밀리
- `asset_ref`
- `correlation_ref`

의미:
- 인벤토리는 전환 계획의 사실 기반 출발점이다.
- 같은 자산을 findings, inventory, recommendation 사이에서 추적할 수 있다.

### 3.3 AI Migration Recommendations

목적:
- 무엇을 먼저 바꿔야 하는지, 그리고 어떤 방식으로 접근해야 하는지 설명한다.

포함 요소:
- 전환 대상 제목
- 현재 알고리즘 또는 취약 클래스
- 권장 PQC 방향
- 우선순위 순번
- 우선순위 사유
- 검증 체크리스트
- benchmark notes
- assumptions
- confidence reason
- citations

중요한 점:
- AI는 **설명과 가이드 보강**을 담당한다.
- AI가 생성한 예시 코드가 곧바로 운영 환경에서 안전하다고 주장하지 않는다.

## 4. 시스템 아키텍처

### 4.1 프론트엔드

주요 스택:
- Next.js / React / TypeScript
- Tailwind CSS
- 대시보드 중심 UI 컴포넌트

주요 역할:
- 스캔 결과 시각화
- recommendation 상세 화면 제공
- trust / evidence UI 제공
- inventory 및 heatmap 탐색

### 4.2 백엔드

주요 스택:
- FastAPI
- Python
- Celery
- Redis
- PostgreSQL

주요 역할:
- 스캔 오케스트레이션
- 결과 저장
- scanner 결과 정규화
- recommendation planning
- AI analysis 실행 및 저장

### 4.3 AI / RAG 계층

주요 스택:
- OpenAI API
- Chroma vector store
- NIST / benchmark / 논문 코퍼스

주요 역할:
- citation retrieval
- 근거 기반 recommendation 생성
- benchmark-aware note 생성
- confidence 및 validation 처리

## 5. 스캐너 계층

Q-shield는 스캐너를 사실 기반 발견 계층으로 본다.

### 5.1 SAST Scanner

초점:
- 소스 코드 내부의 직접적인 암호 API 사용 탐지

예시:
- RSA / ECDSA / DH 사용
- JWT 서명 패턴
- 약한 해시 사용

### 5.2 SCA Scanner

초점:
- PQC 전환 준비가 안 된 라이브러리와 manifest 탐지

예시:
- `package.json`
- `pyproject.toml`
- `requirements.txt`
- `build.gradle`
- `Pipfile`

### 5.3 Config Scanner

초점:
- TLS, 인증서, 설정 레벨의 암호 리스크 탐지

예시:
- 인증서 파일
- TLS 설정
- 암호 관련 설정 선택

## 6. Scanner Facts와 AI Guidance의 분리

이 구분은 Q-shield의 가장 중요한 설계 원칙 중 하나다.

### 6.1 Scanner Facts

실제 저장소 분석으로부터 생성되는 사실 데이터다.

대표 필드:
- algorithm
- file path
- line range
- severity
- scanner type
- evidence excerpt
- dependency name
- config signal

의미:
- 코드, 의존성, 설정 분석에서 나온 실제 발견 사실이다.

### 6.2 AI Guidance

정규화된 scanner findings를 바탕으로 생성되는 해석 계층이다.

대표 필드:
- migration strategy
- PQC direction
- validation checklist
- benchmark notes
- assumptions
- confidence reason
- citations

의미:
- AI는 해석과 설명을 담당한다.
- 반드시 scanner findings와 retrieval 문서에 근거해야 한다.

## 7. Recommendation 모델

Q-shield의 recommendation은 raw finding을 1:1로 복사한 것이 아니다.

recommendation은 **distinct migration target** 단위로 묶인다.

예시:
- 여러 RSA 관련 finding은 하나의 `rsa-public-key` recommendation이 될 수 있다.
- 여러 SHA-1 finding은 하나의 `weak-hash` recommendation이 될 수 있다.

각 recommendation은 다음을 답하도록 설계된다.

- 이 recommendation은 어떤 전환 대상을 의미하는가?
- 왜 중요한가?
- 실제 레포에서 얼마나 넓게 퍼져 있는가?
- 어떤 방식으로 전환해야 하는가?

## 8. 우선순위 모델

우선순위는 현재 결정론적 규칙 기반 모델로 계산한다.

사용되는 주요 factor는 다음과 같다.

- `severity_base`
- `class_risk_bonus`
- `evidence_bonus`
- `spread_bonus`
- `scanner_bonus`
- `exposure_bonus`
- `hndl_bonus`
- `migration_complexity_bonus`
- `interop_risk_bonus`
- `non_production_penalty`

### 8.1 각 factor의 의미

- `severity_base`
  - scanner severity를 정규화한 기본 점수
- `class_risk_bonus`
  - PQC 전환의 핵심이 되는 공개키 계열 클래스에 더 높은 가중치를 부여
- `evidence_bonus`
  - 관련 finding이 많을수록 urgency와 confidence를 높임
- `spread_bonus`
  - 영향 파일 수가 많을수록 migration scope가 넓다고 판단
- `scanner_bonus`
  - SAST / SCA / Config 간 상호 corroboration이 있으면 actionability를 높게 평가
- `exposure_bonus`
  - auth / token / TLS / certificate 경계는 더 긴급하게 평가
- `hndl_bonus`
  - harvest-now-decrypt-later 관점에서 민감한 경로를 더 높게 평가
- `migration_complexity_bonus`
  - 설정, 의존성, 넓은 경계 전환은 조기에 계획해야 하므로 가산
- `interop_risk_bonus`
  - 프로토콜/배포 호환성 리스크를 고려
- `non_production_penalty`
  - test / example / fixture 자산이 실제 운영 전환 대상을 앞지르지 않도록 감점

### 8.2 점수의 근거는 어디서 오는가

이 구분이 중요하다.

- **factor의 종류와 해석 관점**은 NIST / PQC 문헌을 참고한다.
- **구체적인 숫자 가중치**는 현재 엔지니어링 heuristic이다.

즉 현재 우선순위 모델은 다음처럼 설명하는 것이 맞다.

> 문헌 기반 factor 선정 + heuristic weight 설계

반대로 다음처럼 설명하면 안 된다.

> NIST가 직접 제시한 점수식을 그대로 사용했다

## 9. AI Guidance 모델

Q-shield는 AI를 자유형 챗봇처럼 사용하지 않는다.

AI는 다음 역할을 수행한다.

- 전환 설계 가이드 제시
- 예시 전환 방향 제시
- validation checklist 제공
- benchmark note 제공
- assumptions 정리
- confidence explanation 제공

AI가 과장해서는 안 되는 내용:
- 정확한 퍼센트 보안 향상
- 자동으로 운영 환경 적용 가능하다는 주장
- 성능 향상이 반드시 보장된다는 주장

## 10. Evidence 모델

Q-shield에는 현재 두 종류의 support가 존재한다.

### 10.1 Scanner-side support

의미:
- 저장소 내부에서 관련 finding이 얼마나 발견되었는가

예시:
- related findings count
- affected files count
- scanner sources

활용 목적:
- migration scope 파악
- blast radius 판단
- 운영상 urgency 추정

### 10.2 Citation-based support

의미:
- recommendation의 해석을 어떤 NIST / benchmark / 논문 근거가 지지하는가

예시:
- normative citations
- benchmark citations
- planning reference only 여부
- confidence reason

활용 목적:
- 신뢰도 설명
- 교수님 피드백 대응
- 기업 관점의 reviewability 확보

중요:
- scanner-side support는 문헌 기반 신뢰 근거와 동일하지 않다.
- 교수님 평가 관점에서는 citation-based support가 더 핵심적인 trust signal이다.

## 11. 신뢰도와 검증 요소

Q-shield는 명시적인 trust control을 포함한다.

### 11.1 분석 상태

현재 사용자 화면에서 노출되는 상태:
- `AI Guided`
- `Rule-based`
- `AI Fallback`
- `Mock AI`
- `AI Error`

의미:
- `AI Guided`: 실제 AI 보강이 붙은 recommendation
- `Rule-based`: 규칙 기반 분석만 존재하는 recommendation
- `AI Fallback`: AI 대신 제한된 fallback 경로가 사용된 recommendation
- `Mock AI`: 개발 모드용 결과
- `AI Error`: AI 분석 실패 상태

### 11.2 Citation 처리

플랫폼은 다음을 구분한다.
- normative evidence
- benchmark evidence
- other evidence

만약 normative citation이 없으면:
- recommendation을 더 보수적으로 해석한다.
- UI에서는 진짜 standard reference가 아니라 planning reference로 낮춰서 보여줄 수 있다.

### 11.3 Unsupported claim validation

validator는 다음을 제거하거나 강등한다.

- 근거 없는 퍼센트 보안 향상 표현
- benchmark-only claim을 normative support처럼 보이게 하는 표현
- 지나치게 확신하는 reference 표현

## 12. Cross-layer Correlation

Q-shield는 같은 전환 대상을 여러 화면에서 연결할 수 있도록 식별자를 제공한다.

핵심 필드:
- `asset_ref`
- `correlation_ref`

의미:
- findings, inventory, recommendation이 같은 암호 자산 또는 같은 migration target에 연결될 수 있다.
- 단순 이슈 목록이 아니라 CBOM 성격의 전환 계획으로 확장할 수 있다.

## 13. 현재 제품의 경계

현재 Q-shield가 비교적 잘하는 것:
- discovery
- inventory
- migration target grouping
- 설명 가능한 prioritization
- 근거 기반 AI guidance
- trust-aware dashboard rendering

현재 Q-shield가 아직 완전히 보장하지 않는 것:
- 자동 안전 코드 치환
- fully benchmark-calibrated scoring weight
- 모든 언어/암호 라이브러리에 대한 완전한 커버리지
- 모든 저장소에서 production / non-production 자산을 완벽하게 구분하는 것

## 14. 권장 제품 메시지

현재 가장 정확한 짧은 제품 메시지는 다음과 같다.

> Q-shield는 양자 취약 암호 사용을 발견하고, 전환 대상을 우선순위화하며, 근거 기반 AI 전환 가이드와 신뢰 신호를 제공하는 PQC 전환 계획 플랫폼이다.

## 15. 관련 문서

- [PQC_PRIORITY_MODEL.md](C:/Users/KunWoongKyung/Documents/git/git/Q-shield/PQC_PRIORITY_MODEL.md)
- [PQC_PLATFORM_FIX_PLAN.md](C:/Users/KunWoongKyung/Documents/git/git/Q-shield/PQC_PLATFORM_FIX_PLAN.md)
- [EVALUATION_METHODOLOGY.md](C:/Users/KunWoongKyung/Documents/git/git/Q-shield/EVALUATION_METHODOLOGY.md)
- [DEMO_SCENARIO.md](C:/Users/KunWoongKyung/Documents/git/git/Q-shield/DEMO_SCENARIO.md)
- [FINDINGS_SCHEMA.md](C:/Users/KunWoongKyung/Documents/git/git/Q-shield/FINDINGS_SCHEMA.md)
