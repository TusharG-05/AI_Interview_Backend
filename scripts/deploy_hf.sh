#!/bin/bash

# Configuration
# Load from .env if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

if [ -z "$HF_TOKEN" ]; then
    echo "❌ Error: HF_TOKEN is not set in your .env file."
    echo "Please add HF_TOKEN=\"your_token\" to your .env file."
    exit 1
fi
HF_REPO="https://huggingface.co/spaces/ichigo253/AI_Interview_Backend"
DEPLOY_DIR="../hf_deploy"

echo "🚀 Starting Deployment to Hugging Face..."

# 1. Sync local code to deploy directory
echo "📦 Syncing code..."
rsync -av --progress . "$DEPLOY_DIR/" \
    --exclude .git \
    --exclude .venv \
    --exclude __pycache__ \
    --exclude .pytest_cache \
    --exclude .vscode \
    --exclude app.log \
    --exclude .env \
    --exclude frontend \
    --exclude "*.zip"

# 2. Enter deploy directory
cd "$DEPLOY_DIR" || exit

# 2.5 Ensure the HF-specific Dockerfile is used
echo "🐳 Configuring Dockerfile for Hugging Face..."
cp Dockerfile.hf Dockerfile

# 3. Commit and Push
echo "⬆️ Pushing to Hugging Face..."
git add .
git commit -m "Update: $(date +'%Y-%m-%d %H:%M:%S')"
git push --force "https://user:$HF_TOKEN@huggingface.co/spaces/ichigo253/AI_Interview_Backend" main-deploy:main

echo "✅ Push successful! Hugging Face is now rebuilding your Space."
echo "🔗 Check progress here: $HF_REPO?logs=build"
