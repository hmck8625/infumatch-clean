# 🎯 YouTube Influencer Matching Agent

## 📋 プロジェクト概要

YouTubeのマイクロインフルエンサーと企業を自動でマッチングし、AI エージェントが交渉まで代行する革新的なプラットフォームです。

### 🎪 Google Cloud Japan AI Hackathon Vol.2 参加作品

- **開催期間**: 2025年4月14日～6月30日
- **テーマ**: 「AIエージェント、創造性の頂へ」
- **チーム**: InfuMatch Development Team

## 🏗️ システム構成

```
youtube-influencer-agent/
├── docs/                   # プロジェクト文書
├── frontend/               # Next.js フロントエンド
├── backend/               # FastAPI バックエンド
├── functions/             # Cloud Functions
├── infrastructure/        # インフラストラクチャ設定
└── scripts/              # 開発・デプロイスクリプト
```

## 🛠️ 技術スタック

### フロントエンド
- **Next.js 14** (App Router)
- **TypeScript**
- **Tailwind CSS**
- **shadcn/ui**
- **Vercel** (ホスティング)

### バックエンド
- **FastAPI** (Python)
- **Google Cloud Run**
- **Firestore** (NoSQL Database)
- **BigQuery** (分析用DB)

### AI/ML
- **Google Agentspace**
- **Vertex AI**
- **Gemini Pro API**

### その他Google Cloud サービス
- **Cloud Functions**
- **Cloud Scheduler**
- **Cloud Monitoring**
- **YouTube Data API v3**

## 🚀 クイックスタート

### 📋 前提条件

以下の開発ツールがインストールされていることを確認してください：

```bash
# Node.js v18以上
node --version

# Python 3.11以上  
python --version

# Google Cloud CLI
gcloud --version

# Docker (デプロイ用)
docker --version

# Terraform (インフラ構築用)
terraform --version
```

### 🛠️ セットアップ手順

#### 1. プロジェクトのクローン

```bash
git clone <このリポジトリのURL>
cd 250614_hac_iftool
```

#### 2. Google Cloud プロジェクトの設定

```bash
# Google Cloud にログイン
gcloud auth login

# プロジェクトを設定
gcloud config set project hackathon-462905

# アプリケーションデフォルト認証
gcloud auth application-default login
```

#### 3. インフラストラクチャの構築

```bash
# Terraform でインフラを構築
./deploy/scripts/setup-infrastructure.sh
```

#### 4. 環境変数の設定

```bash
# バックエンド用
cp .env.example .env
# 必要に応じて値を調整

# フロントエンド用
cd frontend
cp .env.local.example .env.local
# バックエンドURLを設定
```

#### 5. 開発環境の起動

```bash
# バックエンド起動
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# フロントエンド起動 (別ターミナル)
cd frontend
npm install
npm run dev
```

#### 6. Cloud Functions のデプロイ (オプション)

```bash
cd cloud_functions
./deploy.sh
```

### 🌐 アクセス URL

- **フロントエンド**: http://localhost:3000
- **バックエンド API**: http://localhost:8000
- **API ドキュメント**: http://localhost:8000/docs
- **管理画面**: http://localhost:8000/admin

## 📁 プロジェクト構造詳細

### フロントエンド (`/frontend`)

```
frontend/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # ルートレイアウト
│   ├── page.tsx           # ランディングページ
│   ├── dashboard/         # ダッシュボード機能
│   ├── campaigns/         # キャンペーン管理
│   └── api/              # API Routes (BFF層)
├── components/            # 再利用可能コンポーネント
│   ├── ui/               # shadcn/ui コンポーネント
│   ├── forms/            # フォームコンポーネント
│   └── layout/           # レイアウトコンポーネント
├── lib/                  # ユーティリティ関数
├── hooks/                # カスタムフック
└── types/                # TypeScript型定義
```

### バックエンド (`/backend`)

```
backend/
├── main.py               # FastAPI アプリケーションエントリポイント
├── core/                 # コア設定
│   ├── config.py        # 環境設定
│   ├── security.py      # セキュリティ設定
│   └── database.py      # データベース接続
├── api/                 # API エンドポイント
│   ├── v1/             # APIバージョン管理
│   ├── auth/           # 認証関連
│   ├── campaigns/      # キャンペーン管理
│   ├── influencers/    # インフルエンサー管理
│   └── negotiations/   # 交渉管理
├── services/           # ビジネスロジック
│   ├── youtube.py     # YouTube API連携
│   ├── ai_agents/     # AIエージェント群
│   └── email.py       # メール送信サービス
├── models/             # データモデル
└── tests/              # テストコード
```

### Cloud Functions (`/cloud_functions`)

```
cloud_functions/
├── main.py              # Cloud Functions エントリーポイント
├── requirements.txt     # Python依存関係
├── deploy.sh           # デプロイスクリプト
└── scheduler_config.yaml # Cloud Scheduler設定
```

### AI エージェント (`/backend/services/ai_agents`)

```
ai_agents/
├── base_agent.py        # AIエージェント基底クラス
├── preprocessor_agent.py # データ前処理エージェント
├── recommendation_agent.py # 推薦エージェント
└── negotiation_agent.py # 交渉エージェント
```

### デプロイメント (`/deploy`)

```
deploy/
├── docker/              # Docker設定
│   ├── backend.Dockerfile
│   └── frontend.Dockerfile
├── cloud_run/           # Cloud Run設定
├── terraform/           # Terraformコード
└── scripts/            # デプロイスクリプト
```

## 🔧 開発ガイド

### コーディング規約

- **Python**: PEP 8準拠、type hintsを必須
- **TypeScript**: Prettier + ESLint設定済み
- **コミット**: Conventional Commits形式

### ブランチ戦略

```
main          # 本番環境
├── develop   # 開発環境
├── feature/* # 機能開発
└── hotfix/*  # 緊急修正
```

### テスト戦略

```bash
# フロントエンド
npm run test          # Jest + Testing Library
npm run test:e2e      # Playwright

# バックエンド
pytest                # Unit tests
pytest --cov          # Coverage
```

## 🚢 デプロイメント

### 🏗️ インフラストラクチャ

```bash
# Terraform でGoogle Cloudインフラを構築
./deploy/scripts/setup-infrastructure.sh
```

### 🐳 バックエンドアプリケーション

```bash
# Cloud Run へデプロイ
./deploy/scripts/deploy-backend.sh
```

### ⚡ Cloud Functions

```bash
# 定期実行処理をデプロイ
cd cloud_functions
./deploy.sh
```

### 🌐 フロントエンド

```bash
# Vercel へデプロイ
cd frontend
npx vercel --prod
```

### 🔄 CI/CD パイプライン

GitHub Actions による自動デプロイが設定済み：

- **mainブランチ**: 本番環境への自動デプロイ
- **developブランチ**: ステージング環境への自動デプロイ
- **プルリクエスト**: 自動テスト実行

必要なGitHub Secrets：
- `WIF_PROVIDER`: Workload Identity Federation
- `WIF_SERVICE_ACCOUNT`: サービスアカウント
- `VERCEL_TOKEN`: Vercelデプロイトークン

## 📊 モニタリング

- **フロントエンド**: Vercel Analytics
- **バックエンド**: Cloud Monitoring
- **エラー追跡**: Cloud Error Reporting
- **ログ**: Cloud Logging

## 🤝 コントリビューション

1. Issueの作成
2. ブランチ作成 (`feature/your-feature`)
3. 実装とテスト
4. Pull Request作成

## 📜 ライセンス

MIT License - 詳細は[LICENSE](LICENSE)を参照

## 📞 サポート

- **Issues**: GitHub Issues
- **Discord**: [ハッカソン専用サーバー](https://discord.gg/cvA2Z3yny4)
- **Email**: team@infumatch.com

---

**作成日**: 2025-06-14  
**最終更新**: 2025-06-14  
**バージョン**: v0.1.0