#!/bin/bash

# =============================================================================
# Cloud Functions デプロイスクリプト
# =============================================================================
# Google Cloud Functions の一括デプロイ

set -e

# 設定
PROJECT_ID="hackathon-462905"
REGION="asia-northeast1"
MEMORY="512MB"
TIMEOUT="540s"
RUNTIME="python311"

echo "🚀 Starting Cloud Functions deployment..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

# 1. HTTP トリガー関数のデプロイ
echo "📡 Deploying HTTP trigger function..."
gcloud functions deploy http-trigger-main \
  --gen2 \
  --runtime=$RUNTIME \
  --region=$REGION \
  --source=. \
  --entry-point=http_trigger_main \
  --trigger-http \
  --allow-unauthenticated \
  --memory=$MEMORY \
  --timeout=$TIMEOUT \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_REGION=$REGION" \
  --project=$PROJECT_ID

# 2. YouTube データ収集関数のデプロイ
echo "📺 Deploying YouTube collection function..."
gcloud functions deploy scheduled-youtube-collection \
  --gen2 \
  --runtime=$RUNTIME \
  --region=$REGION \
  --source=. \
  --entry-point=scheduled_youtube_collection \
  --trigger-topic=youtube-collection-trigger \
  --memory=$MEMORY \
  --timeout=$TIMEOUT \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_REGION=$REGION" \
  --project=$PROJECT_ID

# 3. AI 分析関数のデプロイ
echo "🤖 Deploying AI analysis function..."
gcloud functions deploy scheduled-ai-analysis \
  --gen2 \
  --runtime=$RUNTIME \
  --region=$REGION \
  --source=. \
  --entry-point=scheduled_ai_analysis \
  --trigger-topic=ai-analysis-trigger \
  --memory="1GB" \
  --timeout="900s" \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_REGION=$REGION" \
  --project=$PROJECT_ID

# 4. データメンテナンス関数のデプロイ
echo "🧹 Deploying data maintenance function..."
gcloud functions deploy scheduled-data-maintenance \
  --gen2 \
  --runtime=$RUNTIME \
  --region=$REGION \
  --source=. \
  --entry-point=scheduled_data_maintenance \
  --trigger-topic=data-maintenance-trigger \
  --memory=$MEMORY \
  --timeout=$TIMEOUT \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_REGION=$REGION" \
  --project=$PROJECT_ID

# 5. Pub/Sub トピックの作成（存在しない場合）
echo "📮 Creating Pub/Sub topics if not exists..."
topics=("youtube-collection-trigger" "ai-analysis-trigger" "data-maintenance-trigger")

for topic in "${topics[@]}"; do
  if ! gcloud pubsub topics describe $topic --project=$PROJECT_ID > /dev/null 2>&1; then
    echo "Creating topic: $topic"
    gcloud pubsub topics create $topic --project=$PROJECT_ID
  else
    echo "Topic already exists: $topic"
  fi
done

# 6. Cloud Scheduler ジョブの作成
echo "⏰ Creating Cloud Scheduler jobs..."

# YouTube データ収集ジョブ
gcloud scheduler jobs create pubsub youtube-influencer-collection \
  --schedule="0 */6 * * *" \
  --topic=youtube-collection-trigger \
  --message-body='{"source":"cloud-scheduler","job":"youtube_collection"}' \
  --time-zone="Asia/Tokyo" \
  --description="YouTube インフルエンサーデータの定期収集" \
  --project=$PROJECT_ID \
  --location=$REGION \
  || echo "Job already exists: youtube-influencer-collection"

# AI 分析ジョブ
gcloud scheduler jobs create pubsub ai-influencer-analysis \
  --schedule="0 2 * * *" \
  --topic=ai-analysis-trigger \
  --message-body='{"source":"cloud-scheduler","job":"ai_analysis"}' \
  --time-zone="Asia/Tokyo" \
  --description="インフルエンサーのAI分析処理" \
  --project=$PROJECT_ID \
  --location=$REGION \
  || echo "Job already exists: ai-influencer-analysis"

# データメンテナンスジョブ
gcloud scheduler jobs create pubsub data-maintenance \
  --schedule="0 1 * * 0" \
  --topic=data-maintenance-trigger \
  --message-body='{"source":"cloud-scheduler","job":"data_maintenance"}' \
  --time-zone="Asia/Tokyo" \
  --description="データクリーンアップとレポート生成" \
  --project=$PROJECT_ID \
  --location=$REGION \
  || echo "Job already exists: data-maintenance"

# 7. IAM 権限の設定
echo "🔐 Setting up IAM permissions..."

# Cloud Functions サービスアカウントに必要な権限を付与
SERVICE_ACCOUNT="$PROJECT_ID@appspot.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/firestore.user" \
  || echo "IAM binding already exists or failed"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/aiplatform.user" \
  || echo "IAM binding already exists or failed"

# 8. デプロイ完了確認
echo "✅ Deployment completed successfully!"
echo ""
echo "🔗 Function URLs:"
echo "HTTP Trigger: https://$REGION-$PROJECT_ID.cloudfunctions.net/http-trigger-main"
echo ""
echo "📋 Scheduled Jobs:"
echo "- YouTube Collection: Every 6 hours"
echo "- AI Analysis: Daily at 2:00 AM JST"
echo "- Data Maintenance: Weekly on Sunday at 1:00 AM JST"
echo ""
echo "🎯 Next Steps:"
echo "1. Test the functions manually"
echo "2. Monitor logs in Cloud Console"
echo "3. Verify scheduler jobs are running"
echo "4. Check Firestore for collected data"