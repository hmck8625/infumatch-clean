# 交渉エージェント実装ドキュメント

## プロジェクト概要
InfuMatch - YouTubeインフルエンサーマッチングプラットフォーム  
Google Cloud Japan AI Hackathon Vol.2 参加作品

## 実装完了項目

### 1. 設定管理システム ✅
**実装場所**: `frontend/app/settings/page.tsx`, `frontend/app/api/settings/route.ts`

**機能**:
- 4つのタブによる設定管理（企業情報、商材管理、交渉設定、マッチング設定）
- 企業基本情報（企業名、業界、説明、担当者、連絡先）
- 商材情報の登録・管理（商品名、カテゴリ、価格帯、ターゲット層）
- 交渉エージェント設定（予算範囲、交渉トーン、重要ポイント、避けるべきトピック）
- AIマッチング設定（登録者数範囲、優先カテゴリ、キーワード設定）

**技術実装**:
- TypeScript + React Hook Form + Zod validation
- NextAuth.js による認証連携
- RESTful API (GET/PUT /api/settings)
- 現在はモック実装（メモリ内保存）

### 2. AIマッチング機能への設定連携 ✅
**実装場所**: `frontend/app/matching/page.tsx`

**機能**:
- 設定データの自動読み込み
- 登録者数フィルタリング（最小・最大登録者数）
- 優先カテゴリマッチング（スコア加算）
- 予算範囲によるコスト調整
- 設定反映済みのマッチング結果表示

**技術実装**:
```typescript
const customizeMatchingResults = () => {
  // 登録者数でフィルタリング
  // 優先カテゴリがマッチする場合にスコア+5
  // 予算範囲に合わせてコスト調整
  // スコア順でソート
}
```

### 3. 交渉エージェントへの設定連携 ✅
**実装場所**: `backend/services/ai_agents/negotiation_agent.py`

**機能**:
- 設定データによるペルソナ動的更新
- 企業名・担当者名の自動反映
- 交渉トーンによるコミュニケーションスタイル調整
- 特別指示・重要ポイント・避けるべきトピックの反映
- 予算範囲の自動適用

**技術実装**:
```python
def __init__(self, settings: Optional[Dict] = None):
    self.settings = settings or {}
    self._update_persona_from_settings()

def _update_persona_from_settings(self):
    # 企業情報の更新
    # 交渉トーンの反映（friendly/professional/assertive）
    # 特別指示・重要ポイントの設定
```

### 4. モック交渉サーバー設定統合 ✅
**実装場所**: `frontend/frontend/mock_negotiation_server.py`

**機能**:
- 設定データを活用した返信パターン生成
- 企業名・担当者名・予算範囲の動的反映
- 交渉トーンに応じた文体調整
- 重要ポイント（エンゲージメント率、ターゲット適合性）の自動含有

**技術実装**:
```python
def get_mock_settings(self):
    # 設定データのモック取得
    # 返信パターンに企業情報・予算・重要ポイントを反映
```

### 5. ナビゲーション統一 ✅
**実装場所**: 全ページのヘッダーナビゲーション

**機能**:
- 全ページから設定ページへのアクセス可能
- 統一されたナビゲーション体験

## 技術アーキテクチャ

### フロントエンド
- **Next.js 14** (App Router)
- **TypeScript** 
- **Tailwind CSS + shadcn/ui**
- **NextAuth.js** (認証)
- **SWR** (データフェッチング)

### バックエンド  
- **FastAPI** (Python)
- **Vertex AI / Gemini API** (AIエージェント)
- **Pydantic v2** (データバリデーション)

### データ管理
- **現在**: メモリ内モック実装
- **予定**: Google Cloud Firestore

## 設定データ保存の現状と課題

### 現在の実装
```typescript
// モック設定データ（実際にはデータベースを使用）
let mockSettings = { ... }
```

**保存場所**: サーバーメモリ内の変数  
**認証連携**: NextAuth.js セッション確認済み  
**ユーザー管理**: 未実装（全ユーザー共通設定）

### 課題
- ❌ サーバー再起動で設定が消える
- ❌ ユーザー別設定管理なし  
- ❌ 永続化されない
- ❌ 本番環境で使用不可

## ネクストアクション

### 優先度: 高 🔴

#### 1. データベース永続化実装
**目標**: 設定データのFirestore保存

**実装内容**:
```typescript
// frontend/app/api/settings/route.ts
export async function PUT(request: NextRequest) {
  const session = await getServerSession(authOptions);
  const userId = session.user.id;
  
  // Firestore保存実装
  await saveSettingsToFirestore(userId, body);
}

export async function GET(request: NextRequest) {
  const session = await getServerSession(authOptions);
  const userId = session.user.id;
  
  // Firestore取得実装
  const settings = await getSettingsFromFirestore(userId);
  return NextResponse.json(settings);
}
```

**新規ファイル**:
- `lib/firestore.ts` - Firestore操作ライブラリ
- `types/settings.ts` - 設定データ型定義の統一

#### 2. ユーザー別設定管理
**目標**: ユーザーIDによる設定の分離

**実装内容**:
- セッションからのユーザーID取得
- Firestoreコレクション設計: `users/{userId}/settings`
- デフォルト設定の自動作成機能

#### 3. 設定データバリデーション強化
**目標**: フロントエンド・バックエンド統一バリデーション

**実装内容**:
- Zodスキーマの共通化
- APIレスポンス型安全性の確保
- エラーハンドリングの改善

### 優先度: 中 🟡

#### 4. AI機能の設定反映強化
**目標**: より詳細な設定項目のAI反映

**実装内容**:
- 商材情報のマッチング精度向上
- 交渉履歴による学習機能
- 設定変更時のAI再トレーニング

#### 5. 設定インポート・エクスポート機能
**目標**: 設定の移行・バックアップ機能

**実装内容**:
- JSON形式での設定エクスポート
- 設定テンプレートの提供
- 一括設定変更機能

#### 6. 設定変更履歴・監査ログ
**目標**: 設定変更の追跡・監査

**実装内容**:
- 変更履歴の記録
- 変更差分の表示
- ロールバック機能

### 優先度: 低 🟢

#### 7. 高度な設定UI
**目標**: より使いやすい設定インターフェース

**実装内容**:
- 設定ウィザード機能
- プレビュー機能
- 設定推奨値の提案

#### 8. 設定の自動最適化
**目標**: AI による設定の自動調整

**実装内容**:
- 成果データに基づく設定最適化
- A/Bテスト機能
- 自動調整の提案機能

## 開発環境セットアップ

### 必要な環境変数
```bash
# .env.local
NEXTAUTH_SECRET=your-secret
GOOGLE_CLOUD_PROJECT_ID=hackathon-462905
# Firestore実装後に追加予定
```

### 開発サーバー起動
```bash
# フロントエンド
cd frontend && npm run dev

# モック交渉サーバー  
cd frontend/frontend && python mock_negotiation_server.py
```

## 関連ファイル一覧

### 設定関連
- `frontend/app/settings/page.tsx` - 設定管理UI
- `frontend/app/api/settings/route.ts` - 設定API
- `frontend/types/` - 型定義（要作成）

### AI統合関連
- `frontend/app/matching/page.tsx` - AIマッチング
- `backend/services/ai_agents/negotiation_agent.py` - 交渉エージェント
- `frontend/frontend/mock_negotiation_server.py` - モックサーバー

### 認証関連
- `lib/auth.ts` - NextAuth設定
- 各ページのAuthGuardコンポーネント

## メモ・補足事項

### 設定項目の拡張性
現在の設定構造は拡張可能な設計になっており、新しい設定項目の追加が容易です。

### セキュリティ考慮事項
- 設定データにはAPIキーなどの機密情報を含めない
- ユーザー入力のサニタイゼーション実装済み
- CORS設定の適切な管理

### パフォーマンス考慮事項
- 設定データのキャッシュ機能要検討
- 大量設定変更時のバッチ処理要検討

---

**最終更新**: 2025-06-15  
**作成者**: Claude Code AI Assistant  
**プロジェクト**: InfuMatch - Google Cloud Japan AI Hackathon Vol.2