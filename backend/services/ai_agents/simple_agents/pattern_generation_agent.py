"""
3パターン返信生成エージェント - シンプル構成

@description 3つのパターン（相手に合わせる、中立、自分の要求を通す）で返信を生成するエージェント
@author InfuMatch Development Team
@version 3.0.0
"""

import logging
import json
from typing import Dict, Any, List
from datetime import datetime

from ..base_agent import BaseAgent, AgentConfig

logger = logging.getLogger(__name__)


class PatternGenerationAgent(BaseAgent):
    """
    3パターン返信生成エージェント
    
    機能:
    - 3つの異なるアプローチで返信生成
    - パターン1: 相手に合わせる（協調的）
    - パターン2: 中立（バランス型）
    - パターン3: 自分の要求を通す（主張的）
    """
    
    def __init__(self):
        """エージェントの初期化"""
        config = AgentConfig(
            name="PatternGenerationAgent",
            model_name="gemini-1.5-pro",
            temperature=0.5,  # 多様性と一貫性のバランス
            max_output_tokens=1536,  # 3パターン分のため増量
            system_instruction=self._get_generation_instruction()
        )
        super().__init__(config)
        self.agent_id = "pattern_generation_agent"
        self.specialization = "Multi-Pattern Response Generation"
        
        logger.info("🎨 PatternGenerationAgent 初期化完了")
    
    def _get_generation_instruction(self) -> str:
        """システム指示を取得"""
        return """
あなたは交渉スタイル別返信生成の専門家です。
与えられた戦略と評価結果に基づいて、3つの異なるアプローチで返信を生成してください。

生成パターン:
1. 協調的パターン（相手に合わせる）: 相手の要求を受け入れ、協力的な姿勢を示す
2. バランス型パターン（中立）: 双方の利益を考慮し、建設的な対話を重視
3. 主張的パターン（自分の要求を通す）: 自社の条件や要求を明確に主張

各パターンは適切なトーン、言語選択、戦略的アプローチを反映してください。
"""
    
    async def generate_three_patterns(
        self,
        thread_analysis: Dict[str, Any],
        strategy_plan: Dict[str, Any],
        evaluation_result: Dict[str, Any],
        company_settings: Dict[str, Any],
        custom_instructions: str = ""
    ) -> Dict[str, Any]:
        """
        3パターンの返信を生成
        
        Args:
            thread_analysis: スレッド分析結果
            strategy_plan: 戦略立案結果
            evaluation_result: 内容評価結果
            company_settings: 企業設定情報
            custom_instructions: カスタム指示
            
        Returns:
            Dict: 3パターンの返信結果
        """
        try:
            logger.info("🎨 3パターン返信生成開始")
            
            # 企業情報を整理
            company_info = company_settings.get("companyInfo", {})
            products = company_settings.get("products", [])
            company_name = company_info.get("companyName", "InfuMatch")
            contact_person = company_info.get("contactPerson", "田中美咲")
            
            # 基本情報の整理
            negotiation_stage = thread_analysis.get('negotiation_stage', '関心表明')
            partner_concerns = thread_analysis.get('partner_concerns', [])
            key_messages = strategy_plan.get('key_messages', [])
            
            # 3パターン生成プロンプトを構築
            generation_prompt = f"""
以下の情報に基づいて、3つの異なるアプローチで返信メールを生成してください。

【交渉状況】
交渉段階: {negotiation_stage}
相手の懸念: {', '.join(partner_concerns)}
戦略メッセージ: {', '.join(key_messages)}

【企業情報】
会社名: {company_name}
担当者: {contact_person}
主要商品: {', '.join([p.get('name', '') for p in products[:3]])}

【カスタム指示】
{custom_instructions}

以下の3パターンでメールを生成してください（各150-200文字）：

【JSON形式で出力】
{{
    "pattern_collaborative": {{
        "approach": "collaborative",
        "content": "相手に合わせる協調的な返信メール",
        "tone": "accommodating",
        "strategy_focus": "相手の要求受け入れ重視"
    }},
    "pattern_balanced": {{
        "approach": "balanced", 
        "content": "中立的でバランスの取れた返信メール",
        "tone": "professional",
        "strategy_focus": "双方の利益考慮"
    }},
    "pattern_assertive": {{
        "approach": "assertive",
        "content": "自分の要求を通す主張的な返信メール", 
        "tone": "confident",
        "strategy_focus": "自社条件明確化"
    }},
    "generation_metadata": {{
        "base_strategy": "{strategy_plan.get('primary_approach', 'balanced')}",
        "custom_instructions_applied": "{custom_instructions}",
        "language_setting": "{strategy_plan.get('language_setting', 'Japanese')}",
        "confidence_level": 0.0-1.0
    }}
}}
"""
            
            # AI生成を実行
            response = await self._generate_response(generation_prompt)
            
            # JSON解析を試行
            try:
                patterns_result = json.loads(response)
                
                # 各パターンに追加メタデータを付与
                for pattern_key in ['pattern_collaborative', 'pattern_balanced', 'pattern_assertive']:
                    if pattern_key in patterns_result:
                        patterns_result[pattern_key]['generated_at'] = datetime.now().isoformat()
                        patterns_result[pattern_key]['company_name'] = company_name
                        patterns_result[pattern_key]['contact_person'] = contact_person
                
                logger.info("✅ 3パターン返信生成完了")
                return patterns_result
                
            except json.JSONDecodeError:
                # フォールバック生成
                logger.warning("⚠️ JSON解析失敗、フォールバック生成を実行")
                return self._create_fallback_patterns(company_name, contact_person, custom_instructions)
                
        except Exception as e:
            logger.error(f"❌ 3パターン返信生成エラー: {str(e)}")
            return self._create_error_patterns(str(e))
    
    async def generate_single_pattern(
        self,
        pattern_type: str,
        base_content: str,
        strategy_plan: Dict[str, Any],
        company_settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        単一パターンの返信を生成
        
        Args:
            pattern_type: パターンタイプ (collaborative/balanced/assertive)
            base_content: 基本となる返信内容
            strategy_plan: 戦略立案結果
            company_settings: 企業設定情報
            
        Returns:
            Dict: 単一パターンの返信結果
        """
        try:
            logger.info(f"🎨 {pattern_type}パターン生成開始")
            
            company_info = company_settings.get("companyInfo", {})
            company_name = company_info.get("companyName", "InfuMatch")
            contact_person = company_info.get("contactPerson", "田中美咲")
            
            # パターン別の調整指示
            pattern_instructions = {
                "collaborative": "相手の要求を最大限受け入れ、協力的な姿勢を強調してください",
                "balanced": "双方の利益を考慮し、建設的で公平な提案をしてください", 
                "assertive": "自社の条件や要求を明確に主張し、確信を持ったトーンで書いてください"
            }
            
            instruction = pattern_instructions.get(pattern_type, pattern_instructions["balanced"])
            
            # 単一パターン生成プロンプト
            single_prompt = f"""
以下の基本返信内容を{pattern_type}パターンに調整してください。

【基本内容】
{base_content}

【調整指示】
{instruction}

【企業情報】
会社名: {company_name}
担当者: {contact_person}

【出力要求】
- 150-200文字で調整
- 自然で適切なビジネスメール形式
- 署名は「{company_name} {contact_person}」

調整された返信メールのみを出力してください：
"""
            
            response = await self._generate_response(single_prompt)
            
            return {
                "approach": pattern_type,
                "content": response.strip(),
                "tone": self._get_pattern_tone(pattern_type),
                "strategy_focus": self._get_pattern_focus(pattern_type),
                "generated_at": datetime.now().isoformat(),
                "company_name": company_name,
                "contact_person": contact_person
            }
            
        except Exception as e:
            logger.error(f"❌ {pattern_type}パターン生成エラー: {str(e)}")
            return {
                "approach": pattern_type,
                "content": f"パターン生成エラー: {str(e)}",
                "tone": "error",
                "strategy_focus": "エラー対応",
                "generated_at": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def _get_pattern_tone(self, pattern_type: str) -> str:
        """パターンタイプに対応するトーンを取得"""
        tone_map = {
            "collaborative": "accommodating",
            "balanced": "professional", 
            "assertive": "confident"
        }
        return tone_map.get(pattern_type, "professional")
    
    def _get_pattern_focus(self, pattern_type: str) -> str:
        """パターンタイプに対応する戦略フォーカスを取得"""
        focus_map = {
            "collaborative": "相手の要求受け入れ重視",
            "balanced": "双方の利益考慮",
            "assertive": "自社条件明確化"
        }
        return focus_map.get(pattern_type, "バランス重視")
    
    def _create_fallback_patterns(self, company_name: str, contact_person: str, custom_instructions: str) -> Dict[str, Any]:
        """フォールバック3パターンを作成"""
        return {
            "pattern_collaborative": {
                "approach": "collaborative",
                "content": f"ご提案いただいた条件で、ぜひ進めさせていただきたく思います。詳細につきまして、お話しさせていただければ幸いです。\n\n{company_name} {contact_person}",
                "tone": "accommodating",
                "strategy_focus": "相手の要求受け入れ重視",
                "generated_at": datetime.now().isoformat(),
                "company_name": company_name,
                "contact_person": contact_person
            },
            "pattern_balanced": {
                "approach": "balanced",
                "content": f"ご提案を検討させていただき、双方にとってメリットのある形でお話しを進められればと思います。詳細をご相談させてください。\n\n{company_name} {contact_person}",
                "tone": "professional", 
                "strategy_focus": "双方の利益考慮",
                "generated_at": datetime.now().isoformat(),
                "company_name": company_name,
                "contact_person": contact_person
            },
            "pattern_assertive": {
                "approach": "assertive",
                "content": f"弊社としては以下の条件でのご提案をさせていただきます。品質と実績を重視した最適なプランをご用意いたします。\n\n{company_name} {contact_person}",
                "tone": "confident",
                "strategy_focus": "自社条件明確化",
                "generated_at": datetime.now().isoformat(),
                "company_name": company_name,
                "contact_person": contact_person
            },
            "generation_metadata": {
                "base_strategy": "balanced",
                "custom_instructions_applied": custom_instructions,
                "language_setting": "Japanese",
                "confidence_level": 0.7,
                "generation_type": "fallback"
            }
        }
    
    def _create_error_patterns(self, error_message: str) -> Dict[str, Any]:
        """エラー時のパターンを作成"""
        return {
            "pattern_collaborative": {
                "approach": "collaborative",
                "content": f"生成エラー: {error_message}",
                "tone": "error",
                "strategy_focus": "エラー対応"
            },
            "pattern_balanced": {
                "approach": "balanced", 
                "content": f"生成エラー: {error_message}",
                "tone": "error",
                "strategy_focus": "エラー対応"
            },
            "pattern_assertive": {
                "approach": "assertive",
                "content": f"生成エラー: {error_message}",
                "tone": "error",
                "strategy_focus": "エラー対応"
            },
            "generation_metadata": {
                "error": error_message,
                "confidence_level": 0.0,
                "generation_type": "error"
            }
        }
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """BaseAgentの抽象メソッド実装"""
        thread_analysis = input_data.get("thread_analysis", {})
        strategy_plan = input_data.get("strategy_plan", {})
        evaluation_result = input_data.get("evaluation_result", {})
        company_settings = input_data.get("company_settings", {})
        custom_instructions = input_data.get("custom_instructions", "")
        
        result = await self.generate_three_patterns(
            thread_analysis, strategy_plan, evaluation_result, 
            company_settings, custom_instructions
        )
        
        return {
            "success": True,
            "agent_type": "pattern_generation",
            "patterns_result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """エージェント能力情報を取得"""
        return {
            "agent_type": "pattern_generation",
            "specialization": self.specialization,
            "capabilities": [
                "multi_pattern_generation",
                "collaborative_responses",
                "balanced_responses", 
                "assertive_responses",
                "tone_adjustment",
                "strategy_adaptation",
                "custom_instruction_integration"
            ],
            "pattern_types": ["collaborative", "balanced", "assertive"],
            "supported_languages": ["Japanese", "English", "Chinese"],
            "confidence_threshold": 0.7
        }