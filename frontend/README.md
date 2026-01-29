# AI-PQC Scanner Frontend

양자 내성 암호(PQC) 전환을 위한 소스코드 취약점 분석 대시보드 프론트엔드 애플리케이션입니다.

## 📋 프로젝트 개요

**프로젝트명**: AI-PQC Scanner Frontend  
**목적**: GitHub 저장소를 스캔하여 암호화 알고리즘 취약점을 분석하고, PQC 마이그레이션 가이드를 제공하는 대시보드  
**현재 상태**: Phase 1-7 완료, Mock 데이터로 동작 중, 백엔드 API 연동 준비 완료

## 🛠 기술 스택

- **Framework**: React 19.2.0
- **Language**: TypeScript 5.9.3
- **Build Tool**: Vite 7.2.4
- **Routing**: React Router DOM 7.13.0
- **State Management**: Zustand 5.0.10
- **HTTP Client**: Axios 1.13.3
- **Styling**: Tailwind CSS 3.4.19
- **Icons**: Lucide React 0.563.0
- **Charts**: Recharts 3.7.0, Chart.js 4.5.1
- **Code Quality**: ESLint, Prettier

## 🚀 시작하기

### 사전 요구사항

- Node.js 18+ 
- npm 또는 yarn

### 설치

```bash
# 의존성 설치
npm install
```

### 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
# 백엔드 API Base URL
VITE_API_BASE_URL=http://localhost:3000/api
```

**참고**: 현재는 Mock 데이터로 동작하므로 환경 변수 설정 없이도 실행 가능합니다.

### 개발 서버 실행

```bash
npm run dev
```

개발 서버가 시작되면 브라우저에서 `http://localhost:5173`으로 접속하세요.

### 빌드

```bash
# 프로덕션 빌드
npm run build

# 빌드 결과 미리보기
npm run preview
```

### 코드 품질

```bash
# ESLint 실행
npm run lint
```

## 📁 프로젝트 구조

```
frontend/
├── src/
│   ├── api/                    # API 클라이언트 설정
│   │   ├── client.ts          # Axios 인스턴스 및 인터셉터
│   │   └── index.ts
│   ├── components/             # 재사용 가능한 컴포넌트
│   │   ├── ScanForm.tsx       # GitHub URL 입력 폼
│   │   ├── ScanHistoryList.tsx # 스캔 히스토리 목록
│   │   ├── Sidebar.tsx        # 데스크톱 사이드바
│   │   ├── MobileNav.tsx      # 모바일 네비게이션
│   │   ├── PqcReadinessGauge.tsx # PQC 준비도 게이지
│   │   ├── InventoryTable.tsx # 암호화 자산 테이블
│   │   ├── RecommendationFilters.tsx # 추천사항 필터
│   │   ├── RecommendationTable.tsx # 추천사항 테이블
│   │   ├── AIDetailView.tsx   # AI 상세 가이드 모달
│   │   ├── FileTree.tsx       # 파일 트리
│   │   ├── FileNode.tsx       # 파일/폴더 노드 (재귀적)
│   │   ├── AssetDetailList.tsx # 자산 상세 정보
│   │   └── index.ts
│   ├── pages/                  # 페이지 컴포넌트
│   │   ├── ScanInput.tsx      # 스캔 입력 페이지
│   │   ├── ScanHistory.tsx    # 스캔 히스토리 페이지
│   │   ├── Dashboard.tsx      # 대시보드 페이지
│   │   ├── Recommendations.tsx # 추천사항 페이지
│   │   ├── RepositoryHeatmap.tsx # 히트맵 페이지
│   │   ├── InventoryDetail.tsx # 자산 상세 페이지
│   │   └── index.ts
│   ├── services/               # API 서비스 레이어
│   │   ├── scanService.ts     # 스캔 관련 API (Mock)
│   │   ├── inventoryService.ts # 인벤토리 관련 API (Mock)
│   │   ├── recommendationService.ts # 추천사항 관련 API (Mock)
│   │   ├── heatmapService.ts  # 히트맵 관련 API (Mock)
│   │   └── index.ts
│   ├── utils/                  # 유틸리티 함수
│   │   ├── errorHandler.ts    # 에러 처리
│   │   ├── logger.ts          # 로깅
│   │   └── index.ts
│   ├── config/                 # 환경 설정
│   │   └── index.ts
│   ├── App.tsx                # 메인 앱 컴포넌트 (라우팅)
│   ├── main.tsx               # 엔트리 포인트
│   └── index.css              # 글로벌 스타일 (Tailwind)
├── public/                     # 정적 파일
├── BACKEND_API_SPEC.md        # 백엔드 API 연동 스펙
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## 🎨 디자인 시스템

### 스타일 테마

- **스타일**: Modern Cyber-security Dashboard + Glassmorphism
- **배경**: Deep Navy (#020617) + 보라/블루 메시 그라데이션
- **컴포넌트**: `backdrop-blur-md`, `bg-white/5`, `border-white/10`

### 색상 팔레트

- **Danger/Critical**: #FF4136 (빨강)
- **Warning/High**: #FF851B (주황)
- **Medium**: #FFDC00 (노랑)
- **Low**: #7FDBFF (파랑)
- **Success/Safe**: #2ECC40 (초록)
- **Primary Gradient**: `from-indigo-500 to-purple-600`

### 아이콘

- **라이브러리**: lucide-react
- **사용 예**: `<AlertCircle />`, `<Shield />`, `<Sparkles />` 등

## 🎯 주요 기능

### 1. 스캔 입력 및 히스토리 (Phase 3)
- GitHub URL 입력 및 스캔 시작
- 스캔 히스토리 조회 및 상태 확인
- 실시간 스캔 진행 상황 업데이트

### 2. 스캔 모니터링 (Phase 4)
- 실시간 스캔 진행률 표시
- PQC 준비도 점수 시각화 (게이지 차트)
- 암호화 자산 인벤토리 테이블
- 알고리즘 분포 비율 표시

### 3. PQC 추천사항 (Phase 5)
- 우선순위별 마이그레이션 추천사항 표시
- 알고리즘 타입, 컨텍스트, 우선순위 필터링
- AI 생성 상세 마이그레이션 가이드 모달

### 4. 리포지토리 히트맵 (Phase 6)
- 파일/폴더별 리스크 분포 시각화
- 리스크 레벨별 색상 코딩
- 폴더 확장/축소 기능
- 취약점 개수 배지 표시

### 5. 자산 상세 정보 (Phase 7)
- 암호화 자산의 상세 기술 사양
- 코드 스니펫 및 감지된 패턴 표시
- AI 추천 PQC 대체 알고리즘
- 마이그레이션 복잡도 및 예상 작업량

## 🛣 라우팅 구조

```
/                          → /scans/new (리다이렉트)
/scans/new                 → ScanInput 페이지
/scans/history             → ScanHistory 페이지
/dashboard/:uuid           → Dashboard 페이지
/scans/:uuid/recommendations → Recommendations 페이지
/scans/:uuid/heatmap       → RepositoryHeatmap 페이지
/scans/:uuid/inventory/:assetId → InventoryDetail 페이지
```

## 🔌 백엔드 API 연동

현재는 Mock 데이터(localStorage 기반)로 동작합니다. 백엔드 API 연동을 위해서는:

1. **환경 변수 설정**: `.env` 파일에 `VITE_API_BASE_URL` 추가
2. **API 스펙 확인**: `BACKEND_API_SPEC.md` 파일 참조
3. **서비스 파일 수정**: 각 `src/services/*.ts` 파일의 Mock 코드를 실제 API 호출로 교체

자세한 내용은 [BACKEND_API_SPEC.md](./BACKEND_API_SPEC.md)를 참조하세요.

### 주요 API 엔드포인트

- `POST /api/scans` - 스캔 시작
- `GET /api/scans/{uuid}/status` - 스캔 상태 조회
- `GET /api/scans` - 모든 스캔 히스토리 조회
- `GET /api/scans/{uuid}/inventory` - 인벤토리 조회
- `GET /api/scans/{uuid}/inventory/{assetId}` - 자산 상세 조회
- `GET /api/scans/{uuid}/recommendations` - 추천사항 조회
- `GET /api/scans/{uuid}/heatmap` - 히트맵 조회

## 📝 개발 가이드

### 코드 스타일

- **ESLint**: 코드 품질 검사
- **Prettier**: 코드 포맷팅
- **TypeScript**: 타입 안전성

### 컴포넌트 작성 규칙

1. **함수형 컴포넌트** 사용
2. **TypeScript 인터페이스**로 Props 타입 정의
3. **Tailwind CSS**로 스타일링
4. **lucide-react**로 아이콘 사용
5. **Glassmorphism 스타일** 유지 (`bg-white/5`, `backdrop-blur-md`)

### 서비스 레이어 패턴

```typescript
// 서비스 함수는 async/await 사용
async functionName(params): Promise<ResponseType> {
  try {
    const response = await apiClient.get<ResponseType>('/endpoint')
    return response.data
  } catch (error) {
    logError('Failed to...', error)
    throw handleError(error) as AppError
  }
}
```

### 에러 처리

- 모든 API 호출은 `try-catch`로 감싸기
- `handleError()` 유틸리티로 에러 변환
- 사용자에게 친화적인 에러 메시지 표시

## 🧪 테스트

현재 테스트는 구현되지 않았습니다. 향후 추가 예정:

- Unit Tests: `frontend/tests/unit/`
- Integration Tests: `frontend/tests/integration/`

## 📦 빌드 및 배포

### 프로덕션 빌드

```bash
npm run build
```

빌드 결과는 `dist/` 디렉토리에 생성됩니다.

### 환경별 설정

- **Development**: `VITE_API_BASE_URL=http://localhost:3000/api`
- **Production**: `VITE_API_BASE_URL=https://api.yourdomain.com/api`

## 🐛 알려진 이슈

- 현재 Mock 데이터로 동작 중 (백엔드 연동 필요)
- localStorage 기반 데이터 저장 (브라우저별 제한)

## 📚 참고 문서

- [백엔드 API 스펙](./BACKEND_API_SPEC.md)
- [작업 목록](../specs/001-pqc-scanner-frontend/tasks.md)



## 📄 라이선스

이 프로젝트는 비공개 프로젝트입니다.

## 👥 팀

- Frontend Development: AI-PQC Scanner Team

---

**마지막 업데이트**: 2026-01-28  
**버전**: 1.0.0 (Phase 1-7 완료)
