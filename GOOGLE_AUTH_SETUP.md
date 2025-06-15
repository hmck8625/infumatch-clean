# Google認証設定ガイド

このガイドでは、InfuMatchアプリケーションでGoogle認証を設定する手順を説明します。

## 🔧 必要な設定

### 1. Google Cloud Console設定

#### Step 1: Google Cloud Project作成
1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成するか、既存のプロジェクトを選択

#### Step 2: APIs有効化
1. **APIs & Services** → **Library** に移動
2. 以下のAPIを有効化：
   - **Gmail API** (メール機能用)

**注意:** Google認証（OAuth）は自動的に利用可能で、追加のAPI有効化は不要です。

#### Step 3: OAuth 2.0認証情報作成
1. **APIs & Services** → **Credentials** に移動
2. **+ CREATE CREDENTIALS** → **OAuth 2.0 Client IDs** をクリック
3. 設定項目：
   - **Application type**: Web application
   - **Name**: InfuMatch Local Development
   - **Authorized JavaScript origins**:
     - `http://localhost:3000`
     - `http://localhost:3001`
   - **Authorized redirect URIs**:
     - `http://localhost:3000/api/auth/callback/google`
     - `http://localhost:3001/api/auth/callback/google`

4. **CREATE** をクリック
5. 表示されるクライアントIDとクライアントシークレットをコピー

### 2. 環境変数設定

#### `.env.local` ファイルを編集

以下の環境変数を実際の値に置き換えてください：



#### 安全なシークレット生成

NextAuth Secretは以下のコマンドで生成できます：

```bash
openssl rand -base64 32
```

### 3. 設定確認

1. 開発サーバーを再起動：
   ```bash
   npm run dev
   ```

2. ブラウザで `http://localhost:3000/auth/signin` にアクセス

3. 「Googleでログイン」ボタンをクリック

4. Google認証画面が表示されれば設定成功

## 🚨 トラブルシューティング

### よくあるエラー

#### "client_id is required"
- `GOOGLE_CLIENT_ID` が設定されていない
- `.env.local` ファイルの場所が間違っている
- 開発サーバーを再起動していない

#### "redirect_uri_mismatch"
- Google Cloud ConsoleのAuthorized redirect URIsに正しいURLが登録されていない
- ポート番号が一致していない（3000 vs 3001）

#### "access_denied"
- Gmail APIが有効化されていない
- 必要なスコープが設定されていない

### 設定確認方法

環境変数が正しく読み込まれているか確認：

```bash
# 開発サーバーのログを確認
# [next-auth][warn][NEXTAUTH_URL] や [next-auth][warn][NO_SECRET] 
# の警告が表示されなければ正常
```

## 📝 本番環境設定

本番環境では以下の点に注意：

1. **NEXTAUTH_URL** を本番URLに変更
2. **NEXTAUTH_SECRET** を本番用の安全な値に変更  
3. Google Cloud ConsoleのAuthorized redirect URIsに本番URLを追加
4. 環境変数を安全に管理（Vercel環境変数、AWS Systems Manager等）

## 🔗 参考リンク

- [NextAuth.js Documentation](https://next-auth.js.org/)
- [Google Cloud Console](https://console.cloud.google.com/)
- [Gmail API Documentation](https://developers.google.com/gmail/api)