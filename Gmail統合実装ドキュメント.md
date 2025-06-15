# Gmail統合機能実装ドキュメント

## 概要
InfuMatchプロジェクトでGmail統合機能を実装し、AIエージェントによる自動返信候補生成機能を追加しました。

## 実装内容

### 1. Google OAuth認証
- **NextAuth.js v4**を使用したGoogle OAuth2認証
- Gmail API v3のスコープを取得
- セッション管理とアクセストークンの永続化

### 2. Gmail API統合
- スレッド一覧取得（`/api/gmail/threads`）
- 個別スレッド詳細取得（`/api/gmail/threads/[id]`）
- メール送信機能（`/api/gmail/send`）

### 3. UI実装
- **メッセージページ**（`/messages`）での統合UI
- スレッド一覧表示（件名、送信者、日時を表示）
- メール詳細表示とHTML/テキスト本文のレンダリング
- 返信機能とリアルタイム送信

### 4. AIエージェント連携
- **田中美咲（交渉エージェント）**による返信パターン生成
- スレッド分析機能（関係性段階、感情トーン、緊急度判定）
- 3パターンの返信候補自動生成（友好的、慎重、ビジネス重視）

### 5. エラーハンドリング
- Chrome拡張機能エラーの除外処理
- ErrorBoundaryによるアプリケーションクラッシュ防止
- グローバルエラーイベントリスナー

## ファイル構成

### 認証関連
- `frontend/lib/auth.ts` - NextAuth.js設定、JWT/セッションコールバック
- `frontend/types/next-auth.d.ts` - TypeScript型定義拡張
- `frontend/.env.local` - 環境変数（OAuth認証情報）

### API実装
- `frontend/lib/gmail.ts` - Gmail API クライアントライブラリ
- `frontend/app/api/gmail/threads/route.ts` - スレッド一覧API
- `frontend/app/api/gmail/threads/[id]/route.ts` - スレッド詳細API
- `frontend/app/api/gmail/send/route.ts` - メール送信API

### UI実装
- `frontend/app/messages/page.tsx` - メインのメッセージ管理UI
- `frontend/components/error-boundary.tsx` - エラー境界コンポーネント
- `frontend/components/auth-guard.tsx` - 認証ガードコンポーネント

### バックエンド連携
- `backend/api/v1/negotiation/reply-patterns` - AI返信候補生成API（FastAPI）

## 技術仕様

### 認証フロー
1. GoogleでOAuth2認証
2. Gmail APIスコープ取得
3. アクセストークンをJWTセッションに保存
4. APIリクエスト時にトークン使用

### Gmail API統合
```typescript
// スレッド取得例
const response = await fetch('/api/gmail/threads');
const data = await response.json();
// data.threads - EmailThread[]型の配列
```

### AI分析連携
```typescript
// 返信パターン生成例
const response = await fetch('/api/v1/negotiation/reply-patterns', {
  method: 'POST',
  body: JSON.stringify({
    email_thread: { id, subject, participants },
    thread_messages: messages,
    context: { platform: 'gmail', thread_length }
  })
});
```

## 設定手順

### 1. Google Cloud Console設定
```bash
# Gmail API有効化
gcloud services enable gmail.googleapis.com

# OAuth2.0クライアントID作成
# 承認済みリダイレクトURI: http://localhost:3000/api/auth/callback/google
```

### 2. 環境変数設定
```env
# frontend/.env.local
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret-key
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
```

### 3. 開発サーバー起動
```bash
# フロントエンド・バックエンド同時起動
./start-local.sh

# 個別起動
cd frontend && npm run dev
cd backend && uvicorn main:app --reload
```

## 実装済み機能

### ✅ 認証・セキュリティ
- [x] Google OAuth2認証
- [x] Gmail APIスコープ取得
- [x] セッション管理
- [x] Chrome拡張機能エラー除外

### ✅ Gmail統合
- [x] スレッド一覧表示
- [x] メール詳細表示
- [x] HTML/テキスト本文パース
- [x] 返信機能
- [x] リアルタイム更新

### ✅ AI機能
- [x] スレッド分析（関係性、感情、緊急度）
- [x] 返信パターン3種類生成
- [x] 推奨度スコア表示
- [x] ワンクリック適用

### ✅ UI/UX
- [x] レスポンシブデザイン
- [x] ローディング状態表示
- [x] エラーハンドリング
- [x] アニメーション効果

## 課題と制限事項

### 技術的制限
1. **Refresh Token管理** - 長期間のトークン更新が未実装
2. **添付ファイル** - 添付ファイルの表示・送信が未対応
3. **リアルタイム通知** - 新着メールのプッシュ通知なし

### スケーラビリティ
1. **レート制限** - Gmail API制限への対応が必要
2. **大量データ** - ページネーション実装が必要
3. **キャッシュ戦略** - メールデータのキャッシュ最適化

## 次期開発予定

### Phase 1: 基本機能強化
- [ ] Refresh Token自動更新
- [ ] 添付ファイル対応
- [ ] メール検索・フィルタ機能

### Phase 2: AI機能拡張
- [ ] 感情分析精度向上
- [ ] カスタム返信テンプレート
- [ ] 多言語対応

### Phase 3: エンタープライズ対応
- [ ] 複数アカウント管理
- [ ] 権限管理
- [ ] 監査ログ

## 参考リンク

- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [NextAuth.js Documentation](https://next-auth.js.org/)
- [Google Cloud Console](https://console.cloud.google.com/)

---

**最終更新**: 2025年6月15日  
**実装者**: Claude Code  
**プロジェクト**: InfuMatch - YouTube Influencer Matching Agent