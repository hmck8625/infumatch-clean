"""
エージェント間通信メッセージシステム

@description エージェント間の構造化されたメッセージ交換を管理
@author InfuMatch Development Team
@version 2.0.0
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
import uuid


class MessageType(Enum):
    """メッセージタイプ定義"""
    TASK_REQUEST = "task_request"
    TASK_RESULT = "task_result"
    STATUS_UPDATE = "status_update"
    ERROR_REPORT = "error_report"
    COORDINATION_REQUEST = "coordination_request"
    EVALUATION_REQUEST = "evaluation_request"
    EVALUATION_RESULT = "evaluation_result"


class Priority(Enum):
    """優先度定義"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AgentMessage:
    """
    エージェント間通信メッセージ
    
    エージェント間でのタスク依頼、結果報告、ステータス更新等に使用
    """
    
    # メッセージ基本情報
    message_id: str
    sender_id: str
    recipient_id: str
    message_type: MessageType
    
    # メッセージ内容
    task_type: str
    payload: Dict[str, Any]
    
    # メタデータ
    confidence_score: float
    priority: Priority
    timestamp: datetime
    
    # 追跡情報
    correlation_id: Optional[str] = None  # 関連するメッセージチェーンのID
    parent_message_id: Optional[str] = None  # 返信元メッセージID
    
    # 処理情報
    processing_time_ms: Optional[int] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        """初期化後処理"""
        if not self.message_id:
            self.message_id = str(uuid.uuid4())
        
        if not self.correlation_id:
            self.correlation_id = str(uuid.uuid4())
    
    @classmethod
    def create_task_request(
        cls,
        sender_id: str,
        recipient_id: str,
        task_type: str,
        payload: Dict[str, Any],
        priority: Priority = Priority.MEDIUM,
        correlation_id: Optional[str] = None
    ) -> 'AgentMessage':
        """タスク依頼メッセージを作成"""
        return cls(
            message_id=str(uuid.uuid4()),
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_type=MessageType.TASK_REQUEST,
            task_type=task_type,
            payload=payload,
            confidence_score=0.0,  # リクエスト時は未確定
            priority=priority,
            timestamp=datetime.now(),
            correlation_id=correlation_id
        )
    
    @classmethod
    def create_task_result(
        cls,
        sender_id: str,
        recipient_id: str,
        task_type: str,
        payload: Dict[str, Any],
        confidence_score: float,
        parent_message_id: str,
        correlation_id: str,
        processing_time_ms: int
    ) -> 'AgentMessage':
        """タスク結果メッセージを作成"""
        return cls(
            message_id=str(uuid.uuid4()),
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_type=MessageType.TASK_RESULT,
            task_type=task_type,
            payload=payload,
            confidence_score=confidence_score,
            priority=Priority.MEDIUM,
            timestamp=datetime.now(),
            correlation_id=correlation_id,
            parent_message_id=parent_message_id,
            processing_time_ms=processing_time_ms
        )
    
    @classmethod
    def create_error_report(
        cls,
        sender_id: str,
        recipient_id: str,
        error_message: str,
        error_details: Dict[str, Any],
        parent_message_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> 'AgentMessage':
        """エラー報告メッセージを作成"""
        return cls(
            message_id=str(uuid.uuid4()),
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_type=MessageType.ERROR_REPORT,
            task_type="error_handling",
            payload={
                "error_message": error_message,
                "error_details": error_details
            },
            confidence_score=0.0,
            priority=Priority.HIGH,
            timestamp=datetime.now(),
            correlation_id=correlation_id,
            parent_message_id=parent_message_id
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "message_type": self.message_type.value,
            "task_type": self.task_type,
            "payload": self.payload,
            "confidence_score": self.confidence_score,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "parent_message_id": self.parent_message_id,
            "processing_time_ms": self.processing_time_ms,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """辞書からオブジェクトを復元"""
        return cls(
            message_id=data["message_id"],
            sender_id=data["sender_id"],
            recipient_id=data["recipient_id"],
            message_type=MessageType(data["message_type"]),
            task_type=data["task_type"],
            payload=data["payload"],
            confidence_score=data["confidence_score"],
            priority=Priority(data["priority"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            correlation_id=data.get("correlation_id"),
            parent_message_id=data.get("parent_message_id"),
            processing_time_ms=data.get("processing_time_ms"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3)
        )


@dataclass
class MessageBatch:
    """複数メッセージの一括処理用"""
    batch_id: str
    messages: List[AgentMessage]
    created_at: datetime
    priority: Priority
    
    def __post_init__(self):
        if not self.batch_id:
            self.batch_id = str(uuid.uuid4())
    
    def add_message(self, message: AgentMessage):
        """メッセージを追加"""
        self.messages.append(message)
    
    def get_by_type(self, message_type: MessageType) -> List[AgentMessage]:
        """タイプ別にメッセージを取得"""
        return [msg for msg in self.messages if msg.message_type == message_type]
    
    def get_by_sender(self, sender_id: str) -> List[AgentMessage]:
        """送信者別にメッセージを取得"""
        return [msg for msg in self.messages if msg.sender_id == sender_id]