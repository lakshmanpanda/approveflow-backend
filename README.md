
# ApproveFlow Enterprise API - Backend ⚙️

This is the backend orchestration engine for the Dynamic Hierarchical Approval System

It is built with **Python 3.10+, FastAPI, and SQLAlchemy**, and has been engineered for production using a distributed cloud architecture.

## 🏗️ Production Architecture
The system has been migrated from a local Docker environment to a scalable cloud-native stack:* **API Framework:** FastAPI (Asynchronous Python) hosted on **Render.com**.* **Relational Database:** PostgreSQL hosted on **Neon.tech** (Serverless).* **Object Storage:** S3-Compatible cloud storage via **Backblaze B2**.* **PDF Engine:** `xhtml2pdf` for dynamic generation of approved documents with digital stamps.



## 📊 Database Schema & Relationships
The backend uses **SQLAlchemy** to manage a complex hierarchical data model designed for organizational workflows:* **Organization Module:** Manages `User`, `Department`, and `Position`. It supports strict Role-Based Access Control (RBAC).* **Workflow Engine:** `Workflow` and `WorkflowStage` models define the path a document must take.* **Submission Module:** `FormSubmission` and `ApprovalRequest` track the live state and history of every request.* **Audit System:** `AuditLog` provides an immutable trail of every action for enterprise compliance.

## 🛠️ Environment Configuration (Production)
For security, the system relies on environment variables. These are configured in the Render Dashboard:```env
PROJECT_NAME="ApproveFlow Enterprise API"
SECRET_KEY="[SECURE_JWT_SECRET]"
ALGORITHM="HS256"

# Database - Neon PostgreSQL
DATABASE_URL="postgresql://[user]:[password]@[host]/neondb"

# Storage - Backblaze B2 (S3-Compatible)
MINIO_ENDPOINT="s3.us-east-005.backblazeb2.com"
MINIO_ACCESS_KEY="[B2_KEY_ID]"
MINIO_SECRET_KEY="[B2_APPLICATION_KEY]"
MINIO_SECURE="True"
MINIO_BUCKET_NAME="approveflow-vault"
## 🚀 Quick Start & Local Development

### 1️⃣ Install Dependencies

```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2️⃣ Database Initialization

The system automatically generates required tables upon startup using SQLAlchemy's `create_all`.

To seed the initial environment and Super Admin:

```bash
python seed.py
```

### 3️⃣ Start Server

```bash
uvicorn app.main:app --reload --port 10000
```

---

## 📖 API Documentation & Testing

The API is fully documented using **OpenAPI standards**:

- **Interactive Swagger UI:**  
  https://approveflow-api.onrender.com/docs

- **ReDoc:**  
  https://approveflow-api.onrender.com/redoc

---

## 🔐 Authentication Flow

1. Navigate to `/docs`
2. Click **Authorize**
3. Log in using Super Admin credentials:

```
Email: admin@gmail.com
Password: think@123
```

4. All subsequent requests will automatically include the JWT Bearer token.

---

## 🛡️ Security & Performance

- **CORS Protection:**  
  Configured to strictly allow requests only from the production Vercel frontend.

- **Asynchronous Processing:**  
  Leverages Python `async/await` for high-concurrency request handling.

- **Connection Pooling:**  
  Uses `pool_pre_ping` to maintain resilient connections to the serverless PostgreSQL instance.

- **Secure PDF Generation:**  
  Final documents are generated server-side and uploaded to private cloud buckets with pre-signed URL access.