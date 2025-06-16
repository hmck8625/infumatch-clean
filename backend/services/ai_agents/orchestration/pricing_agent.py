"""
価格戦略エージェント

@description 価格戦略の立案、市場価格分析、価格交渉戦術を担当
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


class PricingAgent(BaseOrchestratedAgent):
    """
    価格戦略エージェント
    
    インフルエンサーマーケティングの市場価格分析、
    価格戦略の立案、価格交渉戦術を担当する専門エージェント
    """
    
    def __init__(self):
        """エージェントの初期化"""
        config = AgentConfig(
            name="PricingAgent",
            model_name="gemini-1.5-flash",
            temperature=0.2,  # 価格計算の精確性を重視
            max_output_tokens=1536,
            system_instruction=self._get_pricing_instruction()
        )
        super().__init__(config, "pricing_agent", "Pricing Strategy")
        
        # 基本価格テーブル（実際の実装では外部データソースを使用）
        self.base_pricing_data = {
            "youtube_subscribers": {
                "1000-10000": {"min": 30000, "max": 80000, "avg": 55000},
                "10000-50000": {"min": 80000, "max": 200000, "avg": 140000},
                "50000-100000": {"min": 200000, "max": 400000, "avg": 300000},
                "100000-500000": {"min": 400000, "max": 800000, "avg": 600000},
                "500000+": {"min": 800000, "max": 2000000, "avg": 1400000}
            },
            "engagement_multipliers": {
                "low": 0.8,      # 1%未満
                "medium": 1.0,   # 1-3%
                "high": 1.3,     # 3-5%
                "very_high": 1.6  # 5%以上
            },
            "category_multipliers": {
                "beauty": 1.2,
                "fashion": 1.1,
                "tech": 1.3,
                "food": 1.0,
                "lifestyle": 1.0,
                "gaming": 1.4,
                "education": 0.9
            }
        }
        
        logger.info("💰 PricingAgent 初期化完了")
    
    async def execute_task(self, task_type: str, payload: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """
        価格戦略タスクを実行
        
        Args:
            task_type: タスクタイプ
            payload: タスクデータ
            state: 交渉状態
            
        Returns:
            Dict: 価格戦略結果
        """
        logger.info(f"💰 PricingAgent: {task_type} タスク開始")
        
        if task_type == "calculate_pricing":
            return await self._calculate_market_pricing(payload, state)
        elif task_type == "optimize_pricing":
            return await self._optimize_pricing_strategy(payload, state)
        elif task_type == "analyze_competition":
            return await self._analyze_competitive_pricing(payload, state)
        elif task_type == "negotiate_price":
            return await self._develop_price_negotiation_tactics(payload, state)
        else:
            raise ValueError(f"Unsupported task type: {task_type}")
    
    async def _calculate_market_pricing(self, payload: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """市場価格の算出"""
        influencer_info = payload.get("influencer_info", {})
        company_budget = payload.get("company_budget", {})
        market_conditions = payload.get("market_conditions", {})
        
        pricing_prompt = f"""
以下の情報に基づいて、インフルエンサーマーケティングの適正価格を算出してください：

【インフルエンサー情報】
{json.dumps(influencer_info, ensure_ascii=False, indent=2)}

【企業予算情報】
{json.dumps(company_budget, ensure_ascii=False, indent=2)}

【市場状況】
{json.dumps(market_conditions, ensure_ascii=False, indent=2)}

【価格算出要件】
1. 基本料金の算出（フォロワー数ベース）
2. エンゲージメント率による調整
3. カテゴリ・専門性による調整
4. 市場プレミアム・ディスカウント要因
5. 価格レンジの提示（最低価格・推奨価格・最高価格）

以下のJSON形式で回答してください：
{{
    "pricing_analysis": {{
        "base_calculation": {{
            "follower_based_price": 300000,
            "engagement_adjustment": 1.2,
            "category_premium": 1.1,
            "market_factor": 1.0
        }},
        "calculated_price": {{
            "minimum_price": 250000,
            "recommended_price": 350000,
            "maximum_price": 450000,
            "currency": "JPY"
        }},
        "price_breakdown": {{
            "content_creation": 200000,
            "posting_fee": 100000,
            "usage_rights": 50000,
            "additional_services": 0
        }}
    }},
    "market_positioning": {{
        "price_tier": "mid-tier/premium/budget",
        "competitive_position": "above/at/below market average",
        "value_proposition": "価値提案の説明"
    }},
    "negotiation_parameters": {{
        "negotiation_room": 0.15,
        "minimum_acceptable": 280000,
        "ideal_closing_price": 350000,
        "walk_away_price": 250000
    }},
    "pricing_strategy": {{
        "recommended_approach": "value-based/cost-plus/competitive",
        "key_value_drivers": ["価値要因1", "要因2"],
        "price_justification": "価格根拠の説明"
    }},
    "confidence": 0.8
}}
"""
        
        try:
            # AI価格分析を実行
            response = await self.generate_response(pricing_prompt)
            
            # JSON形式の応答をパース
            try:
                pricing_result = json.loads(response)
            except json.JSONDecodeError:
                # フォールバック: 基本価格計算
                pricing_result = self._calculate_fallback_pricing(influencer_info, company_budget)
            
            # 価格情報を状態に記録
            state.context_memory["latest_pricing_analysis"] = pricing_result
            state.context_memory["pricing_timestamp"] = datetime.now().isoformat()
            
            logger.info(f"✅ PricingAgent: 価格算出完了 (推奨価格: ¥{pricing_result.get('pricing_analysis', {}).get('calculated_price', {}).get('recommended_price', 0):,})")
            return pricing_result
            
        except Exception as e:
            logger.error(f"❌ PricingAgent: 価格算出失敗: {str(e)}")
            return self._calculate_fallback_pricing(influencer_info, company_budget, error=str(e))
    
    def _calculate_fallback_pricing(self, influencer_info: Dict[str, Any], company_budget: Dict[str, Any], error: str = None) -> Dict[str, Any]:
        """フォールバック価格計算"""
        # 基本的な価格計算ロジック
        subscribers = influencer_info.get("subscriber_count", 50000)
        engagement_rate = influencer_info.get("engagement_rate", 2.0)
        category = influencer_info.get("category", "lifestyle")
        
        # フォロワー数による基本価格
        if subscribers < 10000:
            base_price = 55000
        elif subscribers < 50000:
            base_price = 140000
        elif subscribers < 100000:
            base_price = 300000
        elif subscribers < 500000:
            base_price = 600000
        else:
            base_price = 1400000
        
        # エンゲージメント率による調整
        if engagement_rate < 1.0:
            engagement_multiplier = 0.8
        elif engagement_rate < 3.0:
            engagement_multiplier = 1.0
        elif engagement_rate < 5.0:
            engagement_multiplier = 1.3
        else:
            engagement_multiplier = 1.6
        
        # カテゴリによる調整
        category_multiplier = self.base_pricing_data["category_multipliers"].get(category, 1.0)
        
        # 最終価格計算
        calculated_price = int(base_price * engagement_multiplier * category_multiplier)
        minimum_price = int(calculated_price * 0.8)
        maximum_price = int(calculated_price * 1.3)
        
        result = {
            "pricing_analysis": {
                "base_calculation": {
                    "follower_based_price": base_price,
                    "engagement_adjustment": engagement_multiplier,
                    "category_premium": category_multiplier,
                    "market_factor": 1.0
                },
                "calculated_price": {
                    "minimum_price": minimum_price,
                    "recommended_price": calculated_price,
                    "maximum_price": maximum_price,
                    "currency": "JPY"
                },
                "price_breakdown": {
                    "content_creation": int(calculated_price * 0.6),
                    "posting_fee": int(calculated_price * 0.3),
                    "usage_rights": int(calculated_price * 0.1),
                    "additional_services": 0
                }
            },
            "market_positioning": {
                "price_tier": "mid-tier",
                "competitive_position": "at market average",
                "value_proposition": "標準的な市場価格"
            },
            "negotiation_parameters": {
                "negotiation_room": 0.15,
                "minimum_acceptable": minimum_price,
                "ideal_closing_price": calculated_price,
                "walk_away_price": int(minimum_price * 0.9)
            },
            "pricing_strategy": {
                "recommended_approach": "market-based",
                "key_value_drivers": ["フォロワー数", "エンゲージメント率"],
                "price_justification": "市場標準価格に基づく算出"
            },
            "confidence": 0.6 if not error else 0.3
        }
        
        if error:
            result["error"] = error
        
        return result
    
    async def _optimize_pricing_strategy(self, payload: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """価格戦略の最適化"""
        current_pricing = payload.get("current_pricing", {})
        market_feedback = payload.get("market_feedback", {})
        negotiation_context = payload.get("negotiation_context", {})
        
        # 簡易最適化ロジック
        optimization_factors = []
        
        # 市場反応による調整
        if market_feedback.get("price_resistance", False):
            optimization_factors.append("price_reduction")
        elif market_feedback.get("price_acceptance", True):
            optimization_factors.append("value_emphasis")
        
        # 交渉文脈による調整
        if negotiation_context.get("urgency", "medium") == "high":
            optimization_factors.append("premium_pricing")
        
        optimized_strategy = {
            "optimization_recommendations": [
                "市場反応に基づく価格調整",
                "価値提案の強化",
                "柔軟な価格オプションの提示"
            ],
            "adjusted_pricing": current_pricing,  # 実際の実装では調整された価格
            "optimization_confidence": 0.7,
            "expected_improvement": 0.12
        }
        
        logger.info("✅ PricingAgent: 価格戦略最適化完了")
        return optimized_strategy
    
    async def _analyze_competitive_pricing(self, payload: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """競合価格分析"""
        target_market = payload.get("target_market", {})
        competitor_data = payload.get("competitor_data", [])
        
        # 簡易競合分析
        competitive_analysis = {
            "market_price_range": {
                "low_end": 200000,
                "high_end": 800000,
                "average": 400000
            },
            "competitive_position": "competitive",
            "market_gaps": [
                "プレミアムセグメントの機会",
                "バリュー提案の差別化"
            ],
            "pricing_recommendations": [
                "競合より10-15%高い価格設定",
                "付加価値サービスによる差別化"
            ],
            "confidence": 0.6
        }
        
        logger.info("✅ PricingAgent: 競合価格分析完了")
        return competitive_analysis
    
    async def _develop_price_negotiation_tactics(self, payload: Dict[str, Any], state: NegotiationState) -> Dict[str, Any]:
        """価格交渉戦術の開発"""
        price_proposal = payload.get("price_proposal", {})
        client_budget_signals = payload.get("client_budget_signals", {})
        
        negotiation_tactics = {
            "opening_strategy": {
                "initial_price": price_proposal.get("recommended_price", 350000),
                "justification_approach": "value-based",
                "negotiation_stance": "collaborative"
            },
            "concession_strategy": {
                "maximum_discount": 0.15,
                "concession_pattern": "decreasing",
                "value_trades": ["usage rights", "timeline flexibility"]
            },
            "closing_tactics": {
                "trial_close_signals": ["budget confirmation", "timeline discussion"],
                "objection_responses": ["ROI demonstration", "case study presentation"],
                "urgency_creation": "limited availability"
            },
            "alternative_structures": [
                "performance-based pricing",
                "package deal discounts",
                "long-term contract benefits"
            ],
            "confidence": 0.75
        }
        
        logger.info("✅ PricingAgent: 価格交渉戦術開発完了")
        return negotiation_tactics
    
    def get_supported_tasks(self) -> List[str]:
        """サポートするタスクタイプ"""
        return ["calculate_pricing", "optimize_pricing", "analyze_competition", "negotiate_price"]
    
    def _get_pricing_instruction(self) -> str:
        """システムインストラクション"""
        return """
あなたはインフルエンサーマーケティング価格戦略の専門エージェントです。

【役割】
- 市場価格の分析・算出
- 価格戦略の立案・最適化
- 競合価格の調査・比較
- 価格交渉戦術の開発

【価格算出要因】
- フォロワー数・エンゲージメント率
- コンテンツカテゴリ・専門性
- 市場需給・競合状況
- 企業予算・ROI期待値

【戦略原則】
- 価値に基づく価格設定
- 市場競争力の維持
- Win-Winの価格構造
- 長期関係を考慮した柔軟性

【出力品質】
- データに基づく客観的分析
- 実行可能な価格戦略
- 明確な根拠と論理
- 交渉に活用できる戦術
"""