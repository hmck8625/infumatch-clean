"""
交渉戦略最適化エンジン
AI学習に基づく戦略の動的最適化
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging

# NumPy互換の簡易実装（Cloud Run環境用）
class np:
    @staticmethod
    def mean(values):
        if not values:
            return 0
        return sum(values) / len(values)
    
    @staticmethod
    def random():
        import random
        return random
    
    class random:
        @staticmethod
        def random():
            import random
            return random.random()
        
        @staticmethod
        def choice(items):
            import random
            return random.choice(items)

class OptimizationMetric(Enum):
    """最適化指標"""
    DEAL_CLOSURE_RATE = "deal_closure_rate"
    AVERAGE_DEAL_VALUE = "average_deal_value"
    TIME_TO_CLOSE = "time_to_close"
    SATISFACTION_SCORE = "satisfaction_score"
    BUDGET_EFFICIENCY = "budget_efficiency"

class StrategyOptimizationEngine:
    """戦略最適化エンジン"""
    
    def __init__(self, pattern_storage, db_client=None):
        self.pattern_storage = pattern_storage
        self.db = db_client
        self.optimization_cache = {}
        
        # 最適化パラメータ
        self.optimization_params = {
            "learning_rate": 0.1,
            "exploration_rate": 0.2,  # 探索と活用のバランス
            "min_sample_size": 10,    # 最小サンプルサイズ
            "confidence_threshold": 0.7,
            "update_frequency_hours": 24
        }
        
        # 戦略パラメータの重み
        self.strategy_weights = {
            "tone_weights": {
                "friendly": 1.0,
                "professional": 1.0,
                "assertive": 1.0,
                "collaborative": 1.2  # 初期バイアス
            },
            "timing_weights": {
                "immediate": 0.8,
                "within_hour": 1.0,
                "within_day": 0.9,
                "next_day": 0.7
            },
            "flexibility_weights": {
                "high": 1.1,
                "medium": 1.0,
                "low": 0.9
            }
        }
    
    async def optimize_strategy(
        self,
        current_context: Dict,
        historical_patterns: List[Dict],
        optimization_goal: OptimizationMetric = OptimizationMetric.DEAL_CLOSURE_RATE
    ) -> Dict:
        """戦略を最適化"""
        
        print(f"🎯 戦略最適化開始 - 目標: {optimization_goal.value}")
        
        # 基本戦略を取得
        base_strategy = await self.pattern_storage.get_best_strategy(current_context)
        
        # 履歴データから学習
        optimization_insights = self._analyze_historical_performance(
            historical_patterns, optimization_goal
        )
        
        # 戦略パラメータを調整
        optimized_params = self._adjust_strategy_parameters(
            base_strategy, optimization_insights, current_context
        )
        
        # 予測スコアを計算
        prediction_scores = self._predict_outcomes(
            optimized_params, current_context, historical_patterns
        )
        
        # 最適化された戦略を構築
        optimized_strategy = {
            **base_strategy,
            "optimized_approach": optimized_params["best_tone"],
            "response_timing": optimized_params["optimal_timing"],
            "budget_strategy": optimized_params["budget_approach"],
            "negotiation_tactics": self._generate_tactics(optimized_params, current_context),
            "predicted_outcomes": prediction_scores,
            "optimization_confidence": optimized_params["confidence"],
            "optimization_timestamp": datetime.now().isoformat(),
            "optimization_goal": optimization_goal.value,
            "learning_insights": optimization_insights
        }
        
        # キャッシュに保存
        cache_key = self._generate_cache_key(current_context, optimization_goal)
        self.optimization_cache[cache_key] = optimized_strategy
        
        return optimized_strategy
    
    async def update_strategy_weights(
        self,
        outcome_data: Dict,
        strategy_used: Dict
    ) -> None:
        """戦略の重みを更新（強化学習）"""
        
        # 使用された戦略パラメータ
        tone_used = strategy_used.get("optimized_approach", "balanced")
        timing_used = strategy_used.get("response_timing", "within_hour")
        
        # 結果の評価
        success_score = self._evaluate_outcome(outcome_data)
        
        # 重みを更新（簡易的な強化学習）
        learning_rate = self.optimization_params["learning_rate"]
        
        # トーンの重み更新
        if tone_used in self.strategy_weights["tone_weights"]:
            current_weight = self.strategy_weights["tone_weights"][tone_used]
            new_weight = current_weight + learning_rate * (success_score - 0.5)
            self.strategy_weights["tone_weights"][tone_used] = max(0.1, min(2.0, new_weight))
        
        # タイミングの重み更新
        if timing_used in self.strategy_weights["timing_weights"]:
            current_weight = self.strategy_weights["timing_weights"][timing_used]
            new_weight = current_weight + learning_rate * (success_score - 0.5)
            self.strategy_weights["timing_weights"][timing_used] = max(0.1, min(2.0, new_weight))
        
        print(f"📊 戦略重み更新完了 - 成功スコア: {success_score:.2f}")
        
        # DBに保存
        if self.db:
            await self._save_weights_to_db()
    
    async def get_adaptive_recommendations(
        self,
        negotiation_state: Dict,
        real_time_signals: Dict
    ) -> List[Dict]:
        """リアルタイムシグナルに基づく適応的推奨事項"""
        
        recommendations = []
        
        # 感情分析に基づく推奨
        sentiment = real_time_signals.get("current_sentiment", 0)
        if sentiment < -0.3:
            recommendations.append({
                "type": "tone_adjustment",
                "action": "soften_approach",
                "reason": "ネガティブな感情を検出",
                "suggestion": "より協調的で理解を示すトーンに切り替えてください",
                "priority": "high"
            })
        elif sentiment > 0.5:
            recommendations.append({
                "type": "momentum_leverage",
                "action": "push_forward",
                "reason": "ポジティブな勢いを検出",
                "suggestion": "具体的な条件提示に進むタイミングです",
                "priority": "medium"
            })
        
        # 交渉段階に基づく推奨
        stage = negotiation_state.get("current_stage", "initial_contact")
        if stage == "condition_negotiation":
            # 予算柔軟性の推奨
            budget_signals = real_time_signals.get("budget_sensitivity", {})
            if budget_signals.get("high_sensitivity", False):
                recommendations.append({
                    "type": "budget_strategy",
                    "action": "offer_flexibility",
                    "reason": "価格感度が高い",
                    "suggestion": "段階的な価格オプションや付加価値を提示",
                    "priority": "high"
                })
        
        # 時間的要因に基づく推奨
        urgency = real_time_signals.get("urgency_level", "normal")
        if urgency == "high":
            recommendations.append({
                "type": "timing_strategy",
                "action": "accelerate_decision",
                "reason": "高い緊急性を検出",
                "suggestion": "期間限定オファーや即決特典を提示",
                "priority": "medium"
            })
        
        # 競合の存在に基づく推奨
        if real_time_signals.get("competitor_mentioned", False):
            recommendations.append({
                "type": "differentiation",
                "action": "highlight_unique_value",
                "reason": "競合他社への言及を検出",
                "suggestion": "独自の価値提案と差別化ポイントを強調",
                "priority": "high"
            })
        
        return recommendations
    
    async def predict_negotiation_outcome(
        self,
        current_state: Dict,
        proposed_action: Dict
    ) -> Dict:
        """交渉結果を予測"""
        
        # 類似パターンから予測
        similar_patterns = await self.pattern_storage.find_similar_patterns(current_state)
        
        if not similar_patterns:
            return self._get_default_prediction()
        
        # 各パターンの結果を重み付け平均
        success_probabilities = []
        expected_values = []
        expected_durations = []
        
        for pattern in similar_patterns:
            similarity = pattern.get("similarity_score", 0.5)
            metrics = pattern.get("success_metrics", {})
            
            # 成功確率
            if pattern.get("pattern_type") == "success":
                success_prob = 0.8 * similarity
            elif pattern.get("pattern_type") == "partial":
                success_prob = 0.5 * similarity
            else:
                success_prob = 0.2 * similarity
            
            success_probabilities.append(success_prob)
            
            # 期待値
            deal_value = metrics.get("deal_value", 0)
            expected_values.append(deal_value * similarity)
            
            # 期待期間
            duration = metrics.get("negotiation_duration_hours", 72)
            expected_durations.append(duration)
        
        # 予測結果を集計
        prediction = {
            "success_probability": np.mean(success_probabilities) if success_probabilities else 0.5,
            "expected_deal_value": np.mean(expected_values) if expected_values else 0,
            "expected_duration_hours": np.mean(expected_durations) if expected_durations else 48,
            "confidence_level": min(len(similar_patterns) / 5, 1.0),  # パターン数に基づく信頼度
            "risk_factors": self._identify_risk_factors(current_state, similar_patterns),
            "opportunity_factors": self._identify_opportunities(current_state, similar_patterns),
            "recommended_actions": await self.get_adaptive_recommendations(
                current_state, proposed_action
            ),
            "prediction_timestamp": datetime.now().isoformat()
        }
        
        return prediction
    
    def _analyze_historical_performance(
        self,
        patterns: List[Dict],
        optimization_goal: OptimizationMetric
    ) -> Dict:
        """履歴パフォーマンスを分析"""
        
        insights = {
            "best_performing_tones": {},
            "optimal_timing_patterns": {},
            "budget_flexibility_impact": {},
            "key_success_factors": [],
            "common_failure_points": []
        }
        
        # トーン別パフォーマンス
        tone_performance = {}
        for pattern in patterns:
            tone = pattern.get("context", {}).get("negotiation_tone", "unknown")
            metrics = pattern.get("success_metrics", {})
            
            if tone not in tone_performance:
                tone_performance[tone] = []
            
            # 最適化目標に応じたメトリクス
            if optimization_goal == OptimizationMetric.DEAL_CLOSURE_RATE:
                value = 1.0 if pattern.get("outcome") == "deal_closed" else 0.0
            elif optimization_goal == OptimizationMetric.AVERAGE_DEAL_VALUE:
                value = metrics.get("deal_value", 0)
            elif optimization_goal == OptimizationMetric.TIME_TO_CLOSE:
                value = 1.0 / max(metrics.get("negotiation_duration_hours", 1), 1)
            else:
                value = metrics.get("satisfaction_score", 0.5)
            
            tone_performance[tone].append(value)
        
        # 平均パフォーマンスを計算
        for tone, values in tone_performance.items():
            if values:
                insights["best_performing_tones"][tone] = np.mean(values)
        
        # 成功要因の抽出
        success_patterns = [p for p in patterns if p.get("pattern_type") == "success"]
        if success_patterns:
            # 共通のキーフレーズ
            all_phrases = []
            for pattern in success_patterns:
                all_phrases.extend(pattern.get("key_phrases", []))
            
            # 頻出フレーズを成功要因として抽出
            phrase_counts = {}
            for phrase in all_phrases:
                phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1
            
            insights["key_success_factors"] = [
                phrase for phrase, count in sorted(
                    phrase_counts.items(), key=lambda x: x[1], reverse=True
                )[:5]
            ]
        
        return insights
    
    def _adjust_strategy_parameters(
        self,
        base_strategy: Dict,
        optimization_insights: Dict,
        current_context: Dict
    ) -> Dict:
        """戦略パラメータを調整"""
        
        # 最適なトーンを選択
        tone_scores = optimization_insights.get("best_performing_tones", {})
        weighted_scores = {}
        
        for tone, performance in tone_scores.items():
            weight = self.strategy_weights["tone_weights"].get(tone, 1.0)
            weighted_scores[tone] = performance * weight
        
        # 探索と活用のバランス
        if np.random.random() < self.optimization_params["exploration_rate"]:
            # 探索: ランダムに選択
            best_tone = np.random.choice(list(self.strategy_weights["tone_weights"].keys()))
        else:
            # 活用: 最高スコアを選択
            best_tone = max(weighted_scores.items(), key=lambda x: x[1])[0] if weighted_scores else "balanced"
        
        # タイミング戦略
        urgency = current_context.get("urgency_level", "normal")
        if urgency == "high":
            optimal_timing = "immediate"
        elif urgency == "low":
            optimal_timing = "next_day"
        else:
            optimal_timing = "within_hour"
        
        # 予算アプローチ
        budget_sensitivity = current_context.get("budget_sensitivity", "medium")
        if budget_sensitivity == "high":
            budget_approach = "flexible"
        elif budget_sensitivity == "low":
            budget_approach = "firm"
        else:
            budget_approach = "moderate"
        
        return {
            "best_tone": best_tone,
            "optimal_timing": optimal_timing,
            "budget_approach": budget_approach,
            "confidence": self._calculate_confidence(optimization_insights, len(tone_scores))
        }
    
    def _generate_tactics(self, optimized_params: Dict, context: Dict) -> List[Dict]:
        """具体的な交渉戦術を生成"""
        
        tactics = []
        
        # トーンに基づく戦術
        tone = optimized_params.get("best_tone", "balanced")
        if tone == "collaborative":
            tactics.append({
                "name": "共創アプローチ",
                "description": "相手の成功も重視する姿勢を示す",
                "example_phrases": [
                    "一緒に成功を目指しましょう",
                    "お互いにメリットのある形を見つけたい",
                    "長期的なパートナーシップを築きたい"
                ]
            })
        elif tone == "assertive":
            tactics.append({
                "name": "価値強調",
                "description": "自社の価値と実績を明確に伝える",
                "example_phrases": [
                    "弊社の実績をご覧ください",
                    "この条件は業界最高水準です",
                    "限定的なオファーとなります"
                ]
            })
        
        # タイミングに基づく戦術
        timing = optimized_params.get("optimal_timing", "within_hour")
        if timing == "immediate":
            tactics.append({
                "name": "即応戦術",
                "description": "素早い対応で関心を維持",
                "action_items": [
                    "5分以内に初期返信",
                    "具体的な次のステップを提示",
                    "決定を促す要素を含める"
                ]
            })
        
        # 予算戦術
        budget_approach = optimized_params.get("budget_approach", "moderate")
        if budget_approach == "flexible":
            tactics.append({
                "name": "段階的価格提示",
                "description": "複数の価格オプションを提供",
                "options": [
                    "ベーシックプラン（最小構成）",
                    "スタンダードプラン（推奨）",
                    "プレミアムプラン（フルサポート）"
                ]
            })
        
        return tactics
    
    def _predict_outcomes(
        self,
        strategy_params: Dict,
        context: Dict,
        historical_patterns: List[Dict]
    ) -> Dict:
        """結果を予測"""
        
        # 簡易的な予測モデル
        base_success_rate = 0.5
        
        # トーンによる調整
        tone = strategy_params.get("best_tone", "balanced")
        tone_weight = self.strategy_weights["tone_weights"].get(tone, 1.0)
        success_rate = base_success_rate * tone_weight
        
        # コンテキストによる調整
        if context.get("influencer_engagement_rate", 0) > 3.0:
            success_rate *= 1.2
        
        if context.get("budget_match", 0) > 0.8:
            success_rate *= 1.1
        
        # 上限設定
        success_rate = min(success_rate, 0.95)
        
        return {
            "deal_closure_probability": success_rate,
            "expected_negotiation_rounds": 3 if success_rate > 0.7 else 4,
            "confidence_interval": [success_rate - 0.1, success_rate + 0.1],
            "factors_considered": len(historical_patterns)
        }
    
    def _evaluate_outcome(self, outcome_data: Dict) -> float:
        """結果を評価（0-1のスコア）"""
        
        score = 0.0
        
        # 取引成立
        if outcome_data.get("deal_closed", False):
            score += 0.5
        
        # 満足度
        satisfaction = outcome_data.get("satisfaction_score", 0.5)
        score += satisfaction * 0.3
        
        # 効率性
        expected_duration = outcome_data.get("expected_duration", 72)
        actual_duration = outcome_data.get("actual_duration", 72)
        if actual_duration < expected_duration:
            score += 0.2
        
        return min(score, 1.0)
    
    def _identify_risk_factors(
        self,
        current_state: Dict,
        similar_patterns: List[Dict]
    ) -> List[str]:
        """リスク要因を特定"""
        
        risks = []
        
        # 失敗パターンから学習
        failure_patterns = [p for p in similar_patterns if p.get("pattern_type") == "failure"]
        
        if len(failure_patterns) > len(similar_patterns) * 0.3:
            risks.append("類似状況での失敗率が高い")
        
        # 予算ミスマッチ
        if current_state.get("budget_gap", 0) > 0.3:
            risks.append("予算期待値に大きな乖離")
        
        # 応答遅延
        if current_state.get("response_delay_hours", 0) > 48:
            risks.append("応答の遅れによる関心低下")
        
        return risks
    
    def _identify_opportunities(
        self,
        current_state: Dict,
        similar_patterns: List[Dict]
    ) -> List[str]:
        """機会要因を特定"""
        
        opportunities = []
        
        # 成功パターンから学習
        success_patterns = [p for p in similar_patterns if p.get("pattern_type") == "success"]
        
        if success_patterns:
            # 高いエンゲージメント
            if current_state.get("engagement_signals", {}).get("high", False):
                opportunities.append("高い関心度を示すシグナル")
            
            # タイミングの良さ
            if current_state.get("timing_score", 0) > 0.8:
                opportunities.append("最適なタイミングでのアプローチ")
        
        return opportunities
    
    def _generate_cache_key(self, context: Dict, goal: OptimizationMetric) -> str:
        """キャッシュキーを生成"""
        
        key_elements = [
            context.get("influencer_category", ""),
            context.get("product_category", ""),
            context.get("negotiation_stage", ""),
            goal.value
        ]
        
        return "|".join(key_elements)
    
    async def _save_weights_to_db(self) -> None:
        """重みをDBに保存"""
        
        if self.db:
            try:
                weights_doc = {
                    "updated_at": datetime.now().isoformat(),
                    "strategy_weights": self.strategy_weights,
                    "optimization_params": self.optimization_params
                }
                
                self.db.collection("optimization_weights").document("current").set(
                    weights_doc, merge=True
                )
                
            except Exception as e:
                logging.error(f"重み保存エラー: {e}")
    
    def _get_default_prediction(self) -> Dict:
        """デフォルト予測を返す"""
        
        return {
            "success_probability": 0.5,
            "expected_deal_value": 0,
            "expected_duration_hours": 72,
            "confidence_level": 0.3,
            "risk_factors": ["履歴データ不足"],
            "opportunity_factors": [],
            "recommended_actions": [],
            "prediction_timestamp": datetime.now().isoformat()
        }