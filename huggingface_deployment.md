# Deploying to Hugging Face Spaces

## 1. Create the Space
1.  Go to [huggingface.co/new-space](https://huggingface.co/new-space).
2.  **Name**: `face-gaze-backend` (or similar).
3.  **License**: MIT.
4.  **SDK**: Select **Docker**.
5.  **Space Hardware**: Keep "CPU Basic" (Free).
6.  Click **Create Space**.

## 2. Upload Files
You have two options to upload your code:

### Option A: Web Upload (Easiest)
1.  In your new Space, go to the **Files** tab.
2.  Click **Add file** -> **Upload files**.
3.  Drag and drop **ALL** your project files (all folders `app`, `requirements.txt`, etc.).
4.  **Rename Strategy**:
    *   Hugging Face **ONLY** looks for a file named `Dockerfile`.
    *   **However**, your local project already has a `Dockerfile` (for local dev).
    *   **So, do this**:
        1.  Upload `Dockerfile.hf` but **rename it to** `Dockerfile` **DURING the upload process** (or rename it in the Hugging Face web interface after uploading).
        2.  **Do NOT** upload your local `Dockerfile` (the one for local dev).
5.  Click **Commit changes to main**.

### Option B: Git Push (Best for updates)
1.  Clone the Space locally:
    ```bash
    git clone https://huggingface.co/spaces/YOUR_USERNAME/face-gaze-backend
    ```
2.  Copy your project files into that folder.
3.  Replace the `Dockerfile` with `Dockerfile.hf`.
4.  Commit and push:
    ```bash
    git add .
    git commit -m "Deploy backend"
    git push
    ```
    **Authenticate with Access Token**:
    *   Hugging Face no longer supports passwords for Git.
    *   Go to **Settings** -> **Access Tokens** -> **Create new token** (Write permissions).
    *   When asked for "Username": Use your HF username.
    *   When asked for "Password": **Paste the Access Token**.

## 3. Set Environment Variables
1.  In your Space, go to **Settings**.
2.  Scroll to **Variables and secrets**.
3.  Add the following **Secrets** (for sensitive data):
    *   `POSTGRES_PASSWORD`: (Your DB password)
    *   `SECRET_KEY`: (Random string)
    *   `OLLAMA_BASE_URL`: (You can't run Ollama on HF Free Tier easily - Use Modal instead!)
    *   `USE_MODAL`: `true`
    *   `MODAL_TOKEN_ID`: (From Modal dashboard)
    *   `MODAL_TOKEN_SECRET`: (From Modal dashboard)
4.  Add **Variables** (public config):
    *   `ENV`: `production`

## 4. Verification
*   The "Building" status will spin for a few minutes.
*   Once "Running", you will see your API docs at the top right (Embed tab or direct URL).
