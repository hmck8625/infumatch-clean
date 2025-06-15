#!/bin/bash

# =============================================================================
# バックエンド デプロイスクリプト
# =============================================================================
# FastAPI アプリケーションを Cloud Run にデプロイ

set -e

# 設定
PROJECT_ID="hackathon-462905"
REGION="asia-northeast1"
SERVICE_NAME="infumatch-backend"
IMAGE_NAME="asia-northeast1-docker.pkg.dev/$PROJECT_ID/infumatch/backend"
DOCKERFILE_PATH="deploy/docker/backend.Dockerfile"

echo "🚀 Starting backend deployment..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"

# 1. Google Cloud の認証確認
echo "🔐 Checking authentication..."
gcloud auth list --filter=status:ACTIVE --format="value(account)"

# 2. Docker リポジトリの作成（存在しない場合）
echo "📦 Creating Artifact Registry repository if not exists..."
gcloud artifacts repositories create infumatch \
    --repository-format=docker \
    --location=$REGION \
    --description="InfuMatch application images" \
    --project=$PROJECT_ID \
    || echo "Repository already exists"

# 3. Docker の認証設定
echo "🐳 Configuring Docker authentication..."
gcloud auth configure-docker asia-northeast1-docker.pkg.dev

# 4. Docker イメージのビルド
echo "🔨 Building Docker image..."
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
IMAGE_TAG="$IMAGE_NAME:$TIMESTAMP"
IMAGE_LATEST="$IMAGE_NAME:latest"

docker build \
    -f $DOCKERFILE_PATH \
    -t $IMAGE_TAG \
    -t $IMAGE_LATEST \
    .

# 5. Docker イメージのプッシュ
echo "📤 Pushing Docker image..."
docker push $IMAGE_TAG
docker push $IMAGE_LATEST

# 6. シークレットの作成（存在しない場合）
echo "🔒 Creating secrets if not exists..."

# YouTube API Key
if ! gcloud secrets describe youtube-api-key --project=$PROJECT_ID > /dev/null 2>&1; then
    echo "Creating YouTube API Key secret..."
    echo -n "AIzaSyDtPl5WSRdxk744ha5Tlwno4iTBZVO96r4" | \
        gcloud secrets create youtube-api-key \
        --data-file=- \
        --project=$PROJECT_ID
else
    echo "YouTube API Key secret already exists"
fi

# Gemini API Key (新しいキーが必要)
if ! gcloud secrets describe gemini-api-key --project=$PROJECT_ID > /dev/null 2>&1; then
    echo "Creating Gemini API Key secret..."
    echo -n "YOUR_NEW_GEMINI_API_KEY" | \
        gcloud secrets create gemini-api-key \
        --data-file=- \
        --project=$PROJECT_ID
else
    echo "Gemini API Key secret already exists"
fi

# 7. サービスアカウントの権限設定
echo "🔐 Setting up service account permissions..."
SERVICE_ACCOUNT="$PROJECT_ID@appspot.gserviceaccount.com"

# 必要な権限を付与
ROLES=(
    "roles/firestore.user"
    "roles/aiplatform.user"
    "roles/secretmanager.secretAccessor"
    "roles/storage.objectViewer"
    "roles/monitoring.writer"
    "roles/logging.logWriter"
)

for role in "${ROLES[@]}"; do
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="$role" \
        || echo "IAM binding already exists: $role"
done

# 8. Cloud Run サービスのデプロイ
echo "☁️ Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image=$IMAGE_LATEST \
    --platform=managed \
    --region=$REGION \
    --allow-unauthenticated \
    --port=8000 \
    --memory=2Gi \
    --cpu=2 \
    --timeout=300 \
    --concurrency=80 \
    --min-instances=0 \
    --max-instances=10 \
    --execution-environment=gen2 \
    --service-account=$SERVICE_ACCOUNT \
    --set-env-vars="GOOGLE_CLOUD_PROJECT_ID=$PROJECT_ID,GOOGLE_CLOUD_REGION=$REGION,LOG_LEVEL=INFO" \
    --set-secrets="YOUTUBE_API_KEY=youtube-api-key:latest,GEMINI_API_KEY=gemini-api-key:latest" \
    --project=$PROJECT_ID

# 9. カスタムドメインの設定（オプション）
# echo "🌐 Setting up custom domain..."
# gcloud run domain-mappings create \
#     --service=$SERVICE_NAME \
#     --domain=api.infumatch.com \
#     --region=$REGION \
#     --project=$PROJECT_ID \
#     || echo "Domain mapping already exists or skipped"

# 10. デプロイ結果の取得
echo "📋 Getting deployment information..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format="value(status.url)")

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "🔗 Service Information:"
echo "URL: $SERVICE_URL"
echo "Image: $IMAGE_LATEST"
echo "Region: $REGION"
echo ""
echo "🧪 Testing the deployment:"
echo "curl $SERVICE_URL/health"
echo ""
echo "📊 Monitoring:"
echo "Logs: https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME/logs?project=$PROJECT_ID"
echo "Metrics: https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME/metrics?project=$PROJECT_ID"
echo ""
echo "🎯 Next Steps:"
echo "1. Test the API endpoints"
echo "2. Update frontend NEXT_PUBLIC_API_URL"
echo "3. Run integration tests"
echo "4. Monitor performance and logs"

# 11. ヘルスチェックの実行
echo "🏥 Running health check..."
sleep 10
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL/")

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed (HTTP $HTTP_STATUS)"
    echo "Testing API endpoint..."
    curl -i "$SERVICE_URL/api/v1/influencers" | head -10
fi