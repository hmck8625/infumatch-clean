# Environment Variables Management Guide

## 🚨 重要な教訓：環境変数の二重管理による問題

### 発生した問題
- `.env.production` ファイルの古いドメイン（`infumatch-frontend.vercel.app`）が原因で OAuth エラー
- ファイル削除時にすべての環境変数が失われる事態が発生

## ✅ 正しい環境変数管理方法

### 1. Vercel Dashboard（メイン）
**場所**: [Vercel Dashboard](https://vercel.com/dashboard) → Settings → Environment Variables

**本番環境で設定すべき変数**:
```
NEXTAUTH_URL=https://infumatch-clean.vercel.app
NEXTAUTH_SECRET=yFtIW8fTTTHUsYlMwIEo51v56hW8WaR8jVM1jhOw12Iu
GOOGLE_CLIENT_ID=269567634217-dv6rq9i9bh7j54mbt5kbthrniik5qekt.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
```

### 2. .env.production（バックアップ）
**目的**: Vercel 設定のバックアップとして保持
**注意**: Vercel Dashboard の設定と必ず同期させる

### 3. 優先順位の理解
Next.js の環境変数読み込み順序：
1. **Vercel Environment Variables** (最優先)
2. `.env.production`
3. `.env.local`
4. `.env`

## 🔧 継続的な管理手順

### デプロイ前チェックリスト
- [ ] Vercel Dashboard で環境変数が正しく設定されている
- [ ] `.env.production` の内容がVercel設定と一致している
- [ ] `/api/debug-env` でサーバーサイド環境変数を確認
- [ ] Google Cloud Console のリダイレクトURIが正しい

### 環境変数変更時の手順
1. **Vercel Dashboard で変更**
2. **`.env.production` も同じ値に更新**
3. **Git コミット・プッシュ**
4. **デプロイ後に `/api/debug-env` で確認**

### 緊急時の復旧手順
1. `/api/debug-env` で現在の状態確認
2. Vercel Dashboard で環境変数を再設定
3. `.env.production` を正しい値で再作成
4. 強制リデプロイ実行

## 🚫 やってはいけないこと

### ❌ 環境変数ファイルの安易な削除
- `.env.production` を削除する前に、Vercel Dashboard での設定を確認
- バックアップなしでの削除は絶対に避ける

### ❌ ドメイン名のハードコード
- 古いドメイン名（`infumatch-frontend.vercel.app`）を残さない
- 変更時は全ファイルを検索して一括更新

### ❌ 環境変数の競合
- 複数の場所で異なる値を設定しない
- 設定箇所を統一し、定期的に同期確認

## 🔍 監視・確認方法

### 定期確認コマンド
```bash
# サーバーサイド環境変数確認
curl -s "https://infumatch-clean.vercel.app/api/debug-env" | jq .

# OAuth テスト
open "https://infumatch-clean.vercel.app/auth/signin"
```

### アラート設定
- OAuth エラーが発生した場合の自動通知
- 環境変数の値が空の場合のエラー表示

## 📝 今回の具体的な修正内容

### 修正前の問題
```json
{
  "nextAuthUrl": "[PROTOCOL]://infumatch-frontend.vercel.app"  // 古いドメイン
}
```

### 修正後の状態
```json
{
  "nextAuthUrl": "[PROTOCOL]://infumatch-clean.vercel.app"     // 正しいドメイン
}
```

### Google Cloud Console 設定
- **承認済みのリダイレクト URI**: `https://infumatch-clean.vercel.app/api/auth/callback/google`
- **承認済みの JavaScript 生成元**: `https://infumatch-clean.vercel.app`

## 🎯 今後の改善案

1. **環境変数の自動同期スクリプト**作成
2. **CI/CDでの環境変数検証**追加
3. **開発・ステージング・本番環境の分離**強化
4. **環境変数の暗号化管理**導入検討

---

**最重要**: 環境変数は複数箇所で管理せず、Vercel Dashboard を信頼できる単一の情報源として扱う