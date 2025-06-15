"""
AI推薦エンドポイント

@description AIエージェントを使ったインフルエンサー推薦機能のAPI
@author InfuMatch Development Team
@version 1.0.0
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.ai_agents.recommendation_agent import RecommendationAgent
# from services.ai_agents.preprocessor_agent import DataPreprocessorAgent
from api.influencers import mock_influencers

logger = logging.getLogger(__name__)
router = APIRouter()

# リクエスト・レスポンスモデル
class CampaignRequest(BaseModel):
    product_name: str = Field(..., description="商品名")
    budget_min: int = Field(..., description="最小予算")
    budget_max: int = Field(..., description="最大予算")
    target_audience: List[str] = Field(..., description="ターゲット層")
    required_categories: List[str] = Field(..., description="必要カテゴリ")
    campaign_goals: str = Field(..., description="キャンペーン目標")
    min_engagement_rate: float = Field(default=2.0, description="最小エンゲージメント率")
    min_subscribers: int = Field(default=1000, description="最小登録者数")
    max_subscribers: int = Field(default=100000, description="最大登録者数")
    geographic_focus: Optional[str] = Field(default=None, description="地域フォーカス")

class AIRecommendationResponse(BaseModel):
    success: bool
    recommendations: List[Dict[str, Any]]
    ai_evaluation: Dict[str, Any]
    portfolio_optimization: Dict[str, Any]
    matching_summary: Dict[str, Any]
    agent: str
    timestamp: str

class SingleMatchRequest(BaseModel):
    influencer_id: str = Field(..., description="インフルエンサーID")
    campaign: CampaignRequest = Field(..., description="キャンペーン情報")

# エージェントインスタンス（起動時に初期化）
recommendation_agent = None

def initialize_agents():
    """AIエージェントの初期化"""
    global recommendation_agent
    try:
        recommendation_agent = RecommendationAgent()
        logger.info("✅ AI Agents initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize AI Agents: {e}")
        # 開発環境では継続、本番環境では例外を投げる
        recommendation_agent = None

@router.on_event("startup")
async def startup_event():
    """アプリケーション起動時のイベント"""
    initialize_agents()

@router.get("/api/v1/ai/recommendations", response_model=Dict[str, Any])
async def get_ai_recommendations(
    product_name: str = Query(..., description="商品名"),
    budget_min: int = Query(..., description="最小予算"),
    budget_max: int = Query(..., description="最大予算"),
    target_audience: str = Query(..., description="ターゲット層（カンマ区切り）"),
    required_categories: str = Query(..., description="必要カテゴリ（カンマ区切り）"),
    campaign_goals: str = Query(..., description="キャンペーン目標"),
    min_engagement_rate: float = Query(default=2.0, description="最小エンゲージメント率"),
    min_subscribers: int = Query(default=1000, description="最小登録者数"),
    max_subscribers: int = Query(default=100000, description="最大登録者数"),
    max_recommendations: int = Query(default=10, description="最大推薦数")
):
    """
    AI推薦エンドポイント（GET版）
    
    キャンペーン条件に基づいてAIがインフルエンサーを推薦
    """
    try:
        # パラメータの変換
        target_audience_list = [t.strip() for t in target_audience.split(",")]
        required_categories_list = [c.strip() for c in required_categories.split(",")]
        
        # キャンペーンデータの構築
        campaign_data = {
            "product_name": product_name,
            "budget_min": budget_min,
            "budget_max": budget_max,
            "target_audience": target_audience_list,
            "required_categories": required_categories_list,
            "campaign_goals": campaign_goals,
            "min_engagement_rate": min_engagement_rate,
            "min_subscribers": min_subscribers,
            "max_subscribers": max_subscribers
        }
        
        # AIエージェントが利用できない場合はルールベース推薦
        if recommendation_agent is None:
            return await fallback_recommendation(campaign_data, max_recommendations)
        
        # AI推薦の実行
        input_data = {
            "action": "recommend_influencers",
            "campaign": campaign_data,
            "influencers": [inf.__dict__ if hasattr(inf, '__dict__') else inf for inf in mock_influencers],
            "max_recommendations": max_recommendations
        }
        
        result = await recommendation_agent.process(input_data)
        
        if not result.get("success"):
            logger.warning(f"AI recommendation failed: {result.get('error')}")
            return await fallback_recommendation(campaign_data, max_recommendations)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ AI recommendation failed: {e}")
        raise HTTPException(status_code=500, detail=f"推薦処理に失敗しました: {str(e)}")

@router.post("/api/v1/ai/recommendations", response_model=Dict[str, Any])
async def post_ai_recommendations(request: CampaignRequest):
    """
    AI推薦エンドポイント（POST版）
    
    詳細なキャンペーン情報でAI推薦を実行
    """
    try:
        campaign_data = request.dict()
        
        # AIエージェントが利用できない場合はルールベース推薦
        if recommendation_agent is None:
            return await fallback_recommendation(campaign_data, 10)
        
        # AI推薦の実行
        input_data = {
            "action": "recommend_influencers",
            "campaign": campaign_data,
            "influencers": [inf.__dict__ if hasattr(inf, '__dict__') else inf for inf in mock_influencers],
            "max_recommendations": 10
        }
        
        result = await recommendation_agent.process(input_data)
        
        if not result.get("success"):
            logger.warning(f"AI recommendation failed: {result.get('error')}")
            return await fallback_recommendation(campaign_data, 10)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ AI recommendation failed: {e}")
        raise HTTPException(status_code=500, detail=f"推薦処理に失敗しました: {str(e)}")

@router.post("/api/v1/ai/match-evaluation", response_model=Dict[str, Any])
async def evaluate_single_match(request: SingleMatchRequest):
    """
    単一マッチ評価エンドポイント
    
    特定のインフルエンサーとキャンペーンの適合性を評価
    """
    try:
        # インフルエンサーデータを取得
        influencer_data = None
        for inf in mock_influencers:
            inf_dict = inf.__dict__ if hasattr(inf, '__dict__') else inf
            if inf_dict.get("id") == request.influencer_id:
                influencer_data = inf_dict
                break
        
        if not influencer_data:
            raise HTTPException(status_code=404, detail="指定されたインフルエンサーが見つかりません")
        
        campaign_data = request.campaign.dict()
        
        # AIエージェントが利用できない場合は簡易評価
        if recommendation_agent is None:
            return await fallback_match_evaluation(influencer_data, campaign_data)
        
        # AI評価の実行
        input_data = {
            "action": "evaluate_match",
            "influencer": influencer_data,
            "campaign": campaign_data
        }
        
        result = await recommendation_agent.process(input_data)
        
        if not result.get("success"):
            logger.warning(f"AI match evaluation failed: {result.get('error')}")
            return await fallback_match_evaluation(influencer_data, campaign_data)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Match evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=f"マッチ評価に失敗しました: {str(e)}")

@router.get("/api/v1/ai/agents/status")
async def get_agents_status():
    """
    AIエージェントのステータス確認
    """
    return {
        "agents": {
            "recommendation_agent": {
                "status": "ready" if recommendation_agent else "not_available",
                "capabilities": recommendation_agent.get_capabilities() if recommendation_agent else []
            }
        },
        "ai_integration": {
            "vertex_ai": "configured",
            "gemini_api": "available",
            "fallback_mode": recommendation_agent is None
        }
    }

async def fallback_recommendation(campaign_data: Dict[str, Any], max_recommendations: int) -> Dict[str, Any]:
    """
    AIが利用できない場合のフォールバック推薦
    """
    logger.info("🔄 Using fallback recommendation algorithm")
    
    try:
        # 基本フィルタリング
        filtered_influencers = []
        for inf in mock_influencers:
            inf_dict = inf.__dict__ if hasattr(inf, '__dict__') else inf
            
            # 登録者数フィルタ
            if not (campaign_data.get("min_subscribers", 0) <= inf_dict.get("subscriberCount", 0) <= campaign_data.get("max_subscribers", 100000)):
                continue
            
            # エンゲージメント率フィルタ
            if inf_dict.get("engagementRate", 0) < campaign_data.get("min_engagement_rate", 0):
                continue
            
            # カテゴリフィルタ
            required_categories = campaign_data.get("required_categories", [])
            if required_categories:
                inf_category = inf_dict.get("category", "")
                if inf_category not in required_categories:
                    continue
            
            # 簡易スコア計算
            score = calculate_simple_score(inf_dict, campaign_data)
            inf_dict["simple_score"] = score
            filtered_influencers.append(inf_dict)
        
        # スコア順でソート
        filtered_influencers.sort(key=lambda x: x.get("simple_score", 0), reverse=True)
        
        # トップN選択
        top_recommendations = filtered_influencers[:max_recommendations]
        
        # 推薦結果を作成
        recommendations = []
        for idx, inf in enumerate(top_recommendations):
            recommendations.append({
                "channel_id": inf.get("channelId", inf.get("id")),
                "overall_score": inf.get("simple_score", 0.5),
                "detailed_scores": {
                    "category_match": 0.8,
                    "engagement": min(inf.get("engagementRate", 0) / 10.0, 1.0),
                    "audience_fit": 0.7,
                    "budget_fit": 0.6,
                    "availability": 0.9,
                    "risk": 0.2
                },
                "explanation": f"ルールベース推薦による結果（エンゲージメント率: {inf.get('engagementRate')}%）",
                "rank": idx + 1
            })
        
        return {
            "success": True,
            "recommendations": recommendations,
            "ai_evaluation": {
                "recommendation_quality": "medium",
                "expected_roi": "中程度",
                "portfolio_balance": "ルールベース",
                "key_strengths": ["基本的なフィルタリング適用"],
                "concerns": ["AI分析なし"],
                "optimization_suggestions": ["AI機能の有効化を推奨"]
            },
            "portfolio_optimization": {
                "optimized_portfolio": recommendations[:5],
                "optimization_strategy": "rule_based",
                "diversity_score": 0.6
            },
            "matching_summary": {
                "total_candidates": len(mock_influencers),
                "filtered_candidates": len(filtered_influencers),
                "final_recommendations": len(recommendations),
                "criteria_used": campaign_data
            },
            "agent": "FallbackRecommendationSystem",
            "timestamp": "2025-06-14T16:42:00Z"
        }
        
    except Exception as e:
        logger.error(f"❌ Fallback recommendation failed: {e}")
        return {
            "success": False,
            "error": f"フォールバック推薦も失敗しました: {str(e)}",
            "agent": "FallbackRecommendationSystem"
        }

async def fallback_match_evaluation(influencer_data: Dict[str, Any], campaign_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    AIが利用できない場合のフォールバックマッチ評価
    """
    logger.info("🔄 Using fallback match evaluation")
    
    try:
        score = calculate_simple_score(influencer_data, campaign_data)
        
        return {
            "success": True,
            "match_evaluation": {
                "overall_compatibility": score,
                "detailed_scores": {
                    "category_match": 0.8,
                    "engagement": min(influencer_data.get("engagementRate", 0) / 10.0, 1.0),
                    "audience_fit": 0.7,
                    "budget_fit": 0.6,
                    "availability": 0.9,
                    "risk": 0.2
                },
                "match_grade": "Good" if score >= 0.6 else "Fair" if score >= 0.4 else "Poor",
                "explanation": "ルールベース評価による結果",
                "detailed_analysis": {
                    "synergy_potential": "medium",
                    "content_fit_analysis": "基本的な適合性を確認",
                    "audience_overlap_estimate": "中程度",
                    "collaboration_recommendations": ["詳細な事前協議を推奨"],
                    "success_probability": score,
                    "key_risks": ["AI分析なし"],
                    "optimization_opportunities": ["AI機能の有効化"]
                }
            },
            "agent": "FallbackMatchEvaluator",
            "timestamp": "2025-06-14T16:42:00Z"
        }
        
    except Exception as e:
        logger.error(f"❌ Fallback match evaluation failed: {e}")
        return {
            "success": False,
            "error": f"フォールバックマッチ評価も失敗しました: {str(e)}",
            "agent": "FallbackMatchEvaluator"
        }

def calculate_simple_score(influencer: Dict[str, Any], campaign: Dict[str, Any]) -> float:
    """
    簡易スコア計算（AIの代替）
    """
    score = 0.0
    
    # エンゲージメント率スコア (40%)
    engagement_rate = influencer.get("engagementRate", 0)
    score += min(engagement_rate / 10.0, 1.0) * 0.4
    
    # 登録者数適合性 (30%)
    subscriber_count = influencer.get("subscriberCount", 0)
    min_subs = campaign.get("min_subscribers", 1000)
    max_subs = campaign.get("max_subscribers", 100000)
    
    if min_subs <= subscriber_count <= max_subs:
        # 範囲内の場合、中央値に近いほど高スコア
        mid_point = (min_subs + max_subs) / 2
        distance_from_mid = abs(subscriber_count - mid_point) / (max_subs - min_subs)
        score += (1.0 - distance_from_mid) * 0.3
    
    # カテゴリマッチ (20%)
    required_categories = campaign.get("required_categories", [])
    inf_category = influencer.get("category", "")
    if not required_categories or inf_category in required_categories:
        score += 0.2
    
    # ベースライン (10%)
    score += 0.1
    
    return min(score, 1.0)