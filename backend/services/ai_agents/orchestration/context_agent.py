"""
コンテキスト分析エージェント

@description 会話履歴・企業情報・インフルエンサー情報を統合分析し、交渉コンテキストを構築
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


class ContextAgent(BaseOrchestratedAgent):
    """
    コンテキスト分析エージェント
    
    会話履歴、企業情報、インフルエンサー情報を分析し、
    交渉に必要な文脈情報を構築・提供する
    """
    
    def __init__(self):
        """エージェントの初期化"""
        config = AgentConfig(
            name="ContextAgent",
            model_name="gemini-1.5-flash",
            temperature=0.2,  # 分析の一貫性を重視
            max_output_tokens=1024,
            system_instruction=self._get_context_instruction()
        )
        super().__init__(config, "context_agent", "Context Analysis")
        
        logger.info("🔍 ContextAgent 初期化完了")
    
    async def execute_task(self, task_type: str, payload: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """
        コンテキスト分析タスクを実行
        
        Args:
            task_type: タスクタイプ
            payload: タスクデータ
            state: 交渉状態
            
        Returns:
            Dict: 分析結果
        """
        logger.info(f"🔍 ContextAgent: {task_type} タスク開始")
        
        if task_type == "analyze_context":
            return await self._analyze_conversation_context(payload, state)
        elif task_type == "extract_entities":
            return await self._extract_key_entities(payload, state)
        elif task_type == "build_timeline":
            return await self._build_interaction_timeline(payload, state)
        else:
            raise ValueError(f"Unsupported task type: {task_type}")
    
    async def _analyze_conversation_context(self, payload: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """会話コンテキストの包括分析"""
        new_message = payload.get("new_message", "")
        conversation_history = payload.get("conversation_history", [])
        company_info = payload.get("company_info", {})
        
        # プロンプト構築
        analysis_prompt = f"""
以下の情報を分析し、交渉コンテキストを構築してください：

【新着メッセージ】
{new_message}

【会話履歴】
{json.dumps(conversation_history[-5:], ensure_ascii=False, indent=2)}

【企業情報】
{json.dumps(company_info, ensure_ascii=False, indent=2)}

【分析項目】
1. メッセージの主要意図・目的
2. 相手の関心・ニーズの推定
3. 交渉段階の評価
4. 重要なキーワード・情報の抽出
5. コンテキストの継続性評価

以下のJSON形式で回答してください：
{{
    "message_intent": "メッセージの主要意図",
    "stakeholder_needs": ["推定されるニーズ1", "ニーズ2"],
    "negotiation_phase_assessment": "現在の交渉段階の評価",
    "key_information": {{
        "mentioned_topics": ["トピック1", "トピック2"],
        "important_details": ["重要な詳細1", "詳細2"],
        "implicit_concerns": ["懸念事項1", "懸念事項2"]
    }},
    "context_continuity": {{
        "previous_context_relevance": 0.8,
        "context_gaps": ["不足している情報1", "情報2"],
        "context_strength": 0.7
    }},
    "recommended_focus": "次のやり取りで注力すべき点",
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
                    "message_intent": "情報確認・提案検討",
                    "stakeholder_needs": ["詳細情報", "条件確認"],
                    "negotiation_phase_assessment": "初期段階",
                    "key_information": {
                        "mentioned_topics": ["コラボレーション", "条件"],
                        "important_details": ["価格", "スケジュール"],
                        "implicit_concerns": ["品質", "適合性"]
                    },
                    "context_continuity": {
                        "previous_context_relevance": 0.6,
                        "context_gaps": ["詳細要件"],
                        "context_strength": 0.5
                    },
                    "recommended_focus": "要件の詳細確認",
                    "confidence": 0.4
                }
            
            # 分析結果を状態に保存
            state.context_memory["latest_context_analysis"] = analysis_result
            state.context_memory["context_analysis_timestamp"] = datetime.now().isoformat()
            
            logger.info(f"✅ ContextAgent: コンテキスト分析完了 (信頼度: {analysis_result.get('confidence', 0.0):.2f})")
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ ContextAgent: コンテキスト分析失敗: {str(e)}")
            return {
                "message_intent": "不明",
                "stakeholder_needs": [],
                "negotiation_phase_assessment": "分析不可",
                "key_information": {"mentioned_topics": [], "important_details": [], "implicit_concerns": []},
                "context_continuity": {"previous_context_relevance": 0.0, "context_gaps": [], "context_strength": 0.0},
                "recommended_focus": "基本的な情報交換",
                "confidence": 0.1,
                "error": str(e)
            }
    
    async def _extract_key_entities(self, payload: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """重要エンティティの抽出"""
        message = payload.get("message", "")
        
        entity_prompt = f"""
以下のメッセージから重要なエンティティを抽出してください：

【メッセージ】
{message}

以下の情報を抽出してください：
- 人名・組織名
- 商品・サービス名
- 金額・数値
- 日付・期間
- 場所・チャネル
- 条件・要件

JSON形式で回答：
{{
    "entities": {{
        "persons": ["人名1", "人名2"],
        "organizations": ["組織名1", "組織名2"],
        "products_services": ["商品1", "サービス1"],
        "monetary_values": ["金額1", "金額2"],
        "dates_periods": ["日付1", "期間1"],
        "locations_channels": ["場所1", "チャネル1"],
        "conditions_requirements": ["条件1", "要件1"]
    }},
    "confidence": 0.8
}}
"""
        
        try:
            response = await self.generate_response(entity_prompt)
            result = json.loads(response)
            
            logger.info("✅ ContextAgent: エンティティ抽出完了")
            return result
            
        except Exception as e:
            logger.error(f"❌ ContextAgent: エンティティ抽出失敗: {str(e)}")
            return {
                "entities": {
                    "persons": [], "organizations": [], "products_services": [],
                    "monetary_values": [], "dates_periods": [], "locations_channels": [],
                    "conditions_requirements": []
                },
                "confidence": 0.1,
                "error": str(e)
            }
    
    async def _build_interaction_timeline(self, payload: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """やり取りのタイムライン構築"""
        conversation_history = payload.get("conversation_history", [])
        
        timeline_events = []
        for i, exchange in enumerate(conversation_history[-10:]):  # 最新10件
            event = {
                "sequence": i + 1,
                "timestamp": exchange.get("timestamp", ""),
                "type": "message_exchange",
                "summary": exchange.get("message", "")[:100] + "..." if len(exchange.get("message", "")) > 100 else exchange.get("message", ""),
                "key_points": []  # 簡易実装
            }
            timeline_events.append(event)
        
        timeline_result = {
            "timeline_events": timeline_events,
            "interaction_summary": {
                "total_exchanges": len(conversation_history),
                "recent_activity": len([e for e in timeline_events if e.get("timestamp")]),
                "engagement_level": "medium"  # 簡易評価
            },
            "confidence": 0.7
        }
        
        logger.info("✅ ContextAgent: タイムライン構築完了")
        return timeline_result
    
    def get_supported_tasks(self) -> List[str]:
        """サポートするタスクタイプ"""
        return ["analyze_context", "extract_entities", "build_timeline"]
    
    def _get_context_instruction(self) -> str:
        """システムインストラクション"""
        return """
あなたは交渉コンテキスト分析の専門エージェントです。

【役割】
- 会話履歴から重要な文脈情報を抽出
- 相手の意図・ニーズの推定
- 交渉段階の評価
- 情報の整理・構造化

【分析観点】
- 明示的な情報と暗示的な情報
- 相手の関心・優先事項
- 交渉の進捗状況
- 重要な未解決事項

【出力品質】
- 客観的で論理的な分析
- 具体的で実用的な洞察
- 適切な信頼度評価
- JSON形式での構造化
"""