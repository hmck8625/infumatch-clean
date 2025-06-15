#!/bin/bash

# =============================================================================
# 日本のゲーム系YouTuber収集実行スクリプト
# =============================================================================

set -e

echo "🎮 日本のゲーム系YouTuber実データ収集開始"
echo "=============================================="

# プロジェクトディレクトリに移動
cd "$(dirname "$0")"

# backend ディレクトリに移動
cd backend

# 仮想環境の確認と有効化
if [ -d "venv" ]; then
    echo "✅ 仮想環境を有効化中..."
    source venv/bin/activate
else
    echo "❌ 仮想環境が見つかりません。セットアップを実行してください。"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# 環境変数の確認
if [ ! -f "../.env" ]; then
    if [ -f "../.env.local" ]; then
        echo "📝 .env.local を .env にコピーします..."
        cp ../.env.local ../.env
    else
        echo "❌ .env ファイルが見つかりません"
        exit 1
    fi
fi

# YouTube API キーの確認
YOUTUBE_API_KEY=$(grep YOUTUBE_API_KEY ../.env | cut -d '=' -f2 | tr -d '"' | tr -d ' ')
if [ -z "$YOUTUBE_API_KEY" ]; then
    echo "❌ YOUTUBE_API_KEY が設定されていません"
    exit 1
fi

echo "✅ YouTube API キーが設定されています"

# Google Cloud 認証の確認
echo "🔐 Google Cloud 認証を確認中..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "⚠️  Google Cloud にログインしてください"
    gcloud auth login
fi

# プロジェクトIDの確認と設定
PROJECT_ID=$(grep GOOGLE_CLOUD_PROJECT_ID ../.env | cut -d '=' -f2 | tr -d '"' | tr -d ' ')
if [ -n "$PROJECT_ID" ]; then
    echo "📊 プロジェクト: $PROJECT_ID"
    gcloud config set project $PROJECT_ID
fi

echo ""
echo "🚀 データ収集を開始します..."
echo "収集条件:"
echo "  - 対象: マイクロインフルエンサー（1万〜10万人）"
echo "  - ジャンル: ゲーム全般"
echo "  - 地域: 日本"
echo "  - 概要欄: 全内容取得"
echo ""

# データ収集スクリプト実行
python scripts/collect_real_gaming_youtubers.py

echo ""
echo "✅ データ収集完了！"
echo ""
echo "📊 結果確認方法:"
echo "  1. Firestore Console: https://console.firebase.google.com/project/$PROJECT_ID/firestore"
echo "  2. BigQuery Console: https://console.cloud.google.com/bigquery?project=$PROJECT_ID"
echo "  3. API経由: curl http://localhost:8000/api/v1/data/analytics/overview"
echo ""