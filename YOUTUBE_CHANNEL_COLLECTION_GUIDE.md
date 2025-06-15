# YouTubeチャンネル収集・登録完全ガイド

## 📋 概要

このガイドは、YouTubeチャンネルをAI分析付きで収集し、Firestore・BigQueryに自動登録するための包括的な手順書です。他のLLMが独立してシステムを理解・実行できるよう詳細に記述されています。

## 🏗️ システム構成

### データベース構造

#### Firestore: `influencers` コレクション
```json
{
  "channel_id": "UC...",
  "channel_title": "チャンネル名",
  "description": "チャンネル説明",
  "subscriber_count": 50000,
  "video_count": 123,
  "view_count": 1000000,
  "category": "ゲーム",
  "country": "JP",
  "language": "ja",
  "contact_info": {
    "emails": ["contact@example.com"],
    "primary_email": "contact@example.com"
  },
  "engagement_metrics": {
    "engagement_rate": 0.05,
    "avg_views_per_video": 8130.08,
    "has_contact": true
  },
  "ai_analysis": {
    "content_quality_score": 0.8,
    "brand_safety_score": 0.95,
    "growth_potential": 0.7,
    "full_analysis": {...},
    "advanced": {
      "enhanced_at": "2025-06-15T...",
      "category": "ゲーム",
      "sub_categories": ["実況プレイ", "攻略"],
      "content_themes": ["マインクラフト", "建築"],
      "safety_score": 0.95,
      "confidence": 0.8,
      "target_age": "13-35歳",
      "top_product": "エンタメ・ホビー",
      "match_score": 0.9
    }
  },
  "status": "active",
  "created_at": "2025-06-15T...",
  "updated_at": "2025-06-15T...",
  "last_analyzed": "2025-06-15T...",
  "fetched_at": "2025-06-15T...",
  "data_source": "youtube_api",
  "collection_method": "comprehensive_ai_enhanced"
}
```

#### BigQuery: `infumatch_data.influencers` テーブル
```sql
CREATE TABLE `hackathon-462905.infumatch_data.influencers` (
  influencer_id STRING,
  channel_id STRING,
  channel_title STRING,
  description STRING,
  subscriber_count INT64,
  video_count INT64,
  view_count INT64,
  category STRING,
  country STRING,
  language STRING,
  contact_email STRING,
  social_links STRING,
  ai_analysis_json STRING,
  brand_safety_score FLOAT64,
  analysis_confidence FLOAT64,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  is_active BOOLEAN
);
```

## 🚀 実行手順

### 1. 環境セットアップ

#### 必要な認証情報
```bash
# Google Cloud認証
gcloud auth login
gcloud config set project hackathon-462905
gcloud auth application-default login

# サービスアカウントキー（プロジェクトルートに配置）
hackathon-462905-7d72a76d3742.json
```

#### 必要なAPI・サービス
- YouTube Data API v3
- Google Cloud Firestore API  
- Google Cloud BigQuery API
- Google AI Platform (Gemini API)

### 2. データベース接続テスト

```bash
python3 backend/test_database_connection.py
```

期待される出力:
```
🔧 データベース接続診断開始
✅ Firestoreクライアント初期化成功
📊 influencersコレクション: X 件取得
✅ テストドキュメント作成成功
✅ BigQueryクライアント初期化成功
🎉 すべてのデータベース接続が正常です
```

### 3. 包括的チャンネル収集実行

```bash
python3 backend/comprehensive_channel_collector.py
```

## 📊 収集プロセス詳細

### Phase 1: チャンネル検索
- **YouTube Data API** を使用してキーワード検索
- **地域フィルタ**: 日本 (regionCode='JP')
- **言語フィルタ**: 日本語 (relevanceLanguage='ja')
- **最大結果数**: カテゴリあたり35チャンネル

### Phase 2: 詳細データ取得
- **チャンネル統計**: 登録者数、動画数、視聴回数
- **フィルタリング**: マイクロインフルエンサー (10K-500K登録者)
- **メール抽出**: 概要欄から正規表現でメールアドレス抽出
- **エンゲージメント推定**: 登録者数/動画数 * 100

### Phase 3: AI分析実行
**AdvancedChannelAnalyzer** を使用した5次元分析:

1. **カテゴリタグ付与**
   - 主要カテゴリ自動判定
   - サブカテゴリ (最大3個)
   - コンテンツテーマ (最大5個)
   - ターゲット年齢層

2. **チャンネル概要構造化**
   - チャンネル特徴説明
   - コンテンツスタイル分析
   - 更新頻度推定
   - 専門性・エンタメ性・教育価値評価

3. **商材マッチング分析**
   - 推奨商品カテゴリ (最大3個)
   - 価格帯提案
   - マッチ度スコア算出
   - コラボ形式提案

4. **オーディエンス分析**
   - オーディエンス規模分類
   - エンゲージメントレベル評価
   - リーチポテンシャル算出
   - 人口統計推定

5. **ブランドセーフティ評価**
   - コンテンツ適切性評価
   - 炎上リスク評価
   - コンプライアンススコア
   - 総合安全性スコア (0.0-1.0)

### Phase 4: データベース保存
1. **Firestore保存**
   - 既存データ重複チェック
   - 構造化ドキュメント形式で保存
   - エラーハンドリング・リトライ機能

2. **BigQuery保存**  
   - フラット化されたテーブル形式
   - JSON文字列としてAI分析結果を格納
   - バッチ挿入による高速処理

3. **JSONバックアップ**
   - タイムスタンプ付きファイル名
   - カテゴリ別分割保存

## 🔧 トラブルシューティング

### よくある問題と解決法

#### 1. YouTube APIクォータ不足
```
エラー: quotaExceeded
解決: 翌日まで待機するか、別のAPIキーを使用
```

#### 2. Firestore認証エラー
```bash
# 認証情報を再設定
gcloud auth application-default login
```

#### 3. AI分析タイムアウト
```python
# services/ai_channel_analyzer.py の timeout設定を調整
genai.configure(api_key=GEMINI_API_KEY, timeout=60)
```

#### 4. BigQuery テーブル不存在
```sql
-- 手動でテーブル作成
CREATE TABLE `hackathon-462905.infumatch_data.influencers` (
  -- スキーマ定義
);
```

## 🔄 定期実行・自動化

### Cloud Scheduler設定例
```yaml
name: youtube-collection-job
schedule: "0 9 * * 1"  # 毎週月曜日 9:00 JST
time_zone: "Asia/Tokyo"
target:
  cloud_run_job:
    service: youtube-collector-service
    region: asia-northeast1
```

### Docker化
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ ./backend/
CMD ["python3", "backend/comprehensive_channel_collector.py"]
```

## 📈 品質管理・監視

### 収集品質指標
- **AI信頼度**: 平均 0.7 以上
- **ブランド安全性**: 平均 0.8 以上  
- **エラー率**: 5% 以下
- **重複率**: 1% 以下

### 監視アラート
```python
# Cloud Monitoring メトリクス
- firestore_write_success_rate
- ai_analysis_confidence_avg
- collection_error_count
- brand_safety_score_avg
```

## 🎯 カテゴリ別検索戦略

### ゲーム系チャンネル
```python
GAMING_QUERIES = [
    "ゲーム実況", "実況プレイ", "ゲーム配信",
    "マインクラフト 実況", "フォートナイト 実況", 
    "エーペックス 実況", "ゲーム攻略",
    "gaming japan", "日本 ゲーム実況", "ゲーム実況者"
]
```
**期待カテゴリ**: Gaming, エンターテイメント
**推奨商材**: エンタメ・ホビー, テクノロジー

### ビジネス系チャンネル  
```python
BUSINESS_QUERIES = [
    "ビジネス 起業", "経営 コンサル", "投資 株式", 
    "副業 稼ぐ", "マーケティング 戦略", "経済 解説",
    "フリーランス 独立", "business japan", 
    "転職 キャリア", "資産運用 投資"
]
```
**期待カテゴリ**: 教育, ビジネス・経済
**推奨商材**: 教育・学習, テクノロジー

### 料理系チャンネル
```python
COOKING_QUERIES = [
    "料理 レシピ", "クッキング 簡単", "グルメ 食べ物",
    "お弁当 作り方", "お菓子作り スイーツ", "和食 日本料理", 
    "家庭料理 時短", "cooking japan", 
    "ベーキング パン", "食材 節約"
]
```
**期待カテゴリ**: 料理, Howto & Style  
**推奨商材**: 食品・グルメ, ライフスタイル

## 📚 関連ファイル

### 主要スクリプト
- `backend/comprehensive_channel_collector.py` - メイン収集スクリプト
- `backend/test_database_connection.py` - DB接続診断
- `backend/services/ai_channel_analyzer.py` - AI分析エンジン

### 設定ファイル
- `backend/enhanced_youtube_collector.py` - レガシー収集スクリプト  
- `CLAUDE.md` - プロジェクト全体ガイド
- `AI_ANALYSIS_FEATURES.md` - AI分析機能詳細

### 出力ファイル例
- `gaming_channels_20250615_183045.json` - ゲーム系バックアップ
- `business_channels_20250615_183045.json` - ビジネス系バックアップ  
- `cooking_channels_20250615_183045.json` - 料理系バックアップ

## ⚠️ 重要な注意事項

1. **API制限遵守**: YouTube API は 1日10,000クォータ
2. **レート制限**: 各APIコール間に0.5秒以上の間隔
3. **データ品質**: マイクロインフルエンサー(10K-500K)に限定
4. **重複回避**: channel_id による重複チェック必須
5. **エラーハンドリング**: 例外発生時も統計情報を保持
6. **プライバシー**: メールアドレス抽出は公開情報のみ

## 🎉 実行例

```bash
# 完全実行（全カテゴリ収集）
python3 backend/comprehensive_channel_collector.py

# 出力例
🚀 ゲーム系チャンネル収集開始
🔍 ゲーム系チャンネル検索開始
📊 検索結果: 47 チャンネル発見
🤖 47 チャンネルの詳細取得 + AI分析中...
✅ 完了: 鶴太郎 (登録者: 224,000, カテゴリ: ゲーム)
🔥 Firestoreに 26 チャンネルを保存中...
✅ 26. カニヨイ (登録者: 402,000)
🏗️ BigQueryに 26 チャンネルを保存中...
✅ BigQuery保存成功: 26 件

🎯 収集結果サマリー
📊 統計情報:
  - 検索発見: 124 チャンネル
  - フィルタ後: 80 チャンネル  
  - AI分析完了: 80 チャンネル
  - Firestore保存: 80 チャンネル
  - BigQuery保存: 80 チャンネル
  - エラー数: 0

📋 カテゴリ分布:
  - ゲーム: 26 チャンネル
  - 教育: 22 チャンネル  
  - 料理: 32 チャンネル

🎉 すべての収集が完了しました！
```

---

**最終更新**: 2025-06-15  
**作成者**: InfuMatch Development Team  
**バージョン**: 3.0.0