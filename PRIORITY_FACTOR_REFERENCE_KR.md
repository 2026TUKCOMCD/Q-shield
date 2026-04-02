# PQC 우선순위 점수 요소 근거 문서

## 1. 문서 목적

이 문서는 Q-shield의 우선순위 모델이 어떤 문헌을 근거로 설계되었는지 교수님 설명용으로 정리한 문서다.

핵심 원칙은 다음과 같다.

- 우선순위 **factor의 종류와 해석 관점**은 NIST/PQC 문헌을 참고한다.
- 우선순위 **수치 가중치 자체**는 현재 프로토타입 단계의 engineering heuristic이다.
- 따라서 이 문서는 `문헌이 직접 준 규칙`과 `문헌을 참고해 우리가 설계한 heuristic`을 구분해서 설명한다.

중요한 점:
- 공식 PDF는 보통 문단 번호를 별도로 부여하지 않는다.
- 따라서 아래 표에서는 `문서명`, `섹션명`, `페이지`, `핵심 문장 또는 표/그림` 기준으로 근거를 적는다.

## 2. 우선순위 모델의 현재 구조

현재 구현된 점수 요소는 다음과 같다.

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

이 중 일부는 문헌 직접 근거가 강하고, 일부는 운영용 heuristic이다.

## 3. factor별 문헌 근거 정리

| factor | 현재 의미 | 문헌 직접 근거 여부 | 근거 문헌 및 위치 | 설명 |
|---|---|---|---|---|
| `severity_base` | scanner severity를 공통 점수로 정규화 | 약함 | 직접적인 NIST 점수식 없음 | severity 자체는 스캐너 운영 지표이므로 현재는 heuristic이다. 다만 38B가 `발견 -> 리스크 평가 -> 우선순위` 흐름을 제시하므로 severity를 입력 신호로 쓰는 방향은 구조적으로 부합한다. |
| `class_risk_bonus` | RSA, ECC, DH 같은 양자 취약 공개키 계열에 가중치 부여 | 강함 | NIST IR 8547, Background, p.3-4 부근; NIST IR 8547, security category 설명, p.12-13 Table 1; FIPS 203/204/205 각 표준의 category 표 | 8547은 RSA/ECDSA/ECDH 등 기존 공개키 계열이 양자 취약하다는 전환 배경을 직접 설명한다. FIPS 203/204/205는 ML-KEM, ML-DSA, SLH-DSA를 PQC 표준으로 제시한다. 따라서 공개키 계열을 weak hash보다 우선적으로 보는 것은 문헌과 일치한다. |
| `evidence_bonus` | 같은 class의 관련 finding 수가 많을수록 urgency 증가 | 약함 | 직접적인 NIST 수식 없음 | 이 값은 문헌 신뢰도 점수가 아니라 repo 내부의 scanner support 규모를 뜻한다. 38B Figure 2의 `발견 -> 정규화 -> 리스크 평가` 흐름은 상관과 aggregation의 필요성을 뒷받침하지만, issue_count × 3 같은 계산은 heuristic이다. |
| `spread_bonus` | 영향 파일 수가 많을수록 blast radius 증가 | 약함 | 직접적인 NIST 수식 없음 | 38B는 인벤토리와 사용처 파악의 중요성을 강조한다. 즉 영향 범위를 넓게 보는 판단축은 문헌과 맞지만, 파일 수에 비례한 가산 방식은 heuristic이다. |
| `scanner_bonus` | SAST/SCA/Config 다중 corroboration 시 actionability 증가 | 약함 | 38B Figure 2, 정규화/상관 필요성; 38B common format/SARIF 관련 부분 | 38B는 서로 다른 발견 도구 결과를 정규화하고 상관해야 한다고 명시한다. 따라서 cross-scanner corroboration을 신뢰 신호로 쓰는 방향은 문헌 정합적이다. 다만 `scanner_types * 4` 자체는 heuristic이다. |
| `exposure_bonus` | auth/token/TLS/certificate 등 외부 경계면의 긴급도 증가 | 중간~강함 | NIST SP 1800-38B, Summary/How to Use This Guide, “inventory is needed to apply policy and inform transformations”; NIST SP 1800-38C, TLS/QUIC sections, p.25-31 부근 | 38B는 단순 발견이 아니라 정책 적용과 전환 대상 식별을 위한 인벤토리의 중요성을 말한다. 38C는 TLS, QUIC, X.509처럼 외부 인터페이스와 직접 맞닿은 지점이 실제 이행 리스크가 큼을 실험으로 보여준다. 따라서 외부 노출 경계를 더 높게 보는 것은 문헌 기반 판단이다. |
| `hndl_bonus` | HNDL 가능성이 있는 경로를 우선 전환 대상으로 봄 | 강함 | NIST IR 8547, HNDL 설명 부분, Migration Considerations 및 timeline 섹션; 38B Risk Assessment에서 store-now-decrypt-later 언급 | 8547은 “harvest now, decrypt later”를 지금 전환을 시작해야 하는 핵심 이유로 명시한다. 특히 장기 기밀성 또는 장기적 인증 가치가 있는 데이터/경로를 더 일찍 다뤄야 한다는 판단은 이 문헌에 직접 근거한다. |
| `migration_complexity_bonus` | 설정, 의존성, 넓은 경계 전환을 조기에 surfaced | 중간 | NIST SP 1800-38B, common format / normalization / SARIF 관련 섹션; NIST IR 8547, hybrid complexity 관련 부분 | 38B는 여러 도구 결과를 정규화하고 상관해 계획 가능한 단위로 만드는 필요성을 강조한다. 8547은 hybrid가 복잡성과 비용을 증가시키는 임시 수단이라고 말한다. 따라서 전환 복잡성을 별도 factor로 다루는 것은 문헌 기반 해석이 가능하다. 다만 0~8 bonus 계산은 heuristic이다. |
| `interop_risk_bonus` | TLS/certificate/HSM/QUIC 경계의 호환성 리스크 반영 | 강함 | NIST SP 1800-38C 전체; TLS draft compliance 이슈, QUIC 인증서 크기→추가 RTT, Appendix C digest-then-sign 분석 | 38C의 핵심 메시지 중 하나가 바로 상호운용성과 배포 friction이다. 드래프트 버전 불일치, 식별자/코드포인트 관리, QUIC 증폭 방어, HSM/PKCS#11, digest-then-sign 문제 등은 이 factor의 직접 근거다. |
| `non_production_penalty` | tests/examples/fixtures가 운영 자산보다 먼저 올라가지 않도록 감점 | 없음 | 문헌 직접 근거 없음 | 이 값은 운영상 false priority inflation을 막기 위한 제품 heuristic이다. 문헌에서 직접 주는 규칙은 아니며, 발표 시에도 heuristic이라고 명확히 말하는 것이 맞다. |

## 4. 문헌 위치 상세 메모

### 4.1 `class_risk_bonus`

가장 직접적인 근거는 NIST IR 8547이다.

- 문서: `NIST IR 8547 (Initial Public Draft)`
- 참고 위치:
  - `Background`, p.3-4 부근
  - `security category` 설명과 `Table 1`, p.12-13 부근

핵심 의미:
- RSA, ECDSA, ECDH 같은 기존 공개키 계열은 양자 취약 전환 대상이다.
- PQC는 퍼센트 향상이 아니라 category 기반으로 설명된다.
- 따라서 공개키 전환 대상을 weak hash보다 더 큰 migration target으로 보는 것은 문헌 정합적이다.

보조 근거:
- `FIPS 203`: ML-KEM
- `FIPS 204`: ML-DSA
- `FIPS 205`: SLH-DSA

즉 현재 `RSA 18`, `DH 17`, `ECC 18`, `DSA 16`처럼 높은 class_risk를 주는 방향은 문헌 취지와 맞지만, 정확한 숫자 18/17/16은 우리가 heuristic으로 정한 값이다.

### 4.2 `exposure_bonus`

이 factor는 “외부 경계면에 있는 암호가 더 시급하다”는 관점을 반영한다.

주요 근거:

- 문서: `NIST SP 1800-38B`
- 참고 위치:
  - `Summary`
  - `How to Use This Guide`
  - cryptographic inventory가 policy 적용과 transformation에 필요하다고 설명하는 부분

- 문서: `NIST SP 1800-38C`
- 참고 위치:
  - `TLS` 섹션
  - `QUIC` 섹션
  - p.25-31 부근의 handshake / certificate / RTT 관련 표와 그림

해석:
- auth, token, TLS, certificate 경계는 실제 외부 시스템과 맞닿아 있는 지점이다.
- 38C는 이런 경계가 단순한 코드 수정이 아니라 프로토콜/배포/상호운용 리스크와 이어짐을 실험으로 보여준다.
- 따라서 외부 경계 키워드가 있으면 우선순위를 올리는 것은 문헌 기반 해석이다.

단, `10점`이라는 수치 자체는 heuristic이다.

### 4.3 `hndl_bonus`

이 factor는 교수님께 가장 설명하기 쉬운 문헌 기반 factor다.

주요 근거:

- 문서: `NIST IR 8547`
- 참고 위치:
  - `Migration Considerations`
  - `Towards a PQC Standards Transition Timeline`
  - HNDL 설명이 나오는 본문

deep-research 문서 요약에 따르면:
- 8547은 “harvest now, decrypt later” 때문에 지금 전환을 시작해야 한다고 강조한다.
- 장기 기밀성 또는 장기 인증 가치가 있는 영역이 더 빨리 전환되어야 한다는 관점을 제공한다.

보조 근거:
- `NIST SP 1800-38B` Risk Assessment 관련 부분에서도 store-now-decrypt-later 맥락이 언급된다.

해석:
- auth / token / certificate / identity 같은 경로는 장기적으로 의미가 남을 가능성이 커서 HNDL 민감 경로로 가산하는 것이 합리적이다.

단, `8점`이라는 수치 자체는 heuristic이다.

### 4.4 `migration_complexity_bonus`

이 factor는 “복잡한 전환일수록 늦게 보기보다 먼저 surfaced해야 한다”는 제품 설계 판단이다.

주요 근거:

- 문서: `NIST SP 1800-38B`
- 참고 위치:
  - `Architecture`
  - `Normalization`
  - `common format`
  - `SARIF` 관련 부분

핵심 메시지:
- 발견 결과를 그대로 두면 계획 가능한 migration unit이 되지 않는다.
- 정규화와 상관이 필요하다.

보조 근거:

- 문서: `NIST IR 8547`
- 참고 위치:
  - `Migration Considerations`
  - `hybrid solutions add complexity... increase security risks and costs...`

해석:
- config, dependency, library boundary가 걸린 recommendation은 단순 코드 한 줄 수정이 아니라 구조적 전환이 필요할 가능성이 높다.
- hybrid나 경계 전환은 비용과 위험이 증가할 수 있다.
- 따라서 복잡성 신호를 조기 계획 대상으로 올리는 것은 문헌 해석과 정합적이다.

단, `0~8` 범위의 구체 계산은 heuristic이다.

### 4.5 `interop_risk_bonus`

이 factor는 38C가 가장 직접적으로 뒷받침한다.

주요 근거:

- 문서: `NIST SP 1800-38C`
- 참고 위치:
  - `TLS` 섹션
  - `QUIC` 섹션
  - `X.509` 관련 내용
  - `HSMs` 섹션
  - `Appendix C`의 `digest-then-sign` 분석

deep-research 문서 요약에 따르면:
- 드래프트 표준 버전 불일치
- 식별자/코드포인트 관리
- QUIC에서 인증서 체인 크기로 인한 추가 RTT
- PKCS#11/HSM 경계
- digest-then-sign 가정 붕괴

같은 문제가 실제 이행 리스크로 관찰된다.

즉:
- `TLS`
- `certificate`
- `HSM`
- `QUIC`

같은 키워드가 보이면 interop risk를 높게 보는 것은 문헌 직접 근거가 강하다.

단, `8점`이라는 수치는 heuristic이다.

### 4.6 `severity_base`

이 factor는 문헌이 아니라 scanner engineering 기준에 더 가깝다.

설명:
- NIST 문서는 보통 “scanner severity를 45% 반영하라”는 식의 점수식을 주지 않는다.
- 현재 `severity_base = int(SEVERITY_SCORE[max_severity] * 0.45)`는 구현용 heuristic이다.

다만 정당화는 가능하다.

- 38B는 `발견 -> 정규화 -> 리스크 평가 -> 우선순위`를 하나의 파이프라인으로 본다.
- 따라서 스캐너가 낸 severity를 risk assessment 입력값으로 쓰는 것 자체는 구조적으로 맞다.

즉:
- factor 채택은 설명 가능
- 수치는 heuristic

### 4.7 `evidence_bonus`, `spread_bonus`, `scanner_bonus`

이 세 factor는 현재 문헌 직접 근거보다 제품 운영 heuristic 성격이 강하다.

다만 38B와 연결은 가능하다.

- `evidence_bonus`
  - 같은 class의 finding이 많을수록 remediation pressure 증가
- `spread_bonus`
  - 영향 파일이 많을수록 blast radius 증가
- `scanner_bonus`
  - SAST / SCA / Config가 동시에 지지하면 actionability 증가

문헌 연결 지점:

- 문서: `NIST SP 1800-38B`
- 참고 위치:
  - Figure 2의 `discovery -> normalization -> risk assessment -> prioritization`
  - `common format`
  - `normalization`
  - `SARIF`

해석:
- 여러 source를 모아서 정규화하고 상관해 리스크를 판단해야 한다는 점은 38B가 직접 말한다.
- 하지만 `issue_count * 3`, `affected_files * 4`, `scanner_types * 4`는 문헌이 아니라 heuristic이다.

발표에서는 이렇게 말하는 것이 맞다.

> 이 세 factor는 문헌이 직접 준 수치 모델은 아니고, 38B의 정규화/상관/우선순위화 구조를 구현하기 위한 운영용 heuristic입니다.

### 4.8 `non_production_penalty`

이 factor는 현재 문헌 직접 근거가 없다.

설명:
- 테스트, fixture, example 자산이 운영 자산보다 먼저 올라오면 실제 기업용 우선순위 판단이 왜곡된다.
- 이를 방지하기 위해 제품 수준에서 감점을 둔 것이다.

따라서 발표 시 이렇게 설명하는 것이 맞다.

> 이 항목은 NIST가 직접 제시한 factor가 아니라, 데모 및 실제 레포 분석에서 테스트 자산이 과대평가되는 현상을 줄이기 위한 제품 heuristic입니다.

## 5. 교수님께 설명할 때의 권장 표현

다음처럼 설명하는 것이 가장 안전하다.

### 권장 표현

- 우선순위 모델의 **factor 선정**은 NIST IR 8547, NIST SP 1800-38B, NIST SP 1800-38C, FIPS 203/204/205를 참고했다.
- 특히 공개키 전환 중요도, HNDL, 상호운용성 리스크, 인벤토리/정규화의 필요성은 문헌에 직접 근거한다.
- 다만 현재 **정확한 숫자 가중치**는 프로토타입 단계의 heuristic이며, 향후 공개 레포 실험과 전문가 검토를 통해 보정할 예정이다.

### 피해야 할 표현

- “이 점수식은 NIST가 직접 제시한 공식이다.”
- “모든 숫자 weight를 논문에서 그대로 가져왔다.”

## 6. 현재 모델의 한계

이 문서를 기준으로 현재 모델의 한계도 분명히 말해야 한다.

1. `severity_base`, `evidence_bonus`, `spread_bonus`, `scanner_bonus`, `non_production_penalty`는 문헌 직접 근거보다 heuristic 성격이 강하다.
2. `exposure_bonus`, `migration_complexity_bonus`도 문헌 해석 기반이지만 수치화는 heuristic이다.
3. 따라서 현재 모델은 “문헌 기반 factor selection + heuristic scoring”으로 설명하는 것이 정확하다.

## 7. 결론

현재 Q-shield의 우선순위 모델은 완전히 문헌이 제공한 점수표를 구현한 것이 아니다.

대신 다음에 가깝다.

> NIST/PQC 문헌이 제시한 전환 관점과 리스크 축을 가져오고, 이를 실제 스캐너 findings에 적용할 수 있도록 heuristic 기반 점수 모델로 구현한 상태

즉 교수님께는 다음처럼 답하는 것이 가장 적절하다.

- 공개키 양자 취약성, HNDL, 상호운용성 리스크, inventory/normalization 필요성은 NIST 문헌에 직접 근거합니다.
- 반면 severity 가중치, finding 수 가중치, 테스트 경로 감점 등은 현재 프로토타입 단계의 heuristic입니다.
- 앞으로는 공개 GitHub 레포와 hand-crafted fixture를 이용한 ranking evaluation으로 weight를 보정할 계획입니다.
