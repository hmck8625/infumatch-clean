"""
拡張版インフルエンサーAPI

@description YouTube API統合とAI分析機能を含む完全版API
アーキテクチャ設計書の要件に対応

@author InfuMatch Development Team
@version 2.0.0
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from services.youtube_api import YouTubeInfluencerService
from services.batch_processor import YouTubeBatchProcessor
from services.ai_analyzers import IntegratedAIAnalyzer
from core.config import get_settings
from core.database import FirestoreClient, DatabaseHelper, DatabaseCollections

logger = logging.getLogger(__name__)
settings = get_settings()

# APIルーター
router = APIRouter(prefix="/api/v2", tags=["influencers"])

# 依存関係
def get_youtube_service():
    return YouTubeInfluencerService()

def get_batch_processor():
    return YouTubeBatchProcessor()

def get_ai_analyzer():
    return IntegratedAIAnalyzer()

def get_db_helper():
    db_client = FirestoreClient()
    return DatabaseHelper(db_client)


# レスポンスモデル
class InfluencerResponse(BaseModel):
    """インフルエンサー情報レスポンス"""
    channel_id: str
    channel_name: str
    description: str
    subscriber_count: int
    video_count: int
    view_count: int
    engagement_rate: float
    thumbnail_url: Optional[str] = None
    country: Optional[str] = None
    
    # AI分析結果
    category_analysis: Optional[Dict[str, Any]] = None
    email_analysis: Optional[List[Dict[str, Any]]] = None
    trend_analysis: Optional[Dict[str, Any]] = None
    overall_score: Optional[Dict[str, Any]] = None
    
    # 連絡可能性
    has_business_email: bool = False
    contactability_score: float = 0.0
    
    # データ品質
    data_quality_score: float = 0.0
    last_analyzed: Optional[str] = None
    fetched_at: str


class SearchRequest(BaseModel):
    """検索リクエスト"""
    keyword: Optional[str] = Field(None, description="検索キーワード")
    category: Optional[str] = Field(None, description="カテゴリ")
    min_subscribers: Optional[int] = Field(1000, description="最小登録者数")
    max_subscribers: Optional[int] = Field(1000000, description="最大登録者数")
    min_engagement: Optional[float] = Field(0.0, description="最小エンゲージメント率")
    has_email: Optional[bool] = Field(None, description="メールアドレス有無")
    min_quality_score: Optional[float] = Field(0.0, description="最小品質スコア")
    sort_by: str = Field("engagement_rate", description="ソート項目")
    sort_order: str = Field("desc", description="ソート順")
    limit: int = Field(20, description="取得件数")
    offset: int = Field(0, description="オフセット")


class BatchRequest(BaseModel):
    """バッチ処理リクエスト"""
    categories: List[str] = Field(default=["beauty", "gaming", "cooking", "tech"])
    max_per_category: int = Field(50, description="カテゴリあたり最大取得数")
    subscriber_ranges: Optional[List[List[int]]] = Field(None, description="登録者数範囲")


class AnalysisResponse(BaseModel):
    """分析結果レスポンス"""
    channel_id: str
    analysis_timestamp: str
    category_analysis: Dict[str, Any]
    email_analysis: List[Dict[str, Any]]
    trend_analysis: Dict[str, Any]
    overall_score: Dict[str, Any]
    recommendation: str


# API エンドポイント

@router.get("/influencers/search")
async def search_influencers(
    request: SearchRequest = Depends(),
    db_helper: DatabaseHelper = Depends(get_db_helper)
) -> Dict[str, Any]:
    """
    高度なインフルエンサー検索
    
    データベースから条件に合致するインフルエンサーを検索
    """
    try:
        logger.info(f"🔍 Advanced influencer search: {request.keyword}")
        
        # クエリ条件構築
        conditions = []
        
        # 登録者数範囲
        if request.min_subscribers:
            conditions.append(('subscriber_count', '>=', request.min_subscribers))
        if request.max_subscribers:
            conditions.append(('subscriber_count', '<=', request.max_subscribers))
        
        # エンゲージメント率
        if request.min_engagement:
            conditions.append(('engagement_rate', '>=', request.min_engagement))
        
        # メールアドレス有無
        if request.has_email is not None:
            conditions.append(('has_business_email', '==', request.has_email))
        
        # 品質スコア
        if request.min_quality_score:
            conditions.append(('data_quality_score', '>=', request.min_quality_score))
        
        # アクティブ状態
        conditions.append(('status', '==', 'active'))
        
        # データベース検索実行
        results = await db_helper.query_documents(
            collection=DatabaseCollections.INFLUENCERS,
            conditions=conditions,
            limit=request.limit + request.offset,  # オフセット考慮
            order_by=(request.sort_by, request.sort_order)
        )
        
        # キーワード検索（インメモリフィルタ）
        if request.keyword:
            keyword_lower = request.keyword.lower()
            filtered_results = []
            for result in results:
                if (keyword_lower in result.get('channel_name', '').lower() or
                    keyword_lower in result.get('description', '').lower()):
                    filtered_results.append(result)
            results = filtered_results
        
        # カテゴリフィルタ
        if request.category and request.category != "all":
            results = [
                r for r in results 
                if r.get('category_analysis', {}).get('main_category') == request.category
            ]
        
        # ページング
        total_count = len(results)
        paginated_results = results[request.offset:request.offset + request.limit]
        
        return {
            "results": paginated_results,
            "total_count": total_count,
            "page_info": {
                "limit": request.limit,
                "offset": request.offset,
                "has_next": request.offset + request.limit < total_count
            },
            "search_params": request.dict()
        }
        
    except Exception as e:
        logger.error(f"❌ Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/influencers/{channel_id}")
async def get_influencer_detail(
    channel_id: str,
    include_analysis: bool = Query(True, description="AI分析結果を含める"),
    db_helper: DatabaseHelper = Depends(get_db_helper)
) -> InfluencerResponse:
    """
    インフルエンサー詳細情報取得
    """
    try:
        logger.info(f"📊 Getting influencer details: {channel_id}")
        
        # データベースから取得
        influencer = await db_helper.get_document(
            collection=DatabaseCollections.INFLUENCERS,
            document_id=channel_id
        )
        
        if not influencer:
            raise HTTPException(status_code=404, detail="Influencer not found")
        
        # AI分析結果を除外する場合
        if not include_analysis:
            for key in ['category_analysis', 'email_analysis', 'trend_analysis', 'overall_score']:
                influencer.pop(key, None)
        
        return InfluencerResponse(**influencer)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get influencer details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/influencers/discover")
async def discover_new_influencers(
    search_queries: List[str],
    background_tasks: BackgroundTasks,
    min_subscribers: int = Query(1000, description="最小登録者数"),
    max_subscribers: int = Query(100000, description="最大登録者数"),
    max_per_query: int = Query(20, description="クエリあたり最大取得数"),
    youtube_service: YouTubeInfluencerService = Depends(get_youtube_service)
) -> Dict[str, Any]:
    """
    新規インフルエンサー発見
    
    YouTube API を使用してリアルタイムでインフルエンサーを発見
    """
    try:
        logger.info(f"🔍 Discovering influencers for queries: {search_queries}")
        
        # インフルエンサー発見を実行
        discovered = await youtube_service.discover_influencers(
            search_queries=search_queries,
            subscriber_min=min_subscribers,
            subscriber_max=max_subscribers,
            max_per_query=max_per_query
        )
        
        # バックグラウンドでデータベース保存
        if discovered:
            background_tasks.add_task(
                youtube_service.save_influencers_to_db,
                discovered
            )
        
        return {
            "discovered_count": len(discovered),
            "influencers": discovered[:10],  # プレビューとして最初の10件
            "status": "discovery_completed",
            "message": f"{len(discovered)}件のインフルエンサーを発見しました"
        }
        
    except Exception as e:
        logger.error(f"❌ Discovery failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/influencers/batch-discovery")
async def batch_discover_influencers(
    request: BatchRequest,
    background_tasks: BackgroundTasks,
    batch_processor: YouTubeBatchProcessor = Depends(get_batch_processor)
) -> Dict[str, Any]:
    """
    大規模バッチインフルエンサー発見
    
    複数カテゴリでの大規模データ収集
    """
    try:
        logger.info(f"🚀 Starting batch discovery for categories: {request.categories}")
        
        # バックグラウンドでバッチ処理実行
        background_tasks.add_task(
            _run_batch_discovery,
            batch_processor,
            request.categories,
            request.subscriber_ranges,
            request.max_per_category
        )
        
        return {
            "status": "batch_started",
            "categories": request.categories,
            "estimated_duration_minutes": len(request.categories) * 5,
            "message": "バッチ処理を開始しました。完了まで数分お待ちください。"
        }
        
    except Exception as e:
        logger.error(f"❌ Batch discovery failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/influencers/{channel_id}/analyze")
async def analyze_influencer(
    channel_id: str,
    force_refresh: bool = Query(False, description="強制再分析"),
    ai_analyzer: IntegratedAIAnalyzer = Depends(get_ai_analyzer),
    db_helper: DatabaseHelper = Depends(get_db_helper)
) -> AnalysisResponse:
    """
    インフルエンサーのAI分析実行
    """
    try:
        logger.info(f"🤖 Analyzing influencer: {channel_id}")
        
        # 既存データ取得
        influencer = await db_helper.get_document(
            collection=DatabaseCollections.INFLUENCERS,
            document_id=channel_id
        )
        
        if not influencer:
            raise HTTPException(status_code=404, detail="Influencer not found")
        
        # 分析済みかチェック（強制再分析でない場合）
        if not force_refresh and influencer.get('category_analysis'):
            last_analyzed = influencer.get('last_analyzed')
            if last_analyzed:
                # 1週間以内に分析済みの場合はスキップ
                analyzed_date = datetime.fromisoformat(last_analyzed.replace('Z', '+00:00'))
                if (datetime.utcnow() - analyzed_date.replace(tzinfo=None)).days < 7:
                    return AnalysisResponse(
                        channel_id=channel_id,
                        analysis_timestamp=last_analyzed,
                        category_analysis=influencer.get('category_analysis', {}),
                        email_analysis=influencer.get('email_analysis', []),
                        trend_analysis=influencer.get('trend_analysis', {}),
                        overall_score=influencer.get('overall_score', {}),
                        recommendation=influencer.get('recommendation', '')
                    )
        
        # AI分析実行
        analysis_result = await ai_analyzer.comprehensive_analysis(influencer)
        
        # 結果をデータベースに保存
        update_data = {
            'category_analysis': analysis_result.get('category_analysis'),
            'email_analysis': analysis_result.get('email_analysis'),
            'trend_analysis': analysis_result.get('trend_analysis'),
            'overall_score': analysis_result.get('overall_score'),
            'recommendation': analysis_result.get('recommendation'),
            'last_analyzed': analysis_result.get('analysis_timestamp')
        }
        
        await db_helper.update_document(
            collection=DatabaseCollections.INFLUENCERS,
            document_id=channel_id,
            data=update_data
        )
        
        return AnalysisResponse(**analysis_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/trending")
async def get_trending_analytics(
    region: str = Query("JP", description="地域コード"),
    max_results: int = Query(50, description="最大取得数"),
    batch_processor: YouTubeBatchProcessor = Depends(get_batch_processor)
) -> Dict[str, Any]:
    """
    トレンド分析取得
    """
    try:
        logger.info(f"📈 Getting trending analytics for {region}")
        
        result = await batch_processor.analyze_trending_channels(
            region=region,
            max_results=max_results
        )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Trending analytics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/categories")
async def get_category_distribution(
    db_helper: DatabaseHelper = Depends(get_db_helper)
) -> Dict[str, Any]:
    """
    カテゴリ分布分析
    """
    try:
        logger.info("📊 Getting category distribution")
        
        # 全インフルエンサーを取得
        all_influencers = await db_helper.query_documents(
            collection=DatabaseCollections.INFLUENCERS,
            conditions=[('status', '==', 'active')],
            limit=1000
        )
        
        # カテゴリ分布計算
        category_stats = {}
        total_count = len(all_influencers)
        
        for influencer in all_influencers:
            category_analysis = influencer.get('category_analysis', {})
            main_category = category_analysis.get('main_category', 'unknown')
            
            if main_category not in category_stats:
                category_stats[main_category] = {
                    'count': 0,
                    'avg_subscribers': 0,
                    'avg_engagement': 0,
                    'total_subscribers': 0,
                    'total_engagement': 0
                }
            
            stats = category_stats[main_category]
            stats['count'] += 1
            stats['total_subscribers'] += influencer.get('subscriber_count', 0)
            stats['total_engagement'] += influencer.get('engagement_rate', 0)
        
        # 平均値計算
        for category, stats in category_stats.items():
            if stats['count'] > 0:
                stats['avg_subscribers'] = stats['total_subscribers'] // stats['count']
                stats['avg_engagement'] = round(stats['total_engagement'] / stats['count'], 2)
                stats['percentage'] = round((stats['count'] / total_count) * 100, 1)
        
        return {
            'total_influencers': total_count,
            'category_distribution': category_stats,
            'analysis_date': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Category distribution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/maintenance/update-analytics")
async def update_influencer_analytics(
    background_tasks: BackgroundTasks,
    batch_size: int = Query(50, description="バッチサイズ"),
    days_since_update: int = Query(7, description="更新対象日数"),
    batch_processor: YouTubeBatchProcessor = Depends(get_batch_processor)
) -> Dict[str, Any]:
    """
    インフルエンサー分析データの一括更新
    """
    try:
        logger.info("🔄 Starting analytics update")
        
        # バックグラウンドで更新実行
        background_tasks.add_task(
            batch_processor.update_existing_influencers,
            batch_size,
            days_since_update
        )
        
        return {
            "status": "update_started",
            "batch_size": batch_size,
            "days_since_update": days_since_update,
            "message": "分析データの更新を開始しました"
        }
        
    except Exception as e:
        logger.error(f"❌ Analytics update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# バックグラウンドタスク関数

async def _run_batch_discovery(
    batch_processor: YouTubeBatchProcessor,
    categories: List[str],
    subscriber_ranges: Optional[List[List[int]]],
    max_per_category: int
):
    """バッチ発見のバックグラウンド実行"""
    try:
        # subscriber_ranges の変換
        ranges = None
        if subscriber_ranges:
            ranges = [(r[0], r[1]) for r in subscriber_ranges]
        
        result = await batch_processor.discover_influencers_batch(
            categories=categories,
            subscriber_ranges=ranges,
            max_per_category=max_per_category
        )
        
        logger.info(f"✅ Batch discovery completed: {result}")
        
    except Exception as e:
        logger.error(f"❌ Background batch discovery failed: {e}")


# ヘルスチェック
@router.get("/health")
async def health_check():
    """APIヘルスチェック"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0"
    }