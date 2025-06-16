"""
オーケストレーション対応ベースエージェント

@description オーケストレーション機能を持つエージェントの基底クラス
@author InfuMatch Development Team
@version 2.0.0
"""

import logging
import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..base_agent import BaseAgent, AgentConfig
from .agent_message import AgentMessage, MessageType, Priority
from .negotiation_state import NegotiationState


logger = logging.getLogger(__name__)


class BaseOrchestratedAgent(BaseAgent):
    """
    オーケストレーション対応ベースエージェント
    
    マネージャーからの指示を受けて専門タスクを実行し、
    結果を構造化して返す機能を提供
    """
    
    def __init__(self, config: AgentConfig, agent_id: str, specialization: str):
        """
        エージェントの初期化
        
        Args:
            config: エージェント設定
            agent_id: 一意のエージェントID
            specialization: 専門分野
        """
        super().__init__(config)
        self.agent_id = agent_id
        self.specialization = specialization
        self.performance_metrics = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "average_confidence": 0.0,
            "average_processing_time": 0.0,
            "last_activity": None
        }
        
        logger.info(f"🤖 {self.agent_id} ({self.specialization}) エージェント初期化完了")
    
    async def process_message(self, message: AgentMessage, state: NegotiationState) -> AgentMessage:
        """
        メッセージを処理して結果を返す
        
        Args:
            message: 受信メッセージ
            state: 現在の交渉状態
            
        Returns:
            AgentMessage: 処理結果メッセージ
        """
        start_time = time.time()
        
        try:
            logger.info(f"📨 {self.agent_id}: タスク開始 - {message.task_type}")
            
            # タスクタイプに応じた処理
            if message.message_type == MessageType.TASK_REQUEST:
                result = await self.execute_task(message.task_type, message.payload, state)
                
                processing_time_ms = int((time.time() - start_time) * 1000)
                
                # 成功メトリクスを更新
                self._update_performance_metrics(True, result.get("confidence", 0.0), processing_time_ms)
                
                # 結果メッセージを作成
                response = AgentMessage.create_task_result(
                    sender_id=self.agent_id,
                    recipient_id=message.sender_id,
                    task_type=message.task_type,
                    payload=result,
                    confidence_score=result.get("confidence", 0.0),
                    parent_message_id=message.message_id,
                    correlation_id=message.correlation_id,
                    processing_time_ms=processing_time_ms
                )
                
                logger.info(f"✅ {self.agent_id}: タスク完了 - {message.task_type} (信頼度: {result.get('confidence', 0.0):.2f})")
                return response
                
            elif message.message_type == MessageType.EVALUATION_REQUEST:
                # 他のエージェントの成果を評価
                evaluation = await self.evaluate_peer_result(message.payload, state)
                
                processing_time_ms = int((time.time() - start_time) * 1000)
                
                response = AgentMessage.create_task_result(
                    sender_id=self.agent_id,
                    recipient_id=message.sender_id,
                    task_type="peer_evaluation",
                    payload=evaluation,
                    confidence_score=evaluation.get("confidence", 0.0),
                    parent_message_id=message.message_id,
                    correlation_id=message.correlation_id,
                    processing_time_ms=processing_time_ms
                )
                
                return response
            
            else:
                raise ValueError(f"Unsupported message type: {message.message_type}")
                
        except Exception as e:
            logger.error(f"❌ {self.agent_id}: タスク失敗 - {message.task_type}: {str(e)}")
            
            # 失敗メトリクスを更新
            processing_time_ms = int((time.time() - start_time) * 1000)
            self._update_performance_metrics(False, 0.0, processing_time_ms)
            
            # エラーメッセージを作成
            return AgentMessage.create_error_report(
                sender_id=self.agent_id,
                recipient_id=message.sender_id,
                error_message=str(e),
                error_details={
                    "task_type": message.task_type,
                    "specialization": self.specialization,
                    "processing_time_ms": processing_time_ms
                },
                parent_message_id=message.message_id,
                correlation_id=message.correlation_id
            )
    
    @abstractmethod
    async def execute_task(self, task_type: str, payload: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """
        専門タスクを実行
        
        Args:
            task_type: タスクタイプ
            payload: タスクデータ
            state: 交渉状態
            
        Returns:
            Dict: 実行結果（confidenceフィールドを含む）
        """
        pass
    
    async def evaluate_peer_result(self, peer_result: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """
        他エージェントの結果を評価（デフォルト実装）
        
        Args:
            peer_result: 他エージェントの結果
            state: 交渉状態
            
        Returns:
            Dict: 評価結果
        """
        # デフォルトは評価なし
        return {
            "evaluation_score": 0.5,
            "feedback": "評価機能未実装",
            "confidence": 0.1
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        エージェントの能力情報を取得
        
        Returns:
            Dict: 能力情報
        """
        return {
            "agent_id": self.agent_id,
            "specialization": self.specialization,
            "supported_tasks": self.get_supported_tasks(),
            "performance_metrics": self.performance_metrics,
            "status": "active"
        }
    
    @abstractmethod
    def get_supported_tasks(self) -> List[str]:
        """
        サポートするタスクタイプのリストを取得
        
        Returns:
            List[str]: サポートするタスクタイプ
        """
        pass
    
    def _update_performance_metrics(self, success: bool, confidence: float, processing_time_ms: int):
        """パフォーマンスメトリクスを更新"""
        self.performance_metrics["total_tasks"] += 1
        
        if success:
            self.performance_metrics["successful_tasks"] += 1
        
        # 平均信頼度を更新
        total_tasks = self.performance_metrics["total_tasks"]
        current_avg_confidence = self.performance_metrics["average_confidence"]
        self.performance_metrics["average_confidence"] = (
            (current_avg_confidence * (total_tasks - 1) + confidence) / total_tasks
        )
        
        # 平均処理時間を更新
        current_avg_time = self.performance_metrics["average_processing_time"]
        self.performance_metrics["average_processing_time"] = (
            (current_avg_time * (total_tasks - 1) + processing_time_ms) / total_tasks
        )
        
        self.performance_metrics["last_activity"] = datetime.now().isoformat()
    
    def get_success_rate(self) -> float:
        """成功率を取得"""
        if self.performance_metrics["total_tasks"] == 0:
            return 0.0
        return self.performance_metrics["successful_tasks"] / self.performance_metrics["total_tasks"]
    
    def get_status_summary(self) -> Dict[str, Any]:
        """ステータス要約を取得"""
        return {
            "agent_id": self.agent_id,
            "specialization": self.specialization,
            "success_rate": self.get_success_rate(),
            "average_confidence": self.performance_metrics["average_confidence"],
            "average_processing_time_ms": self.performance_metrics["average_processing_time"],
            "total_tasks_completed": self.performance_metrics["total_tasks"],
            "last_activity": self.performance_metrics["last_activity"]
        }