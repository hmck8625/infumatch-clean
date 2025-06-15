"""
交渉エージェント API エンドポイント

@description AIエージェントによる交渉機能のHTTPエンドポイント
@author InfuMatch Development Team
@version 1.0.0
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from services.ai_agents.negotiation_agent import NegotiationAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/negotiation", tags=["Negotiation"])


# リクエスト・レスポンスモデル
class InitialContactRequest(BaseModel):
    """初回コンタクト生成リクエスト"""
    influencer: Dict[str, Any] = Field(..., description="インフルエンサー情報")
    campaign: Dict[str, Any] = Field(..., description="キャンペーン情報")
    
    class Config:
        schema_extra = {
            "example": {
                "influencer": {
                    "channel_name": "料理系YouTuber",
                    "subscriber_count": 50000,
                    "categories": ["料理", "レシピ"],
                    "description": "簡単で美味しい料理レシピを紹介しています"
                },
                "campaign": {
                    "product_name": "新調味料",
                    "budget_min": 30000,
                    "budget_max": 50000,
                    "campaign_type": "商品紹介"
                }
            }
        }


class ContinueNegotiationRequest(BaseModel):
    """交渉継続リクエスト"""
    conversation_history: list = Field(..., description="会話履歴")
    new_message: str = Field(..., description="新着メッセージ")
    context: Dict[str, Any] = Field(default_factory=dict, description="追加コンテキスト")


class PriceNegotiationRequest(BaseModel):
    """価格交渉リクエスト"""
    current_offer: int = Field(..., description="相手の希望価格")
    target_price: int = Field(..., description="目標価格")
    influencer_stats: Dict[str, Any] = Field(..., description="インフルエンサー統計")


class ReplyPatternsRequest(BaseModel):
    """返信パターン生成リクエスト"""
    email_thread: Dict[str, Any] = Field(..., description="メールスレッド情報")
    thread_messages: list = Field(..., description="スレッドメッセージ履歴")
    context: Dict[str, Any] = Field(default_factory=dict, description="追加コンテキスト")
    
    class Config:
        schema_extra = {
            "example": {
                "email_thread": {
                    "id": "thread_123",
                    "subject": "コラボレーションについて",
                    "participants": ["田中美咲", "料理YouTuber"]
                },
                "thread_messages": [
                    {
                        "sender": "料理YouTuber",
                        "content": "お疲れ様です。ご提案いただいた件、興味があります。料金はどのくらいを想定されていますか？",
                        "date": "2024-06-14T10:00:00Z"
                    }
                ],
                "context": {
                    "campaign_type": "商品紹介",
                    "budget_range": "30000-50000"
                }
            }
        }


class NegotiationResponse(BaseModel):
    """交渉エージェントレスポンス"""
    success: bool
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# グローバルエージェントインスタンス
negotiation_agent = None


def get_negotiation_agent() -> NegotiationAgent:
    """交渉エージェントインスタンスを取得"""
    global negotiation_agent
    if negotiation_agent is None:
        negotiation_agent = NegotiationAgent()
    return negotiation_agent


@router.post("/initial-contact", response_model=NegotiationResponse)
async def generate_initial_contact(
    request: InitialContactRequest,
    agent: NegotiationAgent = Depends(get_negotiation_agent)
) -> NegotiationResponse:
    """
    初回コンタクトメールを生成
    
    インフルエンサーとキャンペーン情報に基づいて、
    人間らしい自然な初回コンタクトメールを生成します。
    """
    try:
        logger.info(f"🤖 Generating initial contact for {request.influencer.get('channel_name', 'Unknown')}")
        
        # エージェント処理実行
        result = await agent.process({
            "action": "generate_initial_email",
            "influencer": request.influencer,
            "campaign": request.campaign
        })
        
        if result.get("success"):
            return NegotiationResponse(
                success=True,
                content=result.get("email_content"),
                metadata={
                    "personalization_score": result.get("personalization_score"),
                    "agent": result.get("agent"),
                    "action": "initial_contact"
                }
            )
        else:
            logger.error(f"❌ Initial contact generation failed: {result.get('error')}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to generate initial contact: {result.get('error')}"
            )
            
    except Exception as e:
        logger.error(f"❌ Initial contact API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/continue", response_model=NegotiationResponse)
async def continue_negotiation(
    request: ContinueNegotiationRequest,
    agent: NegotiationAgent = Depends(get_negotiation_agent)
) -> NegotiationResponse:
    """
    交渉を継続
    
    会話履歴と新着メッセージに基づいて、
    適切な返信メールを生成します。
    """
    try:
        logger.info(f"🤖 Continuing negotiation with {len(request.conversation_history)} messages")
        
        # エージェント処理実行
        result = await agent.process({
            "action": "continue_negotiation",
            "conversation_history": request.conversation_history,
            "new_message": request.new_message,
            "context": request.context
        })
        
        if result.get("success"):
            return NegotiationResponse(
                success=True,
                content=result.get("reply_content"),
                metadata={
                    "relationship_stage": result.get("relationship_stage"),
                    "agent": result.get("agent"),
                    "action": "continue_negotiation"
                }
            )
        else:
            logger.error(f"❌ Negotiation continuation failed: {result.get('error')}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to continue negotiation: {result.get('error')}"
            )
            
    except Exception as e:
        logger.error(f"❌ Continue negotiation API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/price-negotiate", response_model=NegotiationResponse)
async def negotiate_price(
    request: PriceNegotiationRequest,
    agent: NegotiationAgent = Depends(get_negotiation_agent)
) -> NegotiationResponse:
    """
    価格交渉を実行
    
    現在の価格提案と目標価格に基づいて、
    適正な価格交渉メッセージを生成します。
    """
    try:
        logger.info(f"🤖 Negotiating price: {request.current_offer} -> {request.target_price}")
        
        # エージェント処理実行
        result = await agent.process({
            "action": "price_negotiation",
            "current_offer": request.current_offer,
            "target_price": request.target_price,
            "influencer_stats": request.influencer_stats
        })
        
        if result.get("success"):
            return NegotiationResponse(
                success=True,
                content=result.get("negotiation_content"),
                metadata={
                    "proposed_price": result.get("proposed_price"),
                    "strategy": result.get("strategy"),
                    "agent": result.get("agent"),
                    "action": "price_negotiation"
                }
            )
        else:
            logger.error(f"❌ Price negotiation failed: {result.get('error')}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to negotiate price: {result.get('error')}"
            )
            
    except Exception as e:
        logger.error(f"❌ Price negotiation API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capabilities")
async def get_capabilities(
    agent: NegotiationAgent = Depends(get_negotiation_agent)
) -> Dict[str, Any]:
    """
    交渉エージェントの機能一覧を取得
    
    エージェントが提供する機能の詳細情報を返します。
    """
    try:
        capabilities = agent.get_capabilities()
        
        return {
            "success": True,
            "capabilities": capabilities,
            "agent_info": {
                "name": agent.config.name,
                "model": agent.config.model_name,
                "temperature": agent.config.temperature,
                "persona": agent.persona
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Get capabilities error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_agent_status() -> Dict[str, Any]:
    """
    エージェントの状態確認
    
    エージェントの動作状況とシステム情報を返します。
    """
    try:
        global negotiation_agent
        
        return {
            "success": True,
            "status": {
                "agent_initialized": negotiation_agent is not None,
                "agent_ready": negotiation_agent is not None,
                "system_time": datetime.utcnow().isoformat(),
                "features": [
                    "initial_contact_generation",
                    "conversation_continuation", 
                    "price_negotiation",
                    "human_like_communication"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Get status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_agent(
    background_tasks: BackgroundTasks,
    agent: NegotiationAgent = Depends(get_negotiation_agent)
) -> Dict[str, Any]:
    """
    エージェントのテスト実行
    
    開発・デバッグ用のテストエンドポイント
    """
    try:
        # サンプルデータでテスト実行
        test_data = {
            "action": "generate_initial_email",
            "influencer": {
                "channel_name": "テスト料理チャンネル",
                "subscriber_count": 10000,
                "categories": ["料理"],
                "description": "簡単料理レシピを紹介"
            },
            "campaign": {
                "product_name": "テスト商品",
                "budget_min": 20000,
                "budget_max": 30000,
                "campaign_type": "商品紹介"
            }
        }
        
        result = await agent.process(test_data)
        
        return {
            "success": True,
            "test_result": result,
            "message": "Agent test completed successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Agent test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reply-patterns", response_model=NegotiationResponse)
async def generate_reply_patterns(
    request: ReplyPatternsRequest,
    agent: NegotiationAgent = Depends(get_negotiation_agent)
) -> NegotiationResponse:
    """
    返信パターンを複数生成
    
    メールスレッドの内容を分析し、3つの異なるスタイルの
    返信パターンを生成します：
    - 友好的・積極的パターン
    - 控えめ・慎重パターン  
    - ビジネス重視パターン
    """
    try:
        logger.info(f"🤖 Generating reply patterns for thread {request.email_thread.get('id', 'unknown')}")
        
        # エージェント処理実行
        result = await agent.process({
            "action": "generate_reply_patterns",
            "email_thread": request.email_thread,
            "thread_messages": request.thread_messages,
            "context": request.context
        })
        
        if result.get("success"):
            return NegotiationResponse(
                success=True,
                content=None,  # 複数パターンなのでcontentは使用しない
                metadata={
                    "reply_patterns": result.get("reply_patterns", []),
                    "thread_analysis": result.get("thread_analysis", {}),
                    "pattern_count": len(result.get("reply_patterns", [])),
                    "agent": result.get("agent"),
                    "action": "generate_reply_patterns"
                }
            )
        else:
            logger.error(f"❌ Reply patterns generation failed: {result.get('error')}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate reply patterns: {result.get('error')}"
            )
            
    except Exception as e:
        logger.error(f"❌ Reply patterns API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))