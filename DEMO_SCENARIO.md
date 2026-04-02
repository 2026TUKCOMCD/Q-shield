# Q-shield Demo Scenario

This document fixes the live demo flow for Q-shield as a PQC migration planning platform.

## 1. Demo Goal

Show that Q-shield does more than detect weak cryptography.

The demo must prove four points:

1. Q-shield discovers quantum-vulnerable cryptographic usage across code, dependencies, and config.
2. Q-shield groups raw findings into distinct migration targets instead of flooding the user with duplicates.
3. Q-shield produces explainable priority rankings using deterministic factors.
4. Q-shield provides trust-backed AI migration guidance with citations, assumptions, benchmark notes, and validation checklists.

## 2. Recommended Demo Repositories

Use at least two repositories in the presentation.

### A. Legacy Crypto Detection Demo

Recommended repo:
- `https://github.com/pycrypto/pycrypto`

Why:
- easy to show legacy public-key and weak crypto findings
- produces visible inventory and recommendation results
- good for explaining scanner coverage and migration target grouping

### B. JWT / Auth Boundary Demo

Recommended repo:
- a JWT-focused repo that triggers the current SAST/SCA rules in your environment

Pick one that your current scanner actually detects reliably before the presentation.

Why:
- demonstrates auth/token boundary risk
- useful for explaining HNDL, exposure, and migration complexity

### C. TLS / Config Boundary Demo

Recommended repo:
- a TLS or reverse proxy config repo that your config scanner parses reliably

Why:
- shows that Q-shield is not only code-centric
- supports the product message around protocol and infrastructure planning

## 3. Pre-Demo Checklist

Run this before the presentation.

### Backend / AI

- Redis and PostgreSQL are running.
- Celery worker is running.
- RAG corpus is loaded.
- benchmark and NIST documents are ingested.
- AI analysis is not stuck in `fallback`, `mock`, or `error` mode unless intentionally demonstrating fallback behavior.

### UI

- Recommendation table shows:
  - priority rank
  - normalized vulnerability class
  - priority factors
  - trust state
- Recommendation detail shows:
  - priority reason
  - citations
  - benchmark notes
  - validation checklist
  - assumptions
  - confidence reason
  - related asset refs
  - correlation refs
- Inventory detail shows:
  - asset ref
  - correlation ref
  - algorithm family

### Validation

- Run backend tests before the demo.
- Confirm at least one repo returns real citations.
- Confirm benchmark evidence and normative evidence are visually separated.

## 4. Live Demo Flow

### Step 1. Product Framing

Say this first:

> Q-shield is not a generic vulnerability scanner. It is a PQC migration planning platform that helps answer what to migrate first, why, and with what evidence.

### Step 2. Scan Start

Input a GitHub repository URL.

Show:
- scan creation
- async processing
- scan progress

Key message:
- the platform runs SAST, SCA, and config analysis independently
- scanner facts are stored separately from AI reasoning

### Step 3. Findings and Inventory

Open the findings and inventory views.

Show:
- vulnerable algorithm class
- affected files and line numbers
- inventory asset list
- boundary labels such as auth/token, TLS/certificate, configuration

Key message:
- this is discovery and inventory, not yet migration planning

### Step 4. Heatmap

Open the repository heatmap.

Show:
- risky directories and files
- trust notes
- boundary-aware badges

Key message:
- the heatmap helps teams understand where PQC migration work will concentrate

### Step 5. Recommendation Table

Open recommendations.

Show:
- raw findings are grouped into distinct vulnerability classes
- priority rank is computed by deterministic planner factors
- analysis mode is visible
- trust state is visible

Key message:
- this is not a black-box AI ranker
- ranking comes from explicit factors such as severity, exposure, HNDL, migration complexity, and interoperability risk

### Step 6. Recommendation Detail

Open one recommendation detail panel.

Show these sections in order:

1. `Priority Basis`
2. `Priority Factors`
3. `Affected Asset Scope`
4. `Validation Checklist`
5. `Benchmark Notes`
6. `Assumptions`
7. `Evidence`
8. `Confidence`

Key message:
- AI guidance is bounded by retrieved evidence and validator rules
- benchmark notes are reference evidence, not production guarantees

### Step 7. Correlation Story

Point out:
- `asset_ref`
- `correlation_ref`
- related asset refs in recommendation evidence

Key message:
- the same migration target is traceable across findings, inventory, and recommendations
- this supports CBOM-style migration planning instead of isolated issue lists

### Step 8. Trust and Hallucination Control

Show:
- analysis mode
- citations available / missing
- normative evidence vs benchmark evidence
- confidence reason

Key message:
- unsupported claims are validated
- citation-free recommendations are downgraded
- fallback and mock states are disclosed to the user

## 5. Recommended Speaking Points for Professor Feedback

### Priority Algorithm

Say:
- priority is not generated only by AI
- deterministic planner factors are calculated first
- AI only explains and enriches the migration plan

Show:
- priority factors
- priority reason
- documented factor model

### Benchmark / Comparison / Evaluation

Say:
- Q-shield is evaluated with fixture sets, public GitHub repositories, and NIST-driven scenarios
- trust metrics include citation coverage, benchmark linkage coverage, and unsupported claim rate

Show:
- `EVALUATION_METHODOLOGY.md`
- `PQC_PRIORITY_MODEL.md`

### Hallucination / Validation

Say:
- AI output is constrained by RAG evidence and post-validation
- unsupported security-improvement claims are blocked
- benchmark-only evidence is not presented as normative guidance

Show:
- evidence sections
- confidence section
- validation checklist

### Enterprise Trust

Say:
- Q-shield does not claim automatic production-safe migration
- it provides migration guidance, example code, validation steps, and benchmark-aware notes for expert review

## 6. Demo Success Criteria

The live demo is successful if the audience can clearly see:

1. where vulnerable crypto is used
2. which migration target is ranked first
3. why it is ranked first
4. what evidence supports the recommendation
5. what must be validated before enterprise adoption

## 7. Failure Handling Plan

If the live demo environment fails, use this fallback order.

1. Show a completed scan already stored in the database.
2. Show recommendation detail with evidence, benchmark notes, and correlation refs.
3. Show `analysis mode` explicitly if the system is in fallback mode.
4. Explain that Q-shield exposes degraded trust state instead of hiding it.

## 8. Minimal Demo Script

Use this short script if time is limited.

1. Paste the repository URL and start the scan.
2. Open inventory and show quantum-vulnerable asset classes.
3. Open the heatmap and identify the hottest path.
4. Open recommendations and show top ranked migration targets.
5. Open recommendation detail and explain:
   - why this is first
   - which evidence supports it
   - what validation is still required
6. Conclude that the platform supports PQC migration planning rather than one-click code replacement.
