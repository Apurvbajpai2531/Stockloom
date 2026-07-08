# 🚀 StockLoom — Inventory & Warehouse Management Platform

StockLoom is a production-ready **inventory and warehouse management platform** built with **FastAPI, NiceGUI, and PostgreSQL**.

It provides complete inventory lifecycle management with stock tracking, warehouse operations, purchasing, analytics, forecasting, and security automation.

The project follows a **DevSecOps approach** by integrating automated quality checks, security scanning, vulnerability analysis, Docker validation, and CI/CD automation using **GitHub Actions**.

---

# ✨ Features

## 📦 Inventory Management

- Item, category, and supplier management
- Multi-warehouse inventory tracking
- Stock movements:
  - Inbound
  - Outbound
  - Transfer
  - Adjustment
- Purchase order management
- Automatic stock updates
- Low stock alerts

## 📊 Analytics & Intelligence

- Inventory dashboard
- Warehouse analytics
- Reports generation
- Stock forecasting
- ABC analysis
- Cost analysis
- Reorder recommendations

## 🔐 Security

- JWT Authentication
- Role-Based Access Control (RBAC)
- Audit logging
- QR code inventory support
- Secure API communication

## 🎨 Frontend

- Modern NiceGUI interface
- Responsive dashboard
- Dark mode support
- Interactive inventory views

---

# 🏗️ Architecture

```
                Users
                  |
                  |
          NiceGUI Frontend
                  |
                  |
           FastAPI Backend
                  |
                  |
          PostgreSQL Database


          DevSecOps Pipeline

          GitHub Actions

                  |
   --------------------------------
   |          |          |        |
Quality   Security   Docker   Delivery
Checks     Scan       Scan    Pipeline
```

---

# 🛠️ Tech Stack

### Backend
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic
- JWT Authentication

### Frontend
- NiceGUI
- Python

### DevOps
- Docker
- Docker Compose
- GitHub Actions

### Security Tools
- Ruff
- Black
- MyPy
- Bandit
- Semgrep
- pip-audit
- Trivy
- Hadolint
- Gitleaks

---

# 🔄 DevSecOps CI/CD Pipeline

Automated GitHub Actions workflow:

```
Code Push
    |
GitHub Actions
    |
-------------------------
|        |        |
Quality Security Testing
Checks    Scan
    |
Docker Security Scan
    |
Build Docker Images
    |
Push to Docker Registry
```

## Pipeline Includes

✅ Python linting and formatting  
✅ Static type checking  
✅ Automated tests  
✅ Secret scanning  
✅ Dependency vulnerability scanning  
✅ SAST security analysis  
✅ Dockerfile security validation  
✅ Container vulnerability scanning  
✅ Docker image publishing  

---

# 📂 Project Structure

```
StockLoom/

├── backend/
│   ├── app/
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── pages/
│   ├── Dockerfile
│   └── requirements.txt
│
├── docker-compose.yml
│
└── .github/workflows/
    ├── code-quality.yml
    ├── code-test.yml
    ├── security-scan.yml
    ├── docker-scan.yml
    └── docker-push.yml
```

---

# 🚀 Run Locally

### Using Docker Compose

```bash
docker compose up --build
```

Stop:

```bash
docker compose down
```

---

# 🌐 Application URLs
Frontend:

```
http://localhost:8081
```
Backend API:
```
http://localhost:8000
```
Swagger Docs:
```
http://localhost:8000/docs
```
---
# 🎯 Production Practices
✅ Containerized application architecture  
✅ Automated CI/CD pipeline  
✅ DevSecOps security integration  
✅ Code quality enforcement  
✅ Vulnerability scanning  
✅ Secure Docker image lifecycle  
✅ Automated image publishing  

---

# 🔮 Future Enhancements
- Kubernetes deployment
- AWS cloud deployment
- Terraform infrastructure
- Jenkins CI/CD
- Prometheus & Grafana monitoring
- Automated production deployment

---
⭐ **StockLoom demonstrates a complete Full-Stack + DevSecOps implementation for modern inventory management systems.**
