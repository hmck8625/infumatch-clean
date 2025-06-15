# =============================================================================
# FastAPI バックエンド用 Dockerfile
# =============================================================================
# Cloud Run デプロイ用の最適化されたイメージ

FROM python:3.11-slim

# メタデータ
LABEL maintainer="InfuMatch Development Team"
LABEL description="InfuMatch Backend API"
LABEL version="1.0.0"

# 作業ディレクトリの設定
WORKDIR /app

# システムパッケージの更新とインストール
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python 依存関係のインストール
COPY backend/requirements-cloudrun.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-cloudrun.txt

# アプリケーションファイルのコピー
COPY backend/ .

# 非root ユーザーの作成
RUN useradd --create-home --shell /bin/bash app_user
RUN chown -R app_user:app_user /app
USER app_user

# ヘルスチェック用ポートの公開
EXPOSE 8000

# 環境変数の設定
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PORT=8000

# ヘルスチェック用にcurlとrequestsをインストール
RUN pip install --no-cache-dir requests

# ヘルスチェック（ルートエンドポイントを使用）
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

# アプリケーションの起動（simple_firestore_testを使用、ポート8001）
CMD ["python", "-m", "uvicorn", "simple_firestore_test:app", "--host", "0.0.0.0", "--port", "8000"]