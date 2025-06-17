# Google Cloud Run用の軽量Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 依存関係のインストール
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルのコピー
COPY main.py .
# COPY services/ ./services/

# ポートの設定
EXPOSE 8000

# 環境変数の設定
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

# アプリケーションの起動
CMD uvicorn main:app --host 0.0.0.0 --port $PORT