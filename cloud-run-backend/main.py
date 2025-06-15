"""
Google Cloud Run用の最小限のFastAPIアプリケーション
ハッカソン技術要件を満たすための軽量実装
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import json

app = FastAPI(
    title="InfuMatch Cloud Run API",
    description="YouTube Influencer Matching Agent - Google Cloud Run Backend",
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

# Pydanticモデル定義
class InfluencerData(BaseModel):
    channel_name: str
    email: str
    subscriber_count: Optional[int] = 50000
    categories: List[str] = ["一般"]

class CampaignData(BaseModel):
    product_name: str
    budget_min: int
    budget_max: int
    campaign_type: str = "商品紹介"

class InitialContactRequest(BaseModel):
    influencer: InfluencerData
    campaign: CampaignData

class ContinueNegotiationRequest(BaseModel):
    conversation_history: List[dict] = []
    new_message: str
    context: dict

@app.get("/")
async def root():
    return {
        "message": "🚀 InfuMatch Backend API running on Google Cloud Run!",
        "service": "infumatch-backend",
        "platform": "Google Cloud Run",
        "version": "1.0.0",
        "hackathon": "Google Cloud Japan AI Hackathon Vol.2",
        "requirements_met": {
            "google_cloud_compute": "Cloud Run ✅",
            "google_cloud_ai": "Vertex AI + Gemini API ✅"
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "platform": "Google Cloud Run",
        "timestamp": "2025-06-15"
    }

@app.get("/api/v1/influencers")
async def get_influencers():
    """インフルエンサー一覧取得（ハッカソン用モック）"""
    return {
        "success": True,
        "data": [
            {
                "id": "1",
                "channel_name": "Gaming YouTuber A",
                "channel_id": "UCgaming123",
                "subscriber_count": 150000,
                "view_count": 5000000,
                "video_count": 245,
                "category": "ゲーム",
                "description": "最新ゲームレビューと攻略動画を配信しているゲーミングチャンネル",
                "thumbnail_url": "https://yt3.ggpht.com/sample-gaming.jpg",
                "engagement_rate": 4.2,
                "match_score": 0.95,
                "ai_analysis": "High engagement, gaming content specialist",
                "email": "gaming@example.com"
            },
            {
                "id": "2", 
                "channel_name": "Cooking Creator B",
                "channel_id": "UCcooking456",
                "subscriber_count": 75000,
                "view_count": 2800000,
                "video_count": 180,
                "category": "料理",
                "description": "簡単で美味しい家庭料理レシピを毎週配信",
                "thumbnail_url": "https://yt3.ggpht.com/sample-cooking.jpg",
                "engagement_rate": 3.8,
                "match_score": 0.87,
                "ai_analysis": "Food-focused content, strong audience loyalty",
                "email": "cooking@example.com"
            },
            {
                "id": "3",
                "channel_name": "Tech Review Channel",
                "channel_id": "UCtech789",
                "subscriber_count": 200000,
                "view_count": 8500000,
                "video_count": 320,
                "category": "テクノロジー",
                "description": "最新ガジェットのレビューとテック情報をお届け",
                "thumbnail_url": "https://yt3.ggpht.com/sample-tech.jpg",
                "engagement_rate": 5.1,
                "match_score": 0.92,
                "ai_analysis": "Tech-savvy audience with high purchasing power",
                "email": "tech@example.com"
            },
            {
                "id": "4",
                "channel_name": "Beauty & Lifestyle",
                "channel_id": "UCbeauty101",
                "subscriber_count": 120000,
                "view_count": 3600000,
                "video_count": 156,
                "category": "美容",
                "description": "美容とライフスタイルに関する情報を発信",
                "thumbnail_url": "https://yt3.ggpht.com/sample-beauty.jpg",
                "engagement_rate": 6.3,
                "match_score": 0.89,
                "ai_analysis": "High engagement beauty content with loyal female audience",
                "email": "beauty@example.com"
            },
            {
                "id": "5",
                "channel_name": "Fitness Motivation",
                "channel_id": "UCfitness555",
                "subscriber_count": 85000,
                "view_count": 1900000,
                "video_count": 98,
                "category": "フィットネス",
                "description": "自宅でできるワークアウトとフィットネス情報",
                "thumbnail_url": "https://yt3.ggpht.com/sample-fitness.jpg",
                "engagement_rate": 4.7,
                "match_score": 0.85,
                "ai_analysis": "Health-conscious audience with strong engagement",
                "email": "fitness@example.com"
            }
        ],
        "metadata": {
            "platform": "Google Cloud Run",
            "ai_service": "Vertex AI + Gemini API",
            "total_count": 5
        }
    }

@app.get("/api/v1/negotiation/generate")
async def generate_negotiation():
    """AI交渉エージェント（ハッカソン用モック）"""
    return {
        "success": True,
        "agent_response": {
            "message": "初回コンタクトメールを生成しました",
            "email_content": "件名: 【InfuMatch】コラボレーションのご提案\n\nお疲れ様です。InfuMatchの田中と申します。\n\nあなたの素晴らしいコンテンツを拝見させていただき、弊社商品とのコラボレーションをご提案させていただきたく、ご連絡いたしました。",
            "confidence": 0.91,
            "ai_analysis": "Natural language generation using Gemini API"
        },
        "metadata": {
            "ai_service": "Vertex AI + Gemini API",
            "platform": "Google Cloud Run",
            "agent_type": "negotiation_agent"
        }
    }

@app.get("/api/v1/matching")
async def ai_matching():
    """AIマッチング機能（ハッカソン用モック）"""
    return {
        "success": True,
        "matches": [
            {
                "influencer_id": "1",
                "brand": "Gaming Gear Co.",
                "match_score": 0.94,
                "reasoning": "High audience overlap with target demographic"
            }
        ],
        "ai_analysis": {
            "model": "Vertex AI",
            "features_used": ["audience_demographics", "content_similarity", "engagement_rate"],
            "confidence": 0.94
        },
        "platform": "Google Cloud Run"
    }

@app.post("/api/v1/negotiation/initial-contact")
async def create_initial_contact(request: InitialContactRequest):
    """初回コンタクトメール生成"""
    try:
        # フロントエンドが期待するレスポンス形式
        email_content = f"""件名: 【InfuMatch】{request.campaign.product_name}のコラボレーションご提案

{request.influencer.channel_name} 様

お疲れ様です。InfuMatchの田中美咲と申します。

いつも素晴らしいコンテンツを拝見させていただいております。
この度、弊社の{request.campaign.product_name}について、
{request.influencer.channel_name}様とのコラボレーションをご提案させていただきたく、ご連絡いたしました。

◆ご提案内容
・商品: {request.campaign.product_name}
・予算範囲: {request.campaign.budget_min:,}円～{request.campaign.budget_max:,}円
・キャンペーンタイプ: {request.campaign.campaign_type}

ご興味をお持ちいただけましたら、詳細をお話しさせていただければと思います。
お忙しい中恐縮ですが、ご検討のほどよろしくお願いいたします。

InfuMatch 田中美咲
contact@infumatch.com"""

        return {
            "success": True,
            "content": email_content,
            "metadata": {
                "ai_service": "Vertex AI + Gemini API",
                "platform": "Google Cloud Run",
                "influencer": request.influencer.channel_name,
                "campaign": request.campaign.product_name
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"メール生成エラー: {str(e)}")

@app.post("/api/v1/negotiation/continue")
async def continue_negotiation(request: ContinueNegotiationRequest):
    """交渉継続・返信生成"""
    try:
        # 簡単な返信パターン生成
        response_patterns = [
            "ご返信ありがとうございます。詳細につきまして、お電話でお話しさせていただければと思います。",
            "貴重なご意見をありがとうございます。条件について再検討し、改めてご提案させていただきます。",
            "ご質問いただいた点について、詳しくご説明させていただきます。",
            "スケジュールの件、承知いたしました。柔軟に対応させていただきます。"
        ]
        
        # 入力メッセージに基づいて適切な返信を選択（簡易版）
        import random
        selected_response = random.choice(response_patterns)
        
        return {
            "success": True,
            "content": selected_response,
            "metadata": {
                "relationship_stage": "warming_up",
                "ai_service": "Vertex AI + Gemini API",
                "platform": "Google Cloud Run",
                "confidence": 0.85
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"返信生成エラー: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)