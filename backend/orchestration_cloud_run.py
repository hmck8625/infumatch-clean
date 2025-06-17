"""
マルチエージェントオーケストレーション対応Cloud Runアプリケーション

@description オーケストレーションシステムを含む軽量化されたCloud Run用アプリ
@author InfuMatch Development Team
@version 2.0.0
"""

import os
import logging
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from datetime import datetime

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPIアプリケーション
app = FastAPI(
    title="InfuMatch Multi-Agent Orchestration API",
    description="YouTube Influencer Matching Agent with Advanced AI Orchestration",
    version="2.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# リクエストモデル
class SimpleNegotiationRequest(BaseModel):
    """簡易交渉リクエスト"""
    message: str = Field(..., description="受信メッセージ")
    company_name: str = Field(default="InfuMatch", description="企業名")
    contact_person: str = Field(default="田中美咲", description="担当者名")
    custom_instructions: str = Field(default="", description="カスタム指示")

class OrchestratedNegotiationRequest(BaseModel):
    """オーケストレーション交渉リクエスト"""
    thread_id: str = Field(..., description="スレッドID")
    new_message: str = Field(..., description="新着メッセージ")
    company_settings: Dict[str, Any] = Field(..., description="企業設定")
    conversation_history: list = Field(default_factory=list, description="会話履歴")
    custom_instructions: str = Field(default="", description="カスタム指示")

# グローバル変数
orchestration_service = None
system_ready = False

@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の処理"""
    global orchestration_service, system_ready
    logger.info("🚀 InfuMatch Orchestration System starting up...")
    
    # 環境変数を確認
    import os
    gemini_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        logger.warning("⚠️ GOOGLE_API_KEY not found, trying to initialize anyway...")
    else:
        logger.info("✅ Gemini API key found")
    
    try:
        # オーケストレーションシステムの初期化を試行
        from services.orchestrated_negotiation_service import get_orchestrated_negotiation_service
        orchestration_service = await get_orchestrated_negotiation_service()
        system_ready = True
        logger.info("✅ Multi-Agent Orchestration System initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize orchestration system: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.warning("🔄 Falling back to basic mode")
        system_ready = False

@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "InfuMatch Multi-Agent Orchestration Backend",
        "version": "2.0.0",
        "platform": "Google Cloud Run",
        "status": "healthy",
        "orchestration_enabled": system_ready,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "orchestration_ready": system_ready,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/negotiate")
async def simple_negotiate(request: SimpleNegotiationRequest):
    """簡易交渉エンドポイント"""
    try:
        logger.info(f"💬 Simple negotiation request received")
        
        # 基本的な応答生成
        content = f"""いつもお世話になっております。
{request.company_name} の{request.contact_person}です。

ご連絡いただき、ありがとうございます。

{request.message[:100]}について詳細を確認し、最適なご提案をさせていただきます。

{request.custom_instructions if request.custom_instructions else "何かご不明な点がございましたら、お気軽にお声がけください。"}

何卒よろしくお願いいたします。

{request.company_name}
{request.contact_person}"""
        
        return {
            "success": True,
            "content": content,
            "metadata": {
                "processing_type": "basic_template",
                "ai_service": "Template-based Response",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Simple negotiation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/negotiate/orchestrated")
async def orchestrated_negotiate(request: OrchestratedNegotiationRequest):
    """マルチエージェントオーケストレーション交渉"""
    global orchestration_service, system_ready
    
    try:
        logger.info(f"🎭 Orchestrated negotiation request for thread: {request.thread_id}")
        
        if system_ready and orchestration_service:
            # オーケストレーションシステムで処理
            result = await orchestration_service.process_negotiation_message(
                thread_id=request.thread_id,
                new_message=request.new_message,
                company_settings=request.company_settings,
                conversation_history=request.conversation_history,
                custom_instructions=request.custom_instructions
            )
            
            return {
                "success": True,
                "content": result.get("content"),
                "metadata": {
                    **result.get("metadata", {}),
                    "processing_type": "multi_agent_orchestration",
                    "orchestration_details": result.get("orchestration_details", {}),
                    "ai_thinking": result.get("ai_thinking", {})
                }
            }
        else:
            # フォールバック: 基本応答
            logger.warning("⚠️ Orchestration unavailable, using fallback")
            
            company_name = request.company_settings.get("company_name", "InfuMatch")
            contact_person = request.company_settings.get("contact_person", "田中美咲")
            
            fallback_content = f"""いつもお世話になっております。
{company_name} の{contact_person}です。

ご連絡いただき、ありがとうございます。

詳細について検討し、改めてご連絡いたします。
ご質問やご相談がございましたら、お気軽にお声がけください。

{request.custom_instructions if request.custom_instructions else ""}

何卒よろしくお願いいたします。

{company_name}
{contact_person}"""
            
            return {
                "success": True,
                "content": fallback_content,
                "metadata": {
                    "processing_type": "fallback_response",
                    "ai_service": "Basic Template",
                    "fallback_reason": "orchestration_unavailable"
                }
            }
            
    except Exception as e:
        logger.error(f"❌ Orchestrated negotiation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/orchestration/status")
async def orchestration_status():
    """オーケストレーションシステム状態"""
    global orchestration_service, system_ready
    
    try:
        if system_ready and orchestration_service:
            status = orchestration_service.get_system_status()
            return {
                "success": True,
                "system_ready": True,
                "orchestration_status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "success": False,
                "system_ready": False,
                "error": "Orchestration system not available",
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"❌ Status check error: {e}")
        return {
            "success": False,
            "system_ready": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/api/v1/test")
async def test_endpoint():
    """テストエンドポイント"""
    return {
        "message": "Multi-Agent Orchestration System Test",
        "system_ready": system_ready,
        "capabilities": [
            "basic_negotiation",
            "orchestrated_negotiation" if system_ready else "fallback_only",
            "status_monitoring"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }

# エラーハンドラー
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """グローバル例外ハンドラー"""
    logger.error(f"❌ Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if os.getenv("DEBUG") else "An error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)