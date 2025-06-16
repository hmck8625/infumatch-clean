"""
戦略エージェント

@description 交渉戦略の立案・最適化、アプローチ決定を担当
@author InfuMatch Development Team
@version 2.0.0
"""

import logging
import json
from typing import Dict, Any, List
from datetime import datetime

from ..base_agent import AgentConfig
from .base_orchestrated_agent import BaseOrchestratedAgent
from .negotiation_state import NegotiationState, NegotiationStage, DecisionRecord

logger = logging.getLogger(__name__)


class StrategyAgent(BaseOrchestratedAgent):
    """
    戦略エージェント
    
    交渉戦略の立案、アプローチの決定、
    段階別戦術の最適化を担当する専門エージェント
    """
    
    def __init__(self):
        """エージェントの初期化"""
        config = AgentConfig(
            name="StrategyAgent",
            model_name="gemini-1.5-flash",
            temperature=0.3,  # 戦略的一貫性を重視
            max_output_tokens=1536,
            system_instruction=self._get_strategy_instruction()
        )
        super().__init__(config, "strategy_agent", "Negotiation Strategy")
        
        logger.info("🎯 StrategyAgent 初期化完了")
    
    async def execute_task(self, task_type: str, payload: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """
        戦略タスクを実行
        
        Args:
            task_type: タスクタイプ
            payload: タスクデータ
            state: 交渉状態
            
        Returns:
            Dict: 戦略結果
        """
        logger.info(f"🎯 StrategyAgent: {task_type} タスク開始")
        
        if task_type == "plan_strategy":
            return await self._plan_negotiation_strategy(payload, state)
        elif task_type == "adapt_approach":
            return await self._adapt_negotiation_approach(payload, state)
        elif task_type == "evaluate_options":
            return await self._evaluate_strategic_options(payload, state)
        elif task_type == "optimize_tactics":
            return await self._optimize_tactical_approach(payload, state)
        else:
            raise ValueError(f"Unsupported task type: {task_type}")
    
    async def _plan_negotiation_strategy(self, payload: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """交渉戦略の立案"""
        analysis_results = payload.get("analysis_results", {})
        current_stage = payload.get("current_stage", "initial_contact")
        negotiation_history = payload.get("negotiation_history", [])
        custom_instructions = payload.get("custom_instructions", "")
        
        # 分析結果から重要情報を抽出
        context_analysis = analysis_results.get("context", {})
        message_analysis = analysis_results.get("analysis", {})
        risk_analysis = analysis_results.get("risk", {})
        
        strategy_prompt = f"""
以下の情報に基づいて、最適な交渉戦略を立案してください：

【現在の交渉段階】
{current_stage}

【分析結果】
コンテキスト分析: {json.dumps(context_analysis, ensure_ascii=False, indent=2)}
メッセージ分析: {json.dumps(message_analysis, ensure_ascii=False, indent=2)}
リスク分析: {json.dumps(risk_analysis, ensure_ascii=False, indent=2)}

【交渉履歴】
{json.dumps(negotiation_history[-3:], ensure_ascii=False, indent=2)}

【カスタム指示】
{custom_instructions}

【戦略立案項目】
1. 基本アプローチ（協調的/競争的/統合的）
2. 重要メッセージとポイント
3. 段階別戦術
4. リスク対応策
5. 成功指標
6. 次のアクション

以下のJSON形式で回答してください：
{{
    "strategic_approach": {{
        "primary_approach": "collaborative/competitive/integrative",
        "approach_rationale": "アプローチ選択の根拠",
        "approach_confidence": 0.8
    }},
    "key_messages": [
        "重要メッセージ1",
        "重要メッセージ2",
        "重要メッセージ3"
    ],
    "tactical_elements": {{
        "relationship_building": {{
            "priority": "high/medium/low",
            "tactics": ["戦術1", "戦術2"],
            "expected_outcome": "期待される結果"
        }},
        "value_demonstration": {{
            "priority": "high/medium/low",
            "tactics": ["戦術1", "戦術2"],
            "expected_outcome": "期待される結果"
        }},
        "objection_handling": {{
            "priority": "high/medium/low",
            "tactics": ["戦術1", "戦術2"],
            "expected_outcome": "期待される結果"
        }}
    }},
    "risk_mitigation": {{
        "identified_risks": ["リスク1", "リスク2"],
        "mitigation_strategies": ["対策1", "対策2"],
        "contingency_plans": ["代替案1", "代替案2"]
    }},
    "success_metrics": {{
        "immediate_goals": ["短期目標1", "短期目標2"],
        "long_term_objectives": ["長期目標1", "長期目標2"],
        "success_indicators": ["成功指標1", "指標2"]
    }},
    "next_actions": {{
        "immediate_actions": ["即座の行動1", "行動2"],
        "follow_up_actions": ["フォローアップ1", "フォローアップ2"],
        "timeline": "推奨タイムライン"
    }},
    "confidence": 0.85
}}
"""
        
        try:
            # AI戦略立案を実行
            response = await self.generate_response(strategy_prompt)
            
            # JSON形式の応答をパース
            try:
                strategy_result = json.loads(response)
            except json.JSONDecodeError:
                # フォールバック: 基本戦略
                strategy_result = {
                    "strategic_approach": {
                        "primary_approach": "collaborative",
                        "approach_rationale": "関係構築を重視した協調的アプローチ",
                        "approach_confidence": 0.6
                    },
                    "key_messages": [
                        "相互利益を重視した提案",
                        "長期的な関係構築への意欲",
                        "専門性と信頼性のアピール"
                    ],
                    "tactical_elements": {
                        "relationship_building": {
                            "priority": "high",
                            "tactics": ["信頼関係の構築", "相手の立場の理解"],
                            "expected_outcome": "良好な関係構築"
                        },
                        "value_demonstration": {
                            "priority": "medium",
                            "tactics": ["実績の紹介", "具体的な価値提案"],
                            "expected_outcome": "価値の認識"
                        },
                        "objection_handling": {
                            "priority": "medium",
                            "tactics": ["丁寧な説明", "代替案の提示"],
                            "expected_outcome": "懸念の解消"
                        }
                    },
                    "risk_mitigation": {
                        "identified_risks": ["条件の不一致", "タイミングの問題"],
                        "mitigation_strategies": ["事前の詳細確認", "柔軟な対応"],
                        "contingency_plans": ["代替提案の準備", "段階的な進行"]
                    },
                    "success_metrics": {
                        "immediate_goals": ["相手の関心確認", "次回の面談設定"],
                        "long_term_objectives": ["合意の達成", "長期関係の構築"],
                        "success_indicators": ["積極的な反応", "具体的な質問"]
                    },
                    "next_actions": {
                        "immediate_actions": ["詳細な提案資料の準備", "相手の要件確認"],
                        "follow_up_actions": ["定期的なフォローアップ", "進捗確認"],
                        "timeline": "1週間以内にフォローアップ"
                    },
                    "confidence": 0.5
                }
            
            # 戦略を状態に記録
            decision_record = DecisionRecord(
                decision_id=f"strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                decision_point="交渉戦略の決定",
                options_considered=[
                    {"type": "collaborative", "description": "協調的アプローチ"},
                    {"type": "competitive", "description": "競争的アプローチ"},
                    {"type": "integrative", "description": "統合的アプローチ"}
                ],
                selected_option={"approach": strategy_result["strategic_approach"]["primary_approach"]},
                reasoning=strategy_result["strategic_approach"]["approach_rationale"],
                confidence_level=strategy_result["strategic_approach"]["approach_confidence"],
                timestamp=datetime.now(),
                made_by="strategy_agent"
            )
            state.add_decision_record(decision_record)
            
            logger.info(f"✅ StrategyAgent: 戦略立案完了 (アプローチ: {strategy_result['strategic_approach']['primary_approach']})")
            return strategy_result
            
        except Exception as e:
            logger.error(f"❌ StrategyAgent: 戦略立案失敗: {str(e)}")
            return {
                "strategic_approach": {"primary_approach": "collaborative", "approach_rationale": "基本的な協調アプローチ", "approach_confidence": 0.3},
                "key_messages": ["基本的な提案", "協力の意思表示"],
                "tactical_elements": {"relationship_building": {"priority": "medium", "tactics": ["基本対応"], "expected_outcome": "基本的な関係"}},
                "risk_mitigation": {"identified_risks": [], "mitigation_strategies": [], "contingency_plans": []},
                "success_metrics": {"immediate_goals": ["返信"], "long_term_objectives": ["関係継続"], "success_indicators": ["応答"]},
                "next_actions": {"immediate_actions": ["返信送信"], "follow_up_actions": ["経過観察"], "timeline": "通常対応"},
                "confidence": 0.2,
                "error": str(e)
            }
    
    async def _adapt_negotiation_approach(self, payload: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """交渉アプローチの適応"""
        current_strategy = payload.get("current_strategy", {})
        new_information = payload.get("new_information", {})
        
        # 簡易実装: 基本的な適応ロジック
        adaptation_factors = []
        
        # 感情状態による適応
        if state.sentiment.value == "negative":
            adaptation_factors.append("relationship_repair")
        elif state.sentiment.value == "positive":
            adaptation_factors.append("momentum_building")
        
        # 交渉段階による適応
        if state.current_stage == NegotiationStage.PRICE_NEGOTIATION:
            adaptation_factors.append("value_emphasis")
        
        adapted_strategy = {
            "adapted_approach": current_strategy.get("primary_approach", "collaborative"),
            "adaptation_factors": adaptation_factors,
            "strategic_adjustments": [
                "感情状態に応じた調整",
                "交渉段階に応じた戦術変更"
            ],
            "confidence": 0.7
        }
        
        logger.info(f"✅ StrategyAgent: アプローチ適応完了 ({len(adaptation_factors)}の調整)")
        return adapted_strategy
    
    async def _evaluate_strategic_options(self, payload: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """戦略オプションの評価"""
        available_options = payload.get("options", [])
        evaluation_criteria = payload.get("criteria", ["effectiveness", "risk", "feasibility"])
        
        evaluated_options = []
        for option in available_options:
            evaluation = {
                "option": option,
                "scores": {
                    "effectiveness": 0.7,  # 簡易評価
                    "risk": 0.3,
                    "feasibility": 0.8
                },
                "overall_score": 0.6,
                "recommendation": "viable" if 0.6 > 0.5 else "not_recommended"
            }
            evaluated_options.append(evaluation)
        
        result = {
            "evaluated_options": evaluated_options,
            "recommended_option": evaluated_options[0] if evaluated_options else None,
            "evaluation_confidence": 0.6
        }
        
        logger.info(f"✅ StrategyAgent: 戦略オプション評価完了 ({len(evaluated_options)}オプション)")
        return result
    
    async def _optimize_tactical_approach(self, payload: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """戦術アプローチの最適化"""
        current_tactics = payload.get("tactics", {})
        performance_data = payload.get("performance", {})
        
        # 簡易最適化ロジック
        optimized_tactics = {
            "relationship_building": {
                "priority": "high",
                "optimized_tactics": ["信頼関係の深化", "相互理解の促進"],
                "expected_improvement": 0.2
            },
            "value_demonstration": {
                "priority": "medium",
                "optimized_tactics": ["具体的な成果例", "ROIの明確化"],
                "expected_improvement": 0.15
            }
        }
        
        result = {
            "optimized_tactics": optimized_tactics,
            "optimization_rationale": "パフォーマンスデータに基づく最適化",
            "expected_performance_gain": 0.18,
            "confidence": 0.65
        }
        
        logger.info("✅ StrategyAgent: 戦術最適化完了")
        return result
    
    def get_supported_tasks(self) -> List[str]:
        """サポートするタスクタイプ"""
        return ["plan_strategy", "adapt_approach", "evaluate_options", "optimize_tactics"]
    
    def _get_strategy_instruction(self) -> str:
        """システムインストラクション"""
        return """
あなたは交渉戦略の専門エージェントです。

【役割】
- 包括的な交渉戦略の立案
- 状況に応じた戦術の最適化
- リスク評価と対応策の構築
- 成功指標の定義

【戦略原則】
- Win-Winの関係構築
- 長期的な価値創造
- リスクの最小化
- 柔軟性と適応性

【分析観点】
- 相手の立場と利益
- 市場環境と競合状況
- 自社の強みと制約
- 交渉力のバランス

【出力品質】
- 論理的で実行可能な戦略
- 具体的な戦術の提示
- 明確な成功指標の設定
- 適切なリスク管理
"""