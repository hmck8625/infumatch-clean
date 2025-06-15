#!/bin/bash

# =============================================================================
# BigQuery データ登録スクリプト
# =============================================================================

set -e

echo "🚀 BigQuery データ登録ツール"
echo "=================================="

# 現在のディレクトリを保存
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

# Backendディレクトリに移動
cd "$BACKEND_DIR"

# Python仮想環境の確認と有効化
if [ -d "venv" ]; then
    echo "✅ 仮想環境を有効化します..."
    source venv/bin/activate
else
    echo "⚠️  仮想環境が見つかりません。作成しますか？ (y/n)"
    read -r response
    if [[ "$response" == "y" ]]; then
        python3 -m venv venv
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
    else
        echo "❌ 仮想環境なしで続行します"
    fi
fi

# 環境変数の確認
if [ ! -f "../.env" ]; then
    if [ -f "../.env.local" ]; then
        echo "📝 .env.local を .env にコピーします..."
        cp ../.env.local ../.env
    else
        echo "❌ .env ファイルが見つかりません。セットアップを実行してください。"
        exit 1
    fi
fi

# Google Cloud 認証の確認
echo "🔐 Google Cloud 認証を確認中..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "⚠️  Google Cloud にログインしてください"
    gcloud auth login
fi

# プロジェクトIDの確認
PROJECT_ID=$(grep GOOGLE_CLOUD_PROJECT_ID ../.env | cut -d '=' -f2 | tr -d '"' | tr -d ' ')
if [ -z "$PROJECT_ID" ]; then
    echo "❌ GOOGLE_CLOUD_PROJECT_ID が設定されていません"
    exit 1
fi

echo "📊 プロジェクト: $PROJECT_ID"

# BigQuery データセットの確認
DATASET=$(grep BIGQUERY_DATASET ../.env | cut -d '=' -f2 | tr -d '"' | tr -d ' ')
if [ -z "$DATASET" ]; then
    DATASET="infumatch_data"
fi

echo "📊 データセット: $DATASET"

# データ登録スクリプトの実行
echo ""
echo "🔄 データ登録を開始します..."
echo ""

python scripts/bigquery_data_loader.py

echo ""
echo "✅ 完了しました！"