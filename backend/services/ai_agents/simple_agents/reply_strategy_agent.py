"""
返信戦略考案エージェント - シンプル構成

@description 現在の交渉状況から返信戦略を考案するエージェント（カスタム指示・設定反映）
@author InfuMatch Development Team
@version 3.0.0
"""

import logging
import json
from typing import Dict, Any, List
from datetime import datetime

from ..base_agent import BaseAgent, AgentConfig

logger = logging.getLogger(__name__)


class ReplyStrategyAgent(BaseAgent):
    """
    返信戦略考案エージェント
    
    機能:
    - 交渉状況に基づく戦略立案
    - カスタム指示の反映
    - 企業設定・商材情報の活用
    - アプローチ方針の決定
    """
    
    def __init__(self):
        """エージェントの初期化"""
        config = AgentConfig(
            name="ReplyStrategyAgent",
            model_name="gemini-1.5-pro",
            temperature=0.4,  # 創造性と安定性のバランス
            max_output_tokens=1024,
            system_instruction=self._get_strategy_instruction()
        )
        super().__init__(config)
        self.agent_id = "reply_strategy_agent"
        self.specialization = "Reply Strategy & Planning"
        
        logger.info("🧠 ReplyStrategyAgent 初期化完了")
    
    def _get_strategy_instruction(self) -> str:
        """システム指示を取得"""
        return """
あなたは交渉戦略の専門家です。
スレッド分析結果、企業設定、カスタム指示を総合して最適な返信戦略を立案してください。

戦略立案項目:
1. 基本アプローチ（協調的/競争的/バランス型）
2. 重要メッセージとポイント
3. 言語・トーン設定
4. 優先順位と緊急度対応
5. リスク回避策

カスタム指示を最優先で反映し、企業の商材・強みを活かした戦略を提案してください。
"""
    
    async def plan_reply_strategy(
        self,
        thread_analysis: Dict[str, Any],
        company_settings: Dict[str, Any],
        custom_instructions: str = ""
    ) -> Dict[str, Any]:
        """
        返信戦略を立案
        
        Args:
            thread_analysis: スレッド分析結果
            company_settings: 企業設定情報
            custom_instructions: カスタム指示
            
        Returns:
            Dict: 戦略立案結果
        """
        try:
            logger.info("🧠 返信戦略立案開始")
            logger.info("📥 詳細INPUT:")
            logger.info(f"   分析結果: 交渉段階={thread_analysis.get('negotiation_stage', '不明')}")
            logger.info(f"   感情トーン: {thread_analysis.get('sentiment_analysis', {}).get('tone', '不明')}")
            logger.info(f"   主要懸念: {thread_analysis.get('partner_concerns', [])}")
            logger.info(f"   カスタム指示: '{custom_instructions}'" if custom_instructions else "   カスタム指示: 未設定")
            
            # 企業情報を整理
            company_info = company_settings.get("companyInfo", {})
            products = company_settings.get("products", [])
            negotiation_settings = company_settings.get("negotiationSettings", {})
            
            if company_info:
                logger.info(f"   企業名: {company_info.get('companyName', '未設定')}")
                logger.info(f"   担当者: {company_info.get('contactPerson', '未設定')}")
            if products:
                logger.info(f"   商材数: {len(products)}件")
            
            # カスタム指示の解析
            custom_analysis = self._analyze_custom_instructions(custom_instructions)
            
            # 戦略立案プロンプトを構築
            strategy_prompt = f"""
以下の情報に基づいて、最適な返信戦略を立案してください。

【スレッド分析結果】
交渉段階: {thread_analysis.get('negotiation_stage', '不明')}
相手の感情: {thread_analysis.get('sentiment_analysis', {}).get('tone', '不明')}
主要トピック: {', '.join(thread_analysis.get('key_topics', []))}
相手の懸念: {', '.join(thread_analysis.get('partner_concerns', []))}
緊急度: {thread_analysis.get('urgency_level', '不明')}
期待されるアクション: {thread_analysis.get('next_expected_action', '不明')}

【企業情報】
会社名: {company_info.get('companyName', 'InfuMatch')}
担当者: {company_info.get('contactPerson', '田中美咲')}
商材数: {len(products)}件
主要商品: {', '.join([p.get('name', '') for p in products[:3]])}

【交渉設定】
予算範囲: {negotiation_settings.get('budget', {}).get('min', '未設定')} - {negotiation_settings.get('budget', {}).get('max', '未設定')}円
重要ポイント: {', '.join(negotiation_settings.get('keyPriorities', []))}

【カスタム指示】
指示内容: {custom_instructions}
言語設定: {custom_analysis.get('language', '日本語')}
トーン調整: {custom_analysis.get('tone_adjustment', '標準')}
特別要求: {', '.join(custom_analysis.get('special_requests', []))}

以下のJSON形式で戦略を立案してください：
{{
    "primary_approach": "collaborative|competitive|balanced",
    "key_messages": ["メッセージ1", "メッセージ2", "メッセージ3"],
    "language_setting": "Japanese|English|Chinese",
    "tone_setting": "formal|friendly|professional|enthusiastic",
    "priority_topics": ["優先トピック1", "優先トピック2"],
    "response_urgency": "immediate|within_day|normal|scheduled",
    "risk_considerations": ["リスク1", "リスク2"],
    "company_strengths_to_highlight": ["強み1", "強み2"],
    "custom_instructions_impact": "カスタム指示の反映内容",
    "recommended_next_steps": ["ステップ1", "ステップ2"],
    "strategy_confidence": 0.0-1.0
}}
"""
            
            # AI戦略立案を実行
            response = await self._generate_response(strategy_prompt)
            
            # JSON解析を試行
            try:
                strategy_result = json.loads(response)
                logger.info("✅ 返信戦略立案完了")
                logger.info("📤 詳細OUTPUT:")
                logger.info(f"   基本アプローチ: {strategy_result.get('primary_approach', '不明')}")
                logger.info(f"   重要メッセージ: {strategy_result.get('key_messages', [])}")
                logger.info(f"   言語設定: {strategy_result.get('language_setting', '不明')}")
                logger.info(f"   トーン設定: {strategy_result.get('tone_setting', '不明')}")
                logger.info(f"   優先トピック: {strategy_result.get('priority_topics', [])}")
                logger.info(f"   戦略信頼度: {strategy_result.get('strategy_confidence', 0.0)}")
                return strategy_result
                
            except json.JSONDecodeError:
                # フォールバック戦略
                logger.warning("⚠️ JSON解析失敗、フォールバック戦略を実行")
                return self._create_fallback_strategy(thread_analysis, custom_analysis)
                
        except Exception as e:
            logger.error(f"❌ 返信戦略立案エラー: {str(e)}")
            return self._create_error_strategy(str(e))
    
    def _analyze_custom_instructions(self, custom_instructions: str) -> Dict[str, Any]:
        """カスタム指示を解析"""
        analysis = {
            "language": "Japanese",
            "tone_adjustment": "標準",
            "special_requests": []
        }
        
        if not custom_instructions:
            return analysis
        
        instructions_lower = custom_instructions.lower()
        
        # 言語設定
        if "英語" in custom_instructions or "english" in instructions_lower:
            analysis["language"] = "English"
        elif "中国語" in custom_instructions or "chinese" in instructions_lower:
            analysis["language"] = "Chinese"
        
        # トーン調整
        if "積極的" in custom_instructions or "aggressive" in instructions_lower:
            analysis["tone_adjustment"] = "積極的"
        elif "丁寧" in custom_instructions or "polite" in instructions_lower:
            analysis["tone_adjustment"] = "丁寧"
        elif "フレンドリー" in custom_instructions or "friendly" in instructions_lower:
            analysis["tone_adjustment"] = "フレンドリー"
        
        # 特別要求
        if "値引き" in custom_instructions or "discount" in instructions_lower:
            analysis["special_requests"].append("価格交渉重視")
        if "急ぎ" in custom_instructions or "urgent" in instructions_lower:
            analysis["special_requests"].append("迅速対応")
        if "詳細" in custom_instructions or "detail" in instructions_lower:
            analysis["special_requests"].append("詳細説明")
        
        return analysis
    
    def _create_fallback_strategy(self, thread_analysis: Dict[str, Any], custom_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """フォールバック戦略を作成"""
        return {
            "primary_approach": "balanced",
            "key_messages": [
                "ご連絡ありがとうございます",
                "詳細について相談させていただきたい",
                "最適な提案をご用意いたします"
            ],
            "language_setting": custom_analysis.get("language", "Japanese"),
            "tone_setting": "professional",
            "priority_topics": thread_analysis.get("key_topics", ["コラボレーション"]),
            "response_urgency": "normal",
            "risk_considerations": ["詳細確認が必要"],
            "company_strengths_to_highlight": ["専門性", "実績"],
            "custom_instructions_impact": f"カスタム指示「{custom_analysis.get('tone_adjustment', '標準')}」を反映",
            "recommended_next_steps": ["詳細提案の準備", "フォローアップ"],
            "strategy_confidence": 0.7
        }
    
    def _create_error_strategy(self, error_message: str) -> Dict[str, Any]:
        """エラー時の戦略を作成"""
        return {
            "primary_approach": "conservative",
            "key_messages": [f"戦略立案エラー: {error_message}"],
            "language_setting": "Japanese",
            "tone_setting": "formal",
            "priority_topics": ["エラー対応"],
            "response_urgency": "normal",
            "risk_considerations": ["戦略立案失敗"],
            "company_strengths_to_highlight": [],
            "custom_instructions_impact": "エラーにより反映不可",
            "recommended_next_steps": ["手動での戦略確認が必要"],
            "strategy_confidence": 0.0
        }
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """BaseAgentの抽象メソッド実装"""
        thread_analysis = input_data.get("thread_analysis", {})
        company_settings = input_data.get("company_settings", {})
        custom_instructions = input_data.get("custom_instructions", "")
        
        result = await self.plan_reply_strategy(thread_analysis, company_settings, custom_instructions)
        
        return {
            "success": True,
            "agent_type": "reply_strategy",
            "strategy_result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """エージェント能力情報を取得"""
        return {
            "agent_type": "reply_strategy",
            "specialization": self.specialization,
            "capabilities": [
                "strategy_planning",
                "custom_instructions_integration",
                "company_settings_utilization",
                "approach_selection",
                "risk_assessment",
                "multilingual_strategy"
            ],
            "supported_languages": ["Japanese", "English", "Chinese"],
            "confidence_threshold": 0.7
        }