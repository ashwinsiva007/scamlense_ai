# ScamLens DigitalOcean & Cloud Deployment Guide

This document provides production-grade, step-by-step instructions for deploying ScamLens. It covers:
1. **Option A: DigitalOcean Droplet** (Docker Compose + Automated HTTPS with Caddy/Nginx)
2. **Option B: DigitalOcean App Platform** (Serverless Managed PaaS)
3. **Option C: Hybrid Frontend on Vercel + Backend on Droplet**
4. **Environment Variables Reference**

---

> [!IMPORTANT]  
> **Hardware & Model Inference Notice:**  
> Standard entry-level Droplets (e.g., Basic 1 vCPU / 2 GB RAM at ~$12/month) are **ideal for Cloud Mode** (using Gemini API endpoints under zero-data-retention). However, they lack the compute and VRAM required for self-hosted local model inference. Running 9B or even quantized local models on a small CPU droplet will cause severe latency (>90 seconds per request) or Out-Of-Memory (OOM) crashes. **For live demonstrations and production web apps, deploy in `MODE=cloud`.**

---

## 1. Option A: DigitalOcean Droplet Deployment

### Step 1: Create and Access Droplet
1. Log in to your [DigitalOcean Control Panel](https://cloud.digitalocean.com).
2. Click **Create** > **Droplets**.
3. Choose **Ubuntu 24.04 LTS (x64)**.
4. Plan recommendation:
   - **For Cloud Mode:** Basic Droplet, Regular SSD, 2 GB RAM / 1 vCPU ($12/mo).
   - **For Local Mode (Self-Hosted Ollama):** CPU-Optimized or Dedicated Droplet with minimum 16 GB RAM ($80+/mo) or an external GPU instance.
5. Select SSH Key authentication.
6. Click **Create Droplet** and note your Droplet's public IPv4 address (e.g. `203.0.113.50`).
7. Connect to your Droplet via SSH:
   ```bash
   ssh root@203.0.113.50
   ```

---

### Step 2: System Update & Docker Installation
Execute the official automated Docker installation script:

```bash
# Update package repositories
apt-get update && apt-get upgrade -y

# Install Docker engine and Docker Compose plugin
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Verify Docker installation
docker --version
docker compose version
```

---

### Step 3: Clone ScamLens Repository
```bash
cd /opt
git clone https://github.com/ashwinsiva007/scamlense_ai.git scamlens
cd scamlens
```

---

### Step 4: Configure Production Environment Variables
Copy `.env.example` and supply your production configuration:

```bash
cp .env.example .env
nano .env
```

Populate the `.env` file:
```env
# Runtime Mode (Use cloud for live demo)
MODE=cloud

# Google Gemini / AI Studio API key (Required in cloud mode)
GEMINI_API_KEY=AIzaSy...your_real_gemini_api_key_here
GEMMA_MODEL=google/gemma-4-9b-it

# Live Threat Intelligence Keys (Optional but recommended)
SAFE_BROWSING_KEY=your_google_safe_browsing_key_here
URLHAUS_KEY=

# Backend CORS & Security
# Replace with your domain name or public IP
ALLOWED_ORIGINS=https://scamlens.yourdomain.com,http://203.0.113.50
MAX_UPLOAD_MB=8
RATE_LIMIT_PER_MIN=30

# Frontend Configuration
NEXT_PUBLIC_API_URL=https://scamlens.yourdomain.com
```

---

### Step 5: Configure UFW Firewall
Secure the Droplet by exposing only SSH, HTTP, and HTTPS ports:

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
ufw status
```

---

### Step 6: Automated HTTPS Reverse Proxy (Caddy)

Caddy automatically provisions and renews free SSL certificates from Let's Encrypt for your domain.

Create a `Caddyfile` in the repository root:
```bash
nano Caddyfile
```

Paste the following configuration (replace `scamlens.yourdomain.com` with your domain):

```caddy
scamlens.yourdomain.com {
    # Route API calls to FastAPI backend container
    handle /api/* {
        reverse_proxy localhost:8000
    }

    # Route documentation or root health checks
    handle /docs* {
        reverse_proxy localhost:8000
    }
    handle /openapi.json {
        reverse_proxy localhost:8000
    }

    # Route all other web traffic to Next.js frontend container
    handle {
        reverse_proxy localhost:3000
    }
}
```

> [!TIP]
> If you do not yet have a custom domain name and want to test directly over your Droplet IP, configure Caddy with `http://203.0.113.50` or map ports `80:3000` and `8000:8000` directly in `docker-compose.yml`.

Install and launch Caddy:
```bash
apt-get install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt-get update
apt-get install -y caddy

# Load your Caddyfile
caddy reload --config /opt/scamlens/Caddyfile
```

---

### Step 7: Launch the Application with Docker Compose

Start the production stack in the background:

```bash
cd /opt/scamlens
docker compose up -d --build
```

Verify service health:
```bash
docker compose ps
docker compose logs -f backend
```

Test endpoint directly:
```bash
curl http://localhost:8000/api/health
```

Expected output:
```json
{"status":"ok","mode":"cloud","model":"google/gemma-4-9b-it","ollama_reachable":false,"cloud_key_set":true}
```

---

## 2. Option B: DigitalOcean App Platform (PaaS)

If you prefer a fully managed container service without maintaining virtual machines or OS updates:

1. In DigitalOcean, navigate to **Apps** > **Create App**.
2. Connect your GitHub repository: `https://github.com/ashwinsiva007/scamlense_ai.git`.
3. Configure the **Backend Service**:
   - **Source Directory:** `backend`
   - **Dockerfile:** `backend/Dockerfile`
   - **HTTP Port:** `8000`
   - **Health Check Path:** `/api/health`
   - **Environment Variables:**
     - `MODE=cloud`
     - `GEMINI_API_KEY=your_key`
     - `ALLOWED_ORIGINS=https://${APP_DOMAIN}`
4. Configure the **Frontend Service**:
   - **Source Directory:** `frontend`
   - **Dockerfile:** `frontend/Dockerfile`
   - **HTTP Port:** `3000`
   - **Environment Variables:**
     - `NEXT_PUBLIC_API_URL=https://${APP_DOMAIN}`
5. Choose the Basic tier ($5/mo for frontend, $12/mo for backend) and click **Deploy**.

---

## 3. Option C: Vercel (Frontend) + DigitalOcean Droplet (Backend)

For global edge CDN performance on the frontend:

1. **Deploy Backend on Droplet** (following Section 1 steps 1–7). Ensure your Droplet's Caddy or Nginx serves `https://api.yourdomain.com`.
2. **Deploy Frontend on Vercel**:
   - Go to [vercel.com](https://vercel.com) and click **Add New Project**.
   - Import `https://github.com/ashwinsiva007/scamlense_ai.git`.
   - Set **Root Directory** to `frontend`.
   - Add Environment Variable:
     - `NEXT_PUBLIC_API_URL=https://api.yourdomain.com`
   - Click **Deploy**.
3. In your Droplet's `.env`, update `ALLOWED_ORIGINS` to include your Vercel deployment URL:
   ```env
   ALLOWED_ORIGINS=https://scamlens.vercel.app,https://yourdomain.com
   ```
4. Restart backend:
   ```bash
   docker compose restart backend
   ```

---

## 4. Environment Variables Reference

| Variable | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `MODE` | string | `mock` | Execution mode: `cloud`, `local`, or `mock`. Use `cloud` for production. |
| `GEMINI_API_KEY` | string | `""` | Google AI Studio Gemini API Key. Required in `cloud` mode. |
| `GEMMA_MODEL` | string | `google/gemma-4-9b-it` | Model identifier for cloud perception and explanation. |
| `OLLAMA_BASE_URL` | string | `http://localhost:11434` | Ollama daemon endpoint (used in `local` mode). |
| `OLLAMA_MODEL` | string | `gemma4:latest` | Local Ollama model tag. |
| `SAFE_BROWSING_KEY` | string | `""` | Optional Google Safe Browsing v4 API key for malicious URL lookup. |
| `URLHAUS_KEY` | string | `""` | Optional Abuse.ch URLhaus API key for threat feed checks. |
| `ALLOWED_ORIGINS` | string | `http://localhost:3000` | Comma-separated CORS allowed origin URLs. |
| `MAX_UPLOAD_MB` | int | `8` | Maximum allowed file size for screenshot uploads in megabytes. |
| `RATE_LIMIT_PER_MIN`| int | `20` | Sliding window rate limit per client IP. |
| `NEXT_PUBLIC_API_URL`| string | `http://localhost:8000` | Target backend URL for frontend API calls. |
| `NEXT_PUBLIC_DEMO_MODE`| boolean| `false` | Set to `true` to force offline mock sample mode on frontend. |
