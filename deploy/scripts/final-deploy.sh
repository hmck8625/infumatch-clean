#!/bin/bash

# =============================================================================
# 最終デプロイスクリプト（バックエンド＋フロントエンド）
# =============================================================================

set -e

PROJECT_ID="hackathon-462905"
REGION="asia-northeast1"
SERVICE_NAME="infumatch-backend"

echo "🚀 Final deployment for InfuMatch..."

# 1. バックエンドをCloud Runにデプロイ
echo "📱 Deploying backend to Cloud Run..."
cd backend
gcloud run deploy $SERVICE_NAME \
    --source=. \
    --platform=managed \
    --region=$REGION \
    --allow-unauthenticated \
    --port=8000 \
    --memory=1Gi \
    --cpu=1 \
    --timeout=300 \
    --min-instances=0 \
    --max-instances=3 \
    --execution-environment=gen2 \
    --set-env-vars="GOOGLE_CLOUD_PROJECT_ID=$PROJECT_ID,GOOGLE_CLOUD_REGION=$REGION" \
    --project=$PROJECT_ID

# サービスURLを取得
BACKEND_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format="value(status.url)")

echo "✅ Backend deployed at: $BACKEND_URL"

# 2. フロントエンドをVercelにデプロイ
echo "🌐 Deploying frontend to Vercel..."
cd ../frontend

# 環境変数を設定してからデプロイ
export NEXT_PUBLIC_API_URL=$BACKEND_URL

# Vercel CLIがない場合はインストール
if ! command -v vercel &> /dev/null; then
    echo "📦 Installing Vercel CLI..."
    npm install -g vercel
fi

# 依存関係をインストール
npm install

# Vercelにデプロイ
vercel --prod --confirm --env NEXT_PUBLIC_API_URL=$BACKEND_URL

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "🔗 Backend API: $BACKEND_URL"
echo "🌐 Frontend: Check Vercel dashboard for URL"
echo ""
echo "🧪 Test backend:"
echo "curl $BACKEND_URL/"
echo "curl $BACKEND_URL/api/v1/influencers"