# Backend API Integration Specification

이 문서는 프론트엔드와 백엔드 API 연동을 위한 상세 스펙입니다.

**작성일**: 2026-01-28  
**프로젝트**: AI-PQC Scanner Frontend  
**기준**: Mock 구현을 실제 백엔드 API로 교체하기 위한 가이드

---

## 목차

1. [API Base Configuration](#api-base-configuration)
2. [API Endpoints](#api-endpoints)
3. [Data Types & Interfaces](#data-types--interfaces)
4. [Migration Guide](#migration-guide)
5. [Additional Integration Points](#additional-integration-points)

---

## API Base Configuration

### Base URL
- **Environment Variable**: `VITE_API_BASE_URL`
- **Default**: `http://localhost:3000`
- **Location**: `frontend/src/config/index.ts:32`

### API Client
- **File**: `frontend/src/api/client.ts`
- **Library**: Axios
- **Timeout**: 30 seconds
- **Interceptors**: Request/Response 로깅 및 에러 처리 포함

---

## API Endpoints

### 1. Initiate Scan

**Endpoint**: `POST /api/scans`

**Description**: 새로운 PQC 스캔을 시작합니다.

#### Request

```typescript
interface InitiateScanRequest {
  githubUrl: string
}
```

**Example Request Body**:
```json
{
  "githubUrl": "https://github.com/owner/repository"
}
```

#### Response

**Status Code**: `202 Accepted`

```typescript
interface InitiateScanResponse {
  uuid: string
}
```

**Example Response**:
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Error Responses

- `400 Bad Request`: 잘못된 GitHub URL
- `500 Internal Server Error`: 서버 내부 오류

---

### 2. Get Scan Status

**Endpoint**: `GET /api/scans/{uuid}/status`

**Description**: 스캔의 현재 상태를 조회합니다.

#### Path Parameters

- `uuid` (string, required): 스캔 UUID

#### Response

**Status Code**: `200 OK`

```typescript
interface ScanStatusResponse {
  uuid: string
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED'
  progress: number // 0-100
}
```

**Example Response**:
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "status": "IN_PROGRESS",
  "progress": 45
}
```

#### Error Responses

- `404 Not Found`: 스캔을 찾을 수 없음
- `500 Internal Server Error`: 서버 내부 오류

---

### 3. Get All Scans (History)

**Endpoint**: `GET /api/scans`

**Description**: 모든 스캔 히스토리를 조회합니다.

#### Response

**Status Code**: `200 OK`

```typescript
interface ScanHistoryItem {
  uuid: string
  githubUrl: string
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED'
  progress: number // 0-100
  createdAt: string // ISO 8601 format
  updatedAt: string // ISO 8601 format
}

type ScanHistoryResponse = ScanHistoryItem[]
```

**Example Response**:
```json
[
  {
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "githubUrl": "https://github.com/owner/repo",
    "status": "COMPLETED",
    "progress": 100,
    "createdAt": "2026-01-28T10:00:00Z",
    "updatedAt": "2026-01-28T10:05:00Z"
  }
]
```

#### Error Responses

- `500 Internal Server Error`: 서버 내부 오류

---

### 4. Get Scan Inventory

**Endpoint**: `GET /api/scans/{uuid}/inventory`

**Description**: 스캔의 암호화 자산 인벤토리를 조회합니다.

#### Path Parameters

- `uuid` (string, required): 스캔 UUID

#### Response

**Status Code**: `200 OK`

```typescript
interface CryptographicAsset {
  id: string
  algorithmType: string
  filePath: string
  lineNumbers: number[]
  riskScore: number // 0.0-10.0
}

interface InventoryResponse {
  uuid: string
  pqcReadinessScore: number // 0.0-10.0
  algorithmRatios: Record<string, number> // 알고리즘별 비율 (0.0-1.0)
  inventory: CryptographicAsset[]
}
```

**Example Response**:
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "pqcReadinessScore": 7.2,
  "algorithmRatios": {
    "RSA-1024": 0.4,
    "SHA-1": 0.35,
    "AES-128": 0.25
  },
  "inventory": [
    {
      "id": "asset-1",
      "algorithmType": "RSA-1024",
      "filePath": "src/auth.c",
      "lineNumbers": [15, 23, 45],
      "riskScore": 9.2
    }
  ]
}
```

#### Error Responses

- `404 Not Found`: 스캔을 찾을 수 없음
- `500 Internal Server Error`: 서버 내부 오류

---

### 5. Get Asset Detail

**Endpoint**: `GET /api/scans/{uuid}/inventory/{assetId}`

**Description**: 특정 암호화 자산의 상세 정보를 조회합니다.

#### Path Parameters

- `uuid` (string, required): 스캔 UUID
- `assetId` (string, required): 자산 ID

#### Response

**Status Code**: `200 OK`

```typescript
interface AssetDetail extends CryptographicAsset {
  // Technical Specifications
  keySize?: number // 비트 단위
  modeOfOperation?: string // e.g., "CBC", "GCM", "ECB"
  implementation?: string // e.g., "OpenSSL", "BouncyCastle"
  standard?: string // e.g., "NIST FIPS 186-4", "RFC 3447"
  keyDerivationFunction?: string
  paddingScheme?: string // e.g., "PKCS#1 v1.5", "OAEP"
  
  // Context & Location
  codeSnippet?: string // 감지된 코드 스니펫
  detectedPattern?: string // 감지된 패턴 설명
  
  // AI Recommendations
  suggestedPQCAlternatives?: string[] // 추천 PQC 알고리즘 목록
  migrationComplexity?: 'Low' | 'Medium' | 'High'
  estimatedEffort?: string // e.g., "5 M/D"
}
```

**Example Response**:
```json
{
  "id": "asset-1",
  "algorithmType": "RSA-1024",
  "filePath": "src/auth.c",
  "lineNumbers": [15, 23, 45],
  "riskScore": 9.2,
  "keySize": 1024,
  "modeOfOperation": "N/A (Asymmetric)",
  "implementation": "OpenSSL",
  "standard": "RFC 3447 (PKCS#1 v1.5)",
  "paddingScheme": "PKCS#1 v1.5",
  "detectedPattern": "RSA_generate_key(1024, RSA_F4, NULL, NULL)",
  "codeSnippet": "// Line 15: RSA key generation\nRSA *rsa = RSA_new();\n...",
  "suggestedPQCAlternatives": ["CRYSTALS-Kyber-768", "CRYSTALS-Kyber-1024"],
  "migrationComplexity": "High",
  "estimatedEffort": "5-7 M/D"
}
```

#### Error Responses

- `404 Not Found`: 스캔 또는 자산을 찾을 수 없음
- `500 Internal Server Error`: 서버 내부 오류

---

### 6. Get Recommendations

**Endpoint**: `GET /api/scans/{uuid}/recommendations`

**Description**: 스캔에 대한 PQC 마이그레이션 추천사항을 조회합니다.

#### Path Parameters

- `uuid` (string, required): 스캔 UUID

#### Query Parameters (Optional)

- `algorithmType` (string, optional): 알고리즘 타입 필터 (e.g., "RSA", "SHA")
- `context` (string, optional): 컨텍스트 필터 (e.g., "authentication", "payment")
- `priority` (string, optional): 우선순위 필터 ("CRITICAL", "HIGH", "MEDIUM", "LOW")

#### Response

**Status Code**: `200 OK`

```typescript
type Priority = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'

interface Recommendation {
  id: string
  priorityRank: number
  priority: Priority
  issueName: string
  estimatedEffort: string // e.g., "3 M/D"
  aiRecommendation: string // Markdown formatted
  recommendedPQCAlgorithm: string
  targetAlgorithm: string
  context: string
  filePath?: string
}

interface RecommendationsResponse {
  uuid: string
  recommendations: Recommendation[]
}
```

**Example Response**:
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "recommendations": [
    {
      "id": "rec-1",
      "priorityRank": 1,
      "priority": "CRITICAL",
      "issueName": "Replace RSA-1024 with Kyber-768",
      "estimatedEffort": "5 M/D",
      "targetAlgorithm": "RSA-1024",
      "recommendedPQCAlgorithm": "Kyber-768",
      "context": "authentication",
      "filePath": "src/auth.c",
      "aiRecommendation": "## Why this is a risk\n\nRSA-1024 is vulnerable..."
    }
  ]
}
```

#### Error Responses

- `404 Not Found`: 스캔을 찾을 수 없음
- `500 Internal Server Error`: 서버 내부 오류

---

### 7. Get Heatmap

**Endpoint**: `GET /api/scans/{uuid}/heatmap`

**Description**: 리포지토리의 리스크 분포 히트맵 데이터를 조회합니다.

#### Path Parameters

- `uuid` (string, required): 스캔 UUID

#### Response

**Status Code**: `200 OK`

```typescript
type FileType = 'file' | 'folder'

interface RepositoryFile {
  filePath: string
  fileName: string
  fileType: FileType
  aggregatedRiskScore: number // 0.0-10.0
  children?: RepositoryFile[] // 폴더인 경우에만 존재
}

type HeatmapResponse = RepositoryFile[]
```

**Example Response**:
```json
[
  {
    "filePath": "src",
    "fileName": "src",
    "fileType": "folder",
    "aggregatedRiskScore": 8.5,
    "children": [
      {
        "filePath": "src/auth.c",
        "fileName": "auth.c",
        "fileType": "file",
        "aggregatedRiskScore": 9.2
      }
    ]
  }
]
```

#### Error Responses

- `404 Not Found`: 스캔을 찾을 수 없음
- `500 Internal Server Error`: 서버 내부 오류

---

## Data Types & Interfaces

모든 타입 정의는 각 서비스 파일에 있습니다:

- **Scan Service**: `frontend/src/services/scanService.ts`
- **Inventory Service**: `frontend/src/services/inventoryService.ts`
- **Recommendation Service**: `frontend/src/services/recommendationService.ts`
- **Heatmap Service**: `frontend/src/services/heatmapService.ts`

---

## Migration Guide

### 1. scanService.ts

**File**: `frontend/src/services/scanService.ts`

#### initiateScan() - Line 97-121

**현재 (Mock)**:
```typescript
async initiateScan(githubUrl: string): Promise<InitiateScanResponse> {
  logInfo('Initiating scan', { githubUrl })
  await simulateNetworkDelay()
  // ... localStorage 로직
  return { uuid }
}
```

**변경 후 (Real API)**:
```typescript
async initiateScan(githubUrl: string): Promise<InitiateScanResponse> {
  logInfo('Initiating scan', { githubUrl })
  
  try {
    const response = await apiClient.post<InitiateScanResponse>('/scans', {
      githubUrl,
    })
    return response.data
  } catch (error) {
    logError('Failed to initiate scan', error)
    throw handleError(error) as AppError
  }
}
```

**추가 필요**: 
- `import { apiClient } from '../api'` (파일 상단에 추가)
- `import { handleError, type AppError } from '../utils/errorHandler'` (에러 처리용)

**제거할 코드**: Line 100-120 (simulateNetworkDelay, localStorage 로직 전체)

---

#### getScanStatus() - Line 127-169

**현재 (Mock)**:
```typescript
async getScanStatus(uuid: string): Promise<ScanStatusResponse> {
  await simulateNetworkDelay()
  // ... localStorage 로직 및 폴링 시뮬레이션
  return { uuid, status, progress }
}
```

**변경 후 (Real API)**:
```typescript
async getScanStatus(uuid: string): Promise<ScanStatusResponse> {
  try {
    const response = await apiClient.get<ScanStatusResponse>(`/scans/${uuid}/status`)
    return response.data
  } catch (error) {
    logError('Failed to get scan status', error)
    throw handleError(error) as AppError
  }
}
```

**추가 필요**: 
- `import { apiClient } from '../api'` (파일 상단에 추가)
- `import { handleError, type AppError } from '../utils/errorHandler'` (에러 처리용)

**제거할 코드**: Line 128-162 (simulateNetworkDelay, localStorage 로직, 폴링 시뮬레이션 전체)

---

#### getAllScans() - Line 175-179

**현재 (Mock)**:
```typescript
async getAllScans(): Promise<ScanHistoryItem[]> {
  await simulateNetworkDelay()
  return loadScansFromStorage()
}
```

**변경 후 (Real API)**:
```typescript
async getAllScans(): Promise<ScanHistoryItem[]> {
  try {
    const response = await apiClient.get<ScanHistoryItem[]>('/scans')
    return response.data
  } catch (error) {
    logError('Failed to get all scans', error)
    throw handleError(error) as AppError
  }
}
```

**추가 필요**: 
- `import { apiClient } from '../api'` (파일 상단에 추가)
- `import { handleError, type AppError } from '../utils/errorHandler'` (에러 처리용)

**제거할 코드**: Line 176-178 (simulateNetworkDelay, loadScansFromStorage 호출)

**추가 필요**: 
- `import { apiClient } from '../api'` (파일 상단에 추가 - Line 1 근처)
- `import { handleError, type AppError } from '../utils/errorHandler'` (에러 처리용, 이미 import되어 있을 수 있음)

---

### 2. inventoryService.ts

**File**: `frontend/src/services/inventoryService.ts`

#### getScanInventory() - Line 64-122

**현재 (Mock)**:
```typescript
async getScanInventory(uuid: string): Promise<InventoryResponse> {
  try {
    await simulateNetworkDelay()
    // const response = await apiClient.get<InventoryResponse>(`/scans/${uuid}/inventory`)
    // return response.data
    
    // localStorage 로직
    return mockInventory
  }
}
```

**변경 후 (Real API)**:
```typescript
async getScanInventory(uuid: string): Promise<InventoryResponse> {
  try {
    const response = await apiClient.get<InventoryResponse>(`/scans/${uuid}/inventory`)
    return response.data
  } catch (error) {
    logError('Failed to get scan inventory', error)
    throw handleError(error) as AppError
  }
}
```

**제거할 코드**: Line 66-117 (simulateNetworkDelay, localStorage 로직, mock 데이터 생성 전체)

**활성화할 코드**: Line 70-71 (주석 해제)

---

#### getAssetDetail() - Line 128-226

**현재 (Mock)**:
```typescript
async getAssetDetail(uuid: string, assetId: string): Promise<AssetDetail> {
  try {
    await simulateNetworkDelay()
    // const response = await apiClient.get<AssetDetail>(`/scans/${uuid}/inventory/${assetId}`)
    // return response.data
    
    // Mock 상세 정보 생성 로직
    return { ...baseAsset, ...detailData }
  }
}
```

**변경 후 (Real API)**:
```typescript
async getAssetDetail(uuid: string, assetId: string): Promise<AssetDetail> {
  try {
    const response = await apiClient.get<AssetDetail>(`/scans/${uuid}/inventory/${assetId}`)
    return response.data
  } catch (error) {
    logError('Failed to get asset detail', error)
    throw handleError(error) as AppError
  }
}
```

**제거할 코드**: Line 130-221 (simulateNetworkDelay, getScanInventory 호출, Mock 데이터 생성 전체)

**활성화할 코드**: Line 134-135 (주석 해제)

---

### 3. recommendationService.ts

**File**: `frontend/src/services/recommendationService.ts`

#### getRecommendations() - Line 294-362

**현재 (Mock)**:
```typescript
async getRecommendations(uuid: string, filters?: {...}): Promise<RecommendationsResponse> {
  try {
    await simulateNetworkDelay()
    // const params = new URLSearchParams()
    // if (filters?.algorithmType) params.append('algorithmType', filters.algorithmType)
    // if (filters?.context) params.append('context', filters.context)
    // const response = await apiClient.get<RecommendationsResponse>(
    //   `/scans/${uuid}/recommendations?${params.toString()}`
    // )
    // return response.data
    
    // localStorage 및 필터링 로직
    return { uuid, recommendations: filtered }
  }
}
```

**변경 후 (Real API)**:
```typescript
async getRecommendations(
  uuid: string,
  filters?: {
    algorithmType?: string
    context?: string
    priority?: Priority
  }
): Promise<RecommendationsResponse> {
  try {
    const params = new URLSearchParams()
    if (filters?.algorithmType) params.append('algorithmType', filters.algorithmType)
    if (filters?.context) params.append('context', filters.context)
    if (filters?.priority) params.append('priority', filters.priority)
    
    const queryString = params.toString()
    const url = `/scans/${uuid}/recommendations${queryString ? `?${queryString}` : ''}`
    
    const response = await apiClient.get<RecommendationsResponse>(url)
    return response.data
  } catch (error) {
    logError('Failed to get recommendations', error)
    throw handleError(error) as AppError
  }
}
```

**제거할 코드**: Line 303-357 (simulateNetworkDelay, localStorage 로직, 필터링 로직 전체)

**활성화할 코드**: Line 307-312 (주석 해제 및 수정)

---

### 4. heatmapService.ts

**File**: `frontend/src/services/heatmapService.ts`

#### getHeatmap() - Line 285-313

**현재 (Mock)**:
```typescript
async getHeatmap(uuid: string): Promise<HeatmapResponse> {
  try {
    await simulateNetworkDelay()
    // const response = await apiClient.get<HeatmapResponse>(`/scans/${uuid}/heatmap`)
    // return response.data
    
    // localStorage 로직
    return mockHeatmap
  }
}
```

**변경 후 (Real API)**:
```typescript
async getHeatmap(uuid: string): Promise<HeatmapResponse> {
  try {
    const response = await apiClient.get<HeatmapResponse>(`/scans/${uuid}/heatmap`)
    return response.data
  } catch (error) {
    logError('Failed to get heatmap', error)
    throw handleError(error) as AppError
  }
}
```

**제거할 코드**: Line 287-308 (simulateNetworkDelay, localStorage 로직, Mock 데이터 생성 전체)

**활성화할 코드**: Line 291-292 (주석 해제)

---

## Additional Integration Points

### 1. API Client Configuration

**File**: `frontend/src/api/client.ts`

현재 API 클라이언트는 이미 설정되어 있습니다. 필요시 다음을 추가할 수 있습니다:

- **인증 토큰**: Line 33-37 주석 해제 및 토큰 관리 로직 추가
- **Request/Response 인터셉터**: 이미 구현됨 (로깅 및 에러 처리)

---

### 2. Environment Configuration

**File**: `frontend/src/config/index.ts`

**환경 변수 설정**:
- `.env` 파일에 `VITE_API_BASE_URL` 추가
- 예: `VITE_API_BASE_URL=http://localhost:3000/api`

---

### 3. Error Handling

**File**: `frontend/src/utils/errorHandler.ts`

현재 에러 핸들러는 Axios 에러를 처리하도록 구현되어 있습니다. 추가 작업 불필요.

---

### 4. CORS Configuration

백엔드에서 CORS 설정이 필요합니다:

- **Allowed Origins**: 프론트엔드 도메인
- **Allowed Methods**: GET, POST
- **Allowed Headers**: Content-Type, Authorization (필요시)

---

## Testing Checklist

백엔드 연동 후 다음을 테스트하세요:

- [ ] 스캔 시작 (`POST /api/scans`)
- [ ] 스캔 상태 조회 (`GET /api/scans/{uuid}/status`)
- [ ] 스캔 히스토리 조회 (`GET /api/scans`)
- [ ] 인벤토리 조회 (`GET /api/scans/{uuid}/inventory`)
- [ ] 자산 상세 조회 (`GET /api/scans/{uuid}/inventory/{assetId}`)
- [ ] 추천사항 조회 (`GET /api/scans/{uuid}/recommendations`)
- [ ] 히트맵 조회 (`GET /api/scans/{uuid}/heatmap`)
- [ ] 에러 처리 (404, 500 등)
- [ ] 네트워크 오류 처리
- [ ] 로딩 상태 표시

---

## Code Cleanup Checklist

백엔드 연동 시 제거해야 할 Mock 관련 코드:

### scanService.ts
- [ ] `generateUUID()` 함수 (Line 46-52)
- [ ] `loadScansFromStorage()` 함수 (Line 57-67)
- [ ] `saveScansToStorage()` 함수 (Line 72-78)
- [ ] `simulateNetworkDelay()` 함수 (Line 83-86) - 다른 서비스에서도 사용 중이면 유지
- [ ] 모든 localStorage 관련 코드

### inventoryService.ts
- [ ] `simulateNetworkDelay()` 함수 (Line 51-54) - 다른 서비스에서도 사용 중이면 유지
- [ ] Mock 데이터 생성 로직 (Line 80-112, 146-214)

### recommendationService.ts
- [ ] `simulateNetworkDelay()` 함수 (Line 37-40) - 다른 서비스에서도 사용 중이면 유지
- [ ] `rankToPriority()` 함수 (Line 45-50) - 백엔드에서 priority를 직접 제공하면 제거
- [ ] `generateMockRecommendations()` 함수 (Line 55-284)
- [ ] localStorage 관련 코드 (Line 316-331)
- [ ] 클라이언트 사이드 필터링 로직 (Line 333-352) - 백엔드에서 필터링하면 제거

### heatmapService.ts
- [ ] `simulateNetworkDelay()` 함수 (Line 88-91) - 다른 서비스에서도 사용 중이면 유지
- [ ] `generateMockHeatmap()` 함수 (Line 96-221)
- [ ] localStorage 관련 코드 (Line 295-306)

**참고**: `getRiskLevel()`, `getRiskColor()`, `calculateFolderMaxRisk()`, `calculateVulnerabilityCount()` 같은 유틸리티 함수는 UI에서 사용되므로 유지해야 합니다.

---

## Notes

1. **localStorage 제거**: Mock 구현에서 사용하던 localStorage는 모두 제거해야 합니다.
2. **시뮬레이션 제거**: `simulateNetworkDelay()` 함수 호출은 모두 제거해야 합니다. 함수 자체는 다른 서비스에서 공유 사용 중이면 유지 가능.
3. **타입 일치**: 백엔드 응답이 프론트엔드 타입 정의와 정확히 일치하는지 확인하세요.
4. **에러 처리**: 모든 API 호출은 try-catch로 감싸져 있으며, `handleError()`를 통해 처리됩니다.
5. **로깅**: 모든 API 요청/응답은 자동으로 로깅됩니다 (`apiClient` 인터셉터).
6. **필터링**: 백엔드에서 필터링을 지원하면 클라이언트 사이드 필터링 로직을 제거하세요.

---

## Quick Reference: File Changes Summary

| File | Functions to Replace | Import to Add |
|------|---------------------|---------------|
| `scanService.ts` | `initiateScan()`, `getScanStatus()`, `getAllScans()` | `apiClient`, `handleError`, `AppError` |
| `inventoryService.ts` | `getScanInventory()`, `getAssetDetail()` | 이미 있음 |
| `recommendationService.ts` | `getRecommendations()` | 이미 있음 |
| `heatmapService.ts` | `getHeatmap()` | 이미 있음 |

---

**마지막 업데이트**: 2026-01-28
