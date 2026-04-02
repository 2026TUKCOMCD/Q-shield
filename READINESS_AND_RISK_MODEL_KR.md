# Q-shield Readiness Score / Risk Score 기준

## 1. 문서 목적
이 문서는 Q-shield에서 사용하는 `PQC Readiness Score`와 `Risk Score`가 어떤 입력을 바탕으로 계산되는지, 그리고 각 점수가 무엇을 의미하는지 한국어로 정리한 문서다.

중요한 전제는 다음과 같다.

- 이 점수는 **실제 스캐너 findings**를 입력으로 사용한다.
- 점수 자체는 `우선순위 점수(priority score)`와 다르다.
- readiness / risk는 **저장소의 현재 상태를 요약하는 운영 지표**이고,
  priority는 **무엇을 먼저 전환해야 하는지 결정하는 planning 지표**다.

---

## 2. 입력 데이터

Q-shield는 정규화된 findings를 기반으로 scoring signal을 만든다.

입력 sources:
- SAST findings
- SCA findings
- Config findings

각 finding에서 score 계산에 직접 쓰는 핵심 값:
- `severity`
- `algorithm`
- 필요 시 dependency 이름으로부터 추론한 algorithm class

관련 구현:
- [backend/app/scoring/__init__.py](C:/Users/KunWoongKyung/Documents/git/git/Q-shield/backend/app/scoring/__init__.py)
- [backend/app/scoring/criteria.py](C:/Users/KunWoongKyung/Documents/git/git/Q-shield/backend/app/scoring/criteria.py)

---

## 3. Signal 변환 방식

각 finding은 먼저 다음 형태의 signal로 변환된다.

```text
{
  severity: finding.severity,
  algorithm: finding.algorithm 또는 dependency/library 기반 추론 결과
}
```

즉 scoring 단계는 findings 전체를 다시 단순화해서,
`얼마나 심각한가 + 어떤 알고리즘 계열인가`를 보는 구조다.

---

## 4. Severity Weight

severity는 다음과 같이 가중치로 변환된다.

- `CRITICAL = 4.0`
- `HIGH = 3.0`
- `MEDIUM = 2.0`
- `LOW = 1.0`
- `INFO = 0.5`

의미:
- severity가 높을수록 readiness에는 더 큰 penalty를 주고,
- risk에는 더 큰 점수를 준다.

이 값은 현재 구현상의 deterministic heuristic이다.

---

## 5. Algorithm Weight

algorithm class는 다음과 같은 가중치를 가진다.

- `Public-key 계열 (RSA, ECC/ECDSA, DSA, DH)` -> `1.6`
- `Weak hash 계열 (SHA-1, MD5)` -> `1.3`
- `Symmetric 계열 (AES, ChaCha)` -> `1.0`
- 그 외/미분류 -> `1.0`

의미:
- PQC 전환의 직접 대상인 공개키 계열은 더 무겁게 본다.
- weak hash는 PQC 직접 대체 대상은 아니지만 migration debt로 간주해 가중한다.
- symmetric path는 readiness에는 영향을 주지만 primary PQC replacement target은 아니므로 상대적으로 낮다.

관련 구현:
- [backend/app/scoring/criteria.py](C:/Users/KunWoongKyung/Documents/git/git/Q-shield/backend/app/scoring/criteria.py)

---

## 6. Finding별 점수

각 finding의 기본 점수는 다음과 같이 계산된다.

```text
finding_points = severity_weight * algorithm_weight
```

예:
- `HIGH + RSA` -> `3.0 * 1.6 = 4.8`
- `MEDIUM + Weak Hash` -> `2.0 * 1.3 = 2.6`

이 finding별 점수를 모두 합산한 값이 `weighted_total`이다.

---

## 7. PQC Readiness Score

### 7.1 계산식

현재 구현은 다음과 같은 방식을 사용한다.

```text
penalty = min(9.0, weighted_total / 3.0)
legacy_score = int(max(1.0, 10.0 - penalty))
```

출력 scale:
- `scale=10`이면 `1~10`
- `scale=100`이면 `10~100`

즉 `10점 만점 readiness`를 먼저 구한 뒤,
100점 화면에서는 `x10` 해서 보여준다.

### 7.2 해석

- score가 높을수록 상대적으로 PQC readiness가 높다.
- score가 낮을수록 quantum-vulnerable public-key, weak hash, legacy dependency/config burden이 많다는 뜻이다.

예시 해석:
- `90~100`: 비교적 준비도 높음
- `70~80`: 일부 취약 자산 정리 필요
- `50~60`: 전환 준비도 낮고 우선순위 계획 필요
- `10~40`: 전환 부채가 크고 즉시 triage 필요

### 7.3 주의점

이 점수는 “보안이 몇 % 향상되었다”를 의미하지 않는다.
의미하는 것은 다음에 가깝다.

- 현재 저장소의 PQC 전환 준비도
- quantum-vulnerable crypto burden의 상대적 크기

---

## 8. Risk Score

### 8.1 계산식

현재 구현은 weighted total을 0~100 범위로 정규화한다.

```text
normalized = min(1.0, weighted_total / 27.0)
risk_score = round(normalized * 100)
```

### 8.2 해석

- score가 높을수록 현재 저장소의 crypto transition burden과 quantum-related risk exposure가 높다.
- score가 낮을수록 취약 신호 수와 강도가 적다는 뜻이다.

### 8.3 readiness와의 관계

둘은 반대 방향으로 읽으면 된다.

- readiness 높음 -> risk 낮음
- readiness 낮음 -> risk 높음

하지만 두 점수는 단순 역수 관계라기보다,
동일한 weighted total을 서로 다른 관점에서 읽는 요약 지표다.

---

## 9. Inventory Risk Score

inventory의 각 asset row에도 별도 risk score가 있다.

이 값은 전체 저장소 점수와 다르며,
**해당 asset에 연결된 findings만 다시 모아서 계산한 local score**다.

즉:
- dashboard readiness/risk = 저장소 전체 상태
- inventory risk score = 특정 asset의 상대적 위험도

예:
- `Weak Hash` asset 하나가 여러 line에서 반복되면,
  그 asset row의 risk score가 올라간다.
- `RSA certificate` asset, `Private Key Material` asset도
  각자 연결된 findings만 기준으로 local risk를 가진다.

---

## 10. 왜 priority score와 따로 두는가

readiness/risk score는 전체 상태 요약용이다.

반면 priority score는 다음 요소까지 포함한다.
- evidence count
- affected file spread
- scanner corroboration
- external exposure
- HNDL sensitivity
- migration complexity
- interoperability risk
- non-production penalty

즉:
- readiness/risk = 상태 요약
- priority = 전환 순서 결정

둘은 역할이 다르다.

---

## 11. 문헌 근거와 heuristic 구분

readiness/risk 모델에서 중요한 구분은 다음과 같다.

### 문헌과 연결되는 부분
- 공개키 계열을 더 무겁게 보는 관점
- weak hash를 migration debt로 보는 관점
- PQC readiness를 “상태 요약”으로 보는 관점

### heuristic인 부분
- severity weight의 정확한 숫자
- algorithm weight의 정확한 숫자
- readiness penalty의 `weighted_total / 3.0`
- risk normalization의 `weighted_total / 27.0`

즉 발표 때는 다음처럼 설명하는 것이 가장 정확하다.

> 점수 요소와 해석 방향은 PQC 문헌/NIST 전환 가이드를 참고했고,  
> 구체적인 수치 가중치는 현재 프로토타입 단계의 deterministic heuristic이다.

---

## 12. 발표 시 설명 문장 예시

짧게 설명하면:

> Readiness Score와 Risk Score는 실제 스캐너 findings를 기반으로 계산합니다.  
> severity와 algorithm class를 공통 signal로 변환한 뒤, 전체 저장소 수준에서는 readiness와 risk를 요약 지표로 계산하고, asset 수준에서는 별도 local risk score를 계산합니다.  
> 이 점수는 PQC 전환 준비도와 전환 부채를 보여주는 운영 지표이며, recommendation 우선순위 점수와는 역할이 다릅니다.
