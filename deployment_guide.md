# Deployment Guide: Self-Hosted Backend

This guide explains how to host your backend on a linux server (VPS) with manual updates, ensuring the server runs even when your local PC is off.

## 1. Server Requirements
To run the full stack (App + DB + AI Models + Ollama LLM), you need a VPS with:
- **OS**: Ubuntu 22.04 LTS (Recommended)
- **RAM**: Minimum 8GB (16GB Recommended for better performance)
- **CPU**: 4 vCPUs or more
- **Storage**: 50GB+ SSD

**Recommended Providers**: DigitalOcean, Hetzner, Linode, or AWS Lightsail.

### Free Hosting Options
Most "Free Tier" offerings (AWS t2.micro, Google e2-micro) only provide **1GB RAM**, which is **insufficient** for running an LLM + AI models.

**The Only Viable Free Option:**
- **Oracle Cloud Always Free**:
    - **Instance**: VM.Standard.A1.Flex (ARM-based)
    - **Specs**: Up to 4 OCPUs (ARM) and **24 GB RAM**.
    - **Storage**: 200 GB Block Volume.
    - *Note: Docker images must be built for ARM architecture. Since you are building ON the server (Step 4), this happens automatically!*

## 2. Initial Server Setup
### A. Oracle Cloud Specifics (If using Free Tier)
1.  **Sign Up**: Create an Oracle Cloud Free Tier account.
2.  **Create Instance**:
    - Go to **Compute** -> **Instances** -> **Create Instance**.
    - **Image**: Canonical Ubuntu 22.04.
    - **Shape**: Select **Ampere** (VM.Standard.A1.Flex).
    - **OCPUs**: Set to 4.
    - **Memory**: Set to 24 GB.
    - **SSH Keys**: Upload your PC's public key (usually `~/.ssh/id_rsa.pub`) or generate a new pair.
    - **Networking**: Ensure you assign a public IPv4 address.
3.  **Open Ports**:
    - In the instance details, click the **Subnet** link.
    - Go to **Security Lists** -> Default Security List.
    - Add **Ingress Rule**:
        - Source: `0.0.0.0/0`
        - Protocol: TCP
        - Destination Port Range: `8000` (for API) and `22` (SSH).

### C. Option 2: Google Colab (Temporary Server - 12 Hours Max)
**If you have NO credit card and cannot keep your PC on**, the only remaining option is **Google Colab**.
*   **Pros**: Free T4 GPU, 12GB RAM, runs in the cloud.
*   **Cons**: **Not permanent**. It will shut down after ~12 hours or if you close the tab. You must restart it every time you want to use the app.

**How to run**:
1.  Open a new Google Colab notebook.
2.  Change Runtime to **T4 GPU** (Runtime -> Change runtime type).
3.  Run the following commands in a cell:
    ```python
    !git clone https://github.com/TusharG-05/AI_Interview_Backend.git
    %cd AI_Interview_Backend
    !pip install -r requirements.txt
    !pip install pyngrok
    
    # Setup ngrok
    from pyngrok import ngrok
    ngrok.set_auth_token("YOUR_NGROK_TOKEN")
    public_url = ngrok.connect(8000)
    print(f"Public URL: {public_url}")
    
    # Run Server (will block the cell)
    !uvicorn app.server:app --host 0.0.0.0 --port 8000
    ```
4.  Copy the `ngrok` URL and use it in your frontend.

### D. Option 3: Hugging Face Spaces (Best "Set and Forget" Option)
**This is the best option for running at night without your PC.**
*   **Pros**: Free, runs 24/7 (pauses after 48h inactivity), 16GB RAM.
### D. Option 3: Hugging Face Spaces + Modal (Best "Managed" Option)
**Since you are using Modal for Heavy Compute (STT)**:
This is the **Perfect Setup** for you.
*   **Architecture**:
    *   **Frontend + API (FastAPI)** runs on **Hugging Face Spaces** (Free CPU Tier).
    *   **Heavy AI (Whisper/LLM)** runs on **Modal** (Serverless).
*   **Cost**:
    *   HF Spaces: $0 (Always Free).
    *   Modal: $30/month "free" credits (usually enough for personal use).
*   **Trade-off**: None! You get GPU speed from Modal and 24/7 uptime from HF Spaces.

**Steps**:
1.  **Deploy backend to Hugging Face Spaces** (Docker SDK).
2.  Set `USE_MODAL=true` in HF Spaces secrets.
3.  Add your `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` to HF Spaces secrets.
4.  The backend will wake up instantly on HF, and offload heavy work to Modal.

### E. Option 4: Home Server (No Credit Card Required)
**If you cannot sign up for Oracle Cloud (requires Credit Card)**, the only **FREE** option that supports your 24GB+ RAM requirement is to use an old unwanted laptop/PC at home as a server.

1.  **Hardware**: Any old laptop/PC with 16GB+ RAM.
2.  **OS**: Install **Ubuntu Server** (or just run Docker Desktop on Windows).
3.  **Tunneling**: Use `ngrok` (already in `docker-compose.yml`) or **Cloudflare Tunnel** to make it accessible from the internet.

**Steps**:
1.  Run `docker compose up -d` on your home "server" PC.
2.  The `ngrok` service will create a public URL (e.g., `https://random-name.ngrok-free.app`).
3.  Use this URL in your frontend app.
*Note: The PC must stay ON for the server to work.*

## 2. Initial Server Setup (For VPS)
Connect to your server via SSH:
```bash
ssh root@your-server-ip
```

### Install Docker & Git
```bash
# Update system
apt update && apt upgrade -y

# Install Git
apt install -y git

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Verify Docker
docker --version
docker compose version
```

## 3. Deployment
### A. Clone the Repository
```bash
# Navigate to a directory
mkdir -p /opt/face_gaze
cd /opt/face_gaze

# Clone your repo (use HTTPS or set up SSH keys)
git clone https://github.com/TusharG-05/AI_Interview_Backend.git .
```

### B. Configure Environment
Create the `.env` file from the example or your local copy.
```bash
nano .env
```
Paste your environment variables (`POSTGRES_PASSWORD`, `SECRET_KEY`, etc.). Ensure `OLLAMA_BASE_URL=http://ollama:11434`.

### C. Start Services
Run the application in detached mode (background):
```bash
docker compose up -d
```
Docker will pull images and build the app container. This may take a few minutes.

### D. Download the LLM Model (One-time Setup)
The `ollama` container starts empty. You must manually pull the model:
```bash
# Execute the pull command inside the running ollama container
docker exec -it face_gaze_ollama ollama pull qwen2.5-coder:3b
```
*Note: This download (approx 2-3GB) happens once and is persisted in the volume.*

## 4. Manual Updates
When you make changes to your code locally and push them to GitHub, follow these steps to update the server manually:

1. **SSH into your server**:
   ```bash
   ssh root@your-server-ip
   cd /opt/face_gaze
   ```

2. **Pull the latest code**:
   ```bash
   git pull origin main  # or your branch name
   ```

3. **Rebuild and Restart**:
   ```bash
   docker compose up -d --build
   ```
   *The `--build` flag ensures the application image is rebuilt with your new code.*

## 5. Maintenance
- **View Logs**: `docker compose logs -f app`
- **Stop Server**: `docker compose down`
- **Restart**: `docker compose restart`
