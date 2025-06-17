"""
交渉マネージャーエージェント

@description 複数の専門エージェントを統括し、交渉プロセス全体を管理
@author InfuMatch Development Team
@version 2.0.0
"""

import logging
import asyncio
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from ..base_agent import BaseAgent, AgentConfig
from .agent_message import AgentMessage, MessageType, Priority
from .negotiation_state import NegotiationState, NegotiationStage, Sentiment, RiskLevel, DecisionRecord
from .base_orchestrated_agent import BaseOrchestratedAgent


logger = logging.getLogger(__name__)


class NegotiationManager(BaseAgent):
    """
    交渉マネージャー
    
    複数の専門エージェントを統括し、交渉プロセス全体を最適化する
    メインコーディネーターとして機能
    """
    
    def __init__(self):
        """マネージャーの初期化"""
        config = AgentConfig(
            name="NegotiationManager",
            model_name="gemini-1.5-pro",
            temperature=0.3,  # 判断の一貫性を重視
            max_output_tokens=2048,
            system_instruction=self._get_manager_instruction()
        )
        super().__init__(config)
        
        self.manager_id = "negotiation_manager"
        self.registered_agents: Dict[str, BaseOrchestratedAgent] = {}
        self.active_negotiations: Dict[str, NegotiationState] = {}
        
        # 評価基準の定義
        self.evaluation_criteria = {
            "accuracy": 0.25,
            "relevance": 0.25,
            "creativity": 0.15,
            "risk_awareness": 0.20,
            "efficiency": 0.15
        }
        
        # 品質基準
        self.quality_thresholds = {
            "minimum_acceptable": 0.60,
            "good_quality": 0.75,
            "excellent_quality": 0.90
        }
        
        logger.info("🎭 NegotiationManager 初期化完了")
    
    def register_agent(self, agent: BaseOrchestratedAgent):
        """専門エージェントを登録"""
        self.registered_agents[agent.agent_id] = agent
        logger.info(f"📝 エージェント登録: {agent.agent_id} ({agent.specialization})")
    
    def unregister_agent(self, agent_id: str):
        """エージェントの登録を解除"""
        if agent_id in self.registered_agents:
            del self.registered_agents[agent_id]
            logger.info(f"🗑️ エージェント登録解除: {agent_id}")
    
    async def start_negotiation(
        self,
        thread_id: str,
        new_message: str,
        company_settings: Dict[str, Any],
        conversation_history: List[Dict[str, Any]] = None,
        custom_instructions: str = ""
    ) -> Dict[str, Any]:
        """
        新しい交渉プロセスを開始
        
        Args:
            thread_id: スレッドID
            new_message: 新しいメッセージ
            company_settings: 企業設定
            conversation_history: 会話履歴
            custom_instructions: カスタム指示
            
        Returns:
            Dict: 交渉結果
        """
        negotiation_id = str(uuid.uuid4())
        
        logger.info(f"🚀 新しい交渉開始: {negotiation_id}")
        
        # 交渉状態を初期化
        state = NegotiationState(
            negotiation_id=negotiation_id,
            thread_id=thread_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            current_stage=NegotiationStage.INITIAL_CONTACT,
            sentiment=Sentiment.NEUTRAL,
            risk_level=RiskLevel.LOW,
            company_info=company_settings,
            influencer_info={},
            conversation_history=conversation_history or [],
            negotiation_constraints={"custom_instructions": custom_instructions}
        )
        
        # アクティブな交渉として登録
        self.active_negotiations[negotiation_id] = state
        
        try:
            # 交渉プロセスを実行
            result = await self._execute_negotiation_process(state, new_message)
            
            logger.info(f"✅ 交渉プロセス完了: {negotiation_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ 交渉プロセス失敗: {negotiation_id}: {str(e)}")
            
            # エラー時のフォールバック応答
            return {
                "success": False,
                "error": str(e),
                "content": "申し訳ございません。システムエラーが発生しました。改めてご連絡いたします。",
                "metadata": {
                    "negotiation_id": negotiation_id,
                    "error_stage": state.current_stage.value
                }
            }
        
        finally:
            # 交渉完了時のクリーンアップ
            if negotiation_id in self.active_negotiations:
                # 実際の実装では永続化を行う
                logger.info(f"💾 交渉状態を永続化: {negotiation_id}")
    
    async def _execute_negotiation_process(self, state: NegotiationState, new_message: str) -> Dict[str, Any]:
        """
        交渉プロセスの実行
        
        Args:
            state: 交渉状態
            new_message: 新しいメッセージ
            
        Returns:
            Dict: 処理結果
        """
        
        # Phase 1: 初期分析 - 複数エージェント並行実行
        analysis_results = await self._phase1_initial_analysis(state, new_message)
        
        # Phase 2: 戦略立案 - 分析結果に基づく戦略決定
        strategy_results = await self._phase2_strategy_planning(state, analysis_results)
        
        # Phase 3: 文章生成 - 戦略に基づく返信生成
        communication_results = await self._phase3_communication_generation(state, strategy_results)
        
        # Phase 4: 最終評価・品質チェック
        final_result = await self._phase4_final_evaluation(state, communication_results)
        
        return final_result
    
    async def _phase1_initial_analysis(self, state: NegotiationState, new_message: str) -> Dict[str, Any]:
        """Phase 1: 初期分析フェーズ"""
        logger.info("🔍 Phase 1: 初期分析開始")
        
        # 並行実行するタスク
        tasks = []
        correlation_id = str(uuid.uuid4())
        
        # Context Agent: 文脈分析
        if "context_agent" in self.registered_agents:
            context_task = self._request_agent_task(
                "context_agent",
                "analyze_context",
                {
                    "new_message": new_message,
                    "conversation_history": state.conversation_history,
                    "company_info": state.company_info
                },
                correlation_id
            )
            tasks.append(("context", context_task))
        
        # Analysis Agent: メッセージ分析
        if "analysis_agent" in self.registered_agents:
            analysis_task = self._request_agent_task(
                "analysis_agent",
                "analyze_message",
                {
                    "message": new_message,
                    "context": state.context_memory
                },
                correlation_id
            )
            tasks.append(("analysis", analysis_task))
        
        # Risk Agent: リスク評価
        if "risk_agent" in self.registered_agents:
            risk_task = self._request_agent_task(
                "risk_agent",
                "assess_risks",
                {
                    "message": new_message,
                    "current_stage": state.current_stage.value,
                    "company_info": state.company_info
                },
                correlation_id
            )
            tasks.append(("risk", risk_task))
        
        # 並行実行
        results = {}
        if tasks:
            task_results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
            
            for i, (task_name, _) in enumerate(tasks):
                if not isinstance(task_results[i], Exception):
                    results[task_name] = task_results[i]
                else:
                    logger.error(f"❌ {task_name} タスク失敗: {task_results[i]}")
                    results[task_name] = {"error": str(task_results[i]), "confidence": 0.0}
        
        # 分析結果を状態に記録
        state.add_agent_result("phase1_analysis", results, self._calculate_phase_confidence(results), 0)
        
        logger.info(f"✅ Phase 1 完了: {len(results)} エージェント結果")
        return results
    
    async def _phase2_strategy_planning(self, state: NegotiationState, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 2: 戦略立案フェーズ"""
        logger.info("🎯 Phase 2: 戦略立案開始")
        
        tasks = []
        correlation_id = str(uuid.uuid4())
        
        # Strategy Agent: 交渉戦略
        if "strategy_agent" in self.registered_agents:
            strategy_task = self._request_agent_task(
                "strategy_agent",
                "plan_strategy",
                {
                    "analysis_results": analysis_results,
                    "current_stage": state.current_stage.value,
                    "negotiation_history": state.conversation_history,
                    "custom_instructions": state.negotiation_constraints.get("custom_instructions", "")
                },
                correlation_id
            )
            tasks.append(("strategy", strategy_task))
        
        # Pricing Agent: 価格戦略
        if "pricing_agent" in self.registered_agents:
            pricing_task = self._request_agent_task(
                "pricing_agent",
                "calculate_pricing",
                {
                    "influencer_info": state.influencer_info,
                    "company_budget": state.company_info.get("budget", {}),
                    "market_conditions": analysis_results.get("analysis", {})
                },
                correlation_id
            )
            tasks.append(("pricing", pricing_task))
        
        # 並行実行
        results = {}
        if tasks:
            task_results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
            
            for i, (task_name, _) in enumerate(tasks):
                if not isinstance(task_results[i], Exception):
                    results[task_name] = task_results[i]
                else:
                    logger.error(f"❌ {task_name} タスク失敗: {task_results[i]}")
                    results[task_name] = {"error": str(task_results[i]), "confidence": 0.0}
        
        # 戦略統合・最適化
        integrated_strategy = await self._integrate_strategies(results, state)
        results["integrated_strategy"] = integrated_strategy
        
        # 戦略結果を状態に記録
        state.add_agent_result("phase2_strategy", results, self._calculate_phase_confidence(results), 0)
        
        logger.info(f"✅ Phase 2 完了: 統合戦略信頼度 {integrated_strategy.get('confidence', 0.0):.2f}")
        return results
    
    async def _phase3_communication_generation(self, state: NegotiationState, strategy_results: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 3: 文章生成フェーズ"""
        logger.info("💬 Phase 3: 文章生成開始")
        
        # Communication Agent: プロ文章生成
        if "communication_agent" not in self.registered_agents:
            # フォールバック: 簡単な返信生成
            return {
                "primary_response": {
                    "content": "ご連絡ありがとうございます。詳細について改めてご連絡いたします。",
                    "confidence": 0.3,
                    "reasoning": "Communication Agentが利用できないため基本応答"
                }
            }
        
        correlation_id = str(uuid.uuid4())
        
        # メイン返信生成
        communication_task = self._request_agent_task(
            "communication_agent",
            "generate_response",
            {
                "strategy": strategy_results.get("integrated_strategy", {}),
                "analysis": strategy_results,
                "company_info": state.company_info,
                "custom_instructions": state.negotiation_constraints.get("custom_instructions", "")
            },
            correlation_id
        )
        
        try:
            communication_result = await communication_task
            
            # 複数パターン生成を要求
            if communication_result.get("confidence", 0.0) >= self.quality_thresholds["good_quality"]:
                # 高品質なので複数バリエーション生成
                variations = await self._generate_response_variations(communication_result, state)
                communication_result["variations"] = variations
            
            # 文章生成結果を状態に記録
            state.add_agent_result("phase3_communication", communication_result, 
                                 communication_result.get("confidence", 0.0), 0)
            
            logger.info(f"✅ Phase 3 完了: 文章品質 {communication_result.get('confidence', 0.0):.2f}")
            return {"primary_response": communication_result}
            
        except Exception as e:
            logger.error(f"❌ Phase 3 失敗: {str(e)}")
            return {
                "primary_response": {
                    "content": "申し訳ございません。改めてご連絡いたします。",
                    "confidence": 0.2,
                    "error": str(e)
                }
            }
    
    async def _phase4_final_evaluation(self, state: NegotiationState, communication_results: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 4: 最終評価フェーズ"""
        logger.info("⚖️ Phase 4: 最終評価開始")
        
        primary_response = communication_results.get("primary_response", {})
        
        # 品質評価
        quality_score = await self._evaluate_response_quality(primary_response, state)
        
        # 最終判定
        if quality_score >= self.quality_thresholds["minimum_acceptable"]:
            # 合格: そのまま返却
            result = {
                "success": True,
                "content": primary_response.get("content", ""),
                "metadata": {
                    "negotiation_id": state.negotiation_id,
                    "stage": state.current_stage.value,
                    "quality_score": quality_score,
                    "confidence": primary_response.get("confidence", 0.0),
                    "ai_service": "Multi-Agent Orchestration",
                    "agents_used": list(self.registered_agents.keys())
                },
                "ai_thinking": self._generate_thinking_process(state)
            }
        else:
            # 不合格: 改善が必要
            logger.warning(f"⚠️ 品質不足 (スコア: {quality_score:.2f}), 改善処理...")
            
            # 簡易改善処理
            improved_content = await self._improve_response(primary_response, state)
            
            result = {
                "success": True,
                "content": improved_content,
                "metadata": {
                    "negotiation_id": state.negotiation_id,
                    "stage": state.current_stage.value,
                    "quality_score": quality_score,
                    "improved": True,
                    "ai_service": "Multi-Agent Orchestration (Improved)"
                },
                "ai_thinking": self._generate_thinking_process(state)
            }
        
        # 交渉状態を更新
        state.update_stage(self._determine_next_stage(state, primary_response))
        state.metrics.total_exchanges += 1
        state.metrics.update_quality_avg(quality_score)
        
        logger.info(f"✅ Phase 4 完了: 最終品質スコア {quality_score:.2f}")
        return result
    
    async def _request_agent_task(self, agent_id: str, task_type: str, payload: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """エージェントにタスクを依頼"""
        if agent_id not in self.registered_agents:
            raise ValueError(f"Agent {agent_id} not registered")
        
        agent = self.registered_agents[agent_id]
        
        # タスクメッセージを作成
        request_message = AgentMessage.create_task_request(
            sender_id=self.manager_id,
            recipient_id=agent_id,
            task_type=task_type,
            payload=payload,
            correlation_id=correlation_id
        )
        
        # 交渉状態を取得（仮実装）
        state = list(self.active_negotiations.values())[0] if self.active_negotiations else None
        
        # エージェントに処理を依頼
        response_message = await agent.process_message(request_message, state)
        
        if response_message.message_type == MessageType.TASK_RESULT:
            return response_message.payload
        elif response_message.message_type == MessageType.ERROR_REPORT:
            raise Exception(response_message.payload.get("error_message", "Agent task failed"))
        else:
            raise Exception(f"Unexpected response type: {response_message.message_type}")
    
    def _calculate_phase_confidence(self, results: Dict[str, Any]) -> float:
        """フェーズ全体の信頼度を計算"""
        if not results:
            return 0.0
        
        confidences = [
            result.get("confidence", 0.0) 
            for result in results.values() 
            if isinstance(result, dict)
        ]
        
        if not confidences:
            return 0.0
        
        return sum(confidences) / len(confidences)
    
    async def _integrate_strategies(self, strategy_results: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """戦略を統合・最適化"""
        # 簡易統合ロジック
        strategy = strategy_results.get("strategy", {})
        pricing = strategy_results.get("pricing", {})
        
        integrated = {
            "approach": strategy.get("approach", "collaborative"),
            "key_messages": strategy.get("key_messages", ["関係構築を重視"]),
            "pricing_strategy": pricing.get("strategy", "standard"),
            "confidence": min(
                strategy.get("confidence", 0.5),
                pricing.get("confidence", 0.5)
            )
        }
        
        return integrated
    
    async def _generate_response_variations(self, base_response: Dict[str, Any], state: NegotiationState) -> List[Dict[str, Any]]:
        """返信のバリエーションを生成"""
        # 簡易実装
        base_content = base_response.get("content", "")
        
        variations = [
            {
                "type": "formal",
                "content": base_content.replace("です。", "であります。"),
                "confidence": base_response.get("confidence", 0.0) * 0.9
            },
            {
                "type": "casual",
                "content": base_content.replace("申し上げます", "お願いします"),
                "confidence": base_response.get("confidence", 0.0) * 0.85
            }
        ]
        
        return variations
    
    async def _evaluate_response_quality(self, response: Dict[str, Any], state: NegotiationState) -> float:
        """返信品質を評価"""
        # 簡易品質評価
        content = response.get("content", "")
        confidence = response.get("confidence", 0.0)
        
        # 基本的な品質チェック
        length_score = min(len(content) / 100, 1.0)  # 長さによる評価
        confidence_score = confidence
        completeness_score = 1.0 if "田中" in content else 0.5  # 署名の存在
        
        overall_score = (length_score + confidence_score + completeness_score) / 3
        return min(overall_score, 1.0)
    
    async def _improve_response(self, response: Dict[str, Any], state: NegotiationState) -> str:
        """返信を改善"""
        content = response.get("content", "")
        
        # 簡易改善処理
        if not content.endswith("田中"):
            content += "\n\nInfuMatch 田中美咲"
        
        if len(content) < 50:
            content = "いつもお世話になっております。\n\n" + content
        
        return content
    
    def _determine_next_stage(self, state: NegotiationState, response: Dict[str, Any]) -> NegotiationStage:
        """次の交渉段階を決定"""
        # 簡易実装: 現在のステージを維持または進行
        current = state.current_stage
        
        if current == NegotiationStage.INITIAL_CONTACT:
            return NegotiationStage.INTEREST_DISCOVERY
        elif current == NegotiationStage.INTEREST_DISCOVERY:
            return NegotiationStage.REQUIREMENT_GATHERING
        else:
            return current
    
    def _generate_thinking_process(self, state: NegotiationState) -> Dict[str, Any]:
        """AI思考過程を生成"""
        return {
            "orchestration_summary": f"マルチエージェント協調による交渉処理 ({len(self.registered_agents)}エージェント)",
            "stage_analysis": f"現在の交渉段階: {state.current_stage.value}",
            "agent_coordination": f"エージェント間協調スコア: {state.metrics.agent_coordination_score:.2f}",
            "quality_optimization": "品質評価システムにより最適化済み",
            "decision_confidence": f"統合判断信頼度: {state.metrics.message_quality_avg:.2f}"
        }
    
    def _get_manager_instruction(self) -> str:
        """マネージャー用システムインストラクション"""
        return """
あなたは複数のAIエージェントを統括する交渉マネージャーです。

【役割】
- 複数の専門エージェントの協調を管理
- 各エージェントの成果を評価・統合
- 交渉プロセス全体の品質保証
- 次のアクションの決定

【判断基準】
- 品質第一: 60%未満は改善必須
- 効率性: 無駄な処理を避ける
- 一貫性: 交渉方針の統一
- リスク管理: 適切なリスク評価

【出力】
- 簡潔で明確な判断
- 論理的な根拠の提示
- 改善案の具体的提案
"""
    
    def get_orchestration_status(self) -> Dict[str, Any]:
        """オーケストレーションステータスを取得"""
        return {
            "manager_id": self.manager_id,
            "registered_agents": {
                agent_id: agent.get_status_summary()
                for agent_id, agent in self.registered_agents.items()
            },
            "active_negotiations": len(self.active_negotiations),
            "evaluation_criteria": self.evaluation_criteria,
            "quality_thresholds": self.quality_thresholds
        }
    
    # BaseAgent抽象メソッドの実装
    def get_capabilities(self) -> Dict[str, Any]:
        """マネージャーの能力情報を返す"""
        return {
            "agent_type": "negotiation_manager",
            "specialization": "multi_agent_orchestration",
            "registered_agents": len(self.registered_agents),
            "active_negotiations": len(self.active_negotiations),
            "capabilities": [
                "agent_coordination",
                "quality_evaluation", 
                "strategy_integration",
                "performance_monitoring"
            ]
        }
    
    async def process(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """マネージャーの処理メソッド（交渉開始をラップ）"""
        if "action" in task_data and task_data["action"] == "start_negotiation":
            return await self.start_negotiation(
                thread_id=task_data.get("thread_id", ""),
                new_message=task_data.get("new_message", ""),
                company_settings=task_data.get("company_settings", {}),
                conversation_history=task_data.get("conversation_history", []),
                custom_instructions=task_data.get("custom_instructions", "")
            )
        else:
            return {
                "success": False,
                "error": "Unsupported task action",
                "supported_actions": ["start_negotiation"]
            }