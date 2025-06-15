#!/bin/bash

# =============================================================================
# インフラストラクチャ セットアップスクリプト
# =============================================================================
# Terraform を使用してGoogle Cloud インフラストラクチャを構築

set -e

# 設定
PROJECT_ID="hackathon-462905"
REGION="asia-northeast1"
TERRAFORM_STATE_BUCKET="$PROJECT_ID-terraform-state"

echo "🏗️ Setting up InfuMatch infrastructure..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

# 1. Google Cloud CLI の認証確認
echo "🔐 Checking authentication..."
gcloud auth list --filter=status:ACTIVE --format="value(account)"

# 2. プロジェクトの設定
echo "📋 Setting up project configuration..."
gcloud config set project $PROJECT_ID

# 3. 必要な API の有効化
echo "🔌 Enabling required APIs..."
APIS=(
    "cloudbuild.googleapis.com"
    "run.googleapis.com"
    "cloudfunctions.googleapis.com"
    "scheduler.googleapis.com"
    "firestore.googleapis.com"
    "aiplatform.googleapis.com"
    "secretmanager.googleapis.com"
    "artifactregistry.googleapis.com"
    "pubsub.googleapis.com"
    "storage.googleapis.com"
    "monitoring.googleapis.com"
    "logging.googleapis.com"
    "cloudresourcemanager.googleapis.com"
)

for api in "${APIS[@]}"; do
    echo "Enabling $api..."
    gcloud services enable $api --project=$PROJECT_ID
done

# 4. Terraform State 用バケットの作成
echo "🪣 Creating Terraform state bucket..."
if ! gsutil ls -b gs://$TERRAFORM_STATE_BUCKET > /dev/null 2>&1; then
    gsutil mb -p $PROJECT_ID -l $REGION gs://$TERRAFORM_STATE_BUCKET
    gsutil versioning set on gs://$TERRAFORM_STATE_BUCKET
    echo "Created bucket: gs://$TERRAFORM_STATE_BUCKET"
else
    echo "Bucket already exists: gs://$TERRAFORM_STATE_BUCKET"
fi

# 5. Terraform のインストール確認
echo "🔧 Checking Terraform installation..."
if ! command -v terraform &> /dev/null; then
    echo "Installing Terraform..."
    # macOS の場合
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install terraform
    # Linux の場合
    else
        wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
        echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
        sudo apt update && sudo apt install terraform
    fi
else
    echo "Terraform is already installed: $(terraform version)"
fi

# 6. Terraform ディレクトリへ移動
cd deploy/terraform

# 7. Terraform 初期化
echo "🚀 Initializing Terraform..."
terraform init

# 8. Terraform プランの確認
echo "📋 Creating Terraform plan..."
terraform plan -out=tfplan

# 9. ユーザー確認
echo ""
echo "🤔 Do you want to apply this Terraform plan? (y/N)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    # 10. Terraform 適用
    echo "🔄 Applying Terraform configuration..."
    terraform apply tfplan
    
    # 11. 出力値の表示
    echo ""
    echo "✅ Infrastructure setup completed!"
    echo ""
    echo "📊 Infrastructure Summary:"
    terraform output
    
    # 12. 手動で実行が必要な作業の案内
    echo ""
    echo "🎯 Next Steps:"
    echo "1. Update .env files with the actual values"
    echo "2. Deploy the backend application:"
    echo "   cd ../../"
    echo "   ./deploy/scripts/deploy-backend.sh"
    echo "3. Deploy Cloud Functions:"
    echo "   cd cloud_functions"
    echo "   ./deploy.sh"
    echo "4. Set up GitHub Actions secrets:"
    echo "   - WIF_PROVIDER"
    echo "   - WIF_SERVICE_ACCOUNT"
    echo "   - VERCEL_TOKEN"
    echo "   - VERCEL_ORG_ID"
    echo "   - VERCEL_PROJECT_ID"
    echo "5. Deploy frontend to Vercel"
    echo ""
    echo "🔗 Useful Links:"
    echo "Cloud Console: https://console.cloud.google.com/home/dashboard?project=$PROJECT_ID"
    echo "Firestore: https://console.cloud.google.com/firestore/data?project=$PROJECT_ID"
    echo "Cloud Run: https://console.cloud.google.com/run?project=$PROJECT_ID"
    echo "Cloud Functions: https://console.cloud.google.com/functions/list?project=$PROJECT_ID"
    echo "Cloud Scheduler: https://console.cloud.google.com/cloudscheduler?project=$PROJECT_ID"
    
else
    echo "❌ Terraform apply cancelled."
    echo "You can run 'terraform apply tfplan' later to apply the changes."
fi

# 13. クリーンアップ
rm -f tfplan

echo ""
echo "🎉 Infrastructure setup script completed!"