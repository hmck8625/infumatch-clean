"""
スレッド分析エージェント - シンプル構成

@description スレッドを読み込み、現在の交渉状況を分析するエージェント
@author InfuMatch Development Team
@version 3.0.0
"""

import logging
import json
from typing import Dict, Any, List
from datetime import datetime

from ..base_agent import BaseAgent, AgentConfig

logger = logging.getLogger(__name__)


class ThreadAnalysisAgent(BaseAgent):
    """
    スレッド分析エージェント
    
    機能:
    - スレッド読み込み・解析
    - 交渉状況の把握
    - 感情・トーン分析
    - 交渉段階判定
    """
    
    def __init__(self):
        """エージェントの初期化"""
        config = AgentConfig(
            name="ThreadAnalysisAgent",
            model_name="gemini-1.5-pro",
            temperature=0.2,  # 分析精度を重視
            max_output_tokens=1024,
            system_instruction=self._get_analysis_instruction()
        )
        super().__init__(config)
        self.agent_id = "thread_analysis_agent"
        self.specialization = "Thread & Negotiation Analysis"
        
        logger.info("📊 ThreadAnalysisAgent 初期化完了")
    
    def _get_analysis_instruction(self) -> str:
        """システム指示を取得"""
        return """
あなたはスレッド分析の専門家です。
メールスレッドの内容を分析し、現在の交渉状況を正確に把握してください。

分析項目:
1. 交渉段階の判定（初期接触/関心表明/条件交渉/決定段階）
2. 相手の感情・トーン分析
3. 主要な関心事・要求の抽出
4. 緊急度・優先度の評価
5. これまでの交渉経緯の要約

結果は構造化されたJSON形式で返してください。
"""
    
    async def analyze_thread(
        self,
        thread_messages: List[Dict[str, Any]],
        company_settings: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        スレッドを分析して交渉状況を把握
        
        Args:
            thread_messages: スレッドメッセージリスト
            company_settings: 企業設定情報
            
        Returns:
            Dict: 分析結果
        """
        try:
            logger.info(f"📊 スレッド分析開始: {len(thread_messages)}件のメッセージ")
            logger.info("📥 詳細INPUT:")
            for i, msg in enumerate(thread_messages[-3:], 1):  # 直近3件をログ出力
                sender = msg.get('sender', '不明')
                content = msg.get('content', '')[:100]  # 100文字まで
                logger.info(f"   {i}. {sender}: {content}...")
            
            if company_settings:
                logger.info(f"   企業設定: {len(company_settings)}項目")
                if 'companyInfo' in company_settings:
                    company_name = company_settings['companyInfo'].get('companyName', '未設定')
                    logger.info(f"   企業名: {company_name}")
            
            # メッセージ履歴を整理
            conversation_summary = self._summarize_conversation(thread_messages)
            latest_message = thread_messages[-1] if thread_messages else {}
            
            # 分析プロンプトを構築
            analysis_prompt = f"""
以下のメールスレッドを分析し、現在の交渉状況を把握してください。

【会話履歴】
{conversation_summary}

【最新メッセージ】
送信者: {latest_message.get('sender', '不明')}
内容: {latest_message.get('content', '')}

【企業情報】
{json.dumps(company_settings or {}, ensure_ascii=False, indent=2)}

以下のJSON形式で分析結果を返してください：
{{
    "negotiation_stage": "initial_contact|interest_shown|condition_negotiation|decision_pending|deal_closing",
    "sentiment_analysis": {{
        "tone": "positive|neutral|negative|urgent|concerned",
        "emotional_level": 0.0-1.0,
        "confidence_level": 0.0-1.0
    }},
    "key_topics": ["トピック1", "トピック2"],
    "partner_concerns": ["懸念事項1", "懸念事項2"],
    "urgency_level": "low|medium|high|critical",
    "conversation_summary": "これまでの交渉経緯の要約",
    "next_expected_action": "相手が期待している次のアクション",
    "analysis_confidence": 0.0-1.0
}}
"""
            
            # AI分析を実行
            response = await self._generate_response(analysis_prompt)
            
            # JSON解析を試行
            try:
                analysis_result = json.loads(response)
                logger.info("✅ スレッド分析完了")
                logger.info("📤 詳細OUTPUT:")
                logger.info(f"   交渉段階: {analysis_result.get('negotiation_stage', '不明')}")
                logger.info(f"   感情トーン: {analysis_result.get('sentiment_analysis', {}).get('tone', '不明')}")
                logger.info(f"   主要トピック: {analysis_result.get('key_topics', [])}")
                logger.info(f"   相手の懸念: {analysis_result.get('partner_concerns', [])}")
                logger.info(f"   緊急度: {analysis_result.get('urgency_level', '不明')}")
                logger.info(f"   信頼度: {analysis_result.get('analysis_confidence', 0.0)}")
                return analysis_result
                
            except json.JSONDecodeError:
                # フォールバック分析
                logger.warning("⚠️ JSON解析失敗、フォールバック分析を実行")
                return self._create_fallback_analysis(thread_messages, latest_message)
                
        except Exception as e:
            logger.error(f"❌ スレッド分析エラー: {str(e)}")
            return self._create_error_analysis(str(e))
    
    def _summarize_conversation(self, messages: List[Dict[str, Any]]) -> str:
        """会話履歴を要約"""
        if not messages:
            return "メッセージなし"
        
        summary_parts = []
        for i, msg in enumerate(messages[-5:], 1):  # 直近5件
            sender = msg.get('sender', '不明')
            content = msg.get('content', '')[:100]  # 100文字まで
            summary_parts.append(f"{i}. {sender}: {content}...")
        
        return "\n".join(summary_parts)
    
    def _create_fallback_analysis(self, messages: List[Dict[str, Any]], latest_message: Dict[str, Any]) -> Dict[str, Any]:
        """フォールバック分析結果を作成"""
        return {
            "negotiation_stage": "interest_shown",
            "sentiment_analysis": {
                "tone": "neutral",
                "emotional_level": 0.5,
                "confidence_level": 0.5
            },
            "key_topics": ["コラボレーション", "商品紹介"],
            "partner_concerns": ["条件確認", "詳細相談"],
            "urgency_level": "medium",
            "conversation_summary": f"{len(messages)}件のメッセージでの交渉が進行中",
            "next_expected_action": "詳細提案の送付",
            "analysis_confidence": 0.6
        }
    
    def _create_error_analysis(self, error_message: str) -> Dict[str, Any]:
        """エラー時の分析結果を作成"""
        return {
            "negotiation_stage": "unknown",
            "sentiment_analysis": {
                "tone": "neutral",
                "emotional_level": 0.0,
                "confidence_level": 0.0
            },
            "key_topics": ["分析エラー"],
            "partner_concerns": [f"分析失敗: {error_message}"],
            "urgency_level": "low",
            "conversation_summary": "分析エラーが発生しました",
            "next_expected_action": "手動での状況確認が必要",
            "analysis_confidence": 0.0
        }
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """BaseAgentの抽象メソッド実装"""
        thread_messages = input_data.get("thread_messages", [])
        company_settings = input_data.get("company_settings", {})
        
        result = await self.analyze_thread(thread_messages, company_settings)
        
        return {
            "success": True,
            "agent_type": "thread_analysis",
            "analysis_result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """エージェント能力情報を取得"""
        return {
            "agent_type": "thread_analysis",
            "specialization": self.specialization,
            "capabilities": [
                "thread_reading",
                "negotiation_stage_detection",
                "sentiment_analysis",
                "conversation_summarization",
                "urgency_assessment"
            ],
            "supported_languages": ["Japanese", "English"],
            "confidence_threshold": 0.6
        }