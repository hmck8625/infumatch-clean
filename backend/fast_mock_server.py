#!/usr/bin/env python3
"""
Fast Mock API Server for Testing Frontend Connection
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Fast Mock API")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Fast Mock API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": "2025-06-15T10:17:00Z"}

@app.get("/api/v1/influencers")
async def get_mock_influencers():
    """Mock influencers data for quick testing"""
    return [
        {
            "id": "UC1234567890",
            "name": "Fast Mock - Tech Review Japan",
            "channelId": "UC1234567890",
            "subscriberCount": 8500,
            "viewCount": 1250000,
            "videoCount": 156,
            "category": "テクノロジー",
            "description": "Mock data - 最新のガジェットレビューと技術解説を行うチャンネル",
            "thumbnailUrl": "https://via.placeholder.com/120x120",
            "engagementRate": 4.5,
            "email": "mock@example.com"
        },
        {
            "id": "UC2345678901",
            "name": "Fast Mock - 料理研究家ゆうこ",
            "channelId": "UC2345678901",
            "subscriberCount": 5200,
            "viewCount": 890000,
            "videoCount": 243,
            "category": "料理",
            "description": "Mock data - 簡単で美味しい家庭料理のレシピを紹介",
            "thumbnailUrl": "https://via.placeholder.com/120x120",
            "engagementRate": 5.2,
            "email": "mock2@example.com"
        },
        {
            "id": "UC3456789012",
            "name": "Fast Mock - Fitness Life Tokyo",
            "channelId": "UC3456789012",
            "subscriberCount": 3800,
            "viewCount": 567000,
            "videoCount": 89,
            "category": "フィットネス",
            "description": "Mock data - 自宅でできるトレーニングとヘルシーライフスタイル",
            "thumbnailUrl": "https://via.placeholder.com/120x120",
            "engagementRate": 6.1,
            "email": "mock3@example.com"
        }
    ]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)