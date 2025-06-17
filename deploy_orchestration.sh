#!/bin/bash

# マルチエージェントオーケストレーションシステムのデプロイスクリプト
echo "🚀 Deploying Multi-Agent Orchestration System..."

cd backend

gcloud run deploy infumatch-orchestration \
  --source . \
  --platform managed \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 900 \
  --concurrency 40 \
  --max-instances 5 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT_ID=hackathon-462905,GEMINI_API_KEY=AIzaSyBY1nBdkB6zMCDzD3N_qEP8LO72OQHFZD8"

echo "✅ Deployment completed!"