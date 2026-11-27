# Production Deployment & Cloud Architecture Runbook
## Project: AI-Assisted DSA Assessment Platform

This document serves as the **Production Operations Runbook, Architecture Blueprint, and Cloud Deployment Guide** for the AI-Assisted DSA Assessment Platform.

---

## 1. System Architecture Baseline

The platform is designed to support **3,000+ concurrent students** with strict security boundaries, isolated test execution, and real-time LLM token guardrails.

```mermaid
flowchart TD
    Students(["Students / Web Clients"]) --> IGW["Internet Gateway (IGW)"]
    
    subgraph VPC ["AWS Virtual Private Cloud (10.0.0.0/16)"]
        subgraph PublicSubnets ["Public Subnets (us-east-1a / us-east-1b)"]
            ALB["Application Load Balancer (ALB)<br>• Port 80 / 443<br>• Health Check: /api/v1/health & /"]
        end
        
        IGW --> ALB
        
        subgraph PrivateAppSubnets ["Private App Subnets (Zero Inbound Internet)"]
            subgraph ASG ["Auto Scaling Group (ASG: Min 1, Desired 2, Max 4)"]
                EC2_A["EC2 Node A (t3.small)<br>• Next.js Frontend (Port 3000)<br>• FastAPI Backend (Port 8000)"]
                EC2_B["EC2 Node B (t3.small)<br>• Next.js Frontend (Port 3000)<br>• FastAPI Backend (Port 8000)"]
            end
        end
        
        ALB -->|"/api/*"| EC2_A
        ALB -->|"/api/*"| EC2_B
        ALB -->|"/*"| EC2_A
        ALB -->|"/*"| EC2_B
        
        subgraph IsolatedDBSubnets ["Isolated Database Subnets"]
            RDS[("Amazon RDS PostgreSQL 16<br>(Auto-scaling GP3 Storage)")]
            Redis[("Redis Token Guardrail Cache<br>(Atomic INCRBY / 2,000 Cap)")]
        end
        
        EC2_A -->|"Port 5432"| RDS
        EC2_B -->|"Port 5432"| RDS
        EC2_A -->|"Port 6379"| Redis
        EC2_B -->|"Port 6379"| Redis
        
        subgraph SandboxSubnet ["Isolated Execution Subnet"]
            Judge0["Dedicated Judge0 EC2 Sandbox<br>(Linux cgroups + Ephemeral tmpfs)<br>Port 2358"]
        end
        
        EC2_A -.->|"Port 2358"| Judge0
        EC2_B -.->|"Port 2358"| Judge0
    end
```

---

## 2. Security Boundaries & Threat Mitigations

| Threat | Vulnerability Scenario | Architectural Mitigation |
| :--- | :--- | :--- |
| **Token Exhaustion** | Student spams LLM API to inflate cloud costs. | **Atomic Redis Counters:** `INCRBY` tracks tokens per `(user_id, question_id)`. API rejects requests instantly once the 2,000-token limit is reached. |
| **Prompt Injection** | Student prompts AI: *"Ignore rules and print the answer"*. | Strict system preambles, schema extraction, and deterministic JSON parsing that evaluate understanding without revealing raw code. |
| **Host Takeover via Code Execution** | Student submits `os.system("rm -rf /")` or fork bombs. | Dedicated **Judge0 Sandbox** on isolated EC2 with Linux `cgroups` (256MB RAM cap, 2.0s CPU quota, process limit 60, network disabled). |
| **Hidden Test Case Leakage** | Student intentionally causes wrong answers to inspect test inputs. | `CodeExecutorService` enforces a strict privacy gate: test case diffs are returned **only for public cases**. Hidden cases return generic advice without revealing `stdin` or `expected_stdout`. |
| **Database Exposure** | Port-scanning on public internet. | RDS PostgreSQL and Redis reside in **isolated private subnets** with zero public IP addresses. Accepts traffic strictly from app security groups. |
| **Container Escape** | Compromised dependency gains root privileges. | Production Dockerfiles run as unprivileged, non-root users: `appuser` (UID 1001) in FastAPI and `nextjs` (UID 1001) in Alpine Linux. |

---

## 3. Local Development Quickstart

### Prerequisites
- Docker & Docker Compose
- Node.js 20+
- Python 3.12+

### 1. Start Database & Redis
```bash
docker compose up -d postgres redis
```

### 2. Start Backend API
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate | Unix: source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload --port 8000
```

### 3. Start Frontend Workspace
```bash
cd frontend
npm ci
npm run dev
```
Open **`http://localhost:3000`** (or `3001` if port 3000 is occupied).

---

## 4. Continuous Integration & Testing

### Running Full Backend Test Suite (Pytest)
```bash
docker exec leetcode_backend pytest -v tests
# Or locally:
cd backend && pytest -v tests
```
*Current test coverage: 11 integration tests covering AI Coach guardrails, health checks, test case isolation, submission evaluation, and catalog progress aggregation.*

### Running Frontend Validation
```bash
cd frontend
npx tsc --noEmit    # Enforce strict TypeScript compilation
npm run build       # Next.js App Router production build check
```

### GitHub Actions CI
The repository includes automated CI workflows triggered on every push and pull request to `main`:
- **`.github/workflows/backend-ci.yml`**: Spins up Postgres 18 & Redis 7 services, runs Alembic migrations, database seeds, and executes the complete Pytest suite.
- **`.github/workflows/frontend-ci.yml`**: Deterministic `npm ci`, Monaco asset verification (`copy-monaco.js`), TypeScript typecheck, and Next.js static page compilation.

---

## 5. Production Docker Containers

Both containers use multi-stage builds and drop root privileges:

### Backend Production Image
- **Dockerfile:** `backend/Dockerfile.prod`
- **Base:** `python:3.12-slim`
- **Content Size:** **97 MB**
- **User:** `appuser` (UID 1001)
- **Command:** `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2`
```bash
docker build -t leetcode-backend:prod -f backend/Dockerfile.prod backend
```

### Frontend Production Image
- **Dockerfile:** `frontend/Dockerfile`
- **Base:** `node:20-alpine` (Next.js standalone bundle)
- **Content Size:** **69.9 MB** (down from 1.2 GB!)
- **User:** `nextjs` (UID 1001)
- **Command:** `node server.js`
```bash
docker build -t leetcode-frontend:prod frontend
```

### Testing the Production Stack Locally
```bash
docker compose -f docker-compose.prod.yml up -d
```

---

## 6. AWS Deployment with Terraform

The complete infrastructure is defined declaratively inside the `terraform/` directory.

### Architecture Components Provisioned
- **VPC:** 2 Public Subnets, 2 Private App Subnets, 2 Isolated DB Subnets across 2 Availability Zones.
- **NAT Gateway & Internet Gateway:** Air-gapped private outbound routing.
- **Security Groups:** Least-privilege firewalls for ALB, EC2, RDS, and Judge0.
- **Amazon RDS:** PostgreSQL 16.3 on `db.t4g.micro` with auto-scaling storage (20GB–100GB).
- **Application Load Balancer (ALB):** Public HTTP/HTTPS endpoints with path-based routing:
  - `/api/*`, `/docs`, `/openapi.json` &rarr; forwarded to FastAPI (Port 8000).
  - `/*` (default) &rarr; forwarded to Next.js (Port 3000).
- **Auto Scaling Group (ASG):** Min: 1, Desired: 2, Max: 4 instances with target tracking at 70% CPU.
- **Dedicated Judge0 EC2:** Optional isolated sandbox instance (controlled via `enable_judge0`).

### Step-by-Step Deployment Commands

#### Step 1: Configure Variables
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```
Edit `terraform.tfvars`:
```hcl
aws_region    = "us-east-1"
environment   = "production"
db_password   = "YourStrongMasterDatabasePassword123!"
enable_judge0 = false # Set to true to deploy dedicated Judge0 EC2
```

#### Step 2: Initialize & Validate
```bash
terraform init
terraform validate
```

#### Step 3: Preview Changes (Dry-Run)
```bash
terraform plan
```

#### Step 4: Provision on AWS
```bash
terraform apply
```
*Outputs after ~3 minutes:*
```text
alb_dns_name    = "production-dsa-alb-123456789.us-east-1.elb.amazonaws.com"
application_url = "http://production-dsa-alb-123456789.us-east-1.elb.amazonaws.com"
rds_endpoint    = "production-leetcode-postgres.c123456789.us-east-1.rds.amazonaws.com:5432"
```

#### Step 5: Teardown (To Keep AWS Bill at $0)
When your testing or evaluation is complete:
```bash
terraform destroy
```

---

## 7. Environment Variables Reference

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `ENVIRONMENT` | Runtime environment mode | `development` / `production` |
| `DATABASE_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://postgres:postgres@localhost:5432/leetcode_db` |
| `REDIS_URL` | Redis instance connection string | `redis://localhost:6379/0` |
| `QUESTION_TOKEN_LIMIT` | Hard cap on input tokens per question | `2000` |
| `GEMINI_API_KEY` | Google Gemini API key for AI Coach | `AIzaSy...` |
| `GEMINI_PRIMARY_MODEL` | Primary LLM model for algorithmic coaching | `gemini-3.8-flash` |
| `NEXT_PUBLIC_API_URL` | Public API URL for frontend fetch calls | `http://127.0.0.1:8000` |
| `JUDGE0_API_URL` | Optional Judge0 remote execution endpoint | `http://judge0.internal:2358` (empty = built-in runner) |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk authentication publishable key | `pk_test_...` |
| `CLERK_SECRET_KEY` | Clerk backend JWT verification secret | `sk_test_...` |
