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
from services.ai_agents.advanced_negotiation_analyzer import (
    AdvancedNegotiationAnalyzer, 
    NegotiationContext,
    NegotiationStrategy
)
from services.orchestrated_negotiation_service import (
    get_orchestrated_negotiation_service,
    process_message_with_orchestration
)

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


class AdvancedAnalysisRequest(BaseModel):
    """高度な交渉分析リクエスト"""
    thread_messages: list = Field(..., description="スレッドメッセージ履歴")
    company_settings: Dict[str, Any] = Field(..., description="企業設定情報")
    include_strategy: bool = Field(default=True, description="戦略生成を含むか")
    
    class Config:
        schema_extra = {
            "example": {
                "thread_messages": [
                    {
                        "sender": "料理YouTuber",
                        "content": "お疲れ様です。ご提案いただいた件、興味があります。料金はどのくらいを想定されていますか？",
                        "date": "2024-06-14T10:00:00Z"
                    }
                ],
                "company_settings": {
                    "company_name": "InfuMatch",
                    "contact_person": "田中美咲"
                },
                "include_strategy": True
            }
        }


class OrchestratedNegotiationRequest(BaseModel):
    """マルチエージェントオーケストレーション交渉リクエスト"""
    thread_id: str = Field(..., description="スレッドID")
    new_message: str = Field(..., description="新着メッセージ")
    company_settings: Dict[str, Any] = Field(..., description="企業設定")
    conversation_history: list = Field(default_factory=list, description="会話履歴")
    custom_instructions: str = Field(default="", description="カスタム指示")
    
    class Config:
        schema_extra = {
            "example": {
                "thread_id": "thread_12345",
                "new_message": "こんにちは。Google Alertsです。弊社の新商品のPRについて、ご協力いただけるインフルエンサーを探しております。",
                "company_settings": {
                    "company_name": "InfuMatch",
                    "contact_person": "田中美咲",
                    "email": "tanaka@infumatch.com",
                    "budget": {
                        "min": 200000,
                        "max": 500000,
                        "currency": "JPY"
                    }
                },
                "conversation_history": [
                    {
                        "timestamp": "2024-06-15T10:00:00Z",
                        "sender": "client",
                        "message": "初回の問い合わせメッセージ"
                    }
                ],
                "custom_instructions": "丁寧で専門的な対応を心がけ、具体的な提案を行ってください。"
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
advanced_analyzer = None


def get_negotiation_agent() -> NegotiationAgent:
    """交渉エージェントインスタンスを取得"""
    global negotiation_agent
    if negotiation_agent is None:
        negotiation_agent = NegotiationAgent()
    return negotiation_agent


def get_advanced_analyzer() -> AdvancedNegotiationAnalyzer:
    """高度な交渉分析器インスタンスを取得"""
    global advanced_analyzer
    if advanced_analyzer is None:
        advanced_analyzer = AdvancedNegotiationAnalyzer()
    return advanced_analyzer


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


@router.post("/analyze-advanced", response_model=NegotiationResponse)
async def analyze_negotiation_advanced(
    request: AdvancedAnalysisRequest,
    analyzer: AdvancedNegotiationAnalyzer = Depends(get_advanced_analyzer),
    agent: NegotiationAgent = Depends(get_negotiation_agent)
) -> NegotiationResponse:
    """
    高度な交渉分析を実行
    
    メールスレッドと企業設定を詳細に分析し、
    交渉段階、感情推移、機会とリスク、戦略提案を含む
    包括的な分析結果を返します。
    """
    try:
        logger.info(f"🔍 Advanced negotiation analysis for {len(request.thread_messages)} messages")
        
        # 高度な分析を実行
        negotiation_context = analyzer.analyze_negotiation_state(
            request.thread_messages,
            request.company_settings
        )
        
        # 戦略を生成（オプション）
        strategy = None
        if request.include_strategy:
            strategy = analyzer.generate_negotiation_strategy(negotiation_context)
        
        # 結果をシリアライズ可能な形式に変換
        context_dict = {
            "current_stage": negotiation_context.current_stage.value,
            "sentiment_trend": negotiation_context.sentiment_trend,
            "key_concerns": negotiation_context.key_concerns,
            "opportunities": negotiation_context.opportunities,
            "risks": negotiation_context.risks,
            "influencer_profile": negotiation_context.influencer_profile,
            "company_goals": negotiation_context.company_goals,
            "message_count": len(negotiation_context.negotiation_history)
        }
        
        strategy_dict = None
        if strategy:
            strategy_dict = {
                "approach": strategy.approach,
                "key_messages": strategy.key_messages,
                "tone": strategy.tone,
                "urgency_level": strategy.urgency_level,
                "next_steps": strategy.next_steps,
                "avoid_topics": strategy.avoid_topics,
                "success_probability": strategy.success_probability
            }
        
        return NegotiationResponse(
            success=True,
            content=f"分析完了: {negotiation_context.current_stage.value}段階",
            metadata={
                "analysis": context_dict,
                "strategy": strategy_dict,
                "analyzer": "advanced_negotiation_analyzer",
                "action": "analyze_advanced"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Advanced analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-strategic-reply", response_model=NegotiationResponse)
async def generate_strategic_reply(
    request: ContinueNegotiationRequest,
    analyzer: AdvancedNegotiationAnalyzer = Depends(get_advanced_analyzer),
    agent: NegotiationAgent = Depends(get_negotiation_agent)
) -> NegotiationResponse:
    """
    戦略的な返信を生成
    
    高度な分析結果に基づいて、最適な戦略を用いた
    返信メールを生成します。交渉の段階、感情状態、
    企業ゴールを考慮した戦略的な内容になります。
    """
    try:
        logger.info(f"🎯 Generating strategic reply based on advanced analysis")
        
        # 企業設定を取得（コンテキストから）
        company_settings = request.context.get("company_settings", {})
        
        # 高度な分析を実行
        negotiation_context = analyzer.analyze_negotiation_state(
            request.conversation_history,
            company_settings
        )
        
        # 戦略を生成
        strategy = analyzer.generate_negotiation_strategy(negotiation_context)
        
        # 分析結果と戦略をエージェントに渡して返信生成
        enhanced_context = {
            **request.context,
            "negotiation_stage": negotiation_context.current_stage.value,
            "sentiment_analysis": {
                "current": negotiation_context.sentiment_trend[-1] if negotiation_context.sentiment_trend else 0.0,
                "trend": "improving" if len(negotiation_context.sentiment_trend) > 1 and negotiation_context.sentiment_trend[-1] > negotiation_context.sentiment_trend[-2] else "stable"
            },
            "strategy": {
                "approach": strategy.approach,
                "tone": strategy.tone,
                "key_messages": strategy.key_messages,
                "avoid_topics": strategy.avoid_topics
            },
            "opportunities": negotiation_context.opportunities,
            "risks": negotiation_context.risks
        }
        
        # エージェントに戦略的な返信を生成させる
        result = await agent.process({
            "action": "continue_negotiation",
            "conversation_history": request.conversation_history,
            "new_message": request.new_message,
            "context": enhanced_context
        })
        
        if result.get("success"):
            return NegotiationResponse(
                success=True,
                content=result.get("reply_content"),
                metadata={
                    "relationship_stage": negotiation_context.current_stage.value,
                    "strategy_used": strategy.approach,
                    "success_probability": strategy.success_probability,
                    "sentiment_score": negotiation_context.sentiment_trend[-1] if negotiation_context.sentiment_trend else 0.0,
                    "key_concerns_addressed": negotiation_context.key_concerns,
                    "opportunities_leveraged": negotiation_context.opportunities,
                    "risks_mitigated": negotiation_context.risks,
                    "next_steps": strategy.next_steps,
                    "agent": result.get("agent"),
                    "analyzer": "advanced_negotiation_analyzer",
                    "action": "generate_strategic_reply"
                }
            )
        else:
            logger.error(f"❌ Strategic reply generation failed: {result.get('error')}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate strategic reply: {result.get('error')}"
            )
            
    except Exception as e:
        logger.error(f"❌ Strategic reply API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orchestrated", response_model=NegotiationResponse)
async def process_orchestrated_negotiation(
    request: OrchestratedNegotiationRequest
) -> NegotiationResponse:
    """
    マルチエージェントオーケストレーション交渉処理
    
    複数の専門AIエージェント（コンテキスト分析、戦略立案、
    コミュニケーション、価格戦略、リスク評価）を協調させて、
    高度で専門的な交渉返信を生成します。
    
    従来の単一エージェントアプローチを大幅に上回る
    プロフェッショナルレベルの交渉対応を実現します。
    """
    try:
        logger.info(f"🎭 Orchestrated negotiation processing started for thread: {request.thread_id}")
        
        # マルチエージェントシステムで処理
        result = await process_message_with_orchestration(
            thread_id=request.thread_id,
            new_message=request.new_message,
            company_settings=request.company_settings,
            conversation_history=request.conversation_history,
            custom_instructions=request.custom_instructions
        )
        
        if result.get("success"):
            logger.info(f"✅ Orchestrated negotiation completed for thread: {request.thread_id}")
            
            return NegotiationResponse(
                success=True,
                content=result.get("content"),
                metadata={
                    **result.get("metadata", {}),
                    "processing_type": "multi_agent_orchestration",
                    "orchestration_details": result.get("orchestration_details", {}),
                    "ai_thinking": result.get("ai_thinking", {}),
                    "action": "orchestrated_negotiation"
                }
            )
        else:
            logger.warning(f"⚠️ Orchestrated negotiation failed for thread: {request.thread_id}")
            
            return NegotiationResponse(
                success=True,  # フォールバック応答も成功とみなす
                content=result.get("content", "申し訳ございません。詳細について改めてご連絡いたします。"),
                metadata={
                    **result.get("metadata", {}),
                    "fallback_reason": result.get("metadata", {}).get("fallback_reason", "system_error"),
                    "action": "orchestrated_negotiation_fallback"
                }
            )
            
    except Exception as e:
        logger.error(f"❌ Orchestrated negotiation API error: {e}")
        
        # 完全にエラーの場合は基本応答を返す
        company_name = request.company_settings.get("company_name", "InfuMatch")
        contact_person = request.company_settings.get("contact_person", "田中美咲")
        
        fallback_content = f"""いつもお世話になっております。
{company_name} の{contact_person}です。

ご連絡いただき、ありがとうございます。

詳細について検討し、改めてご連絡いたします。
ご質問やご相談がございましたら、お気軽にお声がけください。

何卒よろしくお願いいたします。

{company_name}
{contact_person}"""
        
        return NegotiationResponse(
            success=True,
            content=fallback_content,
            metadata={
                "processing_type": "emergency_fallback",
                "error": str(e),
                "action": "orchestrated_negotiation_error_fallback"
            }
        )


@router.get("/orchestration/status")
async def get_orchestration_status():
    """
    マルチエージェントオーケストレーションシステムの状態を取得
    
    システムの健全性、登録されているエージェント、
    パフォーマンス統計などの情報を返します。
    """
    try:
        logger.info("📊 Getting orchestration system status")
        
        # オーケストレーションサービスを取得
        service = await get_orchestrated_negotiation_service()
        status = service.get_system_status()
        
        return {
            "success": True,
            "system_status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Orchestration status API error: {e}")
        return {
            "success": False,
            "error": str(e),
            "system_status": {"status": "error", "ready": False},
            "timestamp": datetime.utcnow().isoformat()
        }