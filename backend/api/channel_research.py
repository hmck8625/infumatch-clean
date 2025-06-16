#!/usr/bin/env python3
"""
チャンネル調査API

@description YouTubeチャンネルのWeb検索ベース調査機能を提供
@author InfuMatch Development Team
@version 1.0.0
"""

import asyncio
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from services.channel_research_service import ChannelResearchService

router = APIRouter(prefix="/api/channel-research", tags=["Channel Research"])

# リクエスト・レスポンスモデル
class ChannelResearchRequest(BaseModel):
    """チャンネル調査リクエスト"""
    channel_id: str = Field(..., description="YouTube チャンネルID")
    channel_title: str = Field(..., description="チャンネル名")
    channel_data: Dict[str, Any] = Field(default_factory=dict, description="追加チャンネル情報")
    research_categories: list[str] = Field(
        default=["basic_info", "reputation", "collaboration", "market_analysis"],
        description="調査カテゴリ"
    )

class ChannelResearchResponse(BaseModel):
    """チャンネル調査レスポンス"""
    success: bool
    channel_id: str
    channel_name: str
    research_timestamp: str
    basic_info: Dict[str, Any]
    reputation_safety: Dict[str, Any]
    collaboration_history: Dict[str, Any]
    market_analysis: Dict[str, Any]
    research_confidence: float
    summary: str
    message: str = "チャンネル調査が正常に完了しました"

class ResearchStatusResponse(BaseModel):
    """調査ステータスレスポンス"""
    success: bool
    status: str  # "pending", "in_progress", "completed", "failed"
    progress: int = 0  # 0-100
    message: str = ""

# 調査サービスのインスタンス
research_service = ChannelResearchService()

# 進行中の調査を管理する辞書（本番環境ではRedisなどを使用）
research_status: Dict[str, Dict[str, Any]] = {}

@router.post("/research", response_model=ChannelResearchResponse)
async def research_channel(
    request: ChannelResearchRequest,
    background_tasks: BackgroundTasks
):
    """
    チャンネルの包括的調査を実行
    
    Args:
        request: チャンネル調査リクエスト
        background_tasks: バックグラウンドタスク管理
        
    Returns:
        ChannelResearchResponse: 調査結果
    """
    try:
        print(f"🔍 チャンネル調査リクエスト受信: {request.channel_title}")
        
        # 調査ステータスを初期化
        research_key = f"{request.channel_id}_{int(asyncio.get_event_loop().time())}"
        research_status[research_key] = {
            "status": "in_progress",
            "progress": 0,
            "start_time": asyncio.get_event_loop().time()
        }
        
        # チャンネルデータの準備
        channel_data = {
            "channel_id": request.channel_id,
            "channel_title": request.channel_title,
            **request.channel_data
        }
        
        # 包括的調査の実行
        research_result = await research_service.research_channel_comprehensive(channel_data)
        
        # ステータス更新
        research_status[research_key] = {
            "status": "completed",
            "progress": 100,
            "end_time": asyncio.get_event_loop().time()
        }
        
        # レスポンス作成
        response = ChannelResearchResponse(
            success=True,
            channel_id=research_result["channel_id"],
            channel_name=research_result["channel_name"],
            research_timestamp=research_result["research_timestamp"],
            basic_info=research_result["basic_info"],
            reputation_safety=research_result["reputation_safety"],
            collaboration_history=research_result["collaboration_history"],
            market_analysis=research_result["market_analysis"],
            research_confidence=research_result["research_confidence"],
            summary=research_result["summary"]
        )
        
        print(f"✅ チャンネル調査完了: {request.channel_title}")
        return response
        
    except Exception as e:
        print(f"❌ チャンネル調査エラー: {e}")
        
        # エラーステータス更新
        if 'research_key' in locals():
            research_status[research_key] = {
                "status": "failed",
                "progress": 0,
                "error": str(e)
            }
        
        raise HTTPException(
            status_code=500,
            detail=f"チャンネル調査中にエラーが発生しました: {str(e)}"
        )

@router.get("/research/status/{research_id}", response_model=ResearchStatusResponse)
async def get_research_status(research_id: str):
    """
    調査進行状況を取得
    
    Args:
        research_id: 調査ID
        
    Returns:
        ResearchStatusResponse: 調査ステータス
    """
    try:
        if research_id not in research_status:
            return ResearchStatusResponse(
                success=False,
                status="not_found",
                message="指定された調査IDが見つかりません"
            )
        
        status_info = research_status[research_id]
        
        return ResearchStatusResponse(
            success=True,
            status=status_info["status"],
            progress=status_info.get("progress", 0),
            message=status_info.get("error", "調査進行中")
        )
        
    except Exception as e:
        print(f"❌ ステータス取得エラー: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"ステータス取得中にエラーが発生しました: {str(e)}"
        )

@router.post("/research/quick", response_model=Dict[str, Any])
async def quick_research_channel(request: ChannelResearchRequest):
    """
    チャンネルのクイック調査（基本情報のみ）
    
    Args:
        request: チャンネル調査リクエスト
        
    Returns:
        Dict: 基本調査結果
    """
    try:
        print(f"⚡ クイック調査リクエスト: {request.channel_title}")
        
        # チャンネルデータの準備
        channel_data = {
            "channel_id": request.channel_id,
            "channel_title": request.channel_title,
            **request.channel_data
        }
        
        # 基本情報のみ調査
        basic_info = await research_service._research_basic_info(
            request.channel_title, 
            request.channel_id
        )
        
        reputation = await research_service._research_reputation_safety(
            request.channel_title,
            request.channel_id
        )
        
        result = {
            "success": True,
            "channel_id": request.channel_id,
            "channel_name": request.channel_title,
            "basic_info": basic_info,
            "reputation_safety": reputation,
            "research_type": "quick",
            "message": "クイック調査が完了しました"
        }
        
        print(f"✅ クイック調査完了: {request.channel_title}")
        return result
        
    except Exception as e:
        print(f"❌ クイック調査エラー: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"クイック調査中にエラーが発生しました: {str(e)}"
        )

@router.get("/research/categories")
async def get_research_categories():
    """
    利用可能な調査カテゴリを取得
    
    Returns:
        Dict: 調査カテゴリ一覧
    """
    try:
        categories = {
            "basic_info": {
                "name": "基本情報・最新動向",
                "description": "チャンネルの最新活動状況、成長傾向、人気コンテンツを分析",
                "estimated_time": "30-60秒"
            },
            "reputation": {
                "name": "評判・安全性分析",
                "description": "炎上履歴、ブランドセーフティ、リスク評価を実施",
                "estimated_time": "60-90秒"
            },
            "collaboration": {
                "name": "コラボ実績・PR履歴",
                "description": "過去の企業コラボ、PR案件の実績と効果を調査",
                "estimated_time": "45-75秒"
            },
            "market_analysis": {
                "name": "競合・市場分析",
                "description": "同カテゴリの競合状況、市場での立ち位置を評価",
                "estimated_time": "60-90秒"
            }
        }
        
        return {
            "success": True,
            "categories": categories,
            "total_categories": len(categories),
            "estimated_total_time": "3-5分"
        }
        
    except Exception as e:
        print(f"❌ カテゴリ取得エラー: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"カテゴリ取得中にエラーが発生しました: {str(e)}"
        )

@router.delete("/research/status/{research_id}")
async def cleanup_research_status(research_id: str):
    """
    調査ステータスをクリーンアップ
    
    Args:
        research_id: 調査ID
        
    Returns:
        Dict: 削除結果
    """
    try:
        if research_id in research_status:
            del research_status[research_id]
            return {
                "success": True,
                "message": "調査ステータスを削除しました"
            }
        else:
            return {
                "success": False,
                "message": "指定された調査IDが見つかりません"
            }
            
    except Exception as e:
        print(f"❌ ステータス削除エラー: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"ステータス削除中にエラーが発生しました: {str(e)}"
        )

@router.get("/health")
async def research_health_check():
    """
    チャンネル調査サービスのヘルスチェック
    
    Returns:
        Dict: サービス状態
    """
    try:
        # サービスの基本チェック
        test_channel = {
            "channel_id": "test",
            "channel_title": "Test Channel"
        }
        
        # 軽微なテスト実行
        service_available = research_service is not None
        
        return {
            "success": True,
            "service_status": "healthy" if service_available else "unavailable",
            "active_researches": len(research_status),
            "version": "1.0.0",
            "features": [
                "comprehensive_research",
                "quick_research", 
                "status_tracking",
                "category_analysis"
            ]
        }
        
    except Exception as e:
        print(f"❌ ヘルスチェックエラー: {e}")
        return {
            "success": False,
            "service_status": "error",
            "error": str(e)
        }