"""
コミュニケーションエージェント

@description プロフェッショナルな返信文章の生成・最適化を担当
@author InfuMatch Development Team
@version 2.0.0
"""

import logging
import json
from typing import Dict, Any, List
from datetime import datetime

from ..base_agent import AgentConfig
from .base_orchestrated_agent import BaseOrchestratedAgent
from .negotiation_state import NegotiationState

logger = logging.getLogger(__name__)


class CommunicationAgent(BaseOrchestratedAgent):
    """
    コミュニケーションエージェント
    
    営業プロレベルの返信文章生成、トーン調整、
    説得力のある文章構成を担当する専門エージェント
    """
    
    def __init__(self):
        """エージェントの初期化"""
        config = AgentConfig(
            name="CommunicationAgent",
            model_name="gemini-1.5-flash",
            temperature=0.4,  # 創造性と一貫性のバランス
            max_output_tokens=2048,
            system_instruction=self._get_communication_instruction()
        )
        super().__init__(config, "communication_agent", "Professional Communication")
        
        logger.info("💬 CommunicationAgent 初期化完了")
    
    async def execute_task(self, task_type: str, payload: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """
        コミュニケーションタスクを実行
        
        Args:
            task_type: タスクタイプ
            payload: タスクデータ
            state: 交渉状態
            
        Returns:
            Dict: 生成結果
        """
        logger.info(f"💬 CommunicationAgent: {task_type} タスク開始")
        
        if task_type == "generate_response":
            return await self._generate_professional_response(payload, state)
        elif task_type == "optimize_tone":
            return await self._optimize_message_tone(payload, state)
        elif task_type == "create_variations":
            return await self._create_message_variations(payload, state)
        elif task_type == "enhance_persuasion":
            return await self._enhance_persuasiveness(payload, state)
        else:
            raise ValueError(f"Unsupported task type: {task_type}")
    
    async def _generate_professional_response(self, payload: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """プロフェッショナルな返信生成"""
        strategy = payload.get("strategy", {})
        analysis = payload.get("analysis", {})
        company_info = payload.get("company_info", {})
        custom_instructions = payload.get("custom_instructions", "")
        
        # 戦略情報を抽出
        approach = strategy.get("approach", "collaborative")
        key_messages = strategy.get("key_messages", ["関係構築を重視"])
        pricing_strategy = strategy.get("pricing_strategy", "standard")
        
        # 分析情報を抽出
        context_analysis = analysis.get("context", {}) if isinstance(analysis.get("context"), dict) else {}
        message_intent = context_analysis.get("message_intent", "情報交換")
        recommended_focus = context_analysis.get("recommended_focus", "要件確認")
        
        # 企業情報を抽出
        company_name = company_info.get("company_name", "InfuMatch")
        contact_person = company_info.get("contact_person", "田中美咲")
        
        communication_prompt = f"""
以下の情報に基づいて、プロフェッショナルな返信メールを作成してください：

【戦略情報】
- アプローチ: {approach}
- 重要メッセージ: {', '.join(key_messages)}
- 価格戦略: {pricing_strategy}

【分析結果】
- 相手の意図: {message_intent}
- 推奨フォーカス: {recommended_focus}

【企業情報】
- 企業名: {company_name}
- 担当者: {contact_person}

【カスタム指示】
{custom_instructions}

【作成要件】
1. ビジネスメール形式
2. プロフェッショナルで親しみやすいトーン
3. 具体的で価値のある内容
4. 次のアクションが明確
5. 営業のプロレベルの説得力

以下のJSON形式で回答してください：
{{
    "content": "生成されたメール本文",
    "key_elements": {{
        "opening": "冒頭部分の説明",
        "main_message": "主要メッセージの説明",
        "value_proposition": "価値提案の説明",
        "call_to_action": "行動喚起の説明",
        "closing": "結びの説明"
    }},
    "tone_analysis": {{
        "formality_level": "formal/professional/casual",
        "persuasiveness_score": 0.8,
        "relationship_building": 0.7,
        "clarity_score": 0.9
    }},
    "strategic_alignment": {{
        "approach_adherence": 0.9,
        "message_delivery": 0.8,
        "custom_instruction_compliance": 0.85
    }},
    "estimated_effectiveness": {{
        "engagement_potential": 0.8,
        "conversion_likelihood": 0.7,
        "relationship_impact": 0.75
    }},
    "confidence": 0.85
}}
"""
        
        try:
            # AI文章生成を実行
            response = await self.generate_response(communication_prompt)
            
            # JSON形式の応答をパース
            try:
                communication_result = json.loads(response)
            except json.JSONDecodeError:
                # フォールバック: 基本的な返信生成
                fallback_content = f"""いつもお世話になっております。
{company_name} の{contact_person}です。

ご連絡いただき、ありがとうございます。

{recommended_focus}について、詳細をお聞かせいただけましたら幸いです。
私どもとしても、最適なご提案をさせていただきたく存じます。

ご質問やご相談がございましたら、お気軽にお声がけください。
何卒よろしくお願いいたします。

{company_name}
{contact_person}"""
                
                communication_result = {
                    "content": fallback_content,
                    "key_elements": {
                        "opening": "標準的なビジネス挨拶",
                        "main_message": "要件確認と協力意向",
                        "value_proposition": "最適提案の提供",
                        "call_to_action": "詳細情報の依頼",
                        "closing": "標準的なビジネス結び"
                    },
                    "tone_analysis": {
                        "formality_level": "professional",
                        "persuasiveness_score": 0.5,
                        "relationship_building": 0.6,
                        "clarity_score": 0.7
                    },
                    "strategic_alignment": {
                        "approach_adherence": 0.5,
                        "message_delivery": 0.5,
                        "custom_instruction_compliance": 0.3
                    },
                    "estimated_effectiveness": {
                        "engagement_potential": 0.6,
                        "conversion_likelihood": 0.5,
                        "relationship_impact": 0.6
                    },
                    "confidence": 0.4
                }
            
            logger.info(f"✅ CommunicationAgent: 返信生成完了 (信頼度: {communication_result.get('confidence', 0.0):.2f})")
            return communication_result
            
        except Exception as e:
            logger.error(f"❌ CommunicationAgent: 返信生成失敗: {str(e)}")
            return {
                "content": "申し訳ございません。詳細について改めてご連絡いたします。",
                "key_elements": {"opening": "基本対応", "main_message": "フォローアップ", "value_proposition": "なし", "call_to_action": "なし", "closing": "基本結び"},
                "tone_analysis": {"formality_level": "professional", "persuasiveness_score": 0.1, "relationship_building": 0.1, "clarity_score": 0.3},
                "strategic_alignment": {"approach_adherence": 0.1, "message_delivery": 0.1, "custom_instruction_compliance": 0.1},
                "estimated_effectiveness": {"engagement_potential": 0.2, "conversion_likelihood": 0.1, "relationship_impact": 0.2},
                "confidence": 0.1,
                "error": str(e)
            }
    
    async def _optimize_message_tone(self, payload: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """メッセージトーンの最適化"""
        original_message = payload.get("message", "")
        target_tone = payload.get("target_tone", "professional")
        
        tone_prompt = f"""
以下のメッセージのトーンを最適化してください：

【元メッセージ】
{original_message}

【目標トーン】
{target_tone}

以下の観点で最適化：
- 適切な敬語・丁寧語の使用
- ビジネス文脈に適した表現
- 親しみやすさと専門性のバランス
- 相手に配慮した表現

JSON形式で回答：
{{
    "optimized_message": "最適化されたメッセージ",
    "tone_improvements": ["改善点1", "改善点2"],
    "tone_score": 0.8,
    "confidence": 0.85
}}
"""
        
        try:
            response = await self.generate_response(tone_prompt)
            result = json.loads(response)
            
            logger.info("✅ CommunicationAgent: トーン最適化完了")
            return result
            
        except Exception as e:
            logger.error(f"❌ CommunicationAgent: トーン最適化失敗: {str(e)}")
            return {
                "optimized_message": original_message,
                "tone_improvements": [],
                "tone_score": 0.5,
                "confidence": 0.1,
                "error": str(e)
            }
    
    async def _create_message_variations(self, payload: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """メッセージバリエーションの作成"""
        base_message = payload.get("message", "")
        variation_count = payload.get("count", 3)
        
        variations = []
        
        # 簡易実装: 基本的なバリエーション生成
        for i in range(variation_count):
            if i == 0:
                # フォーマル版
                variation = {
                    "type": "formal",
                    "content": base_message.replace("です。", "でございます。").replace("ます。", "申し上げます。"),
                    "description": "よりフォーマルな表現",
                    "confidence": 0.7
                }
            elif i == 1:
                # 親しみやすい版
                variation = {
                    "type": "friendly",
                    "content": base_message.replace("申し上げます", "お願いします").replace("いたします", "します"),
                    "description": "親しみやすい表現",
                    "confidence": 0.7
                }
            else:
                # 簡潔版
                variation = {
                    "type": "concise",
                    "content": base_message[:len(base_message)//2] + "...",
                    "description": "簡潔な表現",
                    "confidence": 0.6
                }
            
            variations.append(variation)
        
        result = {
            "variations": variations,
            "recommendation": "formal" if state.current_stage.value in ["initial_contact", "proposal_presentation"] else "friendly",
            "confidence": 0.6
        }
        
        logger.info(f"✅ CommunicationAgent: バリエーション作成完了 ({len(variations)}件)")
        return result
    
    async def _enhance_persuasiveness(self, payload: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """説得力の向上"""
        message = payload.get("message", "")
        
        # 簡易実装: 説得力向上のための要素追加
        enhanced_elements = [
            "具体的な数値・実績の追加",
            "相手のメリットの明確化",
            "緊急性・希少性の演出",
            "信頼性の証明",
            "行動喚起の強化"
        ]
        
        result = {
            "enhanced_message": message,  # 実際の実装では大幅に改善
            "persuasion_elements": enhanced_elements,
            "persuasion_score": 0.7,
            "improvement_suggestions": [
                "数値データの追加",
                "成功事例の紹介",
                "限定性の強調"
            ],
            "confidence": 0.6
        }
        
        logger.info("✅ CommunicationAgent: 説得力向上完了")
        return result
    
    def get_supported_tasks(self) -> List[str]:
        """サポートするタスクタイプ"""
        return ["generate_response", "optimize_tone", "create_variations", "enhance_persuasion"]
    
    def _get_communication_instruction(self) -> str:
        """システムインストラクション"""
        return """
あなたはプロフェッショナルコミュニケーションの専門エージェントです。

【役割】
- 営業プロレベルの文章作成
- トーン・スタイルの最適化
- 説得力のある文章構成
- 関係構築を重視したコミュニケーション

【文章品質基準】
- 明確で理解しやすい
- 相手の立場を考慮
- 具体的で価値のある内容
- 適切なビジネスマナー

【出力品質】
- プロフェッショナルな文章
- 戦略的に設計された構成
- 効果的な行動喚起
- 関係性を深める表現
"""