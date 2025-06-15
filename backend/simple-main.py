"""
超シンプル版 FastAPI アプリケーション
Python 3.13対応版
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from api.influencers import router as influencers_router

# FastAPIアプリケーション作成
app = FastAPI(
    title="YouTube Influencer Matching Agent API",
    description="YouTubeマイクロインフルエンサーマッチングプラットフォーム",
    version="1.0.0",
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "YouTube Influencer Matching Agent API",
        "version": "1.0.0",
        "status": "operational",
        "docs_url": "/docs"
    }

@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "healthy"}

@app.get("/api/v1/test")
async def test_endpoint():
    """テスト用エンドポイント"""
    return {
        "message": "API is working!",
        "features": [
            "インフルエンサー検索",
            "AIマッチング",
            "自動交渉"
        ]
    }

# ルーターを追加
app.include_router(influencers_router)

if __name__ == "__main__":
    uvicorn.run(
        "simple-main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )