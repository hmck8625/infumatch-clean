"""
オーケストレーション対応交渉サービス

@description マルチエージェントシステムを統合した高度な交渉サービス
@author InfuMatch Development Team
@version 2.0.0
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from .ai_agents.orchestration.orchestration_factory import create_negotiation_system, get_negotiation_system_status
from .ai_agents.orchestration import NegotiationManager

logger = logging.getLogger(__name__)


class OrchestratedNegotiationService:
    """
    マルチエージェントオーケストレーション対応交渉サービス
    
    複数の専門AIエージェントを協調させて高度な交渉処理を実現
    """
    
    def __init__(self):
        """サービスの初期化"""
        self.manager: Optional[NegotiationManager] = None
        self.initialization_time: Optional[datetime] = None
        self.is_ready = False
        
        logger.info("🎭 OrchestratedNegotiationService 初期化開始")
    
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        マルチエージェントシステムを初期化
        
        Args:
            config: システム設定
            
        Returns:
            bool: 初期化成功フラグ
        """
        try:
            logger.info("🚀 マルチエージェントシステム初期化中...")
            
            # オーケストレーションシステムを構築
            self.manager = create_negotiation_system(config)
            self.initialization_time = datetime.now()
            
            # システム状態を確認
            status = get_negotiation_system_status(self.manager)
            self.is_ready = status["system_health"]["system_ready"]
            
            if self.is_ready:
                logger.info(f"✅ マルチエージェントシステム初期化完了 ({status['system_health']['total_agents']}エージェント)")
                return True
            else:
                logger.warning("⚠️ マルチエージェントシステム初期化不完全")
                return False
                
        except Exception as e:
            logger.error(f"❌ マルチエージェントシステム初期化失敗: {str(e)}")
            self.is_ready = False
            return False
    
    async def process_negotiation_message(
        self,
        thread_id: str,
        new_message: str,
        company_settings: Dict[str, Any],
        conversation_history: List[Dict[str, Any]] = None,
        custom_instructions: str = ""
    ) -> Dict[str, Any]:
        """
        マルチエージェントによる交渉メッセージ処理
        
        Args:
            thread_id: スレッドID
            new_message: 新着メッセージ
            company_settings: 企業設定
            conversation_history: 会話履歴
            custom_instructions: カスタム指示
            
        Returns:
            Dict: 処理結果
        """
        if not self.is_ready or not self.manager:
            logger.warning("⚠️ システム未初期化、基本応答にフォールバック")
            return await self._fallback_response(new_message, company_settings)
        
        try:
            logger.info(f"🎯 マルチエージェント交渉処理開始: {thread_id}")
            
            # マネージャーに交渉処理を依頼
            result = await self.manager.start_negotiation(
                thread_id=thread_id,
                new_message=new_message,
                company_settings=company_settings,
                conversation_history=conversation_history or [],
                custom_instructions=custom_instructions
            )
            
            # 結果の形式を統一
            if result.get("success", False):
                logger.info(f"✅ マルチエージェント交渉処理完了: {thread_id}")
                return {
                    "success": True,
                    "content": result.get("content", ""),
                    "metadata": {
                        **result.get("metadata", {}),
                        "processing_type": "multi_agent_orchestration",
                        "agent_count": len(self.manager.registered_agents),
                        "system_version": "2.0.0"
                    },
                    "ai_thinking": result.get("ai_thinking", {}),
                    "orchestration_details": {
                        "manager_id": self.manager.manager_id,
                        "active_agents": list(self.manager.registered_agents.keys()),
                        "processing_phases": ["analysis", "strategy", "communication", "evaluation"]
                    }
                }
            else:
                logger.warning(f"⚠️ マルチエージェント処理エラー: {result.get('error', 'Unknown error')}")
                return await self._fallback_response(new_message, company_settings, result.get("error"))
        
        except Exception as e:
            logger.error(f"❌ マルチエージェント交渉処理失敗: {str(e)}")
            return await self._fallback_response(new_message, company_settings, str(e))
    
    async def _fallback_response(
        self, 
        new_message: str, 
        company_settings: Dict[str, Any], 
        error: str = None
    ) -> Dict[str, Any]:
        """
        フォールバック応答生成
        
        Args:
            new_message: メッセージ
            company_settings: 企業設定
            error: エラー情報
            
        Returns:
            Dict: 基本応答
        """
        company_name = company_settings.get("company_name", "InfuMatch")
        contact_person = company_settings.get("contact_person", "田中美咲")
        
        fallback_content = f"""いつもお世話になっております。
{company_name} の{contact_person}です。

ご連絡いただき、ありがとうございます。

詳細について検討し、改めてご連絡いたします。
ご質問やご相談がございましたら、お気軽にお声がけください。

何卒よろしくお願いいたします。

{company_name}
{contact_person}"""
        
        return {
            "success": True,
            "content": fallback_content,
            "metadata": {
                "ai_service": "Fallback Response",
                "processing_type": "basic_template",
                "fallback_reason": error or "system_unavailable",
                "timestamp": datetime.now().isoformat()
            },
            "ai_thinking": {
                "processing_note": "基本応答システムによる処理",
                "reason": "マルチエージェントシステムが利用できないため",
                "error_info": error
            }
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        システム状態を取得
        
        Returns:
            Dict: システム状態情報
        """
        if not self.manager:
            return {
                "status": "not_initialized",
                "ready": False,
                "error": "Manager not initialized"
            }
        
        try:
            orchestration_status = get_negotiation_system_status(self.manager)
            
            return {
                "status": "operational" if self.is_ready else "limited",
                "ready": self.is_ready,
                "initialization_time": self.initialization_time.isoformat() if self.initialization_time else None,
                "orchestration_system": orchestration_status,
                "service_info": {
                    "version": "2.0.0",
                    "capabilities": [
                        "multi_agent_coordination",
                        "context_analysis",
                        "strategy_planning",
                        "risk_assessment",
                        "pricing_optimization",
                        "professional_communication"
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"❌ システム状態取得失敗: {str(e)}")
            return {
                "status": "error",
                "ready": False,
                "error": str(e)
            }
    
    async def shutdown(self):
        """システムのシャットダウン"""
        logger.info("🔄 OrchestratedNegotiationService シャットダウン中...")
        
        if self.manager:
            # アクティブな交渉を安全に終了
            active_count = len(self.manager.active_negotiations)
            if active_count > 0:
                logger.info(f"📝 {active_count}件のアクティブな交渉を保存中...")
                # 実際の実装では交渉状態を永続化
        
        self.manager = None
        self.is_ready = False
        logger.info("✅ OrchestratedNegotiationService シャットダウン完了")


# グローバルサービスインスタンス
_orchestrated_service: Optional[OrchestratedNegotiationService] = None


async def get_orchestrated_negotiation_service() -> OrchestratedNegotiationService:
    """
    オーケストレーション対応交渉サービスを取得
    
    Returns:
        OrchestratedNegotiationService: サービスインスタンス
    """
    global _orchestrated_service
    
    if _orchestrated_service is None:
        _orchestrated_service = OrchestratedNegotiationService()
        await _orchestrated_service.initialize()
    
    return _orchestrated_service


async def process_message_with_orchestration(
    thread_id: str,
    new_message: str,
    company_settings: Dict[str, Any],
    conversation_history: List[Dict[str, Any]] = None,
    custom_instructions: str = ""
) -> Dict[str, Any]:
    """
    マルチエージェントオーケストレーションによるメッセージ処理
    
    Args:
        thread_id: スレッドID
        new_message: 新着メッセージ
        company_settings: 企業設定
        conversation_history: 会話履歴
        custom_instructions: カスタム指示
        
    Returns:
        Dict: 処理結果
    """
    service = await get_orchestrated_negotiation_service()
    
    return await service.process_negotiation_message(
        thread_id=thread_id,
        new_message=new_message,
        company_settings=company_settings,
        conversation_history=conversation_history,
        custom_instructions=custom_instructions
    )