"""
返信内容適切性判定エージェント - シンプル構成

@description 返信内容が適切かどうかを判定するエージェント
@author InfuMatch Development Team
@version 3.0.0
"""

import logging
import json
from typing import Dict, Any
from datetime import datetime

from ..base_agent import BaseAgent, AgentConfig

logger = logging.getLogger(__name__)


class ContentEvaluationAgent(BaseAgent):
    """
    返信内容適切性判定エージェント
    
    機能:
    - 返信内容の適切性判定
    - ビジネスマナー・言語適切性の評価
    - リスク評価・法的問題のチェック
    - 改善提案の生成
    """
    
    def __init__(self):
        """エージェントの初期化"""
        config = AgentConfig(
            name="ContentEvaluationAgent",
            model_name="gemini-1.5-pro",
            temperature=0.1,  # 一貫性重視
            max_output_tokens=1024,
            system_instruction=self._get_evaluation_instruction()
        )
        super().__init__(config)
        self.agent_id = "content_evaluation_agent"
        self.specialization = "Content Quality & Appropriateness Assessment"
        
        logger.info("🔍 ContentEvaluationAgent 初期化完了")
    
    def _get_evaluation_instruction(self) -> str:
        """システム指示を取得"""
        return """
あなたは返信内容の品質評価専門家です。
提案された返信内容を多角的に評価し、適切性を判定してください。

評価項目:
1. ビジネスマナー・言語適切性
2. 相手の期待に対する回答性
3. リスク評価（法的・ブランド・関係性）
4. メッセージの明確性・一貫性
5. 改善提案

総合的な判定スコア（0.0-1.0）と具体的な改善提案を提供してください。
"""
    
    async def evaluate_content(
        self,
        proposed_content: str,
        thread_analysis: Dict[str, Any],
        strategy_plan: Dict[str, Any],
        company_settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        返信内容を評価
        
        Args:
            proposed_content: 提案された返信内容
            thread_analysis: スレッド分析結果
            strategy_plan: 戦略立案結果
            company_settings: 企業設定情報
            
        Returns:
            Dict: 評価結果
        """
        try:
            logger.info("🔍 返信内容評価開始")
            
            # 企業情報を整理
            company_info = company_settings.get("companyInfo", {})
            products = company_settings.get("products", [])
            
            # 評価プロンプトを構築
            evaluation_prompt = f"""
以下の返信内容を多角的に評価してください。

【提案された返信内容】
{proposed_content}

【交渉状況】
交渉段階: {thread_analysis.get('negotiation_stage', '不明')}
相手の感情: {thread_analysis.get('sentiment_analysis', {}).get('tone', '不明')}
相手の懸念: {', '.join(thread_analysis.get('partner_concerns', []))}
期待されるアクション: {thread_analysis.get('next_expected_action', '不明')}

【戦略方針】
基本アプローチ: {strategy_plan.get('primary_approach', '不明')}
重要メッセージ: {', '.join(strategy_plan.get('key_messages', []))}
トーン設定: {strategy_plan.get('tone_setting', '不明')}

【企業情報】
会社名: {company_info.get('companyName', 'InfuMatch')}
主要商品: {', '.join([p.get('name', '') for p in products[:3]])}

以下の観点から評価し、JSON形式で結果を返してください：
{{
    "overall_score": 0.0-1.0,
    "evaluation_details": {{
        "business_manner_score": 0.0-1.0,
        "responsiveness_score": 0.0-1.0,
        "risk_assessment_score": 0.0-1.0,
        "clarity_score": 0.0-1.0,
        "strategy_alignment_score": 0.0-1.0
    }},
    "strengths": ["良い点1", "良い点2"],
    "concerns": ["懸念点1", "懸念点2"],
    "improvement_suggestions": ["改善提案1", "改善提案2"],
    "risk_flags": ["リスク項目1", "リスク項目2"],
    "approval_recommendation": "approve|revise|reject",
    "confidence_level": 0.0-1.0,
    "evaluation_reasoning": "評価理由の詳細説明"
}}
"""
            
            # AI評価を実行
            response = await self._generate_response(evaluation_prompt)
            
            # JSON解析を試行
            try:
                evaluation_result = json.loads(response)
                logger.info("✅ 返信内容評価完了")
                return evaluation_result
                
            except json.JSONDecodeError:
                # フォールバック評価
                logger.warning("⚠️ JSON解析失敗、フォールバック評価を実行")
                return self._create_fallback_evaluation(proposed_content)
                
        except Exception as e:
            logger.error(f"❌ 返信内容評価エラー: {str(e)}")
            return self._create_error_evaluation(str(e))
    
    async def quick_approval_check(
        self,
        proposed_content: str,
        basic_criteria: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        簡易承認チェック
        
        Args:
            proposed_content: 提案された返信内容
            basic_criteria: 基本判定基準
            
        Returns:
            Dict: 簡易評価結果
        """
        try:
            logger.info("⚡ 簡易承認チェック開始")
            
            # 基本的なリスクチェック
            risk_keywords = [
                "保証", "確約", "必ず", "絶対", "100%", "無料", "タダ",
                "法的", "訴訟", "違反", "問題", "苦情"
            ]
            
            content_lower = proposed_content.lower()
            found_risks = [keyword for keyword in risk_keywords if keyword in proposed_content]
            
            # 基本スコア計算
            base_score = 0.8
            if found_risks:
                base_score -= len(found_risks) * 0.1
            
            # 内容の長さチェック
            content_length = len(proposed_content)
            if content_length < 50:
                base_score -= 0.2  # 短すぎる
            elif content_length > 1000:
                base_score -= 0.1  # 長すぎる
            
            approval = "approve" if base_score >= 0.7 else "revise" if base_score >= 0.5 else "reject"
            
            return {
                "quick_score": max(base_score, 0.0),
                "approval_recommendation": approval,
                "risk_flags": found_risks,
                "content_length": content_length,
                "evaluation_type": "quick_check",
                "confidence_level": 0.8
            }
            
        except Exception as e:
            logger.error(f"❌ 簡易承認チェックエラー: {str(e)}")
            return {
                "quick_score": 0.0,
                "approval_recommendation": "reject",
                "risk_flags": [f"評価エラー: {str(e)}"],
                "evaluation_type": "error",
                "confidence_level": 0.0
            }
    
    def _create_fallback_evaluation(self, content: str) -> Dict[str, Any]:
        """フォールバック評価を作成"""
        return {
            "overall_score": 0.7,
            "evaluation_details": {
                "business_manner_score": 0.7,
                "responsiveness_score": 0.7,
                "risk_assessment_score": 0.8,
                "clarity_score": 0.7,
                "strategy_alignment_score": 0.6
            },
            "strengths": ["基本的な返信内容が含まれている"],
            "concerns": ["詳細評価が実行できませんでした"],
            "improvement_suggestions": ["手動での最終確認を推奨"],
            "risk_flags": [],
            "approval_recommendation": "revise",
            "confidence_level": 0.6,
            "evaluation_reasoning": "フォールバック評価により基本的な妥当性を確認"
        }
    
    def _create_error_evaluation(self, error_message: str) -> Dict[str, Any]:
        """エラー時の評価を作成"""
        return {
            "overall_score": 0.0,
            "evaluation_details": {
                "business_manner_score": 0.0,
                "responsiveness_score": 0.0,
                "risk_assessment_score": 0.0,
                "clarity_score": 0.0,
                "strategy_alignment_score": 0.0
            },
            "strengths": [],
            "concerns": [f"評価エラー: {error_message}"],
            "improvement_suggestions": ["手動での内容確認が必要"],
            "risk_flags": ["評価システムエラー"],
            "approval_recommendation": "reject",
            "confidence_level": 0.0,
            "evaluation_reasoning": f"システムエラーにより評価不可: {error_message}"
        }
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """BaseAgentの抽象メソッド実装"""
        proposed_content = input_data.get("proposed_content", "")
        thread_analysis = input_data.get("thread_analysis", {})
        strategy_plan = input_data.get("strategy_plan", {})
        company_settings = input_data.get("company_settings", {})
        
        result = await self.evaluate_content(
            proposed_content, thread_analysis, strategy_plan, company_settings
        )
        
        return {
            "success": True,
            "agent_type": "content_evaluation",
            "evaluation_result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """エージェント能力情報を取得"""
        return {
            "agent_type": "content_evaluation",
            "specialization": self.specialization,
            "capabilities": [
                "content_quality_assessment",
                "business_manner_evaluation",
                "risk_assessment",
                "improvement_suggestions",
                "approval_recommendations",
                "quick_approval_checks"
            ],
            "evaluation_criteria": [
                "business_manner",
                "responsiveness",
                "risk_assessment",
                "clarity",
                "strategy_alignment"
            ],
            "confidence_threshold": 0.7
        }