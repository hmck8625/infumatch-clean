FROM python:3.11-slim

WORKDIR /app

# 必要最小限の依存関係をインストール
COPY requirements-cloudrun.txt .
RUN pip install --no-cache-dir -r requirements-cloudrun.txt

# アプリケーションファイルをコピー
COPY . .

# ポートを公開
EXPOSE 8000

# 環境変数を設定
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# アプリケーションを起動
CMD ["python", "-m", "uvicorn", "simple_firestore_test:app", "--host", "0.0.0.0", "--port", "8000"]