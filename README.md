# 🐱 Cat vs Dog Classifier

> **An end-to-end ML image classification web app deployed on AWS — 100% Free Tier ($0/month)**

Upload any image and our AI will tell you whether it's a **cat** 🐱 or a **dog** 🐶 — complete with confidence probabilities!

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![AWS](https://img.shields.io/badge/AWS-Free%20Tier-FF9900?logo=amazonaws)
![Terraform](https://img.shields.io/badge/Terraform-IaC-7B42BC?logo=terraform)
![Docker](https://img.shields.io/badge/Docker-Container-2496ED?logo=docker)

---

## 🌐 Live Demo

| Service | URL |
|---------|-----|
| **Frontend** | [cat-vs-dog-frontend-235899055608.s3-website.eu-west-2.amazonaws.com](http://cat-vs-dog-frontend-235899055608.s3-website.eu-west-2.amazonaws.com) |
| **API Health** | [af9aiibt3m.execute-api.eu-west-2.amazonaws.com/health](https://af9aiibt3m.execute-api.eu-west-2.amazonaws.com/health) |

---

## 📐 Architecture

```
┌─────────────┐       ┌──────────────┐       ┌─────────────┐       ┌───────────┐
│   Browser   │──────▶│  S3 Static   │       │ API Gateway │──────▶│  Lambda   │
│  (Frontend) │       │   Website    │──────▶│  (HTTP API) │       │ (Docker)  │
└─────────────┘       └──────────────┘       └──────────────┘       └─────┬─────┘
                                                                         │
                      ┌──────────────┐       ┌──────────────┐            │
                      │  CloudWatch  │◀──────│     ECR      │◀───────────┘
                      │   Alarms     │       │ (Container)  │
                      └──────┬───────┘       └──────────────┘
                             │
                      ┌──────▼───────┐
                      │  SNS Email   │
                      │   Alerts     │
                      └──────────────┘
```

**Frontend** → Static HTML/CSS/JS hosted on **S3** (drag-and-drop image upload with light/dark mode)  
**Backend** → **Lambda** (container image from **ECR**) behind **API Gateway**, running ONNX inference  
**Monitoring** → **CloudWatch** alarms → **SNS** email alerts + **AWS Budget** guard  
**CI/CD** → **GitHub Actions** builds Docker, pushes to ECR, deploys frontend to S3

---

## 🧠 How It Works

### ML Pipeline

1. **Image Preprocessing** — Smart resize (128×128), CLAHE contrast enhancement, bilateral filtering
2. **Feature Extraction** — 10,221 handcrafted features from 8 families:
   - HOG (Histogram of Oriented Gradients) — fine + coarse
   - LBP (Local Binary Patterns) — multi-scale
   - Color Histograms (HSV + LAB)
   - Color Moments (mean, std, skew)
   - Haralick Texture Features (GLCM)
   - Hu Moments (shape descriptors)
   - Edge Features (Canny, Sobel, orientation histograms)
   - Gabor Filter Responses (multi-frequency, multi-orientation)
3. **StandardScaler** — Normalizes features to match training distribution
4. **XGBoost (ONNX)** — Gradient-boosted tree ensemble for binary classification
5. **Probability Output** — Returns per-class probabilities (cat % vs dog %)
6. **OOD Detection** — If neither class exceeds 51% confidence, the image is flagged as "unknown"

### Model Performance

| Metric | Score |
|--------|-------|
| **Accuracy** | >80% |
| **F1 Score** | >80% |
| **Model Size** | 2.03 MB (ONNX) |
| **Inference Time** | ~3-5s (Lambda cold start: ~30s first request) |

---

## 📁 Project Structure

```
image_processing/
├── api/                          # Backend API
│   ├── main.py                   # FastAPI app with /health and /predict endpoints
│   ├── lambda_handler.py         # AWS Lambda entry point
│   ├── ml.py                     # ML pipeline (ONNX model + StandardScaler)
│   ├── feature_extractor.py      # Image preprocessing & 10,221-feature extraction
│   ├── schemas.py                # Pydantic response models
│   └── dependencies.py           # Singleton model loader
├── frontend/                     # Static frontend (hosted on S3)
│   ├── index.html                # Main UI with drag-and-drop upload
│   ├── index.css                 # Styles with light/dark mode
│   └── app.js                    # Upload logic, probability bars, theme toggle
├── model/                        # Trained model artifacts
│   ├── xgboost_champion.onnx     # XGBoost model in ONNX format (2.03 MB)
│   └── scaler.joblib             # Fitted StandardScaler (240 KB)
├── infra/                        # Terraform Infrastructure as Code
│   ├── main.tf                   # ECR, S3, Lambda, API Gateway, IAM
│   ├── outputs.tf                # Deployment URLs
│   └── monitoring.tf             # CloudWatch alarms, SNS, Budget guard
├── .github/workflows/
│   └── deploy.yml                # CI/CD: build → ECR → Lambda → S3
├── Dockerfile                    # Lambda Python 3.11 container
├── requirements.txt              # Pinned Python dependencies
├── .dockerignore                 # Excludes data/notebooks from Docker build
└── .gitignore                    # Excludes secrets, data, terraform state
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Docker Desktop
- AWS CLI (configured with `aws configure`)
- Terraform 1.x+

### Local Development

```bash
# 1. Clone the repository
git clone https://github.com/Nduka99/image_processing_deployment.git
cd image_processing_deployment

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the API server
uvicorn api.main:app --host 127.0.0.1 --port 8000

# 4. Open the frontend
# Navigate to http://127.0.0.1:3000 (via a local HTTP server)
# Or open frontend/index.html directly
```

### Deploy to AWS

```bash
# 1. Initialize and apply Terraform
cd infra
terraform init
terraform apply -auto-approve

# 2. Build and push Docker image
aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.eu-west-2.amazonaws.com
docker build -t <ECR_URL>:latest ..
docker push <ECR_URL>:latest

# 3. Upload frontend to S3 (with API URL injected)
# The GitHub Actions workflow handles this automatically on push to main
```

---

## ☁️ AWS Resources (20 total — all Free Tier)

| # | Service | Resource | Free Tier Limit |
|---|---------|----------|-----------------|
| 1-2 | **ECR** | Container registry + lifecycle policy | 500 MB/month |
| 3-6 | **S3** | Bucket + website config + public access + policy | 5 GB, 20K GET/month |
| 7-8 | **IAM** | Lambda execution role + policy | Always free |
| 9 | **Lambda** | Container function (1024 MB, 60s) | 1M requests, 400K GB-s/month |
| 10-13 | **API Gateway** | HTTP API + integration + routes + stage | 1M calls/month |
| 14-15 | **SNS** | Alert topic + email subscription | 1M publishes/month |
| 16-19 | **CloudWatch** | 4 alarms (errors, duration, throttles, 5XX) | 10 alarms free |
| 20 | **Budgets** | Cost guard ($1/month threshold) | Always free |

---

## 🔄 CI/CD Pipeline

GitHub Actions (`.github/workflows/deploy.yml`) triggers on every push to `main`:

1. ✅ Checkout code
2. ✅ Authenticate with AWS
3. ✅ Build Docker image → Push to ECR
4. ✅ Update Lambda function code
5. ✅ Inject API Gateway URL into frontend → Sync to S3

**Setup**: Add `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` as GitHub Secrets in your repository settings.

---

## 🛡️ Monitoring & Alerts

| Alarm | Triggers When | Action |
|-------|---------------|--------|
| Lambda Errors | Any invocation error | Email via SNS |
| Lambda Duration | Average > 50s (timeout = 60s) | Email via SNS |
| Lambda Throttles | Any throttled invocations | Email via SNS |
| API 5XX Errors | 5+ server errors in 5 minutes | Email via SNS |
| Budget Guard | Monthly cost exceeds $1 | Email notification |

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|-----------|
| **ML Model** | XGBoost (ONNX Runtime) |
| **Feature Extraction** | OpenCV, scikit-image, mahotas, scipy |
| **Backend** | FastAPI + AWS Lambda |
| **Frontend** | Vanilla HTML/CSS/JS |
| **Infrastructure** | Terraform (IaC) |
| **Containerization** | Docker (Lambda Python 3.11 base) |
| **CI/CD** | GitHub Actions |
| **Monitoring** | CloudWatch + SNS |
| **Cloud** | AWS (S3, ECR, Lambda, API Gateway) |

---

## 📄 License

This project was developed as part of an Applied AI assessment.

---

*Built with ❤️ using an agentic AI deployment pipeline*
