# Firebase 設定デバッグ手順

## ブラウザ開発者ツールで確認

### 1. コンソールエラーをチェック
- F12 → Console タブ
- Firebase関連のエラーメッセージを確認

### 2. ネットワークタブで確認  
- F12 → Network タブ
- 「設定を保存」クリック時のAPIリクエストを確認

### 3. よくあるエラーと対処法

#### Firebase APIキーエラー
```
Firebase: Error (auth/invalid-api-key)
```
**対処**: Vercelの環境変数でAPIキーを再確認

#### 認証エラー
```
Firebase: Error (auth/unauthorized-domain)
```  
**対処**: Firebase Console → Authentication → Settings → Authorized domains に `infumatch-clean.vercel.app` を追加

#### Firestoreルールエラー
```
FirebaseError: Missing or insufficient permissions
```
**対処**: Firestore → Rules で認証済みユーザーの読み書きを許可

## Firebase Console での確認

### 1. Firestore Database
- Firebase Console → Firestore Database
- `user_settings` コレクションにデータが保存されているか確認

### 2. Authentication
- Firebase Console → Authentication → Users
- ログインしたユーザーが表示されているか確認

### 3. 設定値の再確認
- プロジェクト設定 → 全般 → SDK設定
- Vercelの環境変数と一致しているか確認