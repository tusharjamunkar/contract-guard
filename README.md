# 🛡️ ContractGuard

[![CI](https://github.com/tusharjamunkar/contract-guard/actions/workflows/ci.yml/badge.svg)](https://github.com/tusharjamunkar/contract-guard)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Zero External APIs](https://img.shields.io/badge/API%20Keys-0%20Required-success.svg)](#)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker&logoColor=white)](https://www.docker.com/)

> **Zero-Dependency OpenAPI Breaking Change & Schema Drift Detector for GitHub Actions & CI/CD.**  
> Prevent production outages and broken mobile/web clients by catching API contract breaking changes on Pull Requests before they merge.

---

## 💥 The Problem ContractGuard Solves

In modern engineering teams with microservices, frontend applications, and mobile clients:
- A backend developer accidentally renames a field (`userId` -> `id`), removes an endpoint, or changes an integer to a string.
- Unit tests pass. The PR merges.
- **Production mobile apps immediately crash for thousands of users** because the API contract broke without notice.

**ContractGuard** runs directly in GitHub Actions with **0 external APIs**, comparing your PR branch against `main`, detecting every breaking change in your OpenAPI / Swagger specification, and posting an actionable review comment on the Pull Request.

---

## ⚡ Quickstart

### 1. Run via GitHub Actions

Add this to `.github/workflows/api-contract.yml` in any repository:

```yaml
name: API Contract Guard

on:
  pull_request:
    paths:
      - 'openapi.json'
      - 'openapi.yaml'
      - 'api/**'

jobs:
  verify-contract:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Verify API Contract
        uses: tusharjamunkar/contract-guard@v1
        with:
          spec-path: "openapi.json"
          fail-on-breaking: "true"
```

---

### 2. Run Locally via Python CLI

Install ContractGuard:

```bash
pip install contract-guard
```

Compare any two specifications:

```bash
contractguard diff --base openapi_v1.json --head openapi_v2.json
```

Output formats:
```bash
# Markdown formatted for GitHub PR comments
contractguard diff --base v1.json --head v2.json --format markdown

# SARIF output for GitHub Advanced Security
contractguard diff --base v1.json --head v2.json --format sarif --output results.sarif
```

---

## 🔍 What Counts as a Breaking Change?

| Change Type | Severity | Why It Breaks Clients |
| :--- | :---: | :--- |
| **Endpoint Removed** | 🔴 BREAKING | Clients hitting `DELETE /v1/users/{id}` receive HTTP 404 |
| **HTTP Method Removed** | 🔴 BREAKING | Clients making `POST` request receive HTTP 405 Method Not Allowed |
| **Required Param Added** | 🔴 BREAKING | Existing clients don't send the new required parameter -> HTTP 422 |
| **Param Type Changed** | 🔴 BREAKING | Type mismatch validation errors (`string` vs `integer`) |
| **Request Field Removed** | 🔴 BREAKING | Backend no longer processes fields clients rely on |
| **Response Field Removed** | 🔴 BREAKING | Mobile apps deserializing the missing property crash or error |
| **Response Type Mutated** | 🔴 BREAKING | JSON parsing deserialization crash |
| **Success Status Code Removed** | 🔴 BREAKING | Client expectation of `200 OK` broken by unannounced `204` |
| **Endpoint Deprecated** | 🟡 WARNING | Warning to clients that endpoint will be sunset in next major release |
| **New Optional Field** | 🟢 ADDITIVE | Backward-compatible improvement |

---

## 📊 Sample Pull Request Report

ContractGuard automatically publishes clean Markdown reviews:

> [!CAUTION]
> **4 BREAKING CHANGES DETECTED**
> Merging this PR without a major SemVer bump or backward-compatibility migration may break live clients and frontend integrations.
> 
> | Method | Endpoint | Location | Description |
> | :---: | :--- | :--- | :--- |
> | `DELETE` | `/users/{id}` | `paths./users/{id}.delete` | HTTP method removed: DELETE /users/{id} |
> | `GET` | `/users` | `parameters.query.limit.required` | Parameter 'limit' changed from optional to required |
> | `POST` | `/users` | `requestBody.properties.age` | New REQUIRED request property added: 'age' |
> | `GET` | `/users/{id}` | `responses.200.properties.role` | Response payload property removed: 'role' |

---

## 🛠️ Architecture

```
contract_guard/
├── cli.py          # Command-line interface (diff, git-diff, formatters)
├── comparator.py   # Deep structural comparison across paths, params, bodies & responses
├── parser.py       # OpenAPI 3.0 & 3.1 JSON/YAML loader with recursive $ref dereferencing
├── rules.py        # Breaking vs Additive classification rules
├── reporter.py     # Terminal ANSI, GitHub PR Markdown, and SARIF generators
└── git_utils.py    # Zero-checkout Git history spec extractor
```

---

## 🪝 Pre-Commit Hook Integration

Catch API contract breaks before files are even committed to git:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/tusharjamunkar/contract-guard
    rev: v1.0.0
    hooks:
      - id: contract-guard
        args: ["--spec-path", "openapi.json", "--base-ref", "origin/main"]
```

---

## 🐳 Docker Usage (GitLab CI, Jenkins, Bitbucket)

Run ContractGuard in any containerized environment without installing Python:

```bash
docker build -t contract-guard .
docker run --rm -v $(pwd):/workspace -w /workspace contract-guard diff --base v1.json --head v2.json
```

---

## 🧪 Testing

ContractGuard comes with a 100% passing test suite covering complex schemas and circular `$ref` references:

```bash
pytest tests/ -v
```

---

## 📄 License

MIT License © 2026 Tushar Jamunkar.
