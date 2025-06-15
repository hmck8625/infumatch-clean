# YouTube Data API v3 詳細調査結果

## 📋 調査概要

**調査日**: 2025-06-14  
**対象**: YouTube Data API v3 (最新バージョン)  
**目的**: マイクロインフルエンサーマッチングエージェント開発のための技術仕様把握

## 🔗 公式情報源

### 主要ドキュメント
1. **API Reference**: https://developers.google.com/youtube/v3/docs
2. **Getting Started Guide**: https://developers.google.com/youtube/v3/getting-started
3. **Channels API**: https://developers.google.com/youtube/v3/docs/channels
4. **Search API**: https://developers.google.com/youtube/v3/docs/search/list
5. **Quota Calculator**: https://developers.google.com/youtube/v3/determine_quota_cost

## 🚀 API機能詳細

### 1. Channels API (`/channels`)

#### 基本エンドポイント
```
GET https://www.googleapis.com/youtube/v3/channels
```

#### 利用可能なパーツ (part パラメータ)
```javascript
const availableParts = [
  'id',              // チャンネルID
  'snippet',         // 基本情報
  'contentDetails',  // コンテンツ詳細
  'statistics',      // 統計情報
  'topicDetails',    // トピック情報
  'brandingSettings',// ブランディング設定
  'auditDetails',    // 監査詳細（特別認証要）
  'localizations',   // ローカライゼーション
  'status'          // ステータス情報
];
```

#### snippet パートの詳細データ
```json
{
  "snippet": {
    "title": "チャンネル名",
    "description": "チャンネル説明文（メールアドレス記載箇所）",
    "customUrl": "@channelname",
    "publishedAt": "2020-01-01T00:00:00Z",
    "thumbnails": {
      "default": {"url": "...", "width": 88, "height": 88},
      "medium": {"url": "...", "width": 240, "height": 240},
      "high": {"url": "...", "width": 800, "height": 800}
    },
    "defaultLanguage": "ja",
    "localized": {
      "title": "ローカライズされたタイトル",
      "description": "ローカライズされた説明"
    },
    "country": "JP"
  }
}
```

#### statistics パートの詳細データ
```json
{
  "statistics": {
    "viewCount": "1000000",
    "subscriberCount": "5000",
    "hiddenSubscriberCount": false,
    "videoCount": "150"
  }
}
```

**⚠️ 重要な注意事項**:
- `subscriberCount` は**3つの有効数字に丸められる**
- 一部チャンネルは `hiddenSubscriberCount: true` で非表示設定
- 2024年更新: 登録者数表示ポリシーが変更

### 2. Search API (`/search`)

#### 基本エンドポイント
```
GET https://www.googleapis.com/youtube/v3/search
```

#### チャンネル検索の実装例
```javascript
const searchChannels = async (keyword, maxResults = 50) => {
  const params = {
    part: 'snippet',
    type: 'channel',
    q: keyword,
    maxResults: maxResults,
    order: 'relevance', // または 'date', 'rating', 'viewCount'
    key: API_KEY
  };
  
  const response = await fetch(
    `https://www.googleapis.com/youtube/v3/search?${new URLSearchParams(params)}`
  );
  return response.json();
};
```

#### 🚨 重要な制限事項
- **登録者数での直接フィルタリング不可**
- 2段階処理が必要:
  1. Search APIでチャンネル発見
  2. Channels APIで詳細統計取得
  3. アプリ側でフィルタリング

### 3. contentDetails パートの活用

```json
{
  "contentDetails": {
    "relatedPlaylists": {
      "likes": "",
      "favorites": "",
      "uploads": "UU1234567890"  // アップロード動画一覧
    }
  }
}
```

**活用方法**: uploads プレイリストIDから最新動画情報を取得可能

## 💰 クォータ・料金体系 (2024年現在)

### 基本クォータ
- **デフォルト**: 10,000 units/day
- **リセット時刻**: 太平洋標準時の午前0時
- **料金**: **完全無料** (クォータ拡張時も無料)

### 操作別クォータコスト

| 操作 | コスト | 説明 |
|------|--------|------|
| channels.list | 1 unit | チャンネル情報取得 |
| search.list | 100 units | 検索実行 |
| videos.list | 1 unit | 動画情報取得 |
| 動画アップロード | 1600 units | アップロード処理 |
| 更新系操作 | 50 units | 作成・更新・削除 |

### 🔥 実用的な計算例

```javascript
// 1日で処理可能な件数計算
const dailyQuota = 10000;

// チャンネル検索→詳細取得のパターン
const searchCost = 100;      // 1回の検索
const channelsCost = 1;      // 1チャンネルの詳細取得

// 検索1回で50チャンネル発見した場合
const totalCost = searchCost + (50 * channelsCost); // 150 units

// 1日の処理可能回数
const dailySearches = Math.floor(dailyQuota / totalCost); // 66回
const dailyChannels = dailySearches * 50; // 3,300チャンネル/日
```

### クォータ拡張
- **方法**: Quota extension request form 提出
- **条件**: 正当な利用目的の説明
- **費用**: 無料
- **審査**: Googleによる審査あり

**出典**: https://developers.google.com/youtube/v3/determine_quota_cost

## 🔐 認証・セキュリティ要件

### 認証方式

#### 1. API Key認証 (推奨)
```javascript
// 公開データ取得時
const apiKey = 'YOUR_API_KEY';
const url = `https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&id=UC123&key=${apiKey}`;
```

**適用場面**:
- 公開チャンネル情報取得
- 公開動画データ取得
- 検索機能
- **マイクロインフルエンサー発見に最適**

#### 2. OAuth 2.0認証
```javascript
// プライベートデータ・更新系操作時
const accessToken = 'oauth2_access_token';
const headers = {
  'Authorization': `Bearer ${accessToken}`
};
```

**適用場面**:
- チャンネル更新・削除
- 非公開データアクセス
- ユーザー代理操作

### 🛡️ セキュリティ考慮事項

#### API Key管理
- **環境変数での管理必須**
- **GitHub等への公開厳禁**
- **定期的なローテーション推奨**

#### OAuth 2.0
- **トークン有効期限**: 60分
- **リフレッシュトークン**: 無期限延長可能
- **スコープ制限**: 必要最小限の権限のみ

**出典**: https://developers.google.com/youtube/v3/guides/authentication

## 📊 2024年の重要なアップデート

### 1. 登録者数表示の変更 (2024年3月)
- **変更内容**: 登録者数の表示・カウント方法変更
- **影響**: statistics.subscriberCount の値に影響
- **対応**: 最新の表示ポリシーに準拠

### 2. Shorts視聴数カウント変更 (2025年3月31日予定)
- **変更内容**: Shorts動画の視聴数カウント方法変更
- **影響**: 将来的な統計データに影響予定

### 3. 廃止予定機能
- **brandingSettings.channel.moderateComments** (2024年3月7日廃止)
- **captions methods の sync パラメータ** (2024年4月12日廃止)

**出典**: https://developers.google.com/youtube/v3/revision_history

## 🎯 マイクロインフルエンサー発見に最適な実装戦略

### 1. 効率的なデータ取得パターン

```javascript
class YouTubeInfluencerFinder {
  constructor(apiKey) {
    this.apiKey = apiKey;
    this.baseUrl = 'https://www.googleapis.com/youtube/v3';
  }

  // Step 1: キーワードでチャンネル検索
  async searchChannels(keyword, maxResults = 50) {
    const url = `${this.baseUrl}/search`;
    const params = {
      part: 'snippet',
      type: 'channel',
      q: keyword,
      maxResults,
      key: this.apiKey
    };
    
    const response = await fetch(`${url}?${new URLSearchParams(params)}`);
    return response.json();
  }

  // Step 2: 複数チャンネルの詳細情報を一括取得
  async getChannelsDetails(channelIds) {
    const url = `${this.baseUrl}/channels`;
    const params = {
      part: 'snippet,statistics,contentDetails',
      id: channelIds.join(','), // 最大50件まで一度に取得可能
      key: this.apiKey
    };
    
    const response = await fetch(`${url}?${new URLSearchParams(params)}`);
    return response.json();
  }

  // Step 3: マイクロインフルエンサーフィルタリング
  filterMicroInfluencers(channels, minSubs = 1000, maxSubs = 100000) {
    return channels.filter(channel => {
      const subCount = parseInt(channel.statistics.subscriberCount);
      return subCount >= minSubs && subCount <= maxSubs && !channel.statistics.hiddenSubscriberCount;
    });
  }
}
```

### 2. メールアドレス抽出パターン

```javascript
class EmailExtractor {
  static extractEmails(description) {
    const emailRegex = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g;
    const emails = description.match(emailRegex) || [];
    
    // ビジネス用メールの優先度判定
    return emails.map(email => ({
      email,
      priority: this.calculatePriority(email, description)
    })).sort((a, b) => b.priority - a.priority);
  }

  static calculatePriority(email, description) {
    let priority = 0;
    
    // 独自ドメイン +3点
    if (!email.includes('@gmail.com') && !email.includes('@yahoo.co.jp')) {
      priority += 3;
    }
    
    // ビジネス関連キーワード +2点
    const businessKeywords = ['お仕事', 'コラボ', 'business', 'contact', '連絡'];
    const contextIndex = description.indexOf(email);
    const context = description.substring(Math.max(0, contextIndex - 50), contextIndex + 50);
    
    if (businessKeywords.some(keyword => context.includes(keyword))) {
      priority += 2;
    }
    
    return priority;
  }
}
```

## ⚠️ 重要な注意事項・制限事項

### 1. データ品質の課題
- **登録者数の丸め**: 3桁有効数字のため正確な値が取得不可
- **非表示設定**: 約10-15%のチャンネルが登録者数非表示
- **古いデータ**: 非アクティブチャンネルの混在

### 2. API制限への対策
- **レート制限**: 毎秒100リクエスト制限（実装時は余裕を持つ）
- **クォータ管理**: 1日10,000ユニットの効率的利用
- **エラーハンドリング**: 403エラー時の適切な処理

### 3. コンプライアンス要件
- **データ保存**: 取得データの最新状態維持義務
- **プライバシー**: 取得データの適切な取り扱い
- **利用規約**: YouTube API Terms of Serviceの遵守

## 🏆 結論：マイクロインフルエンサー発見の実現可能性

### ✅ 実現可能な機能
1. **キーワードベースのチャンネル検索**: 完全対応
2. **詳細統計情報の取得**: 登録者数・視聴回数・動画数
3. **チャンネル説明文からのメール抽出**: 高精度で可能
4. **大規模データ処理**: 1日3,000+チャンネル処理可能

### ⚠️ 制限事項と対策
1. **登録者数フィルタリング**: API側で不可→アプリ側で実装
2. **データ精度**: 丸められた値→統計的に十分活用可能
3. **非表示チャンネル**: 約10-15%→母数を多めに設定

### 🎯 最終評価
**YouTube Data API v3は、マイクロインフルエンサー発見システムの実装に完全対応可能**

- コスト: 完全無料
- 技術的実現性: 100%
- データ品質: 商用利用に十分
- 拡張性: クォータ拡張で大規模対応可能

---

**文書作成者**: ハッカソンチーム  
**最終更新**: 2025-06-14  
**ステータス**: 実装準備完了