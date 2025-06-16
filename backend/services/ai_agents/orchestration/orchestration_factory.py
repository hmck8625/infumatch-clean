"""
オーケストレーションファクトリー

@description マルチエージェントシステムの初期化と設定を管理
@author InfuMatch Development Team
@version 2.0.0
"""

import logging
from typing import Dict, Any, Optional

from .negotiation_manager import NegotiationManager
from .context_agent import ContextAgent
from .analysis_agent import AnalysisAgent
from .communication_agent import CommunicationAgent
from .strategy_agent import StrategyAgent
from .pricing_agent import PricingAgent
from .risk_agent import RiskAgent

logger = logging.getLogger(__name__)


class OrchestrationFactory:
    """
    マルチエージェントオーケストレーションシステムのファクトリー
    
    システム全体の初期化、エージェントの登録、設定管理を担当
    """
    
    @classmethod
    def create_full_orchestration_system(cls, config: Optional[Dict[str, Any]] = None) -> NegotiationManager:
        """
        完全なマルチエージェントシステムを構築
        
        Args:
            config: システム設定（オプション）
            
        Returns:
            NegotiationManager: 設定済みの交渉マネージャー
        """
        logger.info("🏭 マルチエージェントシステム構築開始")
        
        # 設定の初期化
        config = config or {}
        
        try:
            # メインマネージャーを初期化
            manager = NegotiationManager()
            
            # 各専門エージェントを初期化・登録
            agents_created = []
            
            # 1. コンテキスト分析エージェント
            try:
                context_agent = ContextAgent()
                manager.register_agent(context_agent)
                agents_created.append("ContextAgent")
            except Exception as e:
                logger.error(f"❌ ContextAgent初期化失敗: {str(e)}")
            
            # 2. メッセージ分析エージェント
            try:
                analysis_agent = AnalysisAgent()
                manager.register_agent(analysis_agent)
                agents_created.append("AnalysisAgent")
            except Exception as e:
                logger.error(f"❌ AnalysisAgent初期化失敗: {str(e)}")
            
            # 3. コミュニケーションエージェント
            try:
                communication_agent = CommunicationAgent()
                manager.register_agent(communication_agent)
                agents_created.append("CommunicationAgent")
            except Exception as e:
                logger.error(f"❌ CommunicationAgent初期化失敗: {str(e)}")
            
            # 4. 戦略エージェント
            try:
                strategy_agent = StrategyAgent()
                manager.register_agent(strategy_agent)
                agents_created.append("StrategyAgent")
            except Exception as e:
                logger.error(f"❌ StrategyAgent初期化失敗: {str(e)}")
            
            # 5. 価格戦略エージェント
            try:
                pricing_agent = PricingAgent()
                manager.register_agent(pricing_agent)
                agents_created.append("PricingAgent")
            except Exception as e:
                logger.error(f"❌ PricingAgent初期化失敗: {str(e)}")
            
            # 6. リスク評価エージェント
            try:
                risk_agent = RiskAgent()
                manager.register_agent(risk_agent)
                agents_created.append("RiskAgent")
            except Exception as e:
                logger.error(f"❌ RiskAgent初期化失敗: {str(e)}")
            
            logger.info(f"✅ マルチエージェントシステム構築完了: {len(agents_created)}エージェント登録")
            logger.info(f"📋 登録エージェント: {', '.join(agents_created)}")
            
            return manager
            
        except Exception as e:
            logger.error(f"❌ マルチエージェントシステム構築失敗: {str(e)}")
            # フォールバック: 最小限のマネージャーを返す
            return NegotiationManager()
    
    @classmethod
    def create_minimal_system(cls) -> NegotiationManager:
        """
        最小限のシステムを構築（開発・テスト用）
        
        Returns:
            NegotiationManager: 基本的な交渉マネージャー
        """
        logger.info("🔧 最小限システム構築開始")
        
        manager = NegotiationManager()
        
        # 必須エージェントのみ登録
        try:
            # 分析とコミュニケーションは最低限必要
            analysis_agent = AnalysisAgent()
            communication_agent = CommunicationAgent()
            
            manager.register_agent(analysis_agent)
            manager.register_agent(communication_agent)
            
            logger.info("✅ 最小限システム構築完了")
            
        except Exception as e:
            logger.error(f"❌ 最小限システム構築失敗: {str(e)}")
        
        return manager
    
    @classmethod
    def create_custom_system(cls, agent_types: list) -> NegotiationManager:
        """
        カスタムエージェント構成でシステムを構築
        
        Args:
            agent_types: 使用するエージェントタイプのリスト
            
        Returns:
            NegotiationManager: カスタム設定の交渉マネージャー
        """
        logger.info(f"⚙️ カスタムシステム構築開始: {agent_types}")
        
        manager = NegotiationManager()
        agent_map = {
            "context": ContextAgent,
            "analysis": AnalysisAgent,
            "communication": CommunicationAgent,
            "strategy": StrategyAgent,
            "pricing": PricingAgent,
            "risk": RiskAgent
        }
        
        created_agents = []
        for agent_type in agent_types:
            if agent_type in agent_map:
                try:
                    agent = agent_map[agent_type]()
                    manager.register_agent(agent)
                    created_agents.append(agent_type)
                except Exception as e:
                    logger.error(f"❌ {agent_type}エージェント作成失敗: {str(e)}")
        
        logger.info(f"✅ カスタムシステム構築完了: {created_agents}")
        return manager
    
    @classmethod
    def get_system_status(cls, manager: NegotiationManager) -> Dict[str, Any]:
        """
        システムステータスを取得
        
        Args:
            manager: 交渉マネージャー
            
        Returns:
            Dict: システム状態情報
        """
        try:
            status = manager.get_orchestration_status()
            
            system_health = {
                "total_agents": len(status["registered_agents"]),
                "active_negotiations": status["active_negotiations"],
                "system_ready": len(status["registered_agents"]) >= 2,  # 最低2エージェント必要
                "agent_health": {}
            }
            
            # 各エージェントの健全性チェック
            for agent_id, agent_status in status["registered_agents"].items():
                health_score = 1.0
                if agent_status.get("success_rate", 0) < 0.8:
                    health_score -= 0.3
                if agent_status.get("average_confidence", 0) < 0.7:
                    health_score -= 0.2
                
                system_health["agent_health"][agent_id] = {
                    "health_score": max(health_score, 0.0),
                    "status": "healthy" if health_score >= 0.8 else "warning" if health_score >= 0.5 else "critical"
                }
            
            return {
                "system_status": "operational" if system_health["system_ready"] else "limited",
                "system_health": system_health,
                "orchestration_details": status
            }
            
        except Exception as e:
            logger.error(f"❌ システムステータス取得失敗: {str(e)}")
            return {
                "system_status": "error",
                "error": str(e),
                "system_health": {"total_agents": 0, "system_ready": False}
            }


# 便利な関数エイリアス
def create_negotiation_system(config: Optional[Dict[str, Any]] = None) -> NegotiationManager:
    """マルチエージェント交渉システムを作成"""
    return OrchestrationFactory.create_full_orchestration_system(config)


def create_minimal_negotiation_system() -> NegotiationManager:
    """最小限の交渉システムを作成"""
    return OrchestrationFactory.create_minimal_system()


def get_negotiation_system_status(manager: NegotiationManager) -> Dict[str, Any]:
    """交渉システムの状態を取得"""
    return OrchestrationFactory.get_system_status(manager)