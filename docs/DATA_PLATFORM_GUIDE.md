# 🏗️ InfuMatch データプラットフォーム完全ガイド

## 📋 目次

1. [概要](#概要)
2. [アーキテクチャ](#アーキテクチャ)
3. [実装済み機能](#実装済み機能)
4. [セットアップ手順](#セットアップ手順)
5. [データ登録方法](#データ登録方法)
6. [データ同期方法](#データ同期方法)
7. [API エンドポイント](#api-エンドポイント)
8. [分析・レポート機能](#分析レポート機能)
9. [トラブルシューティング](#トラブルシューティング)
10. [保守・運用](#保守運用)

---

## 📊 概要

InfuMatch データプラットフォームは、YouTube インフルエンサーマッチングに特化したスケーラブルなデータ基盤です。Google Cloud の Firestore（リアルタイムデータ）と BigQuery（分析データ）を組み合わせた、高性能なハイブリッドアーキテクチャを採用しています。

### 🎯 主要特徴

- **リアルタイム性**: Firestore によるリアルタイムデータ更新
- **スケーラビリティ**: BigQuery による大規模データ分析
- **自動同期**: Firestore ↔ BigQuery 間の自動データ同期
- **AI 統合**: Gemini API との統合による高度な分析
- **RESTful API**: 標準的な API インターフェース

---

## 🏛️ アーキテクチャ

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │  Google Cloud   │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   Services      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │ Data Integration│    │   Firestore     │
                       │    Service      │◄──►│ (Real-time DB)  │
                       └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │    BigQuery     │    │  Analytics &    │
                       │ (Data Warehouse)│◄──►│   Reporting     │
                       └─────────────────┘    └─────────────────┘
```

### 🔧 技術スタック

| レイヤー | テクノロジー | 役割 |
|----------|-------------|------|
| **Frontend** | Next.js 14, TypeScript | ユーザーインターフェース |
| **Backend** | FastAPI, Python 3.11+ | API サーバー、ビジネスロジック |
| **Real-time DB** | Google Firestore | リアルタイムデータ、CRUD操作 |
| **Data Warehouse** | Google BigQuery | 大規模分析、レポート生成 |
| **Integration** | 自作 ETL Service | データ同期、変換処理 |
| **AI/ML** | Vertex AI, Gemini API | 自然言語処理、分析強化 |

---

## ⚡ 実装済み機能

### 1. 🔥 Firestore 機能 (`backend/core/database.py`)

#### **FirestoreClient クラス**
- シングルトンパターンによる効率的な接続管理
- 認証情報の自動読み込み
- エラーハンドリングとログ機能

#### **DatabaseHelper クラス**
```python
from core.database import DatabaseHelper, DatabaseCollections

# インスタンス作成
db_helper = DatabaseHelper()

# 基本的なCRUD操作
await db_helper.create_document(collection, doc_id, data)
await db_helper.get_document(collection, doc_id)
await db_helper.update_document(collection, doc_id, updates)
await db_helper.delete_document(collection, doc_id)

# 複合クエリ
conditions = [('status', '==', 'active'), ('category', '==', 'beauty')]
results = await db_helper.query_documents(collection, conditions)
```

#### **定義済みコレクション**
- `INFLUENCERS`: インフルエンサー情報
- `COMPANIES`: 企業情報
- `CAMPAIGNS`: キャンペーン情報  
- `NEGOTIATIONS`: 交渉履歴
- `MESSAGES`: メッセージ履歴
- `ANALYTICS`: 分析データ

### 2. 🏗️ BigQuery 機能 (`backend/core/bigquery_client.py`)

#### **BigQueryClient クラス**
```python
from core.bigquery_client import get_bigquery_client

# クライアント取得
bq_client = get_bigquery_client()

# データセット・テーブル作成
bq_client.setup_all_tables()

# データ挿入
rows = [{'influencer_id': 'test123', 'channel_title': 'Test Channel'}]
bq_client.insert_rows('influencers', rows)

# クエリ実行
sql = "SELECT COUNT(*) as total FROM `project.dataset.influencers`"
results = bq_client.query_to_dataframe(sql)
```

#### **定義済みテーブル**
- `influencers`: インフルエンサー基本情報
- `influencer_analytics`: 分析メトリクス
- `video_performance`: 動画パフォーマンス
- `campaigns`: キャンペーン情報
- `negotiations`: 交渉データ
- `daily_metrics`: 日次集計データ

### 3. 🔄 データ統合機能 (`backend/services/data_integration.py`)

#### **DataIntegrationService クラス**
```python
from services.data_integration import get_data_integration_service

# サービス取得
integration = get_data_integration_service()

# 完全同期
result = await integration.full_sync()

# 個別同期
await integration.sync_influencers_to_bigquery()
await integration.sync_campaigns_to_bigquery()

# 日次メトリクス生成
await integration.generate_daily_metrics()
```

---

## 🚀 セットアップ手順

### 1. 環境設定

#### **必要な環境変数** (`.env.local`)
```bash
# Google Cloud 設定
GOOGLE_CLOUD_PROJECT_ID=hackathon-462905
GOOGLE_APPLICATION_CREDENTIALS=./hackathon-462905-fd4f661125e5.json

# Firestore 設定  
FIRESTORE_DATABASE_ID=local

# BigQuery 設定
BIGQUERY_DATASET=infumatch_data

# API キー
YOUTUBE_API_KEY=your_youtube_api_key
GEMINI_API_KEY=your_gemini_api_key
```

#### **Google Cloud 認証**
```bash
# Google Cloud CLI にログイン
gcloud auth login

# プロジェクト設定
gcloud config set project hackathon-462905

# アプリケーションデフォルト認証
gcloud auth application-default login
```

### 2. データベース初期化

#### **自動セットアップ**
```bash
# バックエンドディレクトリに移動
cd backend

# セットアップテスト実行（推奨）
python scripts/test_bigquery_setup.py

# サーバー起動（初回起動時に自動初期化）
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### **手動セットアップ**
```python
# BigQuery テーブル作成
from core.bigquery_client import initialize_bigquery
await initialize_bigquery()

# Firestore 初期化
from core.database import get_firestore_client
firestore_client = get_firestore_client()
```

### 3. 接続確認

#### **ヘルスチェック API**
```bash
# データ基盤の状態確認
curl http://localhost:8000/api/v1/data/health

# レスポンス例
{
  "status": "healthy",
  "timestamp": "2024-06-14T10:30:00Z",
  "services": {
    "firestore": "connected",
    "bigquery": "connected"
  }
}
```

---

## 📝 データ登録方法

### 1. インフルエンサーデータ登録

#### **API 経由での登録**
```bash
curl -X POST "http://localhost:8000/api/v2/influencers" \
  -H "Content-Type: application/json" \
  -d '{
    "channel_id": "UC1234567890",
    "channel_title": "サンプルチャンネル",
    "description": "チャンネル説明",
    "subscriber_count": 50000,
    "view_count": 1000000,
    "video_count": 100,
    "category": "beauty",
    "country": "JP",
    "language": "ja",
    "contact_info": {
      "email": "contact@example.com"
    }
  }'
```

#### **プログラム経由での登録**
```python
from core.database import DatabaseHelper, DatabaseCollections
from datetime import datetime, timezone

# データヘルパー取得
db_helper = DatabaseHelper()

# インフルエンサーデータ準備
influencer_data = {
    'channel_id': 'UC1234567890',
    'channel_title': 'サンプルチャンネル',
    'description': 'チャンネル説明文',
    'subscriber_count': 50000,
    'view_count': 1000000,
    'video_count': 100,
    'category': 'beauty',
    'country': 'JP',
    'language': 'ja',
    'contact_info': {
        'email': 'contact@example.com',
        'social_links': {
            'twitter': '@example',
            'instagram': '@example'
        }
    },
    'ai_analysis': {
        'engagement_rate': 0.045,
        'content_quality_score': 0.8,
        'brand_safety_score': 0.9
    },
    'status': 'active',
    'created_at': datetime.now(timezone.utc).isoformat(),
    'updated_at': datetime.now(timezone.utc).isoformat()
}

# Firestore に保存
await db_helper.create_document(
    collection=DatabaseCollections.INFLUENCERS,
    document_id=influencer_data['channel_id'],
    data=influencer_data
)

print(f"✅ インフルエンサー {influencer_data['channel_title']} を登録しました")
```

### 2. キャンペーンデータ登録

#### **API 経由での登録**
```bash
curl -X POST "http://localhost:8000/api/v1/campaigns" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "夏のコスメキャンペーン",
    "description": "新作コスメの PR キャンペーン",
    "company_id": "company_123",
    "budget": 500000,
    "target_category": "beauty",
    "target_demographics": {
      "age_range": "20-35",
      "gender": "female",
      "interests": ["beauty", "fashion"]
    },
    "requirements": {
      "min_subscribers": 10000,
      "min_engagement_rate": 0.03,
      "content_type": "video_review"
    },
    "start_date": "2024-07-01",
    "end_date": "2024-08-31"
  }'
```

#### **プログラム経由での登録**
```python
import shortuuid
from datetime import datetime, timezone

# キャンペーンデータ準備
campaign_data = {
    'campaign_id': f"camp_{shortuuid.uuid()}",
    'title': '夏のコスメキャンペーン',
    'description': '新作コスメの PR キャンペーン',
    'company_id': 'company_123',
    'budget': 500000,
    'target_category': 'beauty',
    'target_demographics': {
        'age_range': '20-35',
        'gender': 'female',
        'interests': ['beauty', 'fashion']
    },
    'requirements': {
        'min_subscribers': 10000,
        'min_engagement_rate': 0.03,
        'content_type': 'video_review'
    },
    'status': 'active',
    'start_date': '2024-07-01',
    'end_date': '2024-08-31',
    'created_at': datetime.now(timezone.utc).isoformat(),
    'updated_at': datetime.now(timezone.utc).isoformat()
}

# Firestore に保存
await db_helper.create_document(
    collection=DatabaseCollections.CAMPAIGNS,
    document_id=campaign_data['campaign_id'],
    data=campaign_data
)

print(f"✅ キャンペーン {campaign_data['title']} を登録しました")
```

### 3. バッチでのデータ登録

#### **YouTube API 経由での一括登録**
```python
from services.batch_processor import YouTubeBatchProcessor

# バッチプロセッサー初期化
processor = YouTubeBatchProcessor()

# カテゴリベースでインフルエンサーを一括発見・登録
result = await processor.discover_influencers_batch(
    categories=['beauty', 'gaming', 'cooking', 'tech'],
    max_per_category=50  # カテゴリあたり最大50件
)

print(f"✅ {result['total_discovered']} 人のインフルエンサーを発見・登録しました")
```

#### **CSV ファイルからの一括登録**
```python
import pandas as pd

# CSV ファイル読み込み
df = pd.read_csv('influencers.csv')

# 各行をFirestoreに登録
for _, row in df.iterrows():
    influencer_data = {
        'channel_id': row['channel_id'],
        'channel_title': row['channel_title'],
        'subscriber_count': int(row['subscriber_count']),
        'category': row['category'],
        'status': 'active',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'updated_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db_helper.create_document(
        collection=DatabaseCollections.INFLUENCERS,
        document_id=row['channel_id'],
        data=influencer_data
    )

print(f"✅ {len(df)} 件のデータを一括登録しました")
```

---

## 🔄 データ同期方法

### 1. 自動同期（推奨）

#### **日次自動同期の設定**
```python
# Cloud Scheduler または Cron での実行
from services.data_integration import run_daily_sync

# 日次同期実行（バックグラウンド処理）
result = await run_daily_sync()

print(f"📊 同期完了:")
print(f"  - 同期レコード数: {result['discovery']['total_discovered']}")
print(f"  - 更新レコード数: {result['updates']['successfully_updated']}")
print(f"  - 処理時間: {result['duration_seconds']:.2f}秒")
```

#### **リアルタイム同期トリガー**
```python
# Firestore 更新時のトリガー設定
from google.cloud import firestore

def on_influencer_update(doc_snapshot, changes, read_time):
    """Firestore ドキュメント更新時の同期処理"""
    for change in changes:
        if change.type.name in ('ADDED', 'MODIFIED'):
            # BigQuery への同期をトリガー
            asyncio.create_task(sync_single_document(change.document))

# Firestore リスナー設定
firestore_client.collection('influencers').on_snapshot(on_influencer_update)
```

### 2. 手動同期

#### **API 経由での手動同期**
```bash
# 完全同期（全データ）
curl -X POST "http://localhost:8000/api/v1/data/sync/full"

# インフルエンサーデータのみ同期
curl -X POST "http://localhost:8000/api/v1/data/sync/influencers?batch_size=100"

# キャンペーンデータのみ同期
curl -X POST "http://localhost:8000/api/v1/data/sync/campaigns?batch_size=50"

# 日次メトリクス生成
curl -X POST "http://localhost:8000/api/v1/data/metrics/generate"
```

#### **プログラム経由での手動同期**
```python
from services.data_integration import get_data_integration_service

# データ統合サービス取得
integration = get_data_integration_service()

# インフルエンサーデータ同期
result = await integration.sync_influencers_to_bigquery(batch_size=100)
print(f"✅ {result['synced_count']} 件のインフルエンサーデータを同期")

# キャンペーンデータ同期
result = await integration.sync_campaigns_to_bigquery(batch_size=50)
print(f"✅ {result['synced_count']} 件のキャンペーンデータを同期")

# 日次メトリクス生成
from datetime import datetime
result = await integration.generate_daily_metrics(
    target_date=datetime.now()
)
print(f"✅ {result['metrics_generated']} 件のメトリクスを生成")
```

### 3. 差分同期

#### **最終更新日時による差分同期**
```python
from datetime import datetime, timedelta

# 過去24時間の更新データのみ同期
cutoff_time = datetime.now() - timedelta(hours=24)

# 更新されたインフルエンサーを取得
updated_influencers = await db_helper.query_documents(
    collection=DatabaseCollections.INFLUENCERS,
    conditions=[('updated_at', '>=', cutoff_time.isoformat())],
    limit=1000
)

print(f"📊 過去24時間で {len(updated_influencers)} 件の更新を検出")

# BigQuery に差分同期
if updated_influencers:
    # データ変換
    bigquery_rows = []
    for influencer in updated_influencers:
        row = integration._convert_influencer_to_bigquery_format(influencer)
        if row:
            bigquery_rows.append(row)
    
    # BigQuery に挿入（MERGE 文で重複処理）
    bq_client.insert_rows('influencers', bigquery_rows)
    print(f"✅ {len(bigquery_rows)} 件の差分データを BigQuery に同期")
```

### 4. バックアップ・復旧

#### **Firestore バックアップ**
```bash
# gcloud CLI でのバックアップ
gcloud firestore export gs://your-backup-bucket/firestore-backup \
  --project=hackathon-462905 \
  --database=local
```

#### **BigQuery バックアップ**
```python
# BigQuery テーブルのエクスポート
from google.cloud import bigquery

client = bigquery.Client()

# テーブルを Cloud Storage にエクスポート
extract_job = client.extract_table(
    'hackathon-462905.infumatch_data.influencers',
    'gs://your-backup-bucket/bigquery-backup/influencers.csv'
)
extract_job.result()  # 完了まで待機
```

---

## 🔌 API エンドポイント

### データ同期 API

| エンドポイント | メソッド | 説明 | パラメータ |
|---------------|---------|------|----------|
| `/api/v1/data/sync/full` | POST | 完全データ同期 | - |
| `/api/v1/data/sync/influencers` | POST | インフルエンサー同期 | `batch_size` |
| `/api/v1/data/sync/campaigns` | POST | キャンペーン同期 | `batch_size` |
| `/api/v1/data/metrics/generate` | POST | 日次メトリクス生成 | `target_date` |
| `/api/v1/data/sync/status` | GET | 同期状況確認 | - |
| `/api/v1/data/health` | GET | ヘルスチェック | - |

### 分析 API

| エンドポイント | メソッド | 説明 | パラメータ |
|---------------|---------|------|----------|
| `/api/v1/data/analytics/overview` | GET | 分析概要取得 | `days` |
| `/api/v1/data/analytics/categories` | GET | カテゴリ別分析 | - |
| `/api/v1/data/analytics/growth-trends` | GET | 成長トレンド分析 | `days` |

### インフルエンサー API (v2)

| エンドポイント | メソッド | 説明 | パラメータ |
|---------------|---------|------|----------|
| `/api/v2/influencers/search` | GET | 高度な検索 | 各種フィルター |
| `/api/v2/influencers/discover` | POST | 新規発見 | `query`, `category` |
| `/api/v2/influencers/batch-discovery` | POST | 一括発見 | `categories`, `max_results` |
| `/api/v2/influencers/{id}/analyze` | POST | AI分析実行 | - |

### 使用例

#### **完全同期の実行**
```bash
curl -X POST "http://localhost:8000/api/v1/data/sync/full" \
  -H "Content-Type: application/json"

# レスポンス
{
  "success": true,
  "synced_count": 1250,
  "failed_count": 0,
  "duration_seconds": 45.3,
  "errors": [],
  "completed_at": "2024-06-14T10:30:00Z"
}
```

#### **分析データの取得**
```bash
curl "http://localhost:8000/api/v1/data/analytics/overview?days=30"

# レスポンス
[
  {
    "date": "2024-06-14",
    "total_influencers": 1250,
    "active_campaigns": 15,
    "completed_negotiations": 8,
    "total_revenue": 2500000.0,
    "avg_engagement_rate": 0.045
  }
]
```

---

## 📊 分析・レポート機能

### 1. BigQuery Analytics クラス

#### **成長トレンド分析**
```python
from core.bigquery_client import get_bigquery_analytics

analytics = get_bigquery_analytics()

# インフルエンサーの成長トレンド（過去30日）
df = analytics.get_influencer_growth_trends(days=30)

# 結果の可視化
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 6))
plt.plot(df['date'], df['subscriber_growth'])
plt.title('登録者数成長トレンド')
plt.xlabel('日付')
plt.ylabel('成長数')
plt.show()
```

#### **カテゴリ別パフォーマンス**
```python
# カテゴリ別の統計データ
df = analytics.get_category_performance()

print("カテゴリ別パフォーマンス:")
for _, row in df.iterrows():
    print(f"  {row['category']}: {row['influencer_count']}人, "
          f"平均エンゲージメント: {row['avg_engagement']:.3f}")
```

#### **キャンペーン ROI 分析**
```python
# ROI分析データ
df = analytics.get_campaign_roi_analysis()

# ROI上位キャンペーンの表示
top_campaigns = df.head(10)
print("ROI上位キャンペーン:")
for _, row in top_campaigns.iterrows():
    roi = (row['total_spent'] / row['budget']) * 100 if row['budget'] > 0 else 0
    print(f"  {row['title']}: ROI {roi:.1f}%")
```

### 2. カスタム分析クエリ

#### **月次成長率の計算**
```sql
WITH monthly_growth AS (
  SELECT 
    DATE_TRUNC(created_at, MONTH) as month,
    COUNT(*) as new_influencers,
    AVG(subscriber_count) as avg_subscribers
  FROM `hackathon-462905.infumatch_data.influencers`
  WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 12 MONTH)
  GROUP BY month
  ORDER BY month
)
SELECT 
  month,
  new_influencers,
  avg_subscribers,
  LAG(new_influencers) OVER (ORDER BY month) as prev_month_count,
  SAFE_DIVIDE(
    new_influencers - LAG(new_influencers) OVER (ORDER BY month),
    LAG(new_influencers) OVER (ORDER BY month)
  ) * 100 as growth_rate_percent
FROM monthly_growth
```

#### **エンゲージメント率分布の分析**
```sql
SELECT 
  CASE 
    WHEN JSON_EXTRACT_SCALAR(ai_analysis, '$.engagement_rate') < 0.01 THEN 'Low (< 1%)'
    WHEN JSON_EXTRACT_SCALAR(ai_analysis, '$.engagement_rate') < 0.03 THEN 'Medium (1-3%)'
    WHEN JSON_EXTRACT_SCALAR(ai_analysis, '$.engagement_rate') < 0.05 THEN 'High (3-5%)'
    ELSE 'Very High (> 5%)'
  END as engagement_tier,
  COUNT(*) as influencer_count,
  AVG(subscriber_count) as avg_subscribers
FROM `hackathon-462905.infumatch_data.influencers`
WHERE is_active = true
  AND JSON_EXTRACT_SCALAR(ai_analysis, '$.engagement_rate') IS NOT NULL
GROUP BY engagement_tier
ORDER BY 
  CASE engagement_tier
    WHEN 'Low (< 1%)' THEN 1
    WHEN 'Medium (1-3%)' THEN 2
    WHEN 'High (3-5%)' THEN 3
    WHEN 'Very High (> 5%)' THEN 4
  END
```

### 3. ダッシュボード連携

#### **Looker Studio（旧 Google Data Studio）連携**
```python
# BigQuery ビューの作成（Looker Studio 用）
create_view_sql = """
CREATE OR REPLACE VIEW `hackathon-462905.infumatch_data.influencer_dashboard` AS
SELECT 
  influencer_id,
  channel_title,
  category,
  subscriber_count,
  CAST(JSON_EXTRACT_SCALAR(ai_analysis, '$.engagement_rate') AS FLOAT64) as engagement_rate,
  CAST(JSON_EXTRACT_SCALAR(ai_analysis, '$.content_quality_score') AS FLOAT64) as quality_score,
  created_at,
  updated_at
FROM `hackathon-462905.infumatch_data.influencers`
WHERE is_active = true
"""

bq_client.query(create_view_sql).result()
```

#### **レポート自動生成**
```python
from datetime import datetime, timedelta
import pandas as pd

async def generate_weekly_report():
    """週次レポートの自動生成"""
    
    # 過去1週間のデータを取得
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    analytics = get_bigquery_analytics()
    
    # 各種メトリクスを取得
    daily_metrics = analytics.get_daily_metrics_summary(days=7)
    growth_trends = analytics.get_influencer_growth_trends(days=7)
    category_performance = analytics.get_category_performance()
    
    # レポート作成
    report = {
        'period': f"{start_date.strftime('%Y-%m-%d')} ～ {end_date.strftime('%Y-%m-%d')}",
        'summary': {
            'total_influencers': daily_metrics['total_influencers'].sum(),
            'new_registrations': len(growth_trends[growth_trends['date'] >= start_date.date()]),
            'avg_engagement': daily_metrics['platform_engagement_rate'].mean(),
            'total_revenue': daily_metrics['daily_revenue'].sum()
        },
        'top_categories': category_performance.head(5).to_dict('records')
    }
    
    return report

# 週次レポート生成実行
report = await generate_weekly_report()
print("📊 週次レポート生成完了")
```

---

## 🚨 トラブルシューティング

### よくある問題と解決方法

#### **1. 認証エラー**
```
Error: google.auth.exceptions.DefaultCredentialsError
```

**解決方法:**
```bash
# 認証情報の再設定
gcloud auth application-default login

# 環境変数の確認
echo $GOOGLE_APPLICATION_CREDENTIALS

# サービスアカウントキーの権限確認
gcloud iam service-accounts describe admin-654@hackathon-462905.iam.gserviceaccount.com
```

#### **2. BigQuery 接続エラー**
```
Error: 403 Access Denied: BigQuery BigQuery: Permission denied
```

**解決方法:**
```bash
# BigQuery API の有効化
gcloud services enable bigquery.googleapis.com

# IAM 権限の確認・追加
gcloud projects add-iam-policy-binding hackathon-462905 \
  --member="serviceAccount:admin-654@hackathon-462905.iam.gserviceaccount.com" \
  --role="roles/bigquery.admin"
```

#### **3. Firestore 接続エラー**
```
Error: google.cloud.exceptions.NotFound: 404 Database not found
```

**解決方法:**
```bash
# Firestore データベースの作成
gcloud firestore databases create --database=local --location=us-central1

# Firestore API の有効化
gcloud services enable firestore.googleapis.com
```

#### **4. 同期処理が遅い**

**原因と対策:**
- **バッチサイズを調整**: `batch_size=50` など小さい値に設定
- **並行処理数を制限**: `max_workers=5` で同時実行数を制限
- **インデックスの追加**: Firestore にクエリ用インデックスを追加

```python
# バッチサイズの最適化
result = await integration.sync_influencers_to_bigquery(batch_size=50)

# 並行処理数の制限
import asyncio
semaphore = asyncio.Semaphore(5)  # 最大5並行

async def limited_sync():
    async with semaphore:
        return await integration.sync_influencers_to_bigquery()
```

#### **5. メモリ不足エラー**

**解決方法:**
```python
# 大量データの分割処理
async def chunked_sync(total_records, chunk_size=1000):
    """チャンク単位での分割同期"""
    for offset in range(0, total_records, chunk_size):
        # チャンクごとにデータを取得・同期
        chunk_data = await get_chunk_data(offset, chunk_size)
        await sync_chunk_to_bigquery(chunk_data)
        
        # メモリ解放のため少し待機
        await asyncio.sleep(1)
        
        print(f"✅ {offset + len(chunk_data)}/{total_records} 件処理完了")
```

### パフォーマンス監視

#### **同期処理の監視**
```python
import time
from datetime import datetime

class SyncMonitor:
    """同期処理の監視クラス"""
    
    def __init__(self):
        self.metrics = {
            'start_time': None,
            'records_processed': 0,
            'errors': [],
            'performance': []
        }
    
    def start_monitoring(self):
        self.metrics['start_time'] = time.time()
    
    def record_batch(self, batch_size, duration):
        self.metrics['records_processed'] += batch_size
        self.metrics['performance'].append({
            'batch_size': batch_size,
            'duration': duration,
            'rate': batch_size / duration if duration > 0 else 0
        })
    
    def get_summary(self):
        total_time = time.time() - self.metrics['start_time']
        avg_rate = self.metrics['records_processed'] / total_time
        
        return {
            'total_records': self.metrics['records_processed'],
            'total_time': total_time,
            'average_rate': avg_rate,
            'errors': len(self.metrics['errors'])
        }

# 使用例
monitor = SyncMonitor()
monitor.start_monitoring()

# 同期処理中に記録
monitor.record_batch(100, 5.2)

# 結果表示
summary = monitor.get_summary()
print(f"📊 同期完了: {summary['total_records']}件, {summary['average_rate']:.1f}件/秒")
```

---

## 🔧 保守・運用

### 定期メンテナンス

#### **1. データクリーンアップ**
```python
# 古いデータの自動削除（90日以上前）
from services.batch_processor import YouTubeBatchProcessor

processor = YouTubeBatchProcessor()
cleanup_result = await processor.cleanup_old_data(days_to_keep=90)

print(f"🧹 クリーンアップ完了: {cleanup_result['deleted_count']}件削除")
```

#### **2. インデックス最適化**
```bash
# Firestore 複合インデックスの作成
gcloud firestore indexes composite create \
  --collection-group=influencers \
  --field-config field-path=category,order=ascending \
  --field-config field-path=subscriber_count,order=descending
```

#### **3. BigQuery パーティション管理**
```sql
-- 古いパーティションの削除（過去1年のデータのみ保持）
DELETE FROM `hackathon-462905.infumatch_data.daily_metrics`
WHERE date < DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
```

### 監視・アラート設定

#### **Cloud Monitoring ダッシュボード**
```python
# カスタムメトリクスの送信
from google.cloud import monitoring_v3

def send_sync_metrics(records_synced, duration):
    """同期メトリクスを Cloud Monitoring に送信"""
    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{settings.GOOGLE_CLOUD_PROJECT_ID}"
    
    # メトリクス定義
    series = monitoring_v3.TimeSeries()
    series.metric.type = "custom.googleapis.com/infumatch/sync_rate"
    series.resource.type = "global"
    
    # データポイント
    point = series.points.add()
    point.value.double_value = records_synced / duration
    point.interval.end_time.seconds = int(time.time())
    
    # 送信
    client.create_time_series(name=project_name, time_series=[series])
```

#### **エラー通知設定**
```python
import logging
from google.cloud import error_reporting

# エラーレポーティングクライアント
error_client = error_reporting.Client()

def report_sync_error(error_message, context=None):
    """同期エラーを Cloud Error Reporting に送信"""
    try:
        error_client.report_exception(
            message=error_message,
            context=context or {}
        )
    except Exception as e:
        logging.error(f"Failed to report error: {e}")

# 使用例
try:
    await integration.sync_influencers_to_bigquery()
except Exception as e:
    report_sync_error(
        f"Influencer sync failed: {str(e)}",
        context={"batch_size": 100, "timestamp": datetime.now().isoformat()}
    )
```

### バックアップ戦略

#### **自動バックアップスクリプト**
```python
async def automated_backup():
    """自動バックアップの実行"""
    from google.cloud import storage
    import json
    
    # Firestore データのエクスポート
    firestore_client = get_firestore_client()
    collections = ['influencers', 'campaigns', 'negotiations']
    
    backup_data = {}
    for collection in collections:
        docs = await db_helper.get_all_documents(collection, limit=10000)
        backup_data[collection] = docs
    
    # Cloud Storage に保存
    storage_client = storage.Client()
    bucket = storage_client.bucket('infumatch-backups')
    
    backup_filename = f"firestore_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    blob = bucket.blob(backup_filename)
    blob.upload_from_string(json.dumps(backup_data, ensure_ascii=False, indent=2))
    
    print(f"✅ バックアップ完了: {backup_filename}")

# 日次バックアップの実行
await automated_backup()
```

#### **災害復旧計画**
```python
async def disaster_recovery(backup_file):
    """災害復旧の実行"""
    import json
    from google.cloud import storage
    
    # バックアップファイルの読み込み
    storage_client = storage.Client()
    bucket = storage_client.bucket('infumatch-backups')
    blob = bucket.blob(backup_file)
    backup_data = json.loads(blob.download_as_text())
    
    # データの復元
    db_helper = DatabaseHelper()
    
    for collection, documents in backup_data.items():
        print(f"📥 {collection} コレクションを復元中...")
        
        for doc in documents:
            doc_id = doc.get('channel_id') or doc.get('campaign_id') or doc.get('id')
            if doc_id:
                await db_helper.create_document(collection, doc_id, doc)
        
        print(f"✅ {collection}: {len(documents)}件復元完了")
    
    print("🎉 災害復旧完了")

# 復旧実行例
# await disaster_recovery('firestore_backup_20240614_103000.json')
```

---

## 📚 参考資料

### 公式ドキュメント
- [Google Cloud Firestore](https://cloud.google.com/firestore/docs)
- [Google Cloud BigQuery](https://cloud.google.com/bigquery/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [YouTube Data API v3](https://developers.google.com/youtube/v3)

### サンプルコード
- [BigQuery Python Client](https://github.com/googleapis/python-bigquery)
- [Firestore Python Client](https://github.com/googleapis/python-firestore)

### 関連プロジェクトファイル
- `backend/core/database.py` - Firestore 操作
- `backend/core/bigquery_client.py` - BigQuery 操作
- `backend/services/data_integration.py` - データ統合
- `backend/api/v1/data_sync.py` - 同期 API
- `backend/scripts/test_bigquery_setup.py` - セットアップテスト

---

**📅 最終更新**: 2024年6月14日  
**📝 作成者**: InfuMatch Development Team  
**📧 サポート**: dev@infumatch.com