#!/bin/bash

# =============================================================================
# 簡単なバックエンド デプロイスクリプト
# =============================================================================

set -e

PROJECT_ID="hackathon-462905"
REGION="asia-northeast1"
SERVICE_NAME="infumatch-backend"

echo "🚀 Quick backend deployment..."

# Cloud Runに直接デプロイ（ソースからビルド）
gcloud run deploy $SERVICE_NAME \
    --source=backend \
    --platform=managed \
    --region=$REGION \
    --allow-unauthenticated \
    --port=8000 \
    --memory=1Gi \
    --cpu=1 \
    --timeout=300 \
    --min-instances=0 \
    --max-instances=5 \
    --execution-environment=gen2 \
    --set-env-vars="GOOGLE_CLOUD_PROJECT_ID=$PROJECT_ID,GOOGLE_CLOUD_REGION=$REGION" \
    --project=$PROJECT_ID

echo "✅ Quick deployment completed!"

# サービスURLを取得
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format="value(status.url)")

echo "🔗 Service URL: $SERVICE_URL"
echo "🧪 Test: curl $SERVICE_URL/"