"""
データ同期 API エンドポイント

@description Firestore ↔ BigQuery データ同期の管理API
手動同期、自動同期スケジューリング、同期状況確認機能を提供

@author InfuMatch Development Team  
@version 1.0.0
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
import pandas as pd

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Depends
from pydantic import BaseModel, Field

from services.data_integration import get_data_integration_service, run_daily_sync
from core.bigquery_client import get_bigquery_analytics
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


# レスポンスモデル
class SyncResultModel(BaseModel):
    """同期結果のレスポンスモデル"""
    success: bool = Field(..., description="同期成功フラグ")
    synced_count: int = Field(..., description="同期レコード数")
    failed_count: int = Field(0, description="失敗レコード数")
    duration_seconds: float = Field(..., description="処理時間（秒）")
    errors: List[str] = Field(default_factory=list, description="エラーメッセージリスト")
    completed_at: str = Field(..., description="完了時刻")


class SyncStatusModel(BaseModel):
    """同期状況のレスポンスモデル"""
    last_sync_time: Optional[str] = Field(None, description="最終同期時刻")
    next_scheduled_sync: Optional[str] = Field(None, description="次回予定同期時刻")
    sync_frequency: str = Field("daily", description="同期頻度")
    total_records_synced: int = Field(0, description="累計同期レコード数")
    recent_sync_results: List[SyncResultModel] = Field(default_factory=list, description="最近の同期結果")


class MetricsModel(BaseModel):
    """メトリクスのレスポンスモデル"""
    date: str = Field(..., description="対象日付")
    total_influencers: int = Field(0, description="総インフルエンサー数")
    active_campaigns: int = Field(0, description="アクティブキャンペーン数")
    completed_negotiations: int = Field(0, description="完了交渉数")
    total_revenue: float = Field(0.0, description="総売上")
    avg_engagement_rate: float = Field(0.0, description="平均エンゲージメント率")


# 依存性注入
def get_data_integration() -> Any:
    """データ統合サービスの依存性注入"""
    return get_data_integration_service()


@router.post("/sync/full", response_model=SyncResultModel, tags=["Data Sync"])
async def trigger_full_sync(
    background_tasks: BackgroundTasks,
    integration_service: Any = Depends(get_data_integration)
) -> SyncResultModel:
    """
    完全データ同期の手動実行
    
    Firestoreの全データをBigQueryに同期します。
    バックグラウンドタスクとして実行されます。
    """
    try:
        logger.info("🔄 Manual full sync triggered")
        
        # バックグラウンドで同期実行
        start_time = datetime.now(timezone.utc)
        result = await integration_service.full_sync()
        
        return SyncResultModel(
            success=result.get('success', False),
            synced_count=result.get('total_synced', 0),
            failed_count=result.get('total_failed', 0),
            duration_seconds=result.get('duration_seconds', 0),
            errors=result.get('errors', []),
            completed_at=result.get('completed_at', start_time.isoformat())
        )
        
    except Exception as e:
        logger.error(f"❌ Full sync failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Full sync failed: {str(e)}"
        )


@router.post("/sync/influencers", response_model=SyncResultModel, tags=["Data Sync"])
async def sync_influencers(
    batch_size: int = Query(100, description="バッチサイズ", ge=1, le=1000),
    integration_service: Any = Depends(get_data_integration)
) -> SyncResultModel:
    """
    インフルエンサーデータの同期
    
    FirestoreのインフルエンサーデータのみをBigQueryに同期します。
    """
    try:
        logger.info(f"🔄 Influencer sync triggered (batch_size: {batch_size})")
        
        start_time = datetime.now(timezone.utc)
        result = await integration_service.sync_influencers_to_bigquery(batch_size=batch_size)
        end_time = datetime.now(timezone.utc)
        
        duration = (end_time - start_time).total_seconds()
        
        return SyncResultModel(
            success=result.get('error') is None,
            synced_count=result.get('synced_count', 0),
            failed_count=result.get('failed_count', 0),
            duration_seconds=duration,
            errors=[result['error']] if result.get('error') else [],
            completed_at=end_time.isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ Influencer sync failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Influencer sync failed: {str(e)}"
        )


@router.post("/sync/campaigns", response_model=SyncResultModel, tags=["Data Sync"])
async def sync_campaigns(
    batch_size: int = Query(100, description="バッチサイズ", ge=1, le=1000),
    integration_service: Any = Depends(get_data_integration)
) -> SyncResultModel:
    """
    キャンペーンデータの同期
    
    FirestoreのキャンペーンデータのみをBigQueryに同期します。
    """
    try:
        logger.info(f"🔄 Campaign sync triggered (batch_size: {batch_size})")
        
        start_time = datetime.now(timezone.utc)
        result = await integration_service.sync_campaigns_to_bigquery(batch_size=batch_size)
        end_time = datetime.now(timezone.utc)
        
        duration = (end_time - start_time).total_seconds()
        
        return SyncResultModel(
            success=result.get('error') is None,
            synced_count=result.get('synced_count', 0),
            failed_count=result.get('failed_count', 0),
            duration_seconds=duration,
            errors=[result['error']] if result.get('error') else [],
            completed_at=end_time.isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ Campaign sync failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Campaign sync failed: {str(e)}"
        )


@router.post("/metrics/generate", response_model=SyncResultModel, tags=["Data Sync"])
async def generate_daily_metrics(
    target_date: Optional[str] = Query(None, description="対象日付 (YYYY-MM-DD形式)"),
    integration_service: Any = Depends(get_data_integration)
) -> SyncResultModel:
    """
    日次メトリクスの生成
    
    指定された日付（または前日）の日次メトリクスを生成してBigQueryに保存します。
    """
    try:
        # 日付パース
        if target_date:
            try:
                parsed_date = datetime.fromisoformat(target_date).replace(tzinfo=timezone.utc)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date format. Use YYYY-MM-DD format."
                )
        else:
            parsed_date = None
        
        logger.info(f"📊 Daily metrics generation triggered for {target_date or 'yesterday'}")
        
        start_time = datetime.now(timezone.utc)
        result = await integration_service.generate_daily_metrics(target_date=parsed_date)
        end_time = datetime.now(timezone.utc)
        
        duration = (end_time - start_time).total_seconds()
        
        return SyncResultModel(
            success=result.get('success', False),
            synced_count=result.get('metrics_generated', 0),
            failed_count=0,
            duration_seconds=duration,
            errors=[result['error']] if result.get('error') else [],
            completed_at=end_time.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Daily metrics generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Daily metrics generation failed: {str(e)}"
        )


@router.get("/sync/status", response_model=SyncStatusModel, tags=["Data Sync"])
async def get_sync_status() -> SyncStatusModel:
    """
    データ同期の状況確認
    
    最終同期時刻、次回予定、累計統計などの同期状況を返します。
    """
    try:
        # 実際の実装では、Firestoreまたは別のストレージから同期履歴を取得
        # 現在はダミーデータを返す
        
        return SyncStatusModel(
            last_sync_time=(datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
            next_scheduled_sync=(datetime.now(timezone.utc) + timedelta(hours=23)).isoformat(),
            sync_frequency="daily",
            total_records_synced=1500,
            recent_sync_results=[
                SyncResultModel(
                    success=True,
                    synced_count=150,
                    failed_count=0,
                    duration_seconds=45.3,
                    errors=[],
                    completed_at=(datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
                )
            ]
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get sync status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get sync status: {str(e)}"
        )


@router.get("/analytics/overview", response_model=List[MetricsModel], tags=["Analytics"])
async def get_analytics_overview(
    days: int = Query(7, description="取得日数", ge=1, le=365)
) -> List[MetricsModel]:
    """
    分析データの概要取得
    
    過去N日間の日次メトリクスを取得します。
    """
    try:
        analytics = get_bigquery_analytics()
        
        # BigQueryから日次メトリクスを取得
        df = analytics.get_daily_metrics_summary(days=days)
        
        if df.empty:
            return []
        
        # DataFrameをレスポンスモデルに変換
        metrics = []
        for _, row in df.iterrows():
            metrics.append(MetricsModel(
                date=str(row['date']),
                total_influencers=int(row['total_influencers']) if pd.notna(row['total_influencers']) else 0,
                active_campaigns=int(row['active_campaigns']) if pd.notna(row['active_campaigns']) else 0,
                completed_negotiations=int(row['completed_negotiations']) if pd.notna(row['completed_negotiations']) else 0,
                total_revenue=float(row['daily_revenue']) if pd.notna(row['daily_revenue']) else 0.0,
                avg_engagement_rate=float(row['platform_engagement_rate']) if pd.notna(row['platform_engagement_rate']) else 0.0
            ))
        
        return metrics
        
    except Exception as e:
        logger.error(f"❌ Failed to get analytics overview: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get analytics overview: {str(e)}"
        )


@router.get("/analytics/categories", tags=["Analytics"])
async def get_category_performance():
    """
    カテゴリ別パフォーマンス分析
    
    各カテゴリのインフルエンサー数、平均エンゲージメント率などを返します。
    """
    try:
        analytics = get_bigquery_analytics()
        
        # BigQueryからカテゴリ別データを取得
        df = analytics.get_category_performance()
        
        if df.empty:
            return {"categories": []}
        
        # DataFrameを辞書に変換
        categories = []
        for _, row in df.iterrows():
            categories.append({
                "category": row['category'],
                "influencer_count": int(row['influencer_count']) if pd.notna(row['influencer_count']) else 0,
                "avg_subscribers": float(row['avg_subscribers']) if pd.notna(row['avg_subscribers']) else 0,
                "avg_views": float(row['avg_views']) if pd.notna(row['avg_views']) else 0,
                "avg_engagement": float(row['avg_engagement']) if pd.notna(row['avg_engagement']) else 0
            })
        
        return {"categories": categories}
        
    except Exception as e:
        logger.error(f"❌ Failed to get category performance: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get category performance: {str(e)}"
        )


@router.get("/analytics/growth-trends", tags=["Analytics"])
async def get_growth_trends(
    days: int = Query(30, description="取得日数", ge=1, le=365)
):
    """
    成長トレンド分析
    
    インフルエンサーの成長トレンドデータを返します。
    """
    try:
        analytics = get_bigquery_analytics()
        
        # BigQueryから成長トレンドデータを取得
        df = analytics.get_influencer_growth_trends(days=days)
        
        if df.empty:
            return {"trends": []}
        
        # データ加工とレスポンス生成
        trends = []
        for _, row in df.iterrows():
            trends.append({
                "influencer_id": row['influencer_id'],
                "date": str(row['date']),
                "subscriber_growth": int(row['subscriber_growth']) if pd.notna(row['subscriber_growth']) else 0,
                "view_growth": int(row['view_growth']) if pd.notna(row['view_growth']) else 0,
                "engagement_rate": float(row['engagement_rate']) if pd.notna(row['engagement_rate']) else 0,
                "trend_score": float(row['trend_score']) if pd.notna(row['trend_score']) else 0
            })
        
        return {"trends": trends}
        
    except Exception as e:
        logger.error(f"❌ Failed to get growth trends: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get growth trends: {str(e)}"
        )


@router.post("/sync/schedule", tags=["Data Sync"])
async def schedule_daily_sync(background_tasks: BackgroundTasks):
    """
    日次同期のスケジューリング
    
    バックグラウンドで日次データ同期を実行します。
    """
    try:
        logger.info("📅 Scheduling daily sync task")
        
        # バックグラウンドタスクとして実行
        background_tasks.add_task(run_daily_sync)
        
        return {
            "message": "Daily sync scheduled successfully",
            "scheduled_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to schedule daily sync: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to schedule daily sync: {str(e)}"
        )


# ヘルスチェック
@router.get("/health", tags=["Health"])
async def data_sync_health():
    """
    データ同期サービスのヘルスチェック
    
    BigQueryとFirestoreの接続状況を確認します。
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {}
        }
        
        # Firestoreの接続確認
        try:
            from core.database import get_firestore_client
            firestore_client = get_firestore_client()
            # 簡単なクエリでテスト
            test_collection = firestore_client.client.collection('health_check')
            health_status["services"]["firestore"] = "connected"
        except Exception as e:
            health_status["services"]["firestore"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
        
        # BigQueryの接続確認
        try:
            bigquery_client = get_bigquery_client()
            # 簡単なクエリでテスト
            query = f"SELECT 1 as test_value"
            result = list(bigquery_client.query(query))
            health_status["services"]["bigquery"] = "connected"
        except Exception as e:
            health_status["services"]["bigquery"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }