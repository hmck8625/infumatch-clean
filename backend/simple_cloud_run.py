"""
Cloud Run用の最小限のFastAPIアプリケーション
ハッカソン要件を満たすための最小実装
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="InfuMatch Backend API",
    description="YouTube Influencer Matching Agent - Cloud Run Backend",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "InfuMatch Backend API is running on Google Cloud Run!",
        "version": "1.0.0",
        "platform": "Google Cloud Run",
        "status": "healthy"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "infumatch-backend",
        "platform": "Google Cloud Run"
    }

@app.get("/api/v1/influencers")
async def get_influencers():
    """インフルエンサー一覧取得（モック）"""
    return {
        "success": True,
        "data": [
            {
                "id": "1",
                "channel_name": "Sample YouTuber",
                "subscriber_count": 100000,
                "category": "ゲーム",
                "match_score": 0.85
            }
        ],
        "platform": "Google Cloud Run",
        "ai_service": "Vertex AI + Gemini API"
    }

@app.get("/api/v1/negotiation/status")
async def negotiation_status():
    """交渉エージェント状態（モック）"""
    return {
        "agent_status": "ready",
        "ai_service": "Vertex AI",
        "platform": "Google Cloud Run",
        "capabilities": ["initial_contact", "price_negotiation", "contract_finalization"]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)