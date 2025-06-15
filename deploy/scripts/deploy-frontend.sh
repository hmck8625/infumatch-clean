#!/bin/bash

# =============================================================================
# フロントエンド Vercel デプロイスクリプト
# =============================================================================

set -e

echo "🚀 Deploying frontend to Vercel..."

# Vercel CLIがインストールされているか確認
if ! command -v vercel &> /dev/null; then
    echo "📦 Installing Vercel CLI..."
    npm install -g vercel
fi

# プロジェクトディレクトリに移動
cd frontend

# 依存関係をインストール
echo "📦 Installing dependencies..."
npm install

# ビルドテスト
echo "🔨 Testing build..."
npm run build

# Vercelにデプロイ
echo "☁️ Deploying to Vercel..."
vercel --prod --confirm

echo "✅ Frontend deployment completed!"
echo ""
echo "🌐 Your application is now live on Vercel"
echo "🔗 Check your deployment at: https://vercel.com/dashboard"