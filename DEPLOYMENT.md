# 🚀 FoodBridge AI - Deployment & Git Guide

This guide explains how to commit, push to GitHub, and deploy your FoodBridge AI Streamlit application.

---

## 📦 Deployment Configuration Files Created

| File | Purpose | Platform |
| :--- | :--- | :--- |
| [`requirements.txt`](requirements.txt) | Python package dependencies manifest | All / Streamlit Cloud |
| [`.streamlit/config.toml`](.streamlit/config.toml) | Theme and headless server configuration | Streamlit Cloud / Local |
| [`Dockerfile`](Dockerfile) | Container image build instructions | Render, Railway, Hugging Face, AWS/GCP |
| [`.dockerignore`](.dockerignore) | Prevents local cache/.venv from entering Docker image | Docker builds |
| [`Procfile`](Procfile) | Web server entry point command | Heroku, Render |
| [`render.yaml`](render.yaml) | Infrastructure-as-code blueprint | Render |
| [`runtime.txt`](runtime.txt) | Explicit Python version specification (3.11.8) | Cloud PaaS platforms |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | Automated unit testing on every push | GitHub Actions |
| [`vercel.json`](vercel.json) | Vercel serverless routing configuration | Vercel (Experimental / Serverless) |

---

## 1️⃣ Pushing to GitHub

Your repository is connected to:
`https://github.com/atharvasalunke006-cloud/FoodBridgeAI.git`

### Option A: Using VS Code / Cursor GUI (Easiest)
1. Click the **Source Control** icon on the left sidebar (or press `Ctrl + Shift + G`).
2. Stage all changes by clicking the `+` icon next to **Changes**.
3. Type a commit message (e.g. `feat: add deployment configuration files`).
4. Click **Commit** (or checkmark), then click **Sync Changes** / **Push**.

### Option B: Using Git Command Line
If Git is installed on your computer, run in PowerShell:
```powershell
cd D:\FoodBridgeAi
git add .
git commit -m "feat: configure files for cloud deployment and docker"
git push -u origin main
```
*(If Git is not yet installed on your machine, download it from [git-scm.com](https://git-scm.com/download/win).)*

---

## 2️⃣ Deploying to the Cloud

### 🌟 Method 1: Streamlit Community Cloud (Recommended - Free & Easiest)
1. Visit **[share.streamlit.io](https://share.streamlit.io)** and log in with your GitHub account.
2. Click **New app**.
3. Select your repository: `atharvasalunke006-cloud/FoodBridgeAI`
4. Set:
   - **Branch:** `main` (or `master`)
   - **Main file path:** `app.py`
5. Click **Deploy!**
   - Streamlit Cloud will install dependencies from `requirements.txt` and launch your app with a permanent, public HTTPS link.

---

### 🐳 Method 2: Render (Free Web Service or Docker)
1. Visit **[render.com](https://render.com)** and sign in.
2. Click **New +** -> **Blueprint**.
3. Connect `atharvasalunke006-cloud/FoodBridgeAI`.
4. Render will automatically detect `render.yaml` and configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
5. Click **Apply**.

---

### 🐋 Method 3: Run with Docker Locally
To build and run the Docker container locally:
```powershell
# Build Docker image
docker build -t foodbridge-ai .

# Run Docker container on port 8501
docker run -p 8501:8501 foodbridge-ai
```
Then visit `http://localhost:8501`.

---

### ⚠️ Note on Vercel
[`vercel.json`](vercel.json) has been provided in the repository root. However, **Vercel is designed for stateless/serverless frontends and APIs (Next.js/React)**, whereas **Streamlit is a stateful Python server that requires persistent WebSocket connections**. 
- Deploying full Streamlit apps directly to Vercel's serverless environment will encounter WebSocket disconnects and function timeout limits.
- For a seamless, 1-click experience identical to Vercel, **Streamlit Community Cloud** ([share.streamlit.io](https://share.streamlit.io)) or **Render** ([render.com](https://render.com)) is strongly recommended.

