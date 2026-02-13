#!/bin/bash

# Configuration
# DO NOT hardcode your token here. Set it as an environment variable: export HF_TOKEN="your_token"
# HF_TOKEN="your_token_here" 
if [ -z "$HF_TOKEN" ]; then
    echo "❌ Error: HF_TOKEN environment variable is not set."
    echo "Run: export HF_TOKEN='your_huggingface_token'"
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
    --exclude .env

# 2. Enter deploy directory
cd "$DEPLOY_DIR" || exit

# 3. Commit and Push
echo "⬆️ Pushing to Hugging Face..."
git add .
git commit -m "Update: $(date +'%Y-%m-%d %H:%M:%S')"
git push --force "https://$HF_TOKEN@huggingface.co/spaces/ichigo253/AI_Interview_Backend" main-deploy:main

echo "✅ Push successful! Hugging Face is now rebuilding your Space."
echo "🔗 Check progress here: $HF_REPO?logs=build"
