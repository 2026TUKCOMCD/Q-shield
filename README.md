# 🛡️ AI 기반 PQC(양자내성암호) 전환 우선순위 진단 플랫폼

> **AI-based PQC Transition Priority Diagnosis Platform**
>
> 사용자의 GitHub 레포지토리를 분석하여 PQC 취약점을 탐지하고, AI 기반으로 비즈니스 문맥을 고려한 전환 우선순위를 제안하는 솔루션입니다.

<br>

## 🏗️ 소프트웨어 구조도

![AI PQC Platform Architecture](software_architecture.png)

1.  **Presentation Layer (Next.js)**
    - 사용자가 GitHub URL을 입력하고 분석 결과를 확인하는 대시보드입니다
    - 서버로부터 받은 JSON 데이터를 기반으로 **PQC 준비도 히트맵**과 **전환 로드맵**을 시각적으로 렌더링합니다

2.  **Application Layer (FastAPI & Scanners)**
    - **API Gateway**: 요청을 받아 인증을 처리하고, 대규모 작업을 처리하기 위해 **Celery & Redis** 비동기 큐로 작업을 넘깁니다.
    - **3-Way Scanners**:
        - `SAST`: 소스코드 내부의 암호 함수 호출 패턴을 분석합니다.
        - `SCA`: 프로젝트의 종속성(라이브러리)을 분석하여 PQC 미지원 버전을 탐지합니다.
        - `Config`: 설정 파일 및 인증서의 취약점을 진단합니다.

3.  **AI Analysis Layer (OpenAI)**
    - 스캐너가 수집한 '기술적 취약점(Fact)'과 사용자의 '비즈니스 문맥(Context)'을 결합합니다.
    - LLM을 활용해 단순 탐지를 넘어 **리팩토링 비용**과 **전환 우선순위**를 산출합니다.

4.  **Data Layer (PostgreSQL & S3)**
    - 분석 결과와 사용자 로그 등 구조화된 데이터는 **PostgreSQL**에 저장합니다.
    - 생성된 PDF 리포트나 시각화용 이미지 파일은 **Amazon S3**에 저장하여 성능을 최적화합니다.

<br>
  
## 🌍 System Environment

| 환경 (Environment) | 목적 (Purpose) | 구성 요소 (Components) |
| :--- | :--- | :--- |
| **💻 개발 (Dev)** | 기능 구현 및 단위 테스트 | • **OS:** Local PC (Win/Mac)<br>• **Infra:** Docker Desktop (Local DB/Redis)<br>• **Tool:** VS Code |
| **🚀 운용 (Prod)** | 실제 사용자 진단 서비스 | • **Cloud:** AWS EC2<br>• **CI/CD:** GitHub Actions<br>• **Monitoring:** Sentry, CloudWatch |
| **🎤 데모 (Demo)** | 발표 및 기능 시연 | • **Data:** Pre-set Sample Project (취약점 포함)<br>• **Feature:** PQC Readiness Dashboard 시연 최적화 |

<br>

## 📅 Project Roadmap & Backlog
### 📌 EPIC별 Product Backlog

| EPIC | 주요 기능 (Stories) | 담당자 |
| :--- | :--- | :---: |
| **Core Scanning** | • SAST(암호패턴), SCA(라이브러리), Config(설정) 스캐너 구현 | 최진혁, 허준영 |
| **AI & Risk** | • OpenAI 프롬프트 엔지니어링<br>• 위험도/비용 산출 알고리즘 | 경건웅 |
| **Backend** | • FastAPI 설계 및 비동기 큐(Celery) 연동<br>• DB 스키마 설계 | 허준영, 최진혁 |
| **Dashboard** | • 히트맵 시각화 및 리포트 PDF 다운로드 구현 | 경건웅 |

<br>
### 🚀 수행 로드맵 (Project Roadmap)

```mermaid
graph TD
    %% 스타일 정의 (이미지의 색상 테마 반영)
    classDef m1 fill:#dbeafe,stroke:#1e40af,stroke-width:2px,color:#1e3a8a;
    classDef m2 fill:#ffedd5,stroke:#c2410c,stroke-width:2px,color:#9a3412;
    classDef m3 fill:#fef9c3,stroke:#a16207,stroke-width:2px,color:#854d0e;
    classDef m4 fill:#dcfce7,stroke:#15803d,stroke-width:2px,color:#14532d;
    classDef m5 fill:#e0f2fe,stroke:#0369a1,stroke-width:2px,color:#075985;
    classDef m6 fill:#f3e8ff,stroke:#7e22ce,stroke-width:2px,color:#6b21a8;

    %% 노드 정의 및 연결
    subgraph M1 [10월~12월: 기획 및 설계 Total: 13 SP]
        direction TB
        T1-01(E1-01. PQC 가이드라인 분석<br/>NIST/NSA 표준 정립 <br/>- 5 SP):::m1
        T1-02(E1-02. 아키텍처 설계<br/>MSA 구조 및 DB ERD <br/>- 5 SP):::m1
        T1-03(E1-03. API 명세서 작성<br/>Swagger/OpenAPI <br/>- 3 SP):::m1
    end

    subgraph M2 [1월 중~1월 말: 스캔 엔진 구현 Total: 21 SP]
        direction TB
        T2-01(E2-01. SAST 파서 개발<br/>AST 기반 코드 분석 <br/>- 8 SP):::m2
        T2-02(E2-02. SCA 종속성 분석<br/>라이브러리 취약점 탐지 <br/>- 8 SP):::m2
        T2-03(E2-03. Config 진단<br/>인증서/설정 파일 스캔 <br/>- 5 SP):::m2
    end

    subgraph M3 [1월 말~2월 초: AI 분석 및 위험도 Total: 18 SP]
        direction TB
        T3-01(E3-01. OpenAI 연동<br/>GPT-4o API 통합<br/> - 5 SP):::m3
        T3-02(E3-02. 프롬프트 엔지니어링<br/>문맥 기반 리팩토링 제안<br/> - 8 SP):::m3
        T3-03(E3-03. 위험도 산출 로직<br/>우선순위 스코어링<br/> - 5 SP):::m3
    end

    subgraph M4 [2월 초~2월 중: 백엔드 & 비동기 Total: 15 SP]
        direction TB
        T4-01(E4-01. 비동기 큐 구축<br/>Celery & Redis <br/>- 5 SP):::m4
        T4-02(E4-02. FastAPI 보안 <br/>- 5 SP):::m4
        T4-03(E4-03. 대용량 처리 최적화 <br/>- 5 SP):::m4
    end

    subgraph M5 [2월 중~2월 말: 프론트엔드 & 시각화 <br/>Total: 13 SP]
        direction TB
        T5-01(E5-01. PQC 히트맵<br/>Recharts 시각화 <br/>- 5 SP):::m5
        T5-02(E5-02. 리포트 생성<br/>PDF Export <br/>- 5 SP):::m5
        T5-03(E5-03. 대시보드 UX<br/>반응형 웹 구현 <br/>- 3 SP):::m5
    end

    subgraph M6 [2월 말: 인프라 & 배포 <br/>Total: 8 SP]
        direction TB
        T6-01(E6-01. AWS 배포<br/>EC2 & S3 연동 <br/>- 5 SP):::m6
        T6-02(E6-02. CI/CD 파이프라인<br/>GitHub Actions <br/>- 3 SP):::m6
    end

    %% 프로세스 흐름 화살표
    M1 ==> M2 ==> M3 ==> M4 ==> M5 ==> M6
