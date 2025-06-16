"""
メッセージ分析エージェント

@description 受信メッセージの詳細分析、感情分析、意図推定を担当
@author InfuMatch Development Team
@version 2.0.0
"""

import logging
import json
from typing import Dict, Any, List
from datetime import datetime

from ..base_agent import AgentConfig
from .base_orchestrated_agent import BaseOrchestratedAgent
from .negotiation_state import NegotiationState, Sentiment

logger = logging.getLogger(__name__)


class AnalysisAgent(BaseOrchestratedAgent):
    """
    メッセージ分析エージェント
    
    受信メッセージの内容分析、感情分析、意図推定、
    緊急度評価などを担当する専門エージェント
    """
    
    def __init__(self):
        """エージェントの初期化"""
        config = AgentConfig(
            name="AnalysisAgent",
            model_name="gemini-1.5-flash",
            temperature=0.1,  # 分析の精確性を重視
            max_output_tokens=1024,
            system_instruction=self._get_analysis_instruction()
        )
        super().__init__(config, "analysis_agent", "Message Analysis")
        
        logger.info("📊 AnalysisAgent 初期化完了")
    
    async def execute_task(self, task_type: str, payload: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """
        メッセージ分析タスクを実行
        
        Args:
            task_type: タスクタイプ
            payload: タスクデータ
            state: 交渉状態
            
        Returns:
            Dict: 分析結果
        """
        logger.info(f"📊 AnalysisAgent: {task_type} タスク開始")
        
        if task_type == "analyze_message":
            return await self._analyze_message_content(payload, state)
        elif task_type == "sentiment_analysis":
            return await self._perform_sentiment_analysis(payload, state)
        elif task_type == "urgency_assessment":
            return await self._assess_urgency_level(payload, state)
        elif task_type == "intent_classification":
            return await self._classify_message_intent(payload, state)
        else:
            raise ValueError(f"Unsupported task type: {task_type}")
    
    async def _analyze_message_content(self, payload: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """メッセージ内容の包括分析"""
        message = payload.get("message", "")
        context = payload.get("context", {})
        
        analysis_prompt = f"""
以下のメッセージを詳細に分析してください：

【分析対象メッセージ】
{message}

【コンテキスト情報】
{json.dumps(context, ensure_ascii=False, indent=2)}

【分析項目】
1. メッセージの主要な意図・目的
2. 感情的トーン（ポジティブ/ネガティブ/中性）
3. 緊急度レベル（低/中/高/緊急）
4. 要求・期待されている行動
5. 潜在的な懸念・問題点
6. 交渉に関連する重要情報
7. 返信の必要性・優先度

以下のJSON形式で回答してください：
{{
    "content_analysis": {{
        "main_intent": "メッセージの主要意図",
        "secondary_intents": ["副次的意図1", "意図2"],
        "key_points": ["重要ポイント1", "ポイント2", "ポイント3"],
        "implicit_messages": ["暗示的メッセージ1", "メッセージ2"]
    }},
    "sentiment_analysis": {{
        "overall_sentiment": "positive/negative/neutral",
        "sentiment_score": 0.7,
        "emotional_indicators": ["感情指標1", "指標2"],
        "tone_description": "感情的トーンの説明"
    }},
    "urgency_assessment": {{
        "urgency_level": "low/medium/high/critical",
        "urgency_score": 0.6,
        "urgency_factors": ["緊急度要因1", "要因2"],
        "response_timeline": "recommended response timeframe"
    }},
    "action_requirements": {{
        "required_actions": ["必要な行動1", "行動2"],
        "optional_actions": ["任意の行動1", "行動2"],
        "information_needs": ["必要な情報1", "情報2"]
    }},
    "negotiation_relevance": {{
        "relevance_score": 0.8,
        "negotiation_topics": ["交渉トピック1", "トピック2"],
        "decision_points": ["決定事項1", "事項2"],
        "potential_objections": ["潜在的反対意見1", "意見2"]
    }},
    "communication_strategy": {{
        "recommended_approach": "推奨アプローチ",
        "key_messages_to_address": ["対応すべきメッセージ1", "メッセージ2"],
        "communication_style": "formal/casual/professional"
    }},
    "confidence": 0.85
}}
"""
        
        try:
            # AI分析を実行
            response = await self.generate_response(analysis_prompt)
            
            # JSON形式の応答をパース
            try:
                analysis_result = json.loads(response)
            except json.JSONDecodeError:
                # フォールバック: 基本分析
                analysis_result = {
                    "content_analysis": {
                        "main_intent": "情報交換・相談",
                        "secondary_intents": ["関係構築"],
                        "key_points": ["コラボレーション提案"],
                        "implicit_messages": ["信頼関係の構築意向"]
                    },
                    "sentiment_analysis": {
                        "overall_sentiment": "neutral",
                        "sentiment_score": 0.5,
                        "emotional_indicators": ["丁寧な表現"],
                        "tone_description": "ビジネス的で中性的"
                    },
                    "urgency_assessment": {
                        "urgency_level": "medium",
                        "urgency_score": 0.5,
                        "urgency_factors": ["通常のビジネス対応"],
                        "response_timeline": "1-2営業日以内"
                    },
                    "action_requirements": {
                        "required_actions": ["返信・回答"],
                        "optional_actions": ["追加情報の提供"],
                        "information_needs": ["詳細要件"]
                    },
                    "negotiation_relevance": {
                        "relevance_score": 0.6,
                        "negotiation_topics": ["条件確認"],
                        "decision_points": ["参画可否"],
                        "potential_objections": ["スケジュール調整"]
                    },
                    "communication_strategy": {
                        "recommended_approach": "協調的・建設的",
                        "key_messages_to_address": ["要件確認", "条件提示"],
                        "communication_style": "professional"
                    },
                    "confidence": 0.4
                }
            
            # 感情状態を更新
            sentiment_mapping = {
                "positive": Sentiment.POSITIVE,
                "negative": Sentiment.NEGATIVE,
                "neutral": Sentiment.NEUTRAL
            }
            
            detected_sentiment = analysis_result.get("sentiment_analysis", {}).get("overall_sentiment", "neutral")
            if detected_sentiment in sentiment_mapping:
                state.update_sentiment(
                    sentiment_mapping[detected_sentiment],
                    analysis_result.get("sentiment_analysis", {}).get("sentiment_score", 0.5)
                )
            
            logger.info(f"✅ AnalysisAgent: メッセージ分析完了 (信頼度: {analysis_result.get('confidence', 0.0):.2f})")
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ AnalysisAgent: メッセージ分析失敗: {str(e)}")
            return {
                "content_analysis": {"main_intent": "不明", "secondary_intents": [], "key_points": [], "implicit_messages": []},
                "sentiment_analysis": {"overall_sentiment": "neutral", "sentiment_score": 0.0, "emotional_indicators": [], "tone_description": "分析不可"},
                "urgency_assessment": {"urgency_level": "medium", "urgency_score": 0.5, "urgency_factors": [], "response_timeline": "通常対応"},
                "action_requirements": {"required_actions": ["返信"], "optional_actions": [], "information_needs": []},
                "negotiation_relevance": {"relevance_score": 0.0, "negotiation_topics": [], "decision_points": [], "potential_objections": []},
                "communication_strategy": {"recommended_approach": "基本対応", "key_messages_to_address": [], "communication_style": "professional"},
                "confidence": 0.1,
                "error": str(e)
            }
    
    async def _perform_sentiment_analysis(self, payload: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """感情分析の実行"""
        message = payload.get("message", "")
        
        sentiment_prompt = f"""
以下のメッセージの感情分析を行ってください：

【メッセージ】
{message}

以下の観点で分析：
- 全体的な感情（ポジティブ/ネガティブ/中性）
- 感情の強度（0.0-1.0）
- 具体的な感情表現
- ビジネス文脈での感情的含意

JSON形式で回答：
{{
    "overall_sentiment": "positive/negative/neutral",
    "sentiment_score": 0.7,
    "specific_emotions": ["興味", "期待", "不安"],
    "emotional_keywords": ["キーワード1", "キーワード2"],
    "business_implications": "ビジネス上の感情的含意",
    "confidence": 0.8
}}
"""
        
        try:
            response = await self.generate_response(sentiment_prompt)
            result = json.loads(response)
            
            logger.info("✅ AnalysisAgent: 感情分析完了")
            return result
            
        except Exception as e:
            logger.error(f"❌ AnalysisAgent: 感情分析失敗: {str(e)}")
            return {
                "overall_sentiment": "neutral",
                "sentiment_score": 0.5,
                "specific_emotions": [],
                "emotional_keywords": [],
                "business_implications": "分析不可",
                "confidence": 0.1,
                "error": str(e)
            }
    
    async def _assess_urgency_level(self, payload: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """緊急度評価"""
        message = payload.get("message", "")
        
        urgency_indicators = [
            "緊急", "急ぎ", "至急", "すぐに", "今すぐ", "今日中",
            "明日まで", "期限", "締切", "早急", "ASAP"
        ]
        
        urgency_score = 0.0
        found_indicators = []
        
        for indicator in urgency_indicators:
            if indicator in message:
                urgency_score += 0.2
                found_indicators.append(indicator)
        
        urgency_score = min(urgency_score, 1.0)
        
        if urgency_score >= 0.8:
            urgency_level = "critical"
        elif urgency_score >= 0.6:
            urgency_level = "high"
        elif urgency_score >= 0.3:
            urgency_level = "medium"
        else:
            urgency_level = "low"
        
        result = {
            "urgency_level": urgency_level,
            "urgency_score": urgency_score,
            "urgency_indicators": found_indicators,
            "recommended_response_time": "24時間以内" if urgency_score > 0.5 else "2-3営業日以内",
            "confidence": 0.8
        }
        
        logger.info(f"✅ AnalysisAgent: 緊急度評価完了 (レベル: {urgency_level})")
        return result
    
    async def _classify_message_intent(self, payload: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """メッセージ意図の分類"""
        message = payload.get("message", "")
        
        # 簡易意図分類（実際の実装ではより高度な分類を行う）
        intent_patterns = {
            "inquiry": ["お聞きしたい", "質問", "確認", "教えて"],
            "proposal": ["提案", "ご提案", "いかがでしょうか"],
            "negotiation": ["条件", "価格", "金額", "料金"],
            "scheduling": ["日程", "スケジュール", "時間", "予定"],
            "agreement": ["同意", "了解", "承知", "賛成"],
            "objection": ["難しい", "困難", "問題", "懸念"]
        }
        
        detected_intents = []
        for intent, patterns in intent_patterns.items():
            for pattern in patterns:
                if pattern in message:
                    detected_intents.append(intent)
                    break
        
        primary_intent = detected_intents[0] if detected_intents else "general_communication"
        
        result = {
            "primary_intent": primary_intent,
            "secondary_intents": detected_intents[1:],
            "intent_confidence": 0.7 if detected_intents else 0.3,
            "intent_description": f"主要意図: {primary_intent}",
            "confidence": 0.6
        }
        
        logger.info(f"✅ AnalysisAgent: 意図分類完了 (主要意図: {primary_intent})")
        return result
    
    def get_supported_tasks(self) -> List[str]:
        """サポートするタスクタイプ"""
        return ["analyze_message", "sentiment_analysis", "urgency_assessment", "intent_classification"]
    
    def _get_analysis_instruction(self) -> str:
        """システムインストラクション"""
        return """
あなたはメッセージ分析の専門エージェントです。

【役割】
- メッセージ内容の詳細分析
- 感情・トーンの分析
- 意図・目的の推定
- 緊急度・優先度の評価

【分析観点】
- 明示的な内容と暗示的な意味
- 感情的なニュアンス
- ビジネス文脈での重要性
- 対応の緊急性

【出力品質】
- 客観的で精確な分析
- 実用的な洞察の提供
- 適切な信頼度評価
- 構造化されたJSON出力
"""