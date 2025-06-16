"""
リスク評価エージェント

@description リスク分析、リスク管理戦略、予防措置の立案を担当
@author InfuMatch Development Team
@version 2.0.0
"""

import logging
import json
from typing import Dict, Any, List
from datetime import datetime

from ..base_agent import AgentConfig
from .base_orchestrated_agent import BaseOrchestratedAgent
from .negotiation_state import NegotiationState, RiskLevel

logger = logging.getLogger(__name__)


class RiskAgent(BaseOrchestratedAgent):
    """
    リスク評価エージェント
    
    交渉プロセスにおけるリスクの識別・評価、
    リスク軽減策の提案、予防措置の立案を担当する専門エージェント
    """
    
    def __init__(self):
        """エージェントの初期化"""
        config = AgentConfig(
            name="RiskAgent",
            model_name="gemini-1.5-flash",
            temperature=0.1,  # リスク評価の客観性を重視
            max_output_tokens=1536,
            system_instruction=self._get_risk_instruction()
        )
        super().__init__(config, "risk_agent", "Risk Assessment")
        
        # リスクカテゴリとリスク要因の定義
        self.risk_categories = {
            "business_risks": [
                "contract_breach", "payment_delay", "scope_creep",
                "quality_issues", "timeline_conflicts", "budget_overrun"
            ],
            "brand_safety_risks": [
                "content_misalignment", "negative_publicity", "controversial_content",
                "audience_mismatch", "competitor_association", "regulatory_violation"
            ],
            "operational_risks": [
                "communication_breakdown", "resource_constraints", "technical_issues",
                "stakeholder_conflicts", "external_dependencies", "market_changes"
            ],
            "legal_risks": [
                "intellectual_property", "privacy_violations", "disclosure_requirements",
                "advertising_standards", "contract_disputes", "liability_issues"
            ]
        }
        
        logger.info("⚠️ RiskAgent 初期化完了")
    
    async def execute_task(self, task_type: str, payload: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """
        リスク評価タスクを実行
        
        Args:
            task_type: タスクタイプ
            payload: タスクデータ
            state: 交渉状態
            
        Returns:
            Dict: リスク評価結果
        """
        logger.info(f"⚠️ RiskAgent: {task_type} タスク開始")
        
        if task_type == "assess_risks":
            return await self._assess_negotiation_risks(payload, state)
        elif task_type == "evaluate_brand_safety":
            return await self._evaluate_brand_safety(payload, state)
        elif task_type == "monitor_risk_changes":
            return await self._monitor_risk_level_changes(payload, state)
        elif task_type == "develop_mitigation":
            return await self._develop_risk_mitigation_plan(payload, state)
        else:
            raise ValueError(f"Unsupported task type: {task_type}")
    
    async def _assess_negotiation_risks(self, payload: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """交渉リスクの総合評価"""
        message = payload.get("message", "")
        current_stage = payload.get("current_stage", "initial_contact")
        company_info = payload.get("company_info", {})
        
        risk_prompt = f"""
以下の情報に基づいて、交渉プロセスのリスクを包括的に評価してください：

【受信メッセージ】
{message}

【現在の交渉段階】
{current_stage}

【企業情報】
{json.dumps(company_info, ensure_ascii=False, indent=2)}

【リスク評価項目】
1. ビジネスリスク（契約・支払・品質・スケジュール）
2. ブランドセーフティリスク（コンテンツ・評判・適合性）
3. オペレーショナルリスク（コミュニケーション・リソース・技術）
4. コンプライアンスリスク（法的・規制・業界基準）

以下のJSON形式で回答してください：
{{
    "risk_assessment": {{
        "overall_risk_level": "low/medium/high/critical",
        "overall_risk_score": 0.65,
        "risk_trend": "increasing/stable/decreasing"
    }},
    "risk_categories": {{
        "business_risks": {{
            "risk_level": "medium",
            "risk_score": 0.6,
            "identified_risks": [
                {{
                    "risk_type": "payment_delay",
                    "probability": 0.3,
                    "impact": 0.7,
                    "severity": "medium",
                    "description": "支払い遅延のリスク"
                }}
            ]
        }},
        "brand_safety_risks": {{
            "risk_level": "low",
            "risk_score": 0.2,
            "identified_risks": [
                {{
                    "risk_type": "content_misalignment",
                    "probability": 0.2,
                    "impact": 0.5,
                    "severity": "low",
                    "description": "コンテンツ不整合のリスク"
                }}
            ]
        }},
        "operational_risks": {{
            "risk_level": "medium",
            "risk_score": 0.5,
            "identified_risks": [
                {{
                    "risk_type": "communication_breakdown",
                    "probability": 0.4,
                    "impact": 0.6,
                    "severity": "medium",
                    "description": "コミュニケーション不全のリスク"
                }}
            ]
        }},
        "compliance_risks": {{
            "risk_level": "low",
            "risk_score": 0.1,
            "identified_risks": [
                {{
                    "risk_type": "disclosure_requirements",
                    "probability": 0.1,
                    "impact": 0.4,
                    "severity": "low",
                    "description": "開示義務のリスク"
                }}
            ]
        }}
    }},
    "risk_indicators": {{
        "warning_signals": ["注意すべき兆候1", "兆候2"],
        "positive_indicators": ["ポジティブな要因1", "要因2"],
        "monitoring_points": ["監視すべき点1", "点2"]
    }},
    "immediate_actions": {{
        "risk_mitigation_steps": ["即座に取るべき対策1", "対策2"],
        "prevention_measures": ["予防措置1", "措置2"],
        "escalation_triggers": ["エスカレーション条件1", "条件2"]
    }},
    "confidence": 0.8
}}
"""
        
        try:
            # AIリスク評価を実行
            response = await self.generate_response(risk_prompt)
            
            # JSON形式の応答をパース
            try:
                risk_result = json.loads(response)
            except json.JSONDecodeError:
                # フォールバック: 基本リスク評価
                risk_result = self._calculate_fallback_risk_assessment(message, current_stage, company_info)
            
            # リスクレベルを状態に更新
            risk_level_mapping = {
                "low": RiskLevel.LOW,
                "medium": RiskLevel.MEDIUM,
                "high": RiskLevel.HIGH,
                "critical": RiskLevel.CRITICAL
            }
            
            overall_risk = risk_result.get("risk_assessment", {}).get("overall_risk_level", "medium")
            if overall_risk in risk_level_mapping:
                risk_factors = [
                    risk["description"] for category in risk_result.get("risk_categories", {}).values()
                    for risk in category.get("identified_risks", [])
                ]
                state.update_risk_level(risk_level_mapping[overall_risk], risk_factors)
            
            # リスク情報を状態に記録
            state.context_memory["latest_risk_assessment"] = risk_result
            state.context_memory["risk_assessment_timestamp"] = datetime.now().isoformat()
            
            logger.info(f"✅ RiskAgent: リスク評価完了 (レベル: {overall_risk}, スコア: {risk_result.get('risk_assessment', {}).get('overall_risk_score', 0.0):.2f})")
            return risk_result
            
        except Exception as e:
            logger.error(f"❌ RiskAgent: リスク評価失敗: {str(e)}")
            return self._calculate_fallback_risk_assessment(message, current_stage, company_info, error=str(e))
    
    def _calculate_fallback_risk_assessment(self, message: str, current_stage: str, company_info: Dict[str, Any], error: str = None) -> Dict[str, Any]:
        """フォールバックリスク評価"""
        # 基本的なリスク要因の検出
        high_risk_keywords = ["緊急", "問題", "困難", "取消", "変更", "遅延"]
        medium_risk_keywords = ["検討", "調整", "確認", "条件", "予算"]
        
        risk_score = 0.3  # 基本スコア
        
        for keyword in high_risk_keywords:
            if keyword in message:
                risk_score += 0.2
        
        for keyword in medium_risk_keywords:
            if keyword in message:
                risk_score += 0.1
        
        risk_score = min(risk_score, 1.0)
        
        if risk_score >= 0.8:
            risk_level = "critical"
        elif risk_score >= 0.6:
            risk_level = "high"
        elif risk_score >= 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        result = {
            "risk_assessment": {
                "overall_risk_level": risk_level,
                "overall_risk_score": risk_score,
                "risk_trend": "stable"
            },
            "risk_categories": {
                "business_risks": {
                    "risk_level": "medium",
                    "risk_score": 0.5,
                    "identified_risks": [
                        {
                            "risk_type": "general_business_risk",
                            "probability": 0.5,
                            "impact": 0.5,
                            "severity": "medium",
                            "description": "一般的なビジネスリスク"
                        }
                    ]
                },
                "brand_safety_risks": {
                    "risk_level": "low",
                    "risk_score": 0.2,
                    "identified_risks": []
                },
                "operational_risks": {
                    "risk_level": "medium",
                    "risk_score": 0.4,
                    "identified_risks": []
                },
                "compliance_risks": {
                    "risk_level": "low",
                    "risk_score": 0.1,
                    "identified_risks": []
                }
            },
            "risk_indicators": {
                "warning_signals": ["詳細確認が必要"],
                "positive_indicators": ["基本的な対応"],
                "monitoring_points": ["進捗状況の確認"]
            },
            "immediate_actions": {
                "risk_mitigation_steps": ["通常の注意深い対応"],
                "prevention_measures": ["定期的な確認"],
                "escalation_triggers": ["重大な問題の発生"]
            },
            "confidence": 0.4 if not error else 0.2
        }
        
        if error:
            result["error"] = error
        
        return result
    
    async def _evaluate_brand_safety(self, payload: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """ブランドセーフティ評価"""
        influencer_info = payload.get("influencer_info", {})
        content_history = payload.get("content_history", [])
        brand_guidelines = payload.get("brand_guidelines", {})
        
        # 簡易ブランドセーフティ評価
        safety_factors = {
            "content_appropriateness": 0.8,
            "audience_alignment": 0.7,
            "past_controversies": 0.9,
            "brand_value_match": 0.8
        }
        
        overall_safety_score = sum(safety_factors.values()) / len(safety_factors)
        
        brand_safety_result = {
            "safety_assessment": {
                "overall_safety_score": overall_safety_score,
                "safety_level": "high" if overall_safety_score >= 0.8 else "medium" if overall_safety_score >= 0.6 else "low",
                "safety_confidence": 0.7
            },
            "safety_factors": safety_factors,
            "risk_areas": [
                "コンテンツ内容の適切性",
                "ターゲット層との整合性"
            ],
            "recommendations": [
                "コンテンツガイドラインの明確化",
                "定期的なモニタリング実施"
            ],
            "confidence": 0.7
        }
        
        logger.info(f"✅ RiskAgent: ブランドセーフティ評価完了 (スコア: {overall_safety_score:.2f})")
        return brand_safety_result
    
    async def _monitor_risk_level_changes(self, payload: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """リスクレベル変化の監視"""
        previous_assessment = payload.get("previous_assessment", {})
        current_conditions = payload.get("current_conditions", {})
        
        # 簡易リスク変化監視
        risk_changes = {
            "trend_analysis": "stable",
            "significant_changes": [],
            "new_risks_identified": [],
            "resolved_risks": [],
            "monitoring_alerts": []
        }
        
        if state.risk_level == RiskLevel.HIGH and len(state.context_memory.get("risk_history", [])) > 1:
            risk_changes["monitoring_alerts"].append("高リスクレベルが継続中")
        
        logger.info("✅ RiskAgent: リスクレベル変化監視完了")
        return {
            "risk_monitoring": risk_changes,
            "recommended_actions": ["継続的な監視", "定期的な見直し"],
            "confidence": 0.6
        }
    
    async def _develop_risk_mitigation_plan(self, payload: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """リスク軽減計画の策定"""
        identified_risks = payload.get("identified_risks", [])
        available_resources = payload.get("available_resources", {})
        
        mitigation_plan = {
            "mitigation_strategies": [
                {
                    "risk_category": "business_risks",
                    "mitigation_actions": ["契約条件の明確化", "支払い条件の確認"],
                    "timeline": "immediate",
                    "responsible_party": "negotiation_team",
                    "success_metrics": ["契約書の完成", "支払い確約の取得"]
                }
            ],
            "contingency_plans": [
                {
                    "scenario": "交渉決裂",
                    "backup_plan": "代替案の提示",
                    "trigger_conditions": ["合意困難", "条件不一致"]
                }
            ],
            "monitoring_framework": {
                "check_points": ["週次レビュー", "マイルストーン確認"],
                "escalation_procedures": ["管理者への報告", "緊急対応プロトコル"],
                "review_cycle": "weekly"
            },
            "confidence": 0.75
        }
        
        logger.info("✅ RiskAgent: リスク軽減計画策定完了")
        return mitigation_plan
    
    def get_supported_tasks(self) -> List[str]:
        """サポートするタスクタイプ"""
        return ["assess_risks", "evaluate_brand_safety", "monitor_risk_changes", "develop_mitigation"]
    
    def _get_risk_instruction(self) -> str:
        """システムインストラクション"""
        return """
あなたはリスク評価の専門エージェントです。

【役割】
- 包括的なリスクの識別・評価
- ブランドセーフティの確保
- リスク軽減策の提案
- 予防措置の立案

【リスク評価観点】
- ビジネスリスク（契約・支払・品質）
- ブランドリスク（評判・適合性・コンプライアンス）
- オペレーショナルリスク（リソース・技術・コミュニケーション）
- 法的リスク（規制・責任・知的財産）

【評価原則】
- 客観的で体系的な分析
- 予防的なアプローチ
- 継続的なモニタリング
- 実行可能な対策の提示

【出力品質】
- 明確なリスクレベルの判定
- 具体的な軽減策の提案
- 監視すべき指標の定義
- 実用的な予防措置
"""