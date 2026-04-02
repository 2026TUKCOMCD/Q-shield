# PQC Priority Model

이 문서는 Q-shield가 PQC 전환 우선순위를 어떻게 계산하는지 설명한다.

핵심 원칙:
- AI는 설명과 전환 가이드를 보강한다.
- 우선순위 자체는 규칙 기반으로 계산한다.
- 각 factor는 `NIST guidance informed` 또는 `engineering heuristic`로 구분한다.
- 문헌은 factor 선정 근거를 제공하고, 최종 가중치는 제품 평가와 전문가 검토로 보정한다.

## 1. 적용 범위

현재 우선순위 모델은 `backend/app/recommendation_planner.py`와 `backend/app/recommendation_priority.py`에 구현되어 있다.

적용 대상:
- scanner finding을 정규화한 vulnerability class
- recommendation rank
- recommendation priority reason

현재 대표 class:
- `rsa-public-key`
- `dh-key-exchange`
- `ecc-signature`
- `dsa-signature`
- `weak-hash`
- `legacy-library`

## 2. 점수식

현재 recommendation 우선순위 점수는 다음과 같이 계산한다.

`priority_score = severity_base + class_risk_bonus + evidence_bonus + spread_bonus + scanner_bonus + exposure_bonus`

각 factor는 다음 의미를 가진다.

### severity_base
- 계산식: `int(SEVERITY_SCORE[max_severity] * 0.45)`
- 의미: 스캐너 severity를 공통 점수축으로 반영
- 근거 유형: `engineering_heuristic`
- 참고 코드: `backend/app/severity_map.py`

### class_risk_bonus
- 계산식: class별 고정 bonus
- 현재 값:
  - RSA: `18`
  - DH/ECDH: `17`
  - ECC/ECDSA: `18`
  - DSA: `16`
  - Weak Hash: `8`
  - Legacy Library: `10`
- 의미: 양자 취약 public-key class를 weak hash보다 우선적으로 다룸
- 근거 유형: `nist_guidance_informed`
- 근거 설명:
  - NIST IR 8547은 PQC 전환의 핵심을 양자 취약 public-key cryptography 교체에 둔다.
  - FIPS 203/204/205는 ML-KEM, ML-DSA, SLH-DSA의 표준화 대상이 key establishment / signature 영역임을 보여준다.

### evidence_bonus
- 계산식: `min(18, issue_count * 3)`
- 의미: 동일 class에 대한 증거가 많을수록 remediation urgency 증가
- 근거 유형: `engineering_heuristic`

### spread_bonus
- 계산식: `min(15, affected_files * 4)`
- 의미: 영향 파일 수가 많을수록 blast radius 증가
- 근거 유형: `engineering_heuristic`

### scanner_bonus
- 계산식: `min(12, scanner_types * 4)`
- 의미: SAST/SCA/Config가 동시에 같은 전환 대상을 지지하면 actionability 증가
- 근거 유형: `engineering_heuristic`

### exposure_bonus
- 계산식: `10 if auth/tls/token/cert/nginx/gateway keyword matched else 0`
- 의미: 외부 인증, TLS, 토큰, 인증서, 게이트웨이 경로는 운영상 우선순위가 높음
- 근거 유형: `nist_guidance_informed`
- 근거 설명:
  - NIST SP 1800-38B는 discovery/inventory 단계에서 실제 사용 맥락 파악의 중요성을 강조한다.
  - NIST SP 1800-38C는 TLS, certificate chain, interoperability, keep-alive, handshake cost 등 운영 경로의 영향을 다룬다.

## 3. 우선순위 등급

현재 rank 기반 priority mapping은 다음과 같다.

- rank 1-2: `CRITICAL`
- rank 3-5: `HIGH`
- rank 6-8: `MEDIUM`
- rank 9+: `LOW`

이는 현재 제품 UI 단순화를 위한 등급이며, 향후에는 절대 점수 기준과 함께 재검토할 수 있다.

## 4. 왜 이 모델이 AI보다 먼저인가

이 모델은 다음 이유로 AI보다 앞선다.

- 우선순위 계산이 재현 가능하다.
- 같은 finding 입력이면 같은 점수가 나온다.
- 각 recommendation에 `priorityReason`을 결정론적으로 남길 수 있다.
- 교수 피드백의 “신뢰도”, “검증 가능성”, “할루시네이션 방지”에 직접 대응한다.

즉 Q-shield에서 AI는 우선순위를 발명하지 않고, 이미 계산된 우선순위를 설명하고 전환 가이드를 보강한다.

## 5. 문헌 근거를 어떻게 제시할 것인가

발표/보고서에서는 다음처럼 설명하는 것이 적절하다.

- factor 선정 근거:
  - NIST IR 8547
  - FIPS 203/204/205
  - NIST SP 1800-38B
  - NIST SP 1800-38C
- 가중치 설정 근거:
  - 내부 heuristic
  - 공개 GitHub fixture
  - hand-crafted test corpus
  - 전문가 검토

중요:
- `모든 숫자 weight가 논문에서 직접 왔다`고 주장하지 않는다.
- 대신 `문헌은 factor를 정당화하고, weight는 제품 평가를 통해 조정한다`고 설명한다.

## 6. 현재 한계

- HNDL은 아직 직접 점수화하지 않았다.
- migration complexity는 effort 문구에만 반영되고 점수에는 제한적으로 반영된다.
- performance/interoperability risk는 AI guidance에는 들어가지만 planner score에는 아직 직접 반영되지 않는다.
- absolute score threshold 대신 rank bucket을 사용한다.

## 7. 다음 확장

다음 단계에서는 아래 항목을 planner factor로 확장한다.

- HNDL risk
- migration complexity
- performance/interoperability risk
- certificate chain / QUIC / HSM 경로 영향
- external exposure를 단순 keyword가 아니라 structured context로 계산

## 8. 관련 코드

- `backend/app/recommendation_priority.py`
- `backend/app/recommendation_planner.py`
- `backend/app/severity_map.py`
- `backend/app/scoring/criteria.py`
- `backend/tests/test_priority_model.py`
