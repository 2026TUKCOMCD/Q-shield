# Feature Specification: AI-PQC Scanner Frontend

**Feature Branch**: `1-pqc-scanner-frontend`  
**Created**: 2026-01-26  
**Status**: Draft  
**Input**: User description: "Functional Specification: AI-PQC Scanner Frontend 1. 개요 (Overview) 본 프로젝트는 소스 코드 내 암호 자산을 식별하고 양자 내성 암호(PQC) 이주 로드맵을 제공하는 보안 플랫폼의 프론트엔드 개발을 목표로 한다. 본 명세서는 백엔드 및 스캐너 엔진과의 협업을 위한 인터페이스 규격과 UI 요구사항을 정의한다. 2. 개발 범위 및 역할 분담 (Scope & Responsibility) 프론트엔드 (본 프로젝트 범위): React 기반 5대 핵심 화면 UI/UX 구현. 백엔드 API 연동 및 상태 관리. 보안 지표 시각화 (Charts, Heatmap). 백엔드 (외부 협업 범위 - 요청 필요): 3단계 분석 엔진(Rule-based, LLM Context, Cost Model) 구현. 소스 코드 스캐너(SAST/SCA/Config) 및 패턴 DB 구축. 프론트엔드 요구에 맞춘 RESTful API 제공. 3. 핵심 화면 및 기능 요구사항 3.1. Dashboard (Scan Overview) 기능: 프로젝트의 전반적인 PQC 준비 상태를 시각화. 주 ECC, AES 등 알고리즘 비율 시각화. Inventory Table: 알고리즘별 사용 횟수 및 최고 위험도 리스트. 백엔드 요청 데이터: /api/scans/{uuid}/inventory. 3.4. Repository Heatmap (Visual Tree) 기능: 리포지토리 내 파일 시스템의 위험도를 직관적으로 파악. 주요 컴포넌트: File Tree Layout: 폴더/파일 구조를 트리 형태로 표시. Risk Coloring: 위험도(Risk Score)에 따라 파일명을 빨강/주황/초록으로 하이라이팅. 백엔드 요청 데이터: /api/scans/{uuid}/heatmap. 3.5. PQC Recommendations (Action Items) 기능: 우선순위가 높은 조치 사항과 AI 리팩토링 가이드 제공. 주요 컴포넌트: Priority Table: 우선순위, 이슈명, 예상 비용(M/D), 추천 알고리즘 표기. AI Detail View: 특정 이슈 클릭 시 노출되는 AI 진단 의견 및 코드 스니펫. 백엔드 요청 데이터: /api/scans/{uuid}/recommendations. 4. 백엔드 협업용 API 인터페이스 규격 (Frontend Requiremoat (0.0-10.0)", // 최종 보정 점수 "priority_rank": "integer", // 우선순위 순위 "estimated_effort": "string", // 예: "3 M/D" "ai_recommendation": "string (Markdown)" // 리팩토링 가이드 } ] } 5. 기술적 제약 및 인터페이스 원칙 상태 동기화: 스캔은 비동기로 진행되므로, 프론트엔드는 폴링(Polling) 또는 상태 확인 API를 통해 UI를 갱신한다. UI 일관성: 모든 위험도는 speckit.constitution에 정의된 테마 컬러(Danger: #FF4136 등)를 준수하여 렌더링한다. 오류 처리: 백엔드 스캐너 장애 시 사용자에게 "스캐너 서버 연결 불가" 등의 명확한 에러 메시지를 노출한다. 6. 유저 스토리 (Frontend POV) "사용자는 GitHub URL 입력 후 스캔이 진행되는 동안 대시보드에서 실시간 상태를 확인하고 싶다." "사용자는 발견된 RSA 알고리즘 중 결제 로직(Context)에 포함된 항목을 가장 먼저 필터링하여 보고 싶다.Functional Specification: AI-PQC Scanner Frontend 1. 개요 (Overview) 본 프로젝트는 소스 코드 내 암호 자산을 식별하고 양자 내성 암호(PQC) 이주 로드맵을 제공하는 보안 플랫폼의 프론트엔드 개발을 목표로 한다. 본 명세서는 백엔드 및 스캐너 엔진과의 협업을 위한 인터페이스 규격과 UI 요구사항을 정의한다. 2. 개발 범위 및 역할 분담 (Scope & Responsibility) 프론트엔드 (본 프로젝트 범위): React 기반 5대 핵심 화면 UI/UX 구현. 백엔드 API 연동 및 상태 관리. 보안 지표 시각화 (Charts, Heatmap). 백엔드 (외부 협업 범위 - 요청 필요): 3단계 분석 엔진(Rule-based, LLM Context, Cost Model) 구현. 소스 코드 스캐너(SAST/SCA/Config) 및 패턴 DB 구축. 프론트엔드 요구에 맞춘 RESTful API 제공. 3. 핵심 화면 및 기능 요구사항 3.1. Dashboard (Scan Overview) 기능: 프로젝트의 전반적인 PQC 준비 상태를 시각화. 주 ECC, AES 등 알고리즘 비율 시각화. Inventory Table: 알고리즘별 사용 횟수 및 최고 위험도 리스트. 백엔드 요청 데이터: /api/scans/{uuid}/inventory. 3.4. Repository Heatmap (Visual Tree) 기능: 리포지토리 내 파일 시스템의 위험도를 직관적으로 파악. 주요 컴포넌트: File Tree Layout: 폴더/파일 구조를 트리 형태로 표시. Risk Coloring: 위험도(Risk Score)에 따라 파일명을 빨강/주황/초록으로 하이라이팅. 백엔드 요청 데이터: /api/scans/{uuid}/heatmap. 3.5. PQC Recommendations (Action Items) 기능: 우선순위가 높은 조치 사항과 AI 리팩토링 가이드 제공. 주요 컴포넌트: Priority Table: 우선순위, 이슈명, 예상 비용(M/D), 추천 알고리즘 표기. AI Detail View: 특정 이슈 클릭 시 노출되는 AI 진단 의견 및 코드 스니펫. 백엔드 요청 데이터: /api/scans/{uuid}/recommendations. 4. 백엔드 협업용 API 인터페이스 규격 (Frontend Requiremoat (0.0-10.0)", // 최종 보정 점수 "priority_rank": "integer", // 우선순위 순위 "estimated_effort": "string", // 예: "3 M/D" "ai_recommendation": "string (Markdown)" // 리팩토링 가이드 } ] } 5. 기술적 제약 및 인터페이스 원칙 상태 동기화: 스캔은 비동기로 진행되므로, 프론트엔드는 폴링(Polling) 또는 상태 확인 API를 통해 UI를 갱신한다. UI 일관성: 모든 위험도는 speckit.constitution에 정의된 테마 컬러(Danger: #FF4136 등)를 준수하여 렌더링한다. 오류 처리: 백엔드 스캐너 장애 시 사용자에게 "스캐너 서버 연결 불가" 등의 명확한 에러 메시지를 노출한다. 6. 유저 스토리 (Frontend POV) "사용자는 GitHub URL 입력 후 스캔이 진행되는 동안 대시보드에서 실시간 상태를 확인하고 싶다." "사용자는 발견된 RSA 알고리즘 중 결제 로직(Context)에 포함된 항목을 가장 먼저 필터링하여 보고 싶다.Functional Specification: AI-PQC Scanner Frontend 1. 개요 (Overview) 본 프로젝트는 소스 코드 내 암호 자산을 식별하고 양자 내성 암호(PQC) 이주 로드맵을 제공하는 보안 플랫폼의 프론트엔드 개발을 목표로 한다. 본 명세서는 백엔드 및 스캐너 엔진과의 협업을 위한 인터페이스 규격과 UI 요구사항을 정의한다. 2. 개발 범위 및 역할 분담 (Scope & Responsibility) 프론트엔드 (본 프로젝트 범위): React 기반 5대 핵심 화면 UI/UX 구현. 백엔드 API 연동 및 상태 관리. 보안 지표 시각화 (Charts, Heatmap). 백엔드 (외부 협업 범위 - 요청 필요): 3단계 분석 엔진(Rule-based, LLM Context, Cost Model) 구현. 소스 코드 스캐너(SAST/SCA/Config) 및 패턴 DB 구축. 프론트엔드 요구에 맞춘 RESTful API 제공. 3. 핵심 화면 및 기능 요구사항 3.1. Dashboard (Scan Overview) 기능: 프로젝트의 전반적인 PQC 준비 상태를 시각화. 주 ECC, AES 등 알고리즘 비율 시각화. Inventory Table: 알고리즘별 사용 횟수 및 최고 위험도 리스트. 백엔드 요청 데이터: /api/scans/{uuid}/inventory. 3.4. Repository Heatmap (Visual Tree) 기능: 리포지토리 내 파일 시스템의 위험도를 직관적으로 파악. 주요 컴포넌트: File Tree Layout: 폴더/파일 구조를 트리 형태로 표시. Risk Coloring: 위험도(Risk Score)에 따라 파일명을 빨강/주황/초록으로 하이라이팅. 백엔드 요청 데이터: /api/scans/{uuid}/heatmap. 3.5. PQC Recommendations (Action Items) 기능: 우선순위가 높은 조치 사항과 AI 리팩토링 가이드 제공. 주요 컴포넌트: Priority Table: 우선순위, 이슈명, 예상 비용(M/D), 추천 알고리즘 표기. AI Detail View: 특정 이슈 클릭 시 노출되는 AI 진단 의견 및 코드 스니펫. 백엔드 요청 데이터: /api/scans/{uuid}/recommendations. 4. 백엔드 협업용 API 인터페이스 규격 (Frontend Requiremoat (0.0-10.0)", // 최종 보정 점수 "priority_rank": "integer", // 우선순위 순위 "estimated_effort": "string", // 예: "3 M/D" "ai_recommendation": "string (Markdown)" // 리팩토링 가이드 } ] } 5. 기술적 제약 및 인터페이스 원칙 상태 동기화: 스캔은 비동기로 진행되므로, 프론트엔드는 폴링(Polling) 또는 상태 확인 API를 통해 UI를 갱신한다. UI 일관성: 모든 위험도는 speckit.constitution에 정의된 테마 컬러(Danger: #FF4136 등)를 준수하여 렌더링한다. 오류 처리: 백엔드 스캐너 장애 시 사용자에게 "스캐너 서버 연결 불가" 등의 명확한 에러 메시지를 노출한다. 6. 유저 스토리 (Frontend POV) "사용자는 GitHub URL 입력 후 스캔이 진행되는 동안 대시보드에서 실시간 상태를 확인하고 싶다." "사용자는 발견된 RSA 알고리즘 중 결제 로직(Context)에 포함된 항목을 가장 먼저 필터링하여 보고 싶다.Functional Specification: AI-PQC Scanner Frontend 1. 개요 (Overview) 본 프로젝트는 소스 코드 내 암호 자산을 식별하고 양자 내성 암호(PQC) 이주 로드맵을 제공하는 보안 플랫폼의 프론트엔드 개발을 목표로 한다. 본 명세서는 백엔드 및 스캐너 엔진과의 협업을 위한 인터페이스 규격과 UI 요구사항을 정의한다. 2. 개발 범위 및 역할 분담 (Scope & Responsibility) 프론트엔드 (본 프로젝트 범위): React 기반 5대 핵심 화면 UI/UX 구현. 백엔드 API 연동 및 상태 관리. 보안 지표 시각화 (Charts, Heatmap). 백엔드 (외부 협업 범위 - 요청 필요): 3단계 분석 엔진(Rule-based, LLM Context, Cost Model) 구현. 소스 코드 스캐너(SAST/SCA/Config) 및 패턴 DB 구축. 프론트엔드 요구에 맞춘 RESTful API 제공. 3. 핵심 화면 및 기능 요구사항 3.1. Dashboard (Scan Overview) 기능: 프로젝트의 전반적인 PQC 준비 상태를 시각화. 주 ECC, AES 등 알고리즘 비율 시각화. Inventory Table: 알고리즘별 사용 횟수 및 최고 위험도 리스트. 백엔드 요청 데이터: /api/scans/{uuid}/inventory. 3.4. Repository Heatmap (Visual Tree) 기능: 리포지토리 내 파일 시스템의 위험도를 직관적으로 파악. 주요 컴포넌트: File Tree Layout: 폴더/파일 구조를 트리 형태로 표시. Risk Coloring: 위험도(Risk Score)에 따라 파일명을 빨강/주황/초록으로 하이라이팅. 백엔드 요청 데이터: /api/scans/{uuid}/heatmap. 3.5. PQC Recommendations (Action Items) 기능: 우선순위가 높은 조치 사항과 AI 리팩토링 가이드 제공. 주요 컴포넌트: Priority Table: 우선순위, 이슈명, 예상 비용(M/D), 추천 알고리즘 표기. AI Detail View: 특정 이슈 클릭 시 노출되는 AI 진단 의견 및 코드 스니펫. 백엔드 요청 데이터: /api/scans/{uuid}/recommendations. 5. 기술적 제약 및 인터페이스 원칙 상태 동기화: 스캔은 비동기로 진행되므로, 프론트엔드는 폴링(Polling) 또는 상태 확인 API를 통해 UI를 갱신한다. UI 일관성: 모든 위험도는 speckit.constitution에 정의된 테마 컬러(Danger: #FF4136 등)를 준수하여 렌더링한다. 오류 처리: 백엔드 스캐너 장애 시 사용자에게 "스캐너 서버 연결 불가" 등의 명확한 에러 메시지를 노출한다. 6. 유저 스토리 (Frontend POV) "사용자는 GitHub URL 입력 후 스캔이 진행되는 동안 대시보드에서 실시간 상태를 확인하고 싶다." "사용자는 발견된 RSA 알고리즘 중 결제 로직(Context)에 포함된 항목을 가장 먼저 필터링하여 보고 싶다.1. 개요 (Overview) 본 프로젝트는 소스 코드 내 암호 자산을 식별하고 양자 내성 암호(PQC) 이주 로드맵을 제공하는 보안 플랫폼의 프론트엔드 개발을 목표로 한다. 본 명세서는 백엔드 및 스캐너 엔진과의 협업을 위한 인터페이스 규격과 UI 요구사항을 정의한다. 2. 개발 범위 및 역할 분담 (Scope & Responsibility) 프론트엔드 (본 프로젝트 범위): React 기반 5대 핵심 화면 UI/UX 구현. 백엔드 API 연동 및 상태 관리. 보안 지표 시각화 (Charts, Heatmap). 백엔드 (외부 협업 범위 - 요청 필요): 3단계 분석 엔진(Rule-based, LLM Context, Cost Model) 구현. 소스 코드 스캐너(SAST/SCA/Config) 및 패턴 DB 구축. 프론트엔드 요구에 맞춘 RESTful API 제공. 3. 핵심 화면 및 기능 요구사항 3.1. Dashboard (Scan Overview) 기능: 프로젝트의 전반적인 PQC 준비 상태를 시각화. 주요 컴포넌트: Readiness Gauge: 현재 점수 v 횟수 및 최고 위험도 리스트. 백엔드 요청 데이터: /api/scans/{uuid}/inventory. 3.4. Repository Heatmap (Visual Tree) 기능: 리포지토리 내 파일 시스템의 위험도를 직관적으로 파악. 주요 컴포넌트: File Tree Layout: 폴더/파일 구조를 트리 형태로 표시. Risk Coloring: 위험도(Risk Score)에 따라 파일명을 빨강/주황/초록으로 하이라이팅. 백엔드 요청 데이터: /api/scans/{uuid}/heatmap. 3.5. PQC Recommendations (Action Items) 기능: 우선순위가 높은 조치 사항과 AI 리팩토링 가이드 제공. 주요 컴포넌트: Priority Table: 우선순위, 이슈명, 예상 비용(M/D), 추천 알고리즘 표기. AI Detail View: 특정 이슈 클릭 시 노출되는 AI 진단 의견 및 코드 스니펫. 백엔드 요청 데이터: /api/scans/{uuid}/recommendations. 5. 기술적 제약 및 인터페이스 원칙 상태 동기화: 스캔은 비동기로 진행되므로, 프론트엔드는 폴링(Polling) 또는 상태 확인 API를 통해 UI를 갱신한다. UI 일관성: 모든 위험도는 speckit.constitution에 정의된 테마 컬러(Danger: #FF4136 등)를 준수하여 렌더링한다. 오류 처리: 백엔드 스캐너 장애 시 사용자에게 "스캐너 서버 연결 불가" 등의 명확한 에러 메시지를 노출한다. 6. 유저 스토리 (Frontend POV) "사용자는 GitHub URL 입력 후 스캔이 진행되는 동안 대시보드에서 실시간 상태를 확인하고 싶다." "사용자는 발견된 RSA 알고리즘 중 결제 로직(Context)에 포함된 항목을 가장 먼저 필터링하여 보고 싶다.""

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Real-time Scan Status Monitoring (Priority: P1)

Users want to input a GitHub URL and monitor the real-time status of the PQC scan on the Dashboard. This includes seeing the overall PQC readiness and basic cryptographic asset inventory as the scan progresses.

**Why this priority**: This is the primary entry point and immediate feedback mechanism for users initiating a scan, directly impacting user engagement and the perceived responsiveness of the platform.

**Independent Test**: Can be fully tested by submitting a GitHub URL and verifying that the Dashboard updates dynamically with scan progress indicators (e.g., loading states, partial data display) and eventually displays initial scan overview data.

**Acceptance Scenarios**:

1.  **Given** the user is on the scan input page, **When** they enter a valid GitHub URL and initiate a scan, **Then** they are redirected to the Dashboard, and a loading indicator is displayed.
2.  **Given** a scan is in progress, **When** the Dashboard is viewed, **Then** the PQC readiness gauge and initial inventory table show real-time updates or pending states.
3.  **Given** the scan completes successfully, **When** the Dashboard is viewed, **Then** the PQC readiness gauge displays the final score and the inventory table is fully populated.

---

### User Story 2 - Prioritized PQC Recommendation Filtering (Priority: P1)

Users want to filter and prioritize PQC recommendations, specifically focusing on cryptographic algorithms (like RSA) within critical contexts such as payment logic.

**Why this priority**: This addresses a critical need for security teams to quickly identify and address high-impact vulnerabilities, enabling targeted PQC migration efforts based on business risk.

**Independent Test**: Can be fully tested by navigating to the PQC Recommendations section, applying filters for specific algorithms (e.g., RSA) and contexts (e.g., payment logic), and verifying that the priority table displays relevant recommendations correctly ordered by priority.

**Acceptance Scenarios**:

1.  **Given** the user is viewing PQC Recommendations, **When** they filter by "RSA" algorithm and "Payment Logic" context, **Then** the Priority Table displays only RSA-related issues within payment logic, ordered by priority.
2.  **Given** filtered recommendations are displayed, **When** the user clicks on a specific issue in the Priority Table, **Then** the AI Detail View opens, showing detailed AI diagnosis and code snippets for that issue.

---

### User Story 3 - Repository Risk Visualization (Priority: P2)

Users want to intuitively understand the cryptographic risk distribution within their repository's file system through a visual heatmap.

**Why this priority**: Provides a quick, at-a-glance overview of code security hotspots, facilitating focused investigations and resource allocation.

**Independent Test**: Can be fully tested by navigating to the Repository Heatmap, verifying that the file tree layout accurately reflects the repository structure, and files are colored according to their risk score.

**Acceptance Scenarios**:

1.  **Given** the user is on the Repository Heatmap page, **When** the page loads successfully, **Then** a file tree layout of the repository is displayed.
2.  **Given** the file tree is displayed, **When** risk scores are available, **Then** filenames are highlighted in appropriate colors (red/orange/green) corresponding to their risk levels.

---

## Requirements *(mandatory)*

### Functional Requirements

-   **FR-001**: The system MUST implement a React-based frontend for 5 core screens: Dashboard, Repository Heatmap, PQC Recommendations, Initial Scan Input & History (for entering GitHub URLs and viewing past scans), and Inventory Detail (for detailed cryptographic asset inventory).
-   **FR-002**: The system MUST integrate with backend APIs for data retrieval and state management, specifically for scan inventory (`/api/scans/{uuid}/inventory`), heatmap data (`/api/scans/{uuid}/heatmap`), and recommendations (`/api/scans/{uuid}/recommendations`).
-   **FR-003**: The Dashboard MUST visualize the overall PQC readiness state, including ECC and AES algorithm ratios, and an inventory table showing algorithm usage and highest risk.
-   **FR-004**: The Repository Heatmap MUST display a file tree layout with risk coloring (red/orange/green) based on file-level risk scores.
-   **FR-005**: The PQC Recommendations section MUST display a prioritized table of action items (issue name, estimated effort, recommended algorithm) and an AI Detail View for individual issue diagnosis and code snippets.
-   **FR-006**: The frontend MUST handle asynchronous scan processes by regularly polling a status check API to update the UI.
-   **FR-007**: The UI MUST adhere to theme colors (e.g., Danger: #FF4136) for risk level visualization, as defined in `speckit.constitution`.
-   **FR-008**: The system MUST display clear and user-friendly error messages (e.g., "Scanner server connection unavailable") if the backend scanner fails or is unreachable.
-   **FR-009**: The system MUST allow users to input a GitHub URL to initiate a scan.
-   **FR-010**: The system MUST provide filtering capabilities for PQC recommendations based on cryptographic algorithms (e.g., RSA) and contextual information (e.g., payment logic).

### Key Entities *(include if feature involves data)*

-   **Scan**: Represents a PQC analysis of a repository. Key attributes include a unique identifier (`uuid`), current status (e.g., in progress, completed, failed), and associated scan results.
-   **Cryptographic Asset**: An identified instance of a cryptographic algorithm or primitive within the source code. Attributes include algorithm type (e.g., ECC, AES, RSA), location (file path, line numbers), and associated risk score.
-   **Recommendation**: A suggested action item for PQC migration. Attributes include priority rank, issue name, estimated effort, AI-generated refactoring guidance (Markdown), and recommended PQC algorithm.
-   **Repository File**: A file within the scanned repository. Attributes include file path, structure within the file tree, and aggregated risk score.

## Success Criteria *(mandatory)*

### Measurable Outcomes

-   **SC-001**: Users can initiate a scan from a GitHub URL and see the "scan in progress" status on the Dashboard within 5 seconds.
-   **SC-002**: The Dashboard's PQC readiness gauge and inventory table data update within 2 seconds of new data being available from the backend during an active scan.
-   **SC-003**: 95% of users can successfully filter recommendations by algorithm and context within 10 seconds.
-   **SC-004**: The Repository Heatmap accurately renders the file tree and risk coloring for repositories up to 10,000 files within 15 seconds.
-   **SC-005**: Error messages for backend scanner failures are displayed within 3 seconds of detection, providing actionable information to the user.

## Edge Cases

-   What happens when a GitHub URL is invalid or the repository is private/inaccessible? (Expected: Clear error message and prevention of scan initiation.)
-   How does the system handle an extremely large repository with tens of thousands of files for the heatmap visualization? (Expected: Performance considerations, potential for pagination or aggregated views if direct rendering is too slow.)
-   What if there are no PQC recommendations for a scanned repository? (Expected: A clear message indicating no recommendations were found, rather than an empty table or error.)
-   How does the system behave if the backend API is temporarily unavailable during a scan or when fetching data? (Expected: Graceful degradation, appropriate error messages, and retry mechanisms for polling.)
-   What if the `speckit.constitution` theme colors are not defined or malformed? (Expected: Fallback to default colors or clear visual indication of missing styling.)

## Clarifications

### Session 2026-01-26

- Q: What are the remaining 2 core screens? -> A: Initial Scan Input & History, and Inventory Detail.
