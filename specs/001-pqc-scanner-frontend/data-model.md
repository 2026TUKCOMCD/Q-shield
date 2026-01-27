# Data Model: AI-PQC Scanner Frontend

## Summary

This document defines the key entities and their attributes for the AI-PQC Scanner Frontend, derived from the feature specification.

## Entities

### 1. Scan

Represents a PQC analysis of a repository. This entity will be used to track the overall state and results of a scan operation.

-   **Attributes**:
    -   `uuid`: string (Unique identifier for the scan)
    -   `status`: enum (e.g., `IN_PROGRESS`, `COMPLETED`, `FAILED`, `PENDING` - Current status of the scan)
    -   `results`: object (Associated scan results, structure to be detailed by backend API contract)

### 2. Cryptographic Asset

An identified instance of a cryptographic algorithm or primitive within the source code. These assets are the core focus of the PQC analysis.

-   **Attributes**:
    -   `id`: string (Unique identifier for the asset - *inferred*)
    -   `algorithmType`: string (e.g., `ECC`, `AES`, `RSA` - Type of cryptographic algorithm)
    -   `location`: object (Details including `filePath`: string, `lineNumbers`: array of integers - Location within the source code)
    -   `riskScore`: number (Aggregated risk score for the asset, e.g., 0.0-10.0)

### 3. Recommendation

A suggested action item for PQC migration. These provide actionable insights for users to address cryptographic vulnerabilities.

-   **Attributes**:
    -   `id`: string (Unique identifier for the recommendation - *inferred*)
    -   `priorityRank`: integer (Priority ranking of the recommendation)
    -   `issueName`: string (Descriptive name of the issue)
    -   `estimatedEffort`: string (e.g., `3 M/D` - Estimated effort to resolve)
    -   `aiRecommendation`: string (Markdown formatted AI-generated refactoring guidance)
    -   `recommendedPQCAlgorithm`: string (Name of the recommended PQC algorithm)
    -   `context`: string (e.g., `payment logic` - Contextual information for filtering - *inferred from user story*)

### 4. Repository File

A file within the scanned repository. This entity is crucial for visualizing the repository structure and risk heatmap.

-   **Attributes**:
    -   `filePath`: string (Absolute or relative path to the file)
    -   `fileName`: string (Name of the file - *inferred*)
    -   `fileType`: string (e.g., `folder`, `file` - *inferred for tree structure*)
    -   `aggregatedRiskScore`: number (Aggregated risk score for the file, influencing heatmap coloring)
    -   `children`: array of `RepositoryFile` (For representing the file tree structure - *inferred*)