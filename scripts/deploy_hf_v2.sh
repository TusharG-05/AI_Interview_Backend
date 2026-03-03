#!/bin/bash

# ============================================================
# Deploy to Hugging Face — v2
# Target Space: https://huggingface.co/spaces/ichigo253/Ai_Interview_Backend_v2
# Deploy Folder: ../hf_deploy_v2  (separate from v1's ../hf_deploy)
# ============================================================

# Load .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

if [ -z "$HF_TOKEN" ]; then
    echo "❌ Error: HF_TOKEN is not set in your .env file."
    echo "Please add HF_TOKEN=\"your_token\" to your .env file."
    exit 1
fi

HF_REPO="https://huggingface.co/spaces/ichigo253/Ai_Interview_Backend_v2"
DEPLOY_DIR="../hf_deploy_v2"

echo "🚀 Starting Deployment to Hugging Face (v2)..."

# ── 1. Bootstrap deploy dir the first time ──────────────────
if [ ! -d "$DEPLOY_DIR/.git" ]; then
    echo "📁 Deploy directory not found. Cloning from Hugging Face..."
    git clone "https://user:$HF_TOKEN@huggingface.co/spaces/ichigo253/Ai_Interview_Backend_v2" "$DEPLOY_DIR"
    if [ $? -ne 0 ]; then
        echo "❌ Clone failed. Check that the HF Space exists and HF_TOKEN is valid."
        exit 1
    fi
    echo "✅ Cloned successfully."
fi

# ── 2. Sync local code into deploy directory ─────────────────
echo "📦 Syncing code to $DEPLOY_DIR ..."
rsync -av --delete --progress . "$DEPLOY_DIR/" \
    --exclude .git \
    --exclude .venv \
    --exclude __pycache__ \
    --exclude .pytest_cache \
    --exclude .vscode \
    --exclude app.log \
    --exclude .env \
    --exclude frontend \
    --exclude "*.zip" \
    --exclude alembic/database.db

# ── 3. Switch to HF-specific Dockerfile ─────────────────────
echo "🐳 Configuring Dockerfile for Hugging Face..."
cp "$DEPLOY_DIR/Dockerfile.hf" "$DEPLOY_DIR/Dockerfile"

# ── 4. Commit and push ───────────────────────────────────────
cd "$DEPLOY_DIR" || exit 1

echo "⬆️  Pushing to Hugging Face (v2)..."
git add .
git commit -m "Update v2: $(date +'%Y-%m-%d %H:%M:%S')"
git push --force "https://user:$HF_TOKEN@huggingface.co/spaces/ichigo253/Ai_Interview_Backend_v2" main:main

echo ""
echo "✅ Push successful! Hugging Face is now rebuilding your Space (v2)."
echo "🔗 Check progress here: $HF_REPO?logs=build"
