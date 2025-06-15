"""
統合マッチングAPI

@description Firebaseデータベースと統合した集権化マッチングエンドポイント
@author InfuMatch Development Team
@version 2.0.0
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from services.centralized_matching_service import (
    centralized_matching_service,
    MatchingRequest,
    MatchingResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()


# リクエスト・レスポンスモデル
class CentralizedMatchingRequest(BaseModel):
    """統合マッチングリクエストモデル"""
    
    # 基本検索条件
    keyword: Optional[str] = Field(None, description="検索キーワード")
    category: Optional[str] = Field(None, description="カテゴリフィルタ")
    min_subscribers: Optional[int] = Field(None, description="最小登録者数")
    max_subscribers: Optional[int] = Field(None, description="最大登録者数")
    min_engagement_rate: Optional[float] = Field(None, description="最小エンゲージメント率")
    
    # AI推薦条件
    product_name: Optional[str] = Field(None, description="商品名")
    budget_min: Optional[int] = Field(None, description="最小予算")
    budget_max: Optional[int] = Field(None, description="最大予算")
    target_audience: List[str] = Field(default=[], description="ターゲット層")
    campaign_goals: Optional[str] = Field(None, description="キャンペーン目標")
    
    # マッチング設定
    use_ai_analysis: bool = Field(True, description="AI分析を使用するか")
    include_analytics: bool = Field(True, description="分析データを含めるか")
    max_results: int = Field(20, description="最大結果件数", ge=1, le=100)
    sort_by: str = Field("overall_score", description="ソート基準")
    
    # ユーザー設定
    user_preferences: Optional[Dict[str, Any]] = Field(None, description="ユーザー設定")


class CentralizedMatchingResponse(BaseModel):
    """統合マッチングレスポンスモデル"""
    
    success: bool
    results: List[Dict[str, Any]]
    ai_analysis: Optional[Dict[str, Any]] = None
    search_metadata: Optional[Dict[str, Any]] = None
    user_context: Optional[Dict[str, Any]] = None
    timestamp: str


@router.post("/api/v1/matching/execute", response_model=CentralizedMatchingResponse)
async def execute_centralized_matching(request: CentralizedMatchingRequest):
    """
    統合マッチング実行API
    
    Firebaseデータベースから実データを検索し、AI分析とユーザー設定を統合して
    最適なインフルエンサーマッチングを実行します。
    """
    try:
        logger.info(f"🎯 Received centralized matching request: {request.keyword}")
        
        # リクエストを内部形式に変換
        matching_request = MatchingRequest(
            keyword=request.keyword,
            category=request.category,
            min_subscribers=request.min_subscribers,
            max_subscribers=request.max_subscribers,
            min_engagement_rate=request.min_engagement_rate,
            product_name=request.product_name,
            budget_min=request.budget_min,
            budget_max=request.budget_max,
            target_audience=request.target_audience,
            campaign_goals=request.campaign_goals,
            use_ai_analysis=request.use_ai_analysis,
            include_analytics=request.include_analytics,
            max_results=request.max_results,
            sort_by=request.sort_by,
            user_preferences=request.user_preferences
        )
        
        # 統合マッチング実行
        response = await centralized_matching_service.execute_matching(matching_request)
        
        if not response.success:
            raise HTTPException(
                status_code=500, 
                detail=f"マッチング処理に失敗しました: {response.search_metadata.get('error', 'Unknown error')}"
            )
        
        return CentralizedMatchingResponse(
            success=response.success,
            results=response.results,
            ai_analysis=response.ai_analysis,
            search_metadata=response.search_metadata,
            user_context=response.user_context,
            timestamp=response.timestamp
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Centralized matching API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"統合マッチング処理中にエラーが発生しました: {str(e)}"
        )


@router.get("/api/v1/matching/real-time/{campaign_id}", response_model=CentralizedMatchingResponse)
async def get_real_time_matching(
    campaign_id: str,
    refresh_interval: int = Query(300, description="更新間隔（秒）", ge=60, le=3600)
):
    """
    リアルタイムマッチング更新API
    
    指定されたキャンペーンに対してリアルタイムでマッチング結果を更新します。
    """
    try:
        logger.info(f"🔄 Real-time matching request for campaign: {campaign_id}")
        
        response = await centralized_matching_service.get_real_time_recommendations(
            campaign_id=campaign_id,
            refresh_interval=refresh_interval
        )
        
        return CentralizedMatchingResponse(
            success=response.success,
            results=response.results,
            ai_analysis=response.ai_analysis,
            search_metadata=response.search_metadata,
            user_context=response.user_context,
            timestamp=response.timestamp
        )
        
    except Exception as e:
        logger.error(f"❌ Real-time matching API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"リアルタイムマッチング処理中にエラーが発生しました: {str(e)}"
        )


class OptimizationRequest(BaseModel):
    """最適化リクエストモデル"""
    
    existing_matches: List[Dict[str, Any]] = Field(..., description="既存のマッチ結果")
    optimization_goal: str = Field("balance", description="最適化目標")
    constraints: Optional[Dict[str, Any]] = Field(None, description="制約条件")


@router.post("/api/v1/matching/optimize", response_model=CentralizedMatchingResponse)
async def optimize_existing_matches(request: OptimizationRequest):
    """
    既存マッチの最適化API
    
    既存のマッチング結果を最適化して、よりバランスの取れた
    ポートフォリオを提案します。
    """
    try:
        logger.info(f"🔧 Optimizing {len(request.existing_matches)} existing matches")
        
        # 最適化処理（今後実装）
        # optimized_response = await centralized_matching_service.optimize_matches(request)
        
        # 現在はプレースホルダーレスポンス
        return CentralizedMatchingResponse(
            success=True,
            results=request.existing_matches,
            search_metadata={
                "message": "最適化機能は近日実装予定です",
                "optimization_goal": request.optimization_goal,
                "original_count": len(request.existing_matches)
            },
            timestamp="2025-06-14T16:42:00Z"
        )
        
    except Exception as e:
        logger.error(f"❌ Match optimization API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"マッチング最適化処理中にエラーが発生しました: {str(e)}"
        )


@router.get("/api/v1/matching/health", response_model=Dict[str, Any])
async def get_matching_service_health():
    """
    統合マッチングサービスのヘルスチェックAPI
    """
    try:
        health_status = await centralized_matching_service.health_check()
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return {
            "service": "CentralizedMatchingService",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2025-06-14T16:42:00Z"
        }


# 高度な検索エンドポイント（GET版）
@router.get("/api/v1/matching/search", response_model=CentralizedMatchingResponse)
async def advanced_search(
    keyword: Optional[str] = Query(None, description="検索キーワード"),
    category: Optional[str] = Query(None, description="カテゴリフィルタ"),
    min_subscribers: Optional[int] = Query(None, description="最小登録者数"),
    max_subscribers: Optional[int] = Query(None, description="最大登録者数"),
    min_engagement_rate: Optional[float] = Query(None, description="最小エンゲージメント率"),
    use_ai_analysis: bool = Query(True, description="AI分析を使用するか"),
    max_results: int = Query(20, description="最大結果件数", ge=1, le=100),
    sort_by: str = Query("overall_score", description="ソート基準")
):
    """
    高度なインフルエンサー検索API（GET版）
    
    Firebaseデータベースから実データを検索し、AI分析を含む高度な
    フィルタリングとスコアリングを実行します。
    """
    try:
        # リクエスト構築
        request = MatchingRequest(
            keyword=keyword,
            category=category,
            min_subscribers=min_subscribers,
            max_subscribers=max_subscribers,
            min_engagement_rate=min_engagement_rate,
            use_ai_analysis=use_ai_analysis,
            max_results=max_results,
            sort_by=sort_by
        )
        
        # マッチング実行
        response = await centralized_matching_service.execute_matching(request)
        
        return CentralizedMatchingResponse(
            success=response.success,
            results=response.results,
            ai_analysis=response.ai_analysis,
            search_metadata=response.search_metadata,
            user_context=response.user_context,
            timestamp=response.timestamp
        )
        
    except Exception as e:
        logger.error(f"❌ Advanced search API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"高度検索処理中にエラーが発生しました: {str(e)}"
        )


# 統計情報エンドポイント
@router.get("/api/v1/matching/stats", response_model=Dict[str, Any])
async def get_matching_statistics():
    """
    マッチング統計情報取得API
    
    データベース内のインフルエンサー統計とマッチング実績を取得します。
    """
    try:
        # データベースから基本統計を取得
        # 現在はプレースホルダー
        stats = {
            "total_influencers": 0,
            "categories": {},
            "subscriber_distribution": {},
            "engagement_rate_distribution": {},
            "recent_matches": 0,
            "ai_analysis_coverage": 0.0,
            "last_updated": "2025-06-14T16:42:00Z"
        }
        
        # 実際の統計データ取得（今後実装）
        # stats = await centralized_matching_service.get_statistics()
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Statistics API error: {e}")
        return {
            "error": str(e),
            "message": "統計情報の取得に失敗しました"
        }