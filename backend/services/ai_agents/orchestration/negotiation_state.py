"""
交渉状態管理システム

@description 交渉プロセス全体の状態を追跡・管理
@author InfuMatch Development Team
@version 2.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional
import json


class NegotiationStage(Enum):
    """詳細な交渉段階定義"""
    
    # 初期段階
    INITIAL_CONTACT = "initial_contact"           # 初回接触
    INTEREST_DISCOVERY = "interest_discovery"     # 興味・関心の探索
    RAPPORT_BUILDING = "rapport_building"         # 関係構築
    
    # 情報収集段階
    REQUIREMENT_GATHERING = "requirement_gathering"  # 要件・ニーズの確認
    CAPABILITY_PRESENTATION = "capability_presentation"  # 能力・実績の提示
    MUTUAL_EVALUATION = "mutual_evaluation"       # 相互評価
    
    # 提案段階
    PROPOSAL_PREPARATION = "proposal_preparation"  # 提案準備
    PROPOSAL_PRESENTATION = "proposal_presentation"  # 提案・条件提示
    CLARIFICATION = "clarification"               # 提案内容の説明・質疑応答
    
    # 交渉段階
    NEGOTIATION_ACTIVE = "negotiation_active"     # 積極的な条件交渉
    PRICE_NEGOTIATION = "price_negotiation"       # 価格交渉
    TERMS_ADJUSTMENT = "terms_adjustment"         # 条件調整
    
    # 決定段階
    FINAL_ADJUSTMENT = "final_adjustment"         # 最終調整
    DECISION_PENDING = "decision_pending"         # 相手方意思決定待ち
    CONTRACT_PREPARATION = "contract_preparation"  # 契約準備
    
    # 完了・フォロー段階
    DEAL_CLOSED = "deal_closed"                   # 成約
    POST_DEAL_FOLLOW = "post_deal_follow"         # 契約後フォロー
    
    # 特殊状態
    STALLED = "stalled"                           # 停滞・保留中
    OBJECTION_HANDLING = "objection_handling"     # 異議処理中
    COMPETITOR_COMPARISON = "competitor_comparison"  # 競合比較中
    LOST = "lost"                                 # 失注
    WITHDRAWN = "withdrawn"                       # 取り下げ


class Sentiment(Enum):
    """感情状態"""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    CONCERNED = "concerned"
    NEGATIVE = "negative"
    HOSTILE = "hostile"


class RiskLevel(Enum):
    """リスクレベル"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AgentPerformance:
    """エージェントパフォーマンス記録"""
    agent_id: str
    task_type: str
    confidence_score: float
    processing_time_ms: int
    quality_score: float  # マネージャーによる評価
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "task_type": self.task_type,
            "confidence_score": self.confidence_score,
            "processing_time_ms": self.processing_time_ms,
            "quality_score": self.quality_score,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class DecisionRecord:
    """意思決定記録"""
    decision_id: str
    decision_point: str
    options_considered: List[Dict[str, Any]]
    selected_option: Dict[str, Any]
    reasoning: str
    confidence_level: float
    timestamp: datetime
    made_by: str  # エージェントID
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "decision_point": self.decision_point,
            "options_considered": self.options_considered,
            "selected_option": self.selected_option,
            "reasoning": self.reasoning,
            "confidence_level": self.confidence_level,
            "timestamp": self.timestamp.isoformat(),
            "made_by": self.made_by
        }


@dataclass
class NegotiationMetrics:
    """交渉メトリクス"""
    
    # 基本メトリクス
    total_exchanges: int = 0
    response_time_avg_ms: int = 0
    success_probability: float = 0.0
    
    # 品質メトリクス
    message_quality_avg: float = 0.0
    strategy_effectiveness: float = 0.0
    risk_score: float = 0.0
    
    # 進捗メトリクス
    stage_progression_rate: float = 0.0  # 段階進行率
    stagnation_periods: int = 0  # 停滞回数
    
    # エージェント協調メトリクス
    agent_coordination_score: float = 0.0
    consensus_achievement_rate: float = 0.0
    
    def update_quality_avg(self, new_score: float):
        """品質平均の更新"""
        if self.total_exchanges == 0:
            self.message_quality_avg = new_score
        else:
            total_score = self.message_quality_avg * self.total_exchanges
            self.message_quality_avg = (total_score + new_score) / (self.total_exchanges + 1)


@dataclass
class NegotiationState:
    """
    交渉状態の包括的管理
    
    交渉プロセス全体の状態、エージェントの成果、意思決定履歴を統合管理
    """
    
    # 基本情報
    negotiation_id: str
    thread_id: str
    created_at: datetime
    updated_at: datetime
    
    # 現在の状態
    current_stage: NegotiationStage
    sentiment: Sentiment
    risk_level: RiskLevel
    
    # 参加者情報
    company_info: Dict[str, Any]
    influencer_info: Dict[str, Any]
    
    # 交渉コンテキスト
    context_memory: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # エージェント成果
    agent_results: Dict[str, Any] = field(default_factory=dict)  # エージェントID -> 最新結果
    agent_performance_history: List[AgentPerformance] = field(default_factory=list)
    
    # 意思決定履歴
    decision_history: List[DecisionRecord] = field(default_factory=list)
    
    # アクション管理
    next_actions: List[str] = field(default_factory=list)
    pending_tasks: Dict[str, Any] = field(default_factory=dict)  # タスクID -> タスク詳細
    
    # メトリクス
    metrics: NegotiationMetrics = field(default_factory=NegotiationMetrics)
    
    # 設定・制約
    negotiation_constraints: Dict[str, Any] = field(default_factory=dict)
    success_criteria: Dict[str, Any] = field(default_factory=dict)
    
    def update_stage(self, new_stage: NegotiationStage, reason: str = ""):
        """交渉段階を更新"""
        old_stage = self.current_stage
        self.current_stage = new_stage
        self.updated_at = datetime.now()
        
        # 段階変更を記録
        stage_change_record = {
            "from_stage": old_stage.value,
            "to_stage": new_stage.value,
            "reason": reason,
            "timestamp": self.updated_at.isoformat()
        }
        
        if "stage_changes" not in self.context_memory:
            self.context_memory["stage_changes"] = []
        self.context_memory["stage_changes"].append(stage_change_record)
    
    def add_agent_result(self, agent_id: str, result: Dict[str, Any], confidence: float, processing_time_ms: int):
        """エージェントの成果を追加"""
        self.agent_results[agent_id] = result
        self.updated_at = datetime.now()
        
        # パフォーマンス記録を追加
        performance = AgentPerformance(
            agent_id=agent_id,
            task_type=result.get("task_type", "unknown"),
            confidence_score=confidence,
            processing_time_ms=processing_time_ms,
            quality_score=0.0,  # 後でマネージャーが評価
            timestamp=self.updated_at
        )
        self.agent_performance_history.append(performance)
    
    def add_decision_record(self, decision: DecisionRecord):
        """意思決定記録を追加"""
        self.decision_history.append(decision)
        self.updated_at = datetime.now()
    
    def update_sentiment(self, new_sentiment: Sentiment, confidence: float = 1.0):
        """感情状態を更新"""
        self.sentiment = new_sentiment
        self.updated_at = datetime.now()
        
        # 感情変化を記録
        sentiment_record = {
            "sentiment": new_sentiment.value,
            "confidence": confidence,
            "timestamp": self.updated_at.isoformat()
        }
        
        if "sentiment_history" not in self.context_memory:
            self.context_memory["sentiment_history"] = []
        self.context_memory["sentiment_history"].append(sentiment_record)
    
    def update_risk_level(self, new_risk: RiskLevel, factors: List[str] = None):
        """リスクレベルを更新"""
        self.risk_level = new_risk
        self.updated_at = datetime.now()
        
        # リスク変化を記録
        risk_record = {
            "risk_level": new_risk.value,
            "risk_factors": factors or [],
            "timestamp": self.updated_at.isoformat()
        }
        
        if "risk_history" not in self.context_memory:
            self.context_memory["risk_history"] = []
        self.context_memory["risk_history"].append(risk_record)
    
    def get_latest_agent_performance(self, agent_id: str) -> Optional[AgentPerformance]:
        """特定エージェントの最新パフォーマンスを取得"""
        agent_performances = [p for p in self.agent_performance_history if p.agent_id == agent_id]
        return max(agent_performances, key=lambda p: p.timestamp) if agent_performances else None
    
    def calculate_overall_progress(self) -> float:
        """全体進捗を計算（0.0-1.0）"""
        stage_weights = {
            NegotiationStage.INITIAL_CONTACT: 0.1,
            NegotiationStage.INTEREST_DISCOVERY: 0.2,
            NegotiationStage.RAPPORT_BUILDING: 0.25,
            NegotiationStage.REQUIREMENT_GATHERING: 0.35,
            NegotiationStage.CAPABILITY_PRESENTATION: 0.45,
            NegotiationStage.PROPOSAL_PRESENTATION: 0.6,
            NegotiationStage.NEGOTIATION_ACTIVE: 0.7,
            NegotiationStage.PRICE_NEGOTIATION: 0.75,
            NegotiationStage.FINAL_ADJUSTMENT: 0.9,
            NegotiationStage.DEAL_CLOSED: 1.0,
            NegotiationStage.LOST: 0.0,
            NegotiationStage.WITHDRAWN: 0.0
        }
        return stage_weights.get(self.current_stage, 0.5)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "negotiation_id": self.negotiation_id,
            "thread_id": self.thread_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "current_stage": self.current_stage.value,
            "sentiment": self.sentiment.value,
            "risk_level": self.risk_level.value,
            "company_info": self.company_info,
            "influencer_info": self.influencer_info,
            "context_memory": self.context_memory,
            "conversation_history": self.conversation_history,
            "agent_results": self.agent_results,
            "agent_performance_history": [p.to_dict() for p in self.agent_performance_history],
            "decision_history": [d.to_dict() for d in self.decision_history],
            "next_actions": self.next_actions,
            "pending_tasks": self.pending_tasks,
            "metrics": {
                "total_exchanges": self.metrics.total_exchanges,
                "response_time_avg_ms": self.metrics.response_time_avg_ms,
                "success_probability": self.metrics.success_probability,
                "message_quality_avg": self.metrics.message_quality_avg,
                "strategy_effectiveness": self.metrics.strategy_effectiveness,
                "risk_score": self.metrics.risk_score,
                "stage_progression_rate": self.metrics.stage_progression_rate,
                "agent_coordination_score": self.metrics.agent_coordination_score
            },
            "negotiation_constraints": self.negotiation_constraints,
            "success_criteria": self.success_criteria
        }