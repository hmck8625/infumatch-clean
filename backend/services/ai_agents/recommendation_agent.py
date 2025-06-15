"""
推薦エージェント（仮動作版）

@description インフルエンサーとキャンペーンの最適マッチングを実行
機械学習ベースの推薦システムとルールベースフィルタリングを組み合わせ

@author InfuMatch Development Team
@version 1.0.0
"""

import logging
import json
import asyncio
import math
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import statistics
from dataclasses import dataclass

from .base_agent import BaseAgent, AgentConfig

logger = logging.getLogger(__name__)


@dataclass
class MatchingCriteria:
    """マッチング基準"""
    target_audience: List[str]
    budget_min: int
    budget_max: int
    required_categories: List[str]
    preferred_engagement_rate: float
    geographic_focus: Optional[str] = None
    collaboration_history: bool = False
    min_subscriber_count: int = 1000
    max_subscriber_count: int = 100000


@dataclass
class InfluencerScore:
    """インフルエンサースコア"""
    channel_id: str
    overall_score: float
    category_match_score: float
    engagement_score: float
    audience_fit_score: float
    budget_fit_score: float
    availability_score: float
    risk_score: float
    explanation: str


class RecommendationAgent(BaseAgent):
    """
    推薦エージェント
    
    キャンペーン要件に基づいて最適なインフルエンサーを推薦
    """
    
    def __init__(self):
        """推薦エージェントの初期化"""
        config = AgentConfig(
            name="RecommendationAgent",
            model_name="gemini-1.5-pro",
            temperature=0.4,  # 推薦の一貫性のため中程度に設定
            max_output_tokens=2048,
            system_instruction=self._get_system_instruction()
        )
        super().__init__(config)
        
        # カテゴリ類似度マップ
        self.category_similarity = {
            "美容・ファッション": ["ライフスタイル", "エンタメ"],
            "料理・グルメ": ["ライフスタイル", "旅行"],
            "ゲーム": ["エンタメ", "教育・学習"],
            "ライフスタイル": ["美容・ファッション", "料理・グルメ", "旅行"],
            "エンタメ": ["ゲーム", "音楽", "美容・ファッション"],
            "教育・学習": ["ゲーム", "音楽"],
            "音楽": ["エンタメ", "教育・学習"],
            "旅行": ["料理・グルメ", "ライフスタイル"]
        }
        
        # エンゲージメント重み
        self.engagement_weights = {
            "subscriber_count": 0.2,
            "engagement_rate": 0.4,
            "video_consistency": 0.2,
            "audience_quality": 0.2
        }
    
    def _get_system_instruction(self) -> str:
        """システムインストラクションを取得"""
        return """
あなたはインフルエンサーマーケティングの推薦エキスパートです。

## 主な任務
1. キャンペーン要件とインフルエンサーの最適マッチング
2. 予算とROIの最適化
3. リスク評価と回避策の提案
4. 長期的なパートナーシップの可能性評価
5. A/Bテスト用のバリエーション提案

## 推薦の考慮要素
- コンテンツカテゴリの適合性
- ターゲットオーディエンスの重複度
- エンゲージメント率と品質
- 予算との適合性
- 過去のコラボレーション実績
- ブランドイメージとの親和性

## 出力品質基準
- 定量的スコアと定性的説明の両方を提供
- リスク要因を明確に識別
- 代替案も含めて複数の選択肢を提示
- 長期的な視点でのパートナーシップ価値を評価
"""
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        推薦処理のメイン関数
        
        Args:
            input_data: 入力データ
            
        Returns:
            Dict: 処理結果
        """
        try:
            action = input_data.get("action", "recommend_influencers")
            
            if action == "recommend_influencers":
                return await self.recommend_influencers(input_data)
            elif action == "evaluate_match":
                return await self.evaluate_single_match(input_data)
            elif action == "optimize_campaign":
                return await self.optimize_campaign_distribution(input_data)
            elif action == "analyze_competition":
                return await self.analyze_competitive_landscape(input_data)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
                
        except Exception as e:
            logger.error(f"❌ Recommendation processing failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def recommend_influencers(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        インフルエンサー推薦を実行
        
        Args:
            data: キャンペーン情報とインフルエンサーデータ
            
        Returns:
            Dict: 推薦結果
        """
        try:
            campaign = data.get("campaign", {})
            available_influencers = data.get("influencers", [])
            max_recommendations = data.get("max_recommendations", 10)
            
            # マッチング基準の構築
            criteria = self._build_matching_criteria(campaign)
            
            # 基本フィルタリング
            filtered_influencers = self._apply_basic_filters(available_influencers, criteria)
            
            if not filtered_influencers:
                return {
                    "success": True,
                    "recommendations": [],
                    "message": "条件に合致するインフルエンサーが見つかりませんでした",
                    "criteria_used": criteria.__dict__,
                    "agent": self.config.name,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # スコアリング
            scored_influencers = []
            for influencer in filtered_influencers:
                score = await self._calculate_influencer_score(influencer, criteria, campaign)
                scored_influencers.append(score)
            
            # スコア順でソート
            scored_influencers.sort(key=lambda x: x.overall_score, reverse=True)
            
            # トップN選択
            top_recommendations = scored_influencers[:max_recommendations]
            
            # AI による最終評価
            ai_evaluation = await self._ai_final_evaluation(top_recommendations, campaign)
            
            # ポートフォリオ最適化
            optimized_portfolio = await self._optimize_influencer_portfolio(
                top_recommendations, criteria
            )
            
            return {
                "success": True,
                "recommendations": [
                    {
                        "channel_id": rec.channel_id,
                        "overall_score": rec.overall_score,
                        "detailed_scores": {
                            "category_match": rec.category_match_score,
                            "engagement": rec.engagement_score,
                            "audience_fit": rec.audience_fit_score,
                            "budget_fit": rec.budget_fit_score,
                            "availability": rec.availability_score,
                            "risk": rec.risk_score
                        },
                        "explanation": rec.explanation,
                        "rank": idx + 1
                    }
                    for idx, rec in enumerate(top_recommendations)
                ],
                "ai_evaluation": ai_evaluation,
                "portfolio_optimization": optimized_portfolio,
                "matching_summary": {
                    "total_candidates": len(available_influencers),
                    "filtered_candidates": len(filtered_influencers),
                    "final_recommendations": len(top_recommendations),
                    "criteria_used": criteria.__dict__
                },
                "agent": self.config.name,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Influencer recommendation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_matching_criteria(self, campaign: Dict[str, Any]) -> MatchingCriteria:
        """キャンペーンからマッチング基準を構築"""
        return MatchingCriteria(
            target_audience=campaign.get("target_audience", []),
            budget_min=campaign.get("budget_min", 10000),
            budget_max=campaign.get("budget_max", 100000),
            required_categories=campaign.get("required_categories", []),
            preferred_engagement_rate=campaign.get("min_engagement_rate", 2.0),
            geographic_focus=campaign.get("geographic_focus"),
            collaboration_history=campaign.get("prefer_experienced", False),
            min_subscriber_count=campaign.get("min_subscribers", 1000),
            max_subscriber_count=campaign.get("max_subscribers", 100000)
        )
    
    def _apply_basic_filters(
        self, 
        influencers: List[Dict[str, Any]], 
        criteria: MatchingCriteria
    ) -> List[Dict[str, Any]]:
        """基本フィルタリングを適用"""
        filtered = []
        
        for influencer in influencers:
            # 登録者数フィルタ
            subscriber_count = influencer.get("subscriber_count", 0)
            if not (criteria.min_subscriber_count <= subscriber_count <= criteria.max_subscriber_count):
                continue
            
            # エンゲージメント率フィルタ
            engagement_rate = influencer.get("engagement_rate", 0)
            if engagement_rate < criteria.preferred_engagement_rate:
                continue
            
            # ビジネスメールフィルタ（必須）
            if not influencer.get("has_business_email", False):
                continue
            
            # アクティブステータス
            if influencer.get("status") != "active":
                continue
            
            filtered.append(influencer)
        
        return filtered
    
    async def _calculate_influencer_score(
        self, 
        influencer: Dict[str, Any], 
        criteria: MatchingCriteria, 
        campaign: Dict[str, Any]
    ) -> InfluencerScore:
        """インフルエンサーのスコアを計算"""
        
        # 各スコア要素を計算
        category_score = self._calculate_category_match_score(influencer, criteria)
        engagement_score = self._calculate_engagement_score(influencer)
        audience_score = await self._calculate_audience_fit_score(influencer, criteria)
        budget_score = self._calculate_budget_fit_score(influencer, criteria)
        availability_score = self._calculate_availability_score(influencer)
        risk_score = self._calculate_risk_score(influencer)
        
        # 重み付き総合スコア
        weights = {
            "category": 0.25,
            "engagement": 0.25,
            "audience": 0.20,
            "budget": 0.15,
            "availability": 0.10,
            "risk": 0.05
        }
        
        overall_score = (
            category_score * weights["category"] +
            engagement_score * weights["engagement"] +
            audience_score * weights["audience"] +
            budget_score * weights["budget"] +
            availability_score * weights["availability"] +
            (1.0 - risk_score) * weights["risk"]  # リスクは逆転
        )
        
        # 説明文生成
        explanation = self._generate_score_explanation(
            category_score, engagement_score, audience_score, 
            budget_score, availability_score, risk_score, influencer
        )
        
        return InfluencerScore(
            channel_id=influencer.get("channel_id", ""),
            overall_score=round(overall_score, 3),
            category_match_score=round(category_score, 3),
            engagement_score=round(engagement_score, 3),
            audience_fit_score=round(audience_score, 3),
            budget_fit_score=round(budget_score, 3),
            availability_score=round(availability_score, 3),
            risk_score=round(risk_score, 3),
            explanation=explanation
        )
    
    def _calculate_category_match_score(
        self, 
        influencer: Dict[str, Any], 
        criteria: MatchingCriteria
    ) -> float:
        """カテゴリマッチスコアの計算"""
        if not criteria.required_categories:
            return 1.0  # カテゴリ指定がない場合は満点
        
        # インフルエンサーのカテゴリを取得
        influencer_categories = influencer.get("topic_categories", [])
        primary_category = influencer.get("primary_category", "")
        
        if primary_category:
            influencer_categories.append(primary_category)
        
        # 直接マッチ
        direct_matches = set(criteria.required_categories) & set(influencer_categories)
        direct_score = len(direct_matches) / len(criteria.required_categories)
        
        # 類似カテゴリマッチ
        similar_score = 0.0
        for req_cat in criteria.required_categories:
            if req_cat in direct_matches:
                continue
            
            similar_categories = self.category_similarity.get(req_cat, [])
            for inf_cat in influencer_categories:
                if inf_cat in similar_categories:
                    similar_score += 0.5 / len(criteria.required_categories)
                    break
        
        return min(direct_score + similar_score, 1.0)
    
    def _calculate_engagement_score(self, influencer: Dict[str, Any]) -> float:
        """エンゲージメントスコアの計算"""
        engagement_rate = influencer.get("engagement_rate", 0)
        subscriber_count = influencer.get("subscriber_count", 0)
        video_count = influencer.get("video_count", 0)
        
        # エンゲージメント率の正規化（10%を上限とする）
        engagement_normalized = min(engagement_rate / 10.0, 1.0)
        
        # コンテンツ一貫性スコア
        consistency_score = min(video_count / 50, 1.0) if video_count > 0 else 0.0
        
        # 登録者数によるエンゲージメント補正
        if subscriber_count < 10000:
            size_bonus = 0.1  # 小規模の場合のボーナス
        elif subscriber_count < 50000:
            size_bonus = 0.05
        else:
            size_bonus = 0.0
        
        return min(engagement_normalized * 0.7 + consistency_score * 0.3 + size_bonus, 1.0)
    
    async def _calculate_audience_fit_score(
        self, 
        influencer: Dict[str, Any], 
        criteria: MatchingCriteria
    ) -> float:
        """オーディエンス適合性スコアの計算"""
        if not criteria.target_audience:
            return 1.0
        
        # インフルエンサーの説明文からオーディエンス特性を分析
        description = influencer.get("description", "")
        
        # AIによるオーディエンス分析
        prompt = f"""
        以下のYouTubeチャンネル説明文から、視聴者層を分析してください：
        
        ## チャンネル説明文
        {description}
        
        ## 分析対象のターゲット層
        {', '.join(criteria.target_audience)}
        
        各ターゲット層との適合度を0.0-1.0で評価してJSONで返してください：
        {{
            "target_matches": {{
                "ターゲット1": 適合度,
                "ターゲット2": 適合度
            }},
            "overall_audience_fit": 全体適合度,
            "audience_characteristics": ["特徴1", "特徴2"]
        }}
        """
        
        ai_response = await self.generate_response(prompt)
        
        if ai_response.get("success") and ai_response.get("parsed_content"):
            analysis = ai_response["parsed_content"]
            return analysis.get("overall_audience_fit", 0.5)
        else:
            # AIが失敗した場合はキーワードベースの簡易判定
            return self._simple_audience_match(description, criteria.target_audience)
    
    def _simple_audience_match(self, description: str, target_audience: List[str]) -> float:
        """簡易オーディエンス マッチング"""
        description_lower = description.lower()
        matches = 0
        
        audience_keywords = {
            "10代": ["学生", "高校生", "teenager", "teen"],
            "20代": ["大学生", "社会人", "若者", "20代"],
            "30代": ["アラサー", "30代", "大人"],
            "女性": ["女性", "女子", "レディース", "女の子"],
            "男性": ["男性", "男子", "メンズ", "男の子"],
            "主婦": ["主婦", "ママ", "お母さん", "家族"],
            "学生": ["学生", "勉強", "受験", "学校"]
        }
        
        for target in target_audience:
            keywords = audience_keywords.get(target, [target.lower()])
            if any(kw in description_lower for kw in keywords):
                matches += 1
        
        return matches / max(len(target_audience), 1)
    
    def _calculate_budget_fit_score(
        self, 
        influencer: Dict[str, Any], 
        criteria: MatchingCriteria
    ) -> float:
        """予算適合性スコアの計算"""
        subscriber_count = influencer.get("subscriber_count", 0)
        engagement_rate = influencer.get("engagement_rate", 0)
        
        # 推定価格を計算（登録者数 × 0.5円 + エンゲージメント補正）
        base_price = subscriber_count * 0.5
        engagement_multiplier = min(engagement_rate / 3.0, 2.0)
        estimated_price = int(base_price * engagement_multiplier)
        
        # 予算範囲との適合性
        if estimated_price <= criteria.budget_min:
            return 1.0  # 予算より安い場合は満点
        elif estimated_price <= criteria.budget_max:
            # 予算範囲内での適合度（安いほど高スコア）
            budget_range = criteria.budget_max - criteria.budget_min
            price_position = (estimated_price - criteria.budget_min) / budget_range
            return 1.0 - (price_position * 0.3)  # 最大30%減点
        else:
            # 予算オーバーの場合
            over_ratio = estimated_price / criteria.budget_max
            return max(1.0 - (over_ratio - 1.0), 0.0)
    
    def _calculate_availability_score(self, influencer: Dict[str, Any]) -> float:
        """利用可能性スコアの計算"""
        # 基本的には全て利用可能と仮定
        base_score = 1.0
        
        # 最近の活動状況をチェック
        fetched_at = influencer.get("fetched_at", "")
        if fetched_at:
            try:
                fetch_date = datetime.fromisoformat(fetched_at.replace('Z', '+00:00'))
                days_since_fetch = (datetime.utcnow().replace(tzinfo=fetch_date.tzinfo) - fetch_date).days
                
                # データが古い場合は減点
                if days_since_fetch > 30:
                    base_score -= 0.2
                elif days_since_fetch > 7:
                    base_score -= 0.1
            except:
                base_score -= 0.1  # 日付パースエラーの場合
        
        # ビジネスメールの品質
        emails = influencer.get("emails", [])
        business_emails = [e for e in emails if e.get("is_business", False)]
        
        if business_emails:
            # 優先度の高いビジネスメールがある
            max_priority = max(e.get("priority", 0) for e in business_emails)
            priority_bonus = min(max_priority / 10.0, 0.2)
            base_score += priority_bonus
        
        return min(base_score, 1.0)
    
    def _calculate_risk_score(self, influencer: Dict[str, Any]) -> float:
        """リスクスコアの計算（高いほどリスキー）"""
        risk_factors = 0.0
        
        # データ品質リスク
        data_quality_score = influencer.get("data_quality_score", 0.5)
        if data_quality_score < 0.7:
            risk_factors += 0.3
        
        # 登録者数の信頼性
        subscriber_count = influencer.get("subscriber_count", 0)
        hidden_subscriber_count = influencer.get("hidden_subscriber_count", False)
        if hidden_subscriber_count:
            risk_factors += 0.2
        
        # エンゲージメント率の異常値チェック
        engagement_rate = influencer.get("engagement_rate", 0)
        if engagement_rate > 20.0:  # 異常に高い場合
            risk_factors += 0.3
        elif engagement_rate < 0.5:  # 異常に低い場合
            risk_factors += 0.2
        
        # 新しいチャンネルのリスク
        video_count = influencer.get("video_count", 0)
        if video_count < 10:
            risk_factors += 0.3
        
        return min(risk_factors, 1.0)
    
    def _generate_score_explanation(
        self,
        category_score: float,
        engagement_score: float,
        audience_score: float,
        budget_score: float,
        availability_score: float,
        risk_score: float,
        influencer: Dict[str, Any]
    ) -> str:
        """スコア説明文の生成"""
        explanations = []
        
        # カテゴリマッチ
        if category_score >= 0.8:
            explanations.append("カテゴリが高度に一致")
        elif category_score >= 0.5:
            explanations.append("カテゴリが部分的に一致")
        else:
            explanations.append("カテゴリマッチが低い")
        
        # エンゲージメント
        engagement_rate = influencer.get("engagement_rate", 0)
        if engagement_rate >= 5.0:
            explanations.append("非常に高いエンゲージメント率")
        elif engagement_rate >= 2.0:
            explanations.append("良好なエンゲージメント率")
        else:
            explanations.append("エンゲージメント率が低め")
        
        # 予算適合性
        if budget_score >= 0.8:
            explanations.append("予算内で適正価格")
        elif budget_score >= 0.5:
            explanations.append("予算範囲内")
        else:
            explanations.append("予算をやや超過")
        
        # リスク
        if risk_score <= 0.2:
            explanations.append("低リスク")
        elif risk_score <= 0.5:
            explanations.append("中程度のリスク")
        else:
            explanations.append("要注意のリスク要因")
        
        return " / ".join(explanations)
    
    async def _ai_final_evaluation(
        self, 
        recommendations: List[InfluencerScore], 
        campaign: Dict[str, Any]
    ) -> Dict[str, Any]:
        """AI による最終評価"""
        top_5 = recommendations[:5]
        
        prompt = f"""
        以下のキャンペーンに対する推薦結果を評価してください：
        
        ## キャンペーン情報
        - 商品: {campaign.get('product_name', '')}
        - 予算: {campaign.get('budget_min', 0):,}円〜{campaign.get('budget_max', 0):,}円
        - ターゲット: {', '.join(campaign.get('target_audience', []))}
        - 目標: {campaign.get('campaign_goals', '')}
        
        ## 推薦されたインフルエンサー（上位5名）
        {json.dumps([{
            'channel_id': rec.channel_id,
            'overall_score': rec.overall_score,
            'explanation': rec.explanation
        } for rec in top_5], ensure_ascii=False, indent=2)}
        
        ## 評価観点
        1. 推薦の妥当性
        2. ポートフォリオのバランス
        3. ROI の期待値
        4. リスク要因
        5. 改善提案
        
        JSONで返してください：
        {{
            "recommendation_quality": "high/medium/low",
            "expected_roi": "高い/中程度/低い",
            "portfolio_balance": "バランス良い/偏りあり",
            "key_strengths": ["強み1", "強み2"],
            "concerns": ["懸念1", "懸念2"],
            "optimization_suggestions": ["提案1", "提案2"]
        }}
        """
        
        ai_response = await self.generate_response(prompt)
        
        if ai_response.get("success") and ai_response.get("parsed_content"):
            return ai_response["parsed_content"]
        else:
            return {
                "recommendation_quality": "medium",
                "expected_roi": "中程度",
                "portfolio_balance": "要評価",
                "key_strengths": ["データドリブンな選出"],
                "concerns": ["AI評価が失敗"],
                "optimization_suggestions": ["手動での詳細確認を推奨"]
            }
    
    async def _optimize_influencer_portfolio(
        self, 
        recommendations: List[InfluencerScore], 
        criteria: MatchingCriteria
    ) -> Dict[str, Any]:
        """インフルエンサーポートフォリオの最適化"""
        if len(recommendations) < 3:
            return {
                "optimized_portfolio": recommendations,
                "optimization_strategy": "insufficient_candidates",
                "diversity_score": 0.0
            }
        
        # 予算配分最適化
        total_budget = criteria.budget_max
        budget_per_influencer = total_budget // min(len(recommendations), 5)
        
        # 多様性スコア計算
        diversity_score = self._calculate_portfolio_diversity(recommendations[:5])
        
        # リスク分散
        risk_balanced_portfolio = self._balance_portfolio_risk(recommendations[:5])
        
        return {
            "optimized_portfolio": risk_balanced_portfolio,
            "optimization_strategy": "risk_diversification",
            "diversity_score": diversity_score,
            "recommended_budget_allocation": {
                "budget_per_influencer": budget_per_influencer,
                "total_portfolio_budget": total_budget,
                "expected_reach": self._estimate_portfolio_reach(risk_balanced_portfolio)
            }
        }
    
    def _calculate_portfolio_diversity(self, portfolio: List[InfluencerScore]) -> float:
        """ポートフォリオの多様性スコア計算"""
        if len(portfolio) <= 1:
            return 0.0
        
        # スコア分布の多様性
        scores = [rec.overall_score for rec in portfolio]
        score_variance = statistics.variance(scores) if len(scores) > 1 else 0
        
        # カテゴリ多様性（仮の実装）
        category_diversity = 0.8  # 実際には各インフルエンサーのカテゴリから計算
        
        # リスク多様性
        risks = [rec.risk_score for rec in portfolio]
        risk_variance = statistics.variance(risks) if len(risks) > 1 else 0
        
        diversity_score = (score_variance * 0.4 + category_diversity * 0.4 + risk_variance * 0.2)
        return min(diversity_score, 1.0)
    
    def _balance_portfolio_risk(self, portfolio: List[InfluencerScore]) -> List[InfluencerScore]:
        """ポートフォリオのリスクバランス調整"""
        # 高リスク・高リターンと低リスク・安定のバランスを取る
        high_performance = [rec for rec in portfolio if rec.overall_score >= 0.7]
        low_risk = [rec for rec in portfolio if rec.risk_score <= 0.3]
        
        # バランスの取れたポートフォリオを構築
        balanced = []
        
        # 高パフォーマンス・低リスクを優先
        for rec in high_performance:
            if rec.risk_score <= 0.3:
                balanced.append(rec)
        
        # 残りの枠を埋める
        remaining_slots = 5 - len(balanced)
        for rec in portfolio:
            if rec not in balanced and len(balanced) < 5:
                balanced.append(rec)
        
        return balanced[:5]
    
    def _estimate_portfolio_reach(self, portfolio: List[InfluencerScore]) -> Dict[str, int]:
        """ポートフォリオのリーチ推定"""
        # 実際の実装では、各インフルエンサーの登録者数等から計算
        estimated_total_reach = len(portfolio) * 25000  # 仮の値
        estimated_unique_reach = int(estimated_total_reach * 0.7)  # 重複除去
        
        return {
            "total_reach": estimated_total_reach,
            "unique_reach": estimated_unique_reach,
            "estimated_impressions": estimated_unique_reach * 2
        }
    
    async def evaluate_single_match(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """単一インフルエンサーとキャンペーンのマッチ評価"""
        influencer = data.get("influencer", {})
        campaign = data.get("campaign", {})
        
        criteria = self._build_matching_criteria(campaign)
        score = await self._calculate_influencer_score(influencer, criteria, campaign)
        
        # 詳細分析
        detailed_analysis = await self._generate_detailed_match_analysis(influencer, campaign, score)
        
        return {
            "success": True,
            "match_evaluation": {
                "overall_compatibility": score.overall_score,
                "detailed_scores": {
                    "category_match": score.category_match_score,
                    "engagement": score.engagement_score,
                    "audience_fit": score.audience_fit_score,
                    "budget_fit": score.budget_fit_score,
                    "availability": score.availability_score,
                    "risk": score.risk_score
                },
                "match_grade": self._grade_match_quality(score.overall_score),
                "explanation": score.explanation,
                "detailed_analysis": detailed_analysis
            },
            "agent": self.config.name,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _generate_detailed_match_analysis(
        self, 
        influencer: Dict[str, Any], 
        campaign: Dict[str, Any], 
        score: InfluencerScore
    ) -> Dict[str, Any]:
        """詳細マッチ分析"""
        prompt = f"""
        インフルエンサーとキャンペーンの詳細適合性を分析してください：
        
        ## インフルエンサー情報
        - チャンネル名: {influencer.get('channel_name', '')}
        - 登録者数: {influencer.get('subscriber_count', 0):,}人
        - エンゲージメント率: {influencer.get('engagement_rate', 0)}%
        - 説明: {influencer.get('description', '')[:300]}...
        
        ## キャンペーン情報
        - 商品: {campaign.get('product_name', '')}
        - 予算: {campaign.get('budget_min', 0):,}円〜{campaign.get('budget_max', 0):,}円
        - 目標: {campaign.get('campaign_goals', '')}
        
        ## 算出スコア
        - 総合: {score.overall_score}
        - 説明: {score.explanation}
        
        詳細分析をJSONで返してください：
        {{
            "synergy_potential": "high/medium/low",
            "content_fit_analysis": "分析内容",
            "audience_overlap_estimate": "高い/中程度/低い",
            "collaboration_recommendations": ["推奨1", "推奨2"],
            "success_probability": 0.0-1.0,
            "key_risks": ["リスク1", "リスク2"],
            "optimization_opportunities": ["機会1", "機会2"]
        }}
        """
        
        ai_response = await self.generate_response(prompt)
        
        if ai_response.get("success") and ai_response.get("parsed_content"):
            return ai_response["parsed_content"]
        else:
            return {
                "synergy_potential": "medium",
                "content_fit_analysis": "要手動評価",
                "audience_overlap_estimate": "中程度",
                "collaboration_recommendations": ["詳細協議を推奨"],
                "success_probability": 0.5,
                "key_risks": ["AI分析失敗のため要確認"],
                "optimization_opportunities": ["詳細データ分析"]
            }
    
    def _grade_match_quality(self, score: float) -> str:
        """マッチ品質のグレード判定"""
        if score >= 0.8:
            return "Excellent"
        elif score >= 0.6:
            return "Good"
        elif score >= 0.4:
            return "Fair"
        else:
            return "Poor"
    
    async def optimize_campaign_distribution(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """キャンペーン配分最適化"""
        campaign = data.get("campaign", {})
        selected_influencers = data.get("selected_influencers", [])
        
        if not selected_influencers:
            return {
                "success": False,
                "error": "No influencers selected for optimization"
            }
        
        total_budget = campaign.get("budget_max", 100000)
        
        # 各インフルエンサーの期待ROIを計算
        roi_estimates = []
        for influencer in selected_influencers:
            roi = self._estimate_influencer_roi(influencer, campaign)
            roi_estimates.append(roi)
        
        # 予算配分最適化
        optimized_allocation = self._optimize_budget_allocation(
            selected_influencers, roi_estimates, total_budget
        )
        
        return {
            "success": True,
            "optimization_result": {
                "budget_allocation": optimized_allocation,
                "expected_total_roi": sum(roi["expected_roi"] for roi in roi_estimates),
                "risk_assessment": self._assess_portfolio_risk(selected_influencers),
                "performance_prediction": await self._predict_campaign_performance(
                    selected_influencers, campaign
                )
            },
            "agent": self.config.name,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _estimate_influencer_roi(self, influencer: Dict[str, Any], campaign: Dict[str, Any]) -> Dict[str, Any]:
        """インフルエンサーROI推定"""
        subscriber_count = influencer.get("subscriber_count", 0)
        engagement_rate = influencer.get("engagement_rate", 0)
        
        # 推定リーチ
        estimated_reach = int(subscriber_count * (engagement_rate / 100) * 2)  # エンゲージメント×2
        
        # 推定コスト
        estimated_cost = int(subscriber_count * 0.5 * min(engagement_rate / 3.0, 2.0))
        
        # ROI計算（簡易版）
        roi = estimated_reach / max(estimated_cost, 1)
        
        return {
            "channel_id": influencer.get("channel_id"),
            "estimated_reach": estimated_reach,
            "estimated_cost": estimated_cost,
            "expected_roi": round(roi, 2)
        }
    
    def _optimize_budget_allocation(
        self, 
        influencers: List[Dict[str, Any]], 
        roi_estimates: List[Dict[str, Any]], 
        total_budget: int
    ) -> List[Dict[str, Any]]:
        """予算配分最適化"""
        # ROIに基づく重み付け配分
        total_roi = sum(roi["expected_roi"] for roi in roi_estimates)
        
        allocations = []
        for i, (influencer, roi_data) in enumerate(zip(influencers, roi_estimates)):
            if total_roi > 0:
                weight = roi_data["expected_roi"] / total_roi
                allocated_budget = int(total_budget * weight)
            else:
                allocated_budget = total_budget // len(influencers)
            
            allocations.append({
                "channel_id": influencer.get("channel_id"),
                "channel_name": influencer.get("channel_name"),
                "allocated_budget": allocated_budget,
                "budget_percentage": round((allocated_budget / total_budget) * 100, 1),
                "expected_roi": roi_data["expected_roi"]
            })
        
        return allocations
    
    def _assess_portfolio_risk(self, influencers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """ポートフォリオリスク評価"""
        risk_scores = [self._calculate_risk_score(inf) for inf in influencers]
        
        avg_risk = statistics.mean(risk_scores) if risk_scores else 0
        max_risk = max(risk_scores) if risk_scores else 0
        risk_variance = statistics.variance(risk_scores) if len(risk_scores) > 1 else 0
        
        return {
            "average_risk": round(avg_risk, 2),
            "maximum_risk": round(max_risk, 2),
            "risk_distribution": "分散" if risk_variance > 0.1 else "集中",
            "overall_risk_level": "high" if avg_risk > 0.6 else "medium" if avg_risk > 0.3 else "low"
        }
    
    async def _predict_campaign_performance(
        self, 
        influencers: List[Dict[str, Any]], 
        campaign: Dict[str, Any]
    ) -> Dict[str, Any]:
        """キャンペーンパフォーマンス予測"""
        total_subscribers = sum(inf.get("subscriber_count", 0) for inf in influencers)
        avg_engagement = statistics.mean([inf.get("engagement_rate", 0) for inf in influencers])
        
        # 予測指標
        estimated_reach = int(total_subscribers * 0.3)  # 30%リーチ想定
        estimated_engagements = int(estimated_reach * (avg_engagement / 100))
        estimated_conversions = int(estimated_engagements * 0.02)  # 2%コンバージョン想定
        
        return {
            "estimated_metrics": {
                "total_reach": estimated_reach,
                "total_engagements": estimated_engagements,
                "estimated_conversions": estimated_conversions,
                "reach_rate": round((estimated_reach / total_subscribers) * 100, 1)
            },
            "performance_confidence": "medium",
            "success_probability": 0.7,
            "key_success_factors": [
                "コンテンツ品質",
                "タイミング",
                "インフルエンサーとのコミュニケーション"
            ]
        }
    
    async def analyze_competitive_landscape(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """競合環境分析"""
        category = data.get("category", "")
        budget_range = data.get("budget_range", {})
        
        # 実際の実装では、より詳細な競合分析を行う
        # ここでは簡易的な分析を提供
        
        competitive_analysis = {
            "market_saturation": "medium",
            "price_competitiveness": "competitive",
            "opportunity_areas": [
                "ニッチカテゴリの開拓",
                "中規模インフルエンサーとの長期パートナーシップ"
            ],
            "threat_factors": [
                "大手企業の参入",
                "インフルエンサー料金の高騰"
            ],
            "recommendations": [
                "独自性のあるキャンペーン企画",
                "データドリブンなROI最適化"
            ]
        }
        
        return {
            "success": True,
            "competitive_analysis": competitive_analysis,
            "agent": self.config.name,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_capabilities(self) -> List[str]:
        """エージェントの機能一覧"""
        return [
            "インフルエンサー推薦",
            "マッチング評価",
            "ポートフォリオ最適化",
            "予算配分最適化",
            "ROI予測",
            "リスク評価",
            "パフォーマンス予測",
            "競合分析"
        ]