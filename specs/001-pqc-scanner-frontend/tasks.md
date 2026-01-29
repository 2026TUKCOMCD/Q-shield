---
description: "Task list for AI-PQC Scanner Frontend feature implementation"
---

# Tasks: AI-PQC Scanner Frontend

**Input**: Design documents from `/specs/001-pqc-scanner-frontend/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are optional and will be generated for core components and services as part of the Polish phase.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[TaskID] [P?] [Story] Description with file path`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3). Setup and Foundational phases do not have a story label.
- Include exact file paths in descriptions

## Path Conventions

- Project Type: Web application (Frontend)
- Source code structure: `frontend/src/`, `frontend/tests/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project structure per implementation plan (`frontend/src/`, `frontend/tests/`)
- [x] T002 Initialize React (TypeScript) project using Vite and install primary dependencies: React Router, Zustand, Chart.js, Axios.
- [x] T003 [P] Configure ESLint and Prettier for code linting and formatting.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Setup API routing and middleware structure (`frontend/src/api/`)
- [x] T005 Configure global error handling and logging infrastructure (`frontend/src/utils/errorHandler.ts`, `frontend/src/utils/logger.ts`)
- [x] T006 Setup environment configuration management (e.g., `.env` files, config loading utilities).

**Checkpoint**: Foundation ready - user story implementation can now begin.

---

## Phase 3: User Story 4 - Scan Input & History (P1)

**Goal**: Allow users to input a GitHub URL, initiate a scan, and view scan history.

**Independent Test**: User can enter URL, initiate scan, and see it in history.

### Implementation for User Story 4

- [x] T007 [US4] Create ScanInput page component in `frontend/src/pages/ScanInput.tsx`.
- [x] T008 [US4] Implement GitHub URL input form and submission logic in `frontend/src/components/ScanForm.tsx`.
- [x] T009 [US4] Integrate API call to initiate scan (`/scans`) using `scanService.ts`. (`frontend/src/services/scanService.ts`)
- [x] T010 [US4] Create ScanHistory page component in `frontend/src/pages/ScanHistory.tsx`.
- [x] T011 [US4] Implement logic to display list of past scans (UUID, status, date) using `scanService.ts`. (`frontend/src/components/ScanHistoryList.tsx`)

**Checkpoint**: User Story 4 is fully functional and testable independently.

---

## Phase 4: User Story 1 - Scan Monitoring (P1)

**Goal**: Display real-time scan progress and PQC readiness overview on Dashboard.

**Independent Test**: Dashboard updates dynamically with scan progress and overview data.

### Implementation for User Story 1

- [x] T012 [US1] Create Dashboard page component in `frontend/src/pages/Dashboard.tsx`.
- [x] T013 [US1] Implement PQC readiness gauge visualization component (`frontend/src/components/PqcReadinessGauge.tsx`).
- [x] T014 [US1] Implement inventory table display component (`frontend/src/components/InventoryTable.tsx`).
- [x] T015 [US1] Integrate API polling for scan status (`/scans/{uuid}/status`) and data fetching for inventory (`/scans/{uuid}/inventory`) using `scanService.ts` and `inventoryService.ts`. (`frontend/src/services/scanService.ts`, `frontend/src/services/inventoryService.ts`)

**Checkpoint**: User Story 1 is fully functional and testable independently.

---

## Phase 5: User Story 2 - Recommendations (P1)

**Goal**: Display prioritized PQC recommendations with filtering.

**Independent Test**: Users can filter recommendations by algorithm/context.

### Implementation for User Story 2

- [x] T016 [US2] Create Recommendations page component (`frontend/src/pages/Recommendations.tsx`).
- [x] T017 [US2] Implement filtering UI for algorithm and context (`frontend/src/components/RecommendationFilters.tsx`).
- [x] T018 [US2] Integrate API call for recommendations (`/scans/{uuid}/recommendations`) using `recommendationService.ts`. (`frontend/src/services/recommendationService.ts`)
- [x] T019 [US2] Display prioritized table of recommendations (`frontend/src/components/RecommendationTable.tsx`).
- [x] T020 [US2] Implement AI Detail View modal/component (`frontend/src/components/AIDetailView.tsx`).

**Checkpoint**: User Story 2 is fully functional and testable independently.

---

## Phase 6: User Story 3 - Heatmap (P2)

**Goal**: Visualize repository risk distribution via a heatmap.

**Independent Test**: File tree layout and risk coloring accurately rendered.

### Implementation for User Story 3

- [ ] T021 [US3] Create RepositoryHeatmap page component (`frontend/src/pages/RepositoryHeatmap.tsx`).
- [ ] T022 [US3] Integrate API call for heatmap data (`/scans/{uuid}/heatmap`) using `heatmapService.ts`. (`frontend/src/services/heatmapService.ts`)
- [ ] T023 [US3] Implement file tree layout display component (`frontend/src/components/FileTree.tsx`).
- [ ] T024 [US3] Implement risk coloring logic for files/folders within `FileNode.tsx`. (`frontend/src/components/FileNode.tsx`)

**Checkpoint**: User Story 3 is fully functional and testable independently.

---

## Phase 7: User Story 5 - Inventory Detail (P2)

**Goal**: Provide detailed view of cryptographic assets.

**Independent Test**: User can navigate to inventory detail and see asset details.

### Implementation for User Story 5

- [ ] T025 [US5] Create InventoryDetail page component (`frontend/src/pages/InventoryDetail.tsx`).
- [ ] T026 [US5] Integrate API call for inventory data (`/scans/{uuid}/inventory`) using `inventoryService.ts`. (`frontend/src/services/inventoryService.ts`)
- [ ] T027 [US5] Display detailed cryptographic asset information component (`frontend/src/components/AssetDetailList.tsx`).

**Checkpoint**: User Story 5 is fully functional and testable independently.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T028 [P] Update documentation in `docs/`.
- [ ] T029 Code cleanup and refactoring across all components and services.
- [ ] T030 [P] Performance optimization for loading large datasets (e.g., heatmap, inventory).
- [ ] T031 [P] Add unit tests for core components and services in `frontend/tests/unit/`.
- [ ] T032 Security hardening review.
- [ ] T033 Run quickstart.md validation (if quickstart.md is generated).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion.
  - **Priority P1 Stories (US4, US1, US2)**: Can start after Foundational phase. US4 logically precedes US1 for full flow, but monitoring (US1) can be tested independently. They can be worked on in parallel by different team members.
  - **Priority P2 Stories (US3, US5)**: Can start after Foundational phase and P1 stories are nearing completion, or in parallel with P1 stories if capacity allows.
- **Polish (Phase N)**: Depends on all user stories being complete.

### User Story Dependencies Summary:

- US4 (Input/History) → US1 (Monitoring) (Logical flow, can be parallel if tested independently)
- US1, US2 (P1) can be parallel.
- US3, US5 (P2) can be parallel.
- All User Stories depend on Foundational Phase.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation.
- Models before services.
- Services before endpoints/UI.
- Core implementation before integration.
- Story complete before moving to next priority.

### Parallel Opportunities

- Setup tasks (T001, T002, T003) can run in parallel.
- Foundational tasks (T004, T005, T006) can run in parallel.
- User Stories US4, US1, US2 (P1) can be worked on in parallel by different team members.
- User Stories US3, US5 (P2) can be worked on in parallel by different team members.

---

## Parallel Example: User Story 1

```bash
# Example of running tests for User Story 1 in parallel (if tests were explicitly requested):
# Task: "Create [component] for US1"
# Task: "Create [service] for US1"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 4 (Scan Input & History)
4. Complete Phase 4: User Story 1 (Scan Monitoring)
5. **STOP and VALIDATE**: Test US4 and US1 independently.
6. Deploy/demo if ready.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready.
2. Add User Story 4 → Test independently → Deploy/Demo (Core Input/History).
3. Add User Story 1 → Test independently → Deploy/Demo (Core Monitoring).
4. Continue adding P1 stories (US2), then P2 stories (US3, US5).
5. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together.
2. Once Foundational is done:
   - Developer A: User Story 4 (P1)
   - Developer B: User Story 1 (P1)
   - Developer C: User Story 2 (P1)
3. Once P1 stories are substantially complete:
   - Developer D: User Story 3 (P2)
   - Developer E: User Story 5 (P2)
4. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies.
- [Story] label maps task to specific user story for traceability.
- Each user story should be independently completable and testable.
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence.
- Commit after each task or logical group.
- Stop at any checkpoint to validate story independently.
