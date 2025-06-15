# YouTube API統合機能 - 完全ドキュメント

## 📋 目次

1. [概要](#概要)
2. [アーキテクチャ](#アーキテクチャ)
3. [実装済み機能](#実装済み機能)
4. [セットアップ方法](#セットアップ方法)
5. [API仕様](#api仕様)
6. [使用方法](#使用方法)
7. [テスト方法](#テスト方法)
8. [トラブルシューティング](#トラブルシューティング)

## 🎯 概要

InfuMatchのYouTube API統合機能は、YouTubeインフルエンサーの発見、分析、管理を自動化するための包括的なシステムです。

### 主な特徴
- **大規模バッチ処理**: 数千のチャンネルを効率的に処理
- **AI強化分析**: Gemini APIによる高精度な分析
- **リアルタイム検索**: 動的なインフルエンサー発見
- **自動データ更新**: 定期的なメトリクス更新
- **高度なフィルタリング**: 多次元検索とソート

---

## 🏗️ アーキテクチャ

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API    │    │  External APIs  │
│                 │    │                  │    │                 │
│ • Search UI     │◄──►│ • influencers.py │◄──►│ • YouTube API   │
│ • Analytics     │    │ • batch_proc.py  │    │ • Gemini API    │
│ • Filters       │    │ • ai_analyzers   │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                               ▲
                               │
                       ┌───────▼────────┐
                       │   Database     │
                       │                │
                       │ • Firestore    │
                       │ • BigQuery     │
                       │ • Cache        │
                       └────────────────┘
```

---

## ⚙️ 実装済み機能

### 1. **batch_processor.py** - 大規模バッチ処理エンジン

#### 🔧 主要クラス: `YouTubeBatchProcessor`

**機能概要:**
- カテゴリベースの大量インフルエンサー発見
- 既存データの定期更新
- トレンド分析
- データクリーンアップ

**主要メソッド:**

```python
# 大規模インフルエンサー発見
async def discover_influencers_batch(
    categories: List[str],
    subscriber_ranges: List[tuple] = None,
    max_per_category: int = 50
) -> Dict[str, Any]

# 既存データ更新
async def update_existing_influencers(
    batch_size: int = 50,
    days_since_last_update: int = 7
) -> Dict[str, Any]

# トレンド分析
async def analyze_trending_channels(
    region: str = 'JP',
    max_results: int = 100
) -> Dict[str, Any]
```

**サポートされるカテゴリ:**
- `beauty` - ビューティー・コスメ
- `gaming` - ゲーム
- `cooking` - 料理・グルメ
- `tech` - テクノロジー
- `fitness` - フィットネス・健康
- `fashion` - ファッション
- `travel` - 旅行
- `education` - 教育・学習

---

### 2. **ai_analyzers.py** - AI分析エージェント

#### 🤖 主要クラス: `IntegratedAIAnalyzer`

**機能概要:**
- Gemini APIを活用した高精度分析
- カテゴリ自動判定
- ビジネスメール抽出
- 成長トレンド予測
- 総合評価スコア算出

#### サブコンポーネント:

##### **CategoryAnalyzer**
```python
async def analyze_channel_category(
    channel_data: Dict[str, Any]
) -> Dict[str, Any]
```
**出力例:**
```json
{
  "main_category": "beauty",
  "main_category_name": "ビューティー・コスメ",
  "sub_categories": ["メイク", "スキンケア"],
  "reasoning": "メイクアップチュートリアルが主要コンテンツ",
  "collaboration_score": 8,
  "target_audience": "20-30代女性",
  "confidence": 0.85
}
```

##### **AdvancedEmailExtractor**
```python
async def extract_business_emails(
    channel_data: Dict[str, Any]
) -> List[Dict[str, Any]]
```
**出力例:**
```json
[
  {
    "email": "business@beautychannel.com",
    "confidence": 9,
    "purpose": "お仕事依頼",
    "context": "ビジネスのお問い合わせは",
    "is_primary": true
  }
]
```

##### **TrendAnalyzer**
```python
async def analyze_growth_trend(
    channel_data: Dict[str, Any],
    historical_data: List[Dict[str, Any]] = None
) -> Dict[str, Any]
```
**出力例:**
```json
{
  "growth_stage": "成長期",
  "growth_rate": "高成長",
  "trend_adaptation": 8,
  "collaboration_timing": "最適",
  "future_prediction": {
    "6_months": {
      "subscriber_growth": "+25%",
      "engagement_trend": "上昇",
      "risk_factors": ["競合増加"]
    }
  }
}
```

---

### 3. **influencers_v2.py** - 拡張APIエンドポイント

#### 🚀 主要エンドポイント

##### **高度検索API**
```http
GET /api/v2/influencers/search
```

**パラメータ:**
- `keyword`: 検索キーワード
- `category`: カテゴリフィルタ
- `min_subscribers`: 最小登録者数
- `max_subscribers`: 最大登録者数
- `min_engagement`: 最小エンゲージメント率
- `has_email`: メールアドレス有無
- `sort_by`: ソート項目
- `limit`: 取得件数

**レスポンス例:**
```json
{
  "results": [
    {
      "channel_id": "UC123456789",
      "channel_name": "ビューティーチャンネル",
      "subscriber_count": 75000,
      "engagement_rate": 4.8,
      "category_analysis": { "main_category": "beauty" },
      "has_business_email": true,
      "overall_score": { "grade": "A", "overall": 8.5 }
    }
  ],
  "total_count": 150,
  "page_info": {
    "limit": 20,
    "offset": 0,
    "has_next": true
  }
}
```

##### **新規発見API**
```http
POST /api/v2/influencers/discover
```

**リクエスト例:**
```json
{
  "search_queries": ["メイク", "コスメレビュー"],
  "min_subscribers": 1000,
  "max_subscribers": 100000,
  "max_per_query": 20
}
```

##### **バッチ発見API**
```http
POST /api/v2/influencers/batch-discovery
```

**リクエスト例:**
```json
{
  "categories": ["beauty", "gaming", "cooking"],
  "max_per_category": 50,
  "subscriber_ranges": [[1000, 10000], [10000, 100000]]
}
```

##### **AI分析API**
```http
POST /api/v2/influencers/{channel_id}/analyze
```

**パラメータ:**
- `force_refresh`: 強制再分析フラグ

**レスポンス例:**
```json
{
  "channel_id": "UC123456789",
  "analysis_timestamp": "2024-12-14T12:35:00Z",
  "category_analysis": { /* カテゴリ分析結果 */ },
  "email_analysis": [ /* メール分析結果 */ ],
  "trend_analysis": { /* トレンド分析結果 */ },
  "overall_score": {
    "overall": 8.5,
    "grade": "A",
    "category_score": 8.0,
    "contactability_score": 9.0,
    "trend_score": 8.0,
    "scale_score": 8.0
  },
  "recommendation": "高い協業価値を持つ優良チャンネルです"
}
```

---

## 🛠️ セットアップ方法

### 1. 必要な環境変数

`.env.local`ファイルに以下を設定:

```bash
# YouTube API設定
YOUTUBE_API_KEY=your_youtube_api_key_here

# Gemini AI設定
GEMINI_API_KEY=your_gemini_api_key_here

# Google Cloud設定
GOOGLE_CLOUD_PROJECT_ID=your_project_id
GOOGLE_APPLICATION_CREDENTIALS=./path/to/service-account.json

# データベース設定
FIRESTORE_DATABASE_ID=default
USE_LOCAL_DATABASE=true

# API設定
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2. 依存関係のインストール

```bash
# バックエンド
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 追加で必要なパッケージ
pip install pydantic-settings httpx google-cloud-aiplatform

# フロントエンド
cd frontend
npm install
```

### 3. APIキーの取得

#### YouTube Data API v3
1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. プロジェクトを作成/選択
3. YouTube Data API v3を有効化
4. 認証情報からAPIキーを作成
5. キーに適切な制限を設定

#### Gemini API
1. [Google AI Studio](https://makersuite.google.com/)にアクセス
2. APIキーを生成
3. 使用量制限を確認

---

## 📊 使用方法

### 1. **基本的なインフルエンサー検索**

```python
import httpx
import asyncio

async def search_influencers():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v2/influencers/search",
            params={
                "keyword": "美容",
                "min_subscribers": 10000,
                "max_subscribers": 100000,
                "has_email": True,
                "sort_by": "engagement_rate",
                "limit": 10
            }
        )
        return response.json()

# 実行
result = asyncio.run(search_influencers())
print(f"Found {result['total_count']} influencers")
```

### 2. **新規インフルエンサー発見**

```python
async def discover_new_influencers():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v2/influencers/discover",
            json={
                "search_queries": ["メイクアップ", "コスメレビュー", "スキンケア"],
                "min_subscribers": 5000,
                "max_subscribers": 50000,
                "max_per_query": 15
            }
        )
        return response.json()

result = asyncio.run(discover_new_influencers())
print(f"Discovered {result['discovered_count']} new influencers")
```

### 3. **大規模バッチ発見**

```python
async def batch_discovery():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v2/influencers/batch-discovery",
            json={
                "categories": ["beauty", "gaming", "cooking", "tech"],
                "max_per_category": 50,
                "subscriber_ranges": [
                    [1000, 10000],    # マイクロインフルエンサー
                    [10000, 100000],  # ミドルインフルエンサー
                ]
            }
        )
        return response.json()

result = asyncio.run(batch_discovery())
print(f"Batch discovery started for {len(result['categories'])} categories")
```

### 4. **AI分析の実行**

```python
async def analyze_influencer(channel_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://localhost:8000/api/v2/influencers/{channel_id}/analyze",
            params={"force_refresh": True}
        )
        return response.json()

# 特定チャンネルの分析
analysis = asyncio.run(analyze_influencer("UC123456789"))
print(f"Overall Grade: {analysis['overall_score']['grade']}")
print(f"Recommendation: {analysis['recommendation']}")
```

### 5. **トレンド分析の取得**

```python
async def get_trending_analytics():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v2/analytics/trending",
            params={
                "region": "JP",
                "max_results": 50
            }
        )
        return response.json()

trends = asyncio.run(get_trending_analytics())
print(f"Analyzed {trends['total_channels_analyzed']} trending channels")
```

### 6. **カテゴリ分布の確認**

```python
async def get_category_distribution():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v2/analytics/categories"
        )
        return response.json()

distribution = asyncio.run(get_category_distribution())
print(f"Total influencers: {distribution['total_influencers']}")
for category, stats in distribution['category_distribution'].items():
    print(f"{category}: {stats['count']} channels ({stats['percentage']}%)")
```

---

## 🧪 テスト方法

### 1. **環境セットアップテスト**

```bash
cd backend
source venv/bin/activate

# 環境変数の確認
python -c "
import os
required = ['YOUTUBE_API_KEY', 'GEMINI_API_KEY']
missing = [var for var in required if not os.getenv(var)]
if missing:
    print(f'Missing: {missing}')
else:
    print('Environment OK')
"
```

### 2. **基本機能テスト**

```bash
# テストスクリプト実行
python simple_test.py
```

**simple_test.py の出力例:**
```
==================================================
🚀 YouTube API Simple Test Suite
==================================================
🧪 Testing Gemini Connection...
✅ Gemini API Response: API connection successful

🧪 Testing Batch Processor Basic Functions...
✅ Search Query Generation:
   Beauty queries: ['メイク', 'コスメ', 'スキンケア', 'beauty', 'makeup tutorial']
   Tech queries: ['テクノロジー', 'ガジェット', 'technology', 'tech review', 'gadget']

✅ Trend Analysis:
   Average subscribers: 37,500
   Average engagement: 5.4%
   Contactable rate: 50%

🧪 Testing Category Analyzer...
✅ Category Analysis Result:
   Main Category: beauty
   Confidence: 0.75
   Sub Categories: ['メイク', 'レビュー']

🧪 Testing Email Extractor...
✅ Email Extraction Result:
   Email: business@techchannel.com
   Confidence: 8
   Purpose: お仕事依頼

==================================================
📊 Test Results: 4/4 tests passed
🎉 All tests passed!
==================================================
```

### 3. **APIエンドポイントテスト**

```bash
# サーバー起動
uvicorn simple-main:app --port 8000 --reload

# 別ターミナルでテスト
curl -X GET "http://localhost:8000/api/v2/health"
curl -X GET "http://localhost:8000/api/v2/influencers/search?keyword=美容&limit=5"
```

### 4. **統合テスト**

```bash
# 完全テストスイート実行
python test_youtube_api.py
```

### 5. **パフォーマンステスト**

```python
import time
import asyncio

async def performance_test():
    start_time = time.time()
    
    # 大量検索テスト
    tasks = []
    for i in range(10):
        task = search_influencers_batch()
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    print(f"10 concurrent searches completed in {end_time - start_time:.2f} seconds")
    
asyncio.run(performance_test())
```

---

## 🚨 トラブルシューティング

### よくある問題と解決方法

#### 1. **APIキー関連**

**問題:** `API key expired`
```
400 API key expired. Please renew the API key.
```

**解決方法:**
- 新しいAPIキーを生成
- `.env.local`ファイルを更新
- サーバーを再起動

#### 2. **依存関係エラー**

**問題:** `ModuleNotFoundError: No module named 'fastapi'`

**解決方法:**
```bash
pip install fastapi uvicorn python-dotenv
pip install google-cloud-firestore google-generativeai
pip install pydantic-settings httpx
```

#### 3. **レート制限**

**問題:** `429 Too Many Requests`

**解決方法:**
- `batch_processor.py`の`delay_between_batches`を増加
- API使用量を監視
- 並行処理数を調整

#### 4. **Firestore接続エラー**

**問題:** `Permission denied`

**解決方法:**
- サービスアカウントキーを確認
- Firestoreルールを確認
- ローカルテスト用に`USE_LOCAL_DATABASE=true`を設定

#### 5. **メモリ不足**

**問題:** 大量データ処理時のメモリエラー

**解決方法:**
```python
# batch_processor.pyで調整
config = BatchConfig(
    max_channels_per_batch=50,  # デフォルト100から削減
    max_concurrent_requests=3,  # デフォルト5から削減
)
```

### 6. **デバッグ方法**

```python
import logging

# ロギング設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 詳細ログを有効化
logger.debug("Processing channel: %s", channel_data)
```

---

## 📈 パフォーマンス最適化

### 1. **バッチ処理の最適化**

```python
# 設定例
config = BatchConfig(
    max_channels_per_batch=100,
    max_concurrent_requests=5,
    delay_between_batches=2.0,
    quota_safety_margin=1000,
    retry_attempts=3
)
```

### 2. **キャッシュ戦略**

```python
# Redis キャッシュ実装例
from redis import Redis

cache = Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))

async def get_cached_analysis(channel_id: str):
    cached = cache.get(f"analysis:{channel_id}")
    if cached:
        return json.loads(cached)
    return None

async def cache_analysis(channel_id: str, analysis: dict):
    cache.setex(
        f"analysis:{channel_id}",
        3600,  # 1時間
        json.dumps(analysis)
    )
```

### 3. **データベース最適化**

```python
# インデックス作成例
indexes = [
    ('subscriber_count', 'desc'),
    ('engagement_rate', 'desc'),
    ('category_analysis.main_category', 'asc'),
    ('last_analyzed', 'desc')
]
```

---

## 🔐 セキュリティ考慮事項

### 1. **APIキー管理**
- 環境変数での管理
- 定期的な更新
- 適切な権限設定

### 2. **データ保護**
- 個人情報の適切な取り扱い
- データ暗号化
- アクセス制御

### 3. **レート制限**
- API使用量の監視
- 適切な制限設定
- エラーハンドリング

---

## 📞 サポート

### 開発チーム連絡先
- 技術的問題: [技術サポート]
- API仕様: [API ドキュメント]
- バグ報告: [GitHub Issues]

### 参考資料
- [YouTube Data API Documentation](https://developers.google.com/youtube/v3)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

**最終更新:** 2024年12月14日  
**バージョン:** 1.0.0  
**作成者:** InfuMatch Development Team