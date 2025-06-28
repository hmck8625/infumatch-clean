"""
予測分析モジュール
交渉の成功確率と最適なアクションを予測
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

class PredictionType(Enum):
    """予測タイプ"""
    SUCCESS_PROBABILITY = "success_probability"
    OPTIMAL_TIMING = "optimal_timing"
    BUDGET_CONVERGENCE = "budget_convergence"
    ENGAGEMENT_TREND = "engagement_trend"
    RISK_ASSESSMENT = "risk_assessment"

class PredictiveAnalyticsModule:
    """予測分析モジュール"""
    
    def __init__(self, pattern_storage, optimization_engine):
        self.pattern_storage = pattern_storage
        self.optimization_engine = optimization_engine
        
        # 予測モデルパラメータ
        self.model_params = {
            "time_decay_factor": 0.95,  # 時間経過による重み減衰
            "min_confidence_threshold": 0.6,
            "prediction_horizon_hours": 72,
            "feature_importance": {
                "response_time": 0.25,
                "sentiment_trend": 0.20,
                "budget_alignment": 0.20,
                "engagement_level": 0.15,
                "negotiation_stage": 0.10,
                "historical_success": 0.10
            }
        }
    
    async def generate_comprehensive_prediction(
        self,
        thread_id: str,
        current_state: Dict,
        conversation_history: List[Dict]
    ) -> Dict:
        """包括的な予測を生成"""
        
        print(f"🔮 包括的予測分析開始 - Thread: {thread_id}")
        
        # 各種予測を実行
        predictions = {
            "thread_id": thread_id,
            "timestamp": datetime.now().isoformat(),
            "current_stage": current_state.get("negotiation_stage", "unknown"),
            
            # 成功確率予測
            "success_prediction": await self._predict_success_probability(
                current_state, conversation_history
            ),
            
            # タイミング予測
            "timing_prediction": await self._predict_optimal_timing(
                current_state, conversation_history
            ),
            
            # 予算収束予測
            "budget_prediction": await self._predict_budget_convergence(
                current_state, conversation_history
            ),
            
            # エンゲージメント予測
            "engagement_prediction": await self._predict_engagement_trend(
                current_state, conversation_history
            ),
            
            # リスク評価
            "risk_assessment": await self._assess_negotiation_risks(
                current_state, conversation_history
            ),
            
            # 推奨アクション
            "recommended_actions": await self._generate_action_recommendations(
                current_state
            ),
            
            # 全体的な信頼度
            "overall_confidence": 0.0  # 後で計算
        }
        
        # 全体的な信頼度を計算
        confidence_scores = [
            predictions["success_prediction"]["confidence"],
            predictions["timing_prediction"]["confidence"],
            predictions["budget_prediction"]["confidence"],
            predictions["engagement_prediction"]["confidence"]
        ]
        predictions["overall_confidence"] = np.mean(confidence_scores)
        
        return predictions
    
    async def _predict_success_probability(
        self,
        current_state: Dict,
        conversation_history: List[Dict]
    ) -> Dict:
        """成功確率を予測"""
        
        # 特徴量を抽出
        features = self._extract_prediction_features(current_state, conversation_history)
        
        # 履歴パターンから類似ケースを取得
        similar_patterns = await self.pattern_storage.find_similar_patterns(current_state)
        
        # ベース確率
        base_probability = 0.5
        
        # 特徴量による調整
        probability_adjustments = []
        
        # 応答時間の影響
        avg_response_time = features.get("avg_response_time_hours", 24)
        if avg_response_time < 6:
            probability_adjustments.append(0.15)
        elif avg_response_time < 24:
            probability_adjustments.append(0.05)
        else:
            probability_adjustments.append(-0.10)
        
        # センチメント傾向
        sentiment_trend = features.get("sentiment_trend", 0)
        probability_adjustments.append(sentiment_trend * 0.2)
        
        # 予算アライメント
        budget_alignment = features.get("budget_alignment_score", 0.5)
        probability_adjustments.append((budget_alignment - 0.5) * 0.3)
        
        # エンゲージメントレベル
        engagement_score = features.get("engagement_score", 0.5)
        probability_adjustments.append((engagement_score - 0.5) * 0.25)
        
        # 履歴成功率
        if similar_patterns:
            historical_success_rate = self._calculate_historical_success_rate(similar_patterns)
            probability_adjustments.append((historical_success_rate - 0.5) * 0.4)
        
        # 最終確率を計算
        final_probability = base_probability + sum(probability_adjustments)
        final_probability = max(0.05, min(0.95, final_probability))  # 5%-95%に制限
        
        # 信頼区間を計算
        confidence_interval = self._calculate_confidence_interval(
            final_probability, len(similar_patterns)
        )
        
        return {
            "probability": final_probability,
            "confidence": self._calculate_prediction_confidence(features, similar_patterns),
            "confidence_interval": confidence_interval,
            "key_factors": self._identify_key_factors(probability_adjustments, features),
            "trend": self._calculate_probability_trend(current_state, conversation_history)
        }
    
    async def _predict_optimal_timing(
        self,
        current_state: Dict,
        conversation_history: List[Dict]
    ) -> Dict:
        """最適なタイミングを予測"""
        
        # 現在の勢いを分析
        momentum = self._analyze_conversation_momentum(conversation_history)
        
        # 相手の応答パターンを分析
        response_pattern = self._analyze_response_pattern(conversation_history)
        
        # 最適タイミングを決定
        if momentum > 0.7 and response_pattern["avg_response_hours"] < 6:
            optimal_action = "immediate_follow_up"
            timing_window = "0-2時間以内"
            reasoning = "高い勢いと迅速な応答パターン"
        elif momentum > 0.5:
            optimal_action = "timely_response"
            timing_window = "2-6時間以内"
            reasoning = "良好な進展と安定した対話"
        elif response_pattern["pattern"] == "business_hours":
            optimal_action = "next_business_day"
            timing_window = "翌営業日の午前中"
            reasoning = "ビジネスアワー中心の応答パターン"
        else:
            optimal_action = "strategic_pause"
            timing_window = "24-48時間後"
            reasoning = "熟考を促す戦略的な間"
        
        return {
            "optimal_action": optimal_action,
            "timing_window": timing_window,
            "reasoning": reasoning,
            "urgency_score": momentum,
            "response_pattern": response_pattern,
            "confidence": 0.7 + (0.3 * min(len(conversation_history) / 10, 1.0))
        }
    
    async def _predict_budget_convergence(
        self,
        current_state: Dict,
        conversation_history: List[Dict]
    ) -> Dict:
        """予算収束を予測"""
        
        # 予算関連の言及を抽出
        budget_mentions = self._extract_budget_mentions(conversation_history)
        
        if not budget_mentions:
            return {
                "convergence_probability": 0.5,
                "estimated_final_range": None,
                "negotiation_room": "unknown",
                "confidence": 0.3,
                "status": "no_budget_discussion"
            }
        
        # 予算の推移を分析
        budget_trajectory = self._analyze_budget_trajectory(budget_mentions)
        
        # 収束点を予測
        if budget_trajectory["trend"] == "converging":
            convergence_prob = 0.8
            estimated_range = budget_trajectory["projected_range"]
            negotiation_room = "limited"
        elif budget_trajectory["trend"] == "diverging":
            convergence_prob = 0.3
            estimated_range = budget_trajectory["current_gap"]
            negotiation_room = "significant"
        else:
            convergence_prob = 0.5
            estimated_range = budget_trajectory["average_range"]
            negotiation_room = "moderate"
        
        return {
            "convergence_probability": convergence_prob,
            "estimated_final_range": estimated_range,
            "negotiation_room": negotiation_room,
            "trajectory": budget_trajectory,
            "confidence": 0.5 + (0.4 * len(budget_mentions) / 5),
            "recommendation": self._generate_budget_recommendation(budget_trajectory)
        }
    
    async def _predict_engagement_trend(
        self,
        current_state: Dict,
        conversation_history: List[Dict]
    ) -> Dict:
        """エンゲージメント傾向を予測"""
        
        # エンゲージメント指標を計算
        engagement_metrics = self._calculate_engagement_metrics(conversation_history)
        
        # トレンドを分析
        if len(conversation_history) < 3:
            trend = "insufficient_data"
            prediction = "stable"
        else:
            recent_engagement = engagement_metrics["recent_score"]
            overall_engagement = engagement_metrics["overall_score"]
            
            if recent_engagement > overall_engagement * 1.2:
                trend = "increasing"
                prediction = "continued_high_engagement"
            elif recent_engagement < overall_engagement * 0.8:
                trend = "decreasing"
                prediction = "risk_of_disengagement"
            else:
                trend = "stable"
                prediction = "maintained_engagement"
        
        # 次の3ラウンドの予測
        future_engagement = self._project_future_engagement(
            engagement_metrics, trend
        )
        
        return {
            "current_level": engagement_metrics["overall_score"],
            "trend": trend,
            "prediction": prediction,
            "future_projection": future_engagement,
            "risk_indicators": engagement_metrics["risk_indicators"],
            "opportunity_indicators": engagement_metrics["opportunity_indicators"],
            "confidence": engagement_metrics["confidence"]
        }
    
    async def _assess_negotiation_risks(
        self,
        current_state: Dict,
        conversation_history: List[Dict]
    ) -> Dict:
        """交渉リスクを評価"""
        
        risks = {
            "overall_risk_level": "medium",
            "risk_factors": [],
            "mitigation_strategies": [],
            "early_warning_signs": []
        }
        
        # 各リスク要因を評価
        risk_scores = {}
        
        # 1. 応答遅延リスク
        response_delays = self._check_response_delays(conversation_history)
        if response_delays["max_delay_hours"] > 48:
            risk_scores["response_delay"] = 0.8
            risks["risk_factors"].append({
                "type": "response_delay",
                "severity": "high",
                "description": "応答時間の長期化",
                "impact": "関心の低下や他社への流出"
            })
            risks["mitigation_strategies"].append(
                "迅速なフォローアップと価値の再強調"
            )
        
        # 2. 予算ミスマッチリスク
        budget_gap = current_state.get("budget_gap_percentage", 0)
        if budget_gap > 30:
            risk_scores["budget_mismatch"] = 0.9
            risks["risk_factors"].append({
                "type": "budget_mismatch",
                "severity": "high",
                "description": "予算期待値の大きな乖離",
                "impact": "交渉決裂の可能性"
            })
            risks["mitigation_strategies"].append(
                "段階的な価値提案と柔軟な価格オプション"
            )
        
        # 3. 競合リスク
        competitor_mentions = self._detect_competitor_mentions(conversation_history)
        if competitor_mentions > 0:
            risk_scores["competition"] = 0.7
            risks["risk_factors"].append({
                "type": "competition",
                "severity": "medium",
                "description": "競合他社の存在",
                "impact": "価格競争や条件比較"
            })
            risks["mitigation_strategies"].append(
                "独自価値の強調と差別化ポイントの明確化"
            )
        
        # 4. コミュニケーション停滞リスク
        if current_state.get("rounds_without_progress", 0) > 2:
            risk_scores["stagnation"] = 0.6
            risks["risk_factors"].append({
                "type": "stagnation",
                "severity": "medium",
                "description": "交渉の停滞",
                "impact": "モメンタムの喪失"
            })
            risks["mitigation_strategies"].append(
                "新しい提案や視点の導入"
            )
        
        # 全体的なリスクレベルを計算
        if risk_scores:
            avg_risk = np.mean(list(risk_scores.values()))
            if avg_risk > 0.7:
                risks["overall_risk_level"] = "high"
            elif avg_risk > 0.4:
                risks["overall_risk_level"] = "medium"
            else:
                risks["overall_risk_level"] = "low"
        
        # 早期警告サイン
        risks["early_warning_signs"] = [
            "返信間隔の急激な延長",
            "質問の減少や具体性の欠如",
            "価格に関する繰り返しの懸念表明",
            "意思決定の先延ばし"
        ]
        
        return risks
    
    async def _generate_action_recommendations(
        self,
        current_state: Dict
    ) -> List[Dict]:
        """アクション推奨を生成"""
        
        recommendations = []
        stage = current_state.get("negotiation_stage", "unknown")
        
        # ステージ別の推奨アクション
        if stage == "initial_contact":
            recommendations.append({
                "action": "build_rapport",
                "description": "信頼関係の構築に注力",
                "specific_steps": [
                    "パーソナライズされた提案の作成",
                    "過去の成功事例の共有",
                    "相手のニーズの深掘り"
                ],
                "priority": "high",
                "expected_impact": "関心度の向上"
            })
        
        elif stage == "condition_negotiation":
            recommendations.append({
                "action": "value_reinforcement",
                "description": "価値提案の強化",
                "specific_steps": [
                    "ROIの具体的な提示",
                    "追加特典の提案",
                    "柔軟な支払い条件の提示"
                ],
                "priority": "high",
                "expected_impact": "合意確率の向上"
            })
        
        elif stage == "final_agreement":
            recommendations.append({
                "action": "close_deal",
                "description": "クロージングの実行",
                "specific_steps": [
                    "最終条件の明確な提示",
                    "期限付きインセンティブ",
                    "次のステップの具体化"
                ],
                "priority": "critical",
                "expected_impact": "取引成立"
            })
        
        # リスクベースの推奨
        if current_state.get("risk_level", "medium") == "high":
            recommendations.append({
                "action": "risk_mitigation",
                "description": "リスク軽減策の実行",
                "specific_steps": [
                    "懸念事項の直接的な対処",
                    "保証や試用期間の提供",
                    "段階的な導入プランの提案"
                ],
                "priority": "high",
                "expected_impact": "リスク要因の解消"
            })
        
        return recommendations
    
    def _extract_prediction_features(
        self,
        current_state: Dict,
        conversation_history: List[Dict]
    ) -> Dict:
        """予測用の特徴量を抽出"""
        
        features = {
            "conversation_length": len(conversation_history),
            "current_stage": current_state.get("negotiation_stage", "unknown"),
            "rounds_count": current_state.get("round_number", 1),
            "avg_response_time_hours": self._calculate_avg_response_time(conversation_history),
            "sentiment_trend": self._calculate_sentiment_trend(conversation_history),
            "budget_alignment_score": self._calculate_budget_alignment(current_state),
            "engagement_score": self._calculate_engagement_score(conversation_history),
            "message_length_trend": self._analyze_message_length_trend(conversation_history),
            "question_ratio": self._calculate_question_ratio(conversation_history),
            "positive_signal_count": self._count_positive_signals(conversation_history)
        }
        
        return features
    
    def _calculate_historical_success_rate(self, patterns: List[Dict]) -> float:
        """履歴成功率を計算"""
        
        if not patterns:
            return 0.5
        
        success_count = sum(
            1 for p in patterns 
            if p.get("pattern_type") in ["success", "partial"]
        )
        
        return success_count / len(patterns)
    
    def _calculate_confidence_interval(
        self,
        probability: float,
        sample_size: int
    ) -> List[float]:
        """信頼区間を計算"""
        
        # 簡易的な信頼区間計算
        if sample_size < 5:
            margin = 0.2
        elif sample_size < 20:
            margin = 0.1
        else:
            margin = 0.05
        
        return [
            max(0, probability - margin),
            min(1, probability + margin)
        ]
    
    def _calculate_prediction_confidence(
        self,
        features: Dict,
        similar_patterns: List[Dict]
    ) -> float:
        """予測の信頼度を計算"""
        
        confidence = 0.5
        
        # サンプルサイズによる信頼度
        pattern_count = len(similar_patterns)
        if pattern_count >= 20:
            confidence += 0.3
        elif pattern_count >= 10:
            confidence += 0.2
        elif pattern_count >= 5:
            confidence += 0.1
        
        # 会話の長さによる信頼度
        conv_length = features.get("conversation_length", 0)
        if conv_length >= 10:
            confidence += 0.15
        elif conv_length >= 5:
            confidence += 0.1
        
        # データの完全性
        if features.get("budget_alignment_score", 0) > 0:
            confidence += 0.05
        
        return min(confidence, 0.95)
    
    def _identify_key_factors(
        self,
        adjustments: List[float],
        features: Dict
    ) -> List[Dict]:
        """主要な影響要因を特定"""
        
        factor_names = [
            "応答時間",
            "感情傾向",
            "予算適合性",
            "エンゲージメント",
            "過去の成功率"
        ]
        
        factors = []
        for i, (name, adjustment) in enumerate(zip(factor_names, adjustments)):
            if abs(adjustment) > 0.05:
                factors.append({
                    "factor": name,
                    "impact": "positive" if adjustment > 0 else "negative",
                    "magnitude": abs(adjustment)
                })
        
        # 影響度でソート
        factors.sort(key=lambda x: x["magnitude"], reverse=True)
        
        return factors[:3]  # 上位3つ
    
    def _calculate_probability_trend(
        self,
        current_state: Dict,
        conversation_history: List[Dict]
    ) -> str:
        """確率のトレンドを計算"""
        
        if len(conversation_history) < 3:
            return "stable"
        
        # 最近のポジティブシグナル
        recent_positive = self._count_positive_signals(conversation_history[-3:])
        overall_positive = self._count_positive_signals(conversation_history)
        
        recent_rate = recent_positive / 3
        overall_rate = overall_positive / len(conversation_history)
        
        if recent_rate > overall_rate * 1.2:
            return "improving"
        elif recent_rate < overall_rate * 0.8:
            return "declining"
        else:
            return "stable"
    
    def _analyze_conversation_momentum(
        self,
        conversation_history: List[Dict]
    ) -> float:
        """会話の勢いを分析"""
        
        if len(conversation_history) < 2:
            return 0.5
        
        # 応答間隔の短縮
        response_times = []
        for i in range(1, len(conversation_history)):
            # 簡易的な時間差計算
            response_times.append(1)  # 実際は時刻差を計算
        
        # メッセージ長の増加
        recent_length = np.mean([
            len(msg.get("content", "")) 
            for msg in conversation_history[-3:]
        ])
        
        # ポジティブシグナル
        positive_signals = self._count_positive_signals(conversation_history[-3:])
        
        # 総合的な勢いスコア
        momentum = 0.3 + (positive_signals / 3) * 0.4 + min(recent_length / 500, 0.3)
        
        return min(momentum, 1.0)
    
    def _analyze_response_pattern(
        self,
        conversation_history: List[Dict]
    ) -> Dict:
        """応答パターンを分析"""
        
        # 簡易実装
        return {
            "pattern": "business_hours",
            "avg_response_hours": 12,
            "consistency": 0.7,
            "preferred_time": "10:00-18:00"
        }
    
    def _extract_budget_mentions(
        self,
        conversation_history: List[Dict]
    ) -> List[Dict]:
        """予算に関する言及を抽出"""
        
        budget_mentions = []
        budget_keywords = ["予算", "価格", "費用", "料金", "円", "万円"]
        
        for i, msg in enumerate(conversation_history):
            content = msg.get("content", "").lower()
            if any(keyword in content for keyword in budget_keywords):
                # 簡易的な金額抽出
                budget_mentions.append({
                    "message_index": i,
                    "content": content[:100],
                    "role": msg.get("role", "user")
                })
        
        return budget_mentions
    
    def _analyze_budget_trajectory(
        self,
        budget_mentions: List[Dict]
    ) -> Dict:
        """予算の推移を分析"""
        
        # 簡易実装
        return {
            "trend": "converging",
            "projected_range": {"min": 300000, "max": 500000},
            "current_gap": 200000,
            "average_range": {"min": 350000, "max": 450000}
        }
    
    def _generate_budget_recommendation(
        self,
        trajectory: Dict
    ) -> str:
        """予算に関する推奨事項を生成"""
        
        if trajectory["trend"] == "converging":
            return "現在の調整ペースを維持し、追加価値の提示で最終合意へ"
        elif trajectory["trend"] == "diverging":
            return "期待値のリセットと段階的オプションの提示"
        else:
            return "明確な価値提案と柔軟な価格構造の提示"
    
    def _calculate_engagement_metrics(
        self,
        conversation_history: List[Dict]
    ) -> Dict:
        """エンゲージメント指標を計算"""
        
        if not conversation_history:
            return {
                "overall_score": 0.5,
                "recent_score": 0.5,
                "risk_indicators": [],
                "opportunity_indicators": [],
                "confidence": 0.3
            }
        
        # 全体スコア
        overall_score = 0.5
        
        # 質問の数
        question_count = sum(
            1 for msg in conversation_history 
            if "?" in msg.get("content", "")
        )
        overall_score += (question_count / len(conversation_history)) * 0.3
        
        # メッセージの長さ
        avg_length = np.mean([
            len(msg.get("content", "")) 
            for msg in conversation_history
        ])
        overall_score += min(avg_length / 300, 0.2)
        
        # 最近のスコア（直近3メッセージ）
        recent_messages = conversation_history[-3:]
        recent_score = 0.5
        if recent_messages:
            recent_questions = sum(
                1 for msg in recent_messages 
                if "?" in msg.get("content", "")
            )
            recent_score += (recent_questions / len(recent_messages)) * 0.5
        
        return {
            "overall_score": min(overall_score, 1.0),
            "recent_score": min(recent_score, 1.0),
            "risk_indicators": ["返信遅延"] if overall_score < 0.4 else [],
            "opportunity_indicators": ["高関心"] if overall_score > 0.7 else [],
            "confidence": 0.5 + (len(conversation_history) / 20)
        }
    
    def _project_future_engagement(
        self,
        metrics: Dict,
        trend: str
    ) -> List[float]:
        """将来のエンゲージメントを予測"""
        
        current = metrics["overall_score"]
        
        if trend == "increasing":
            return [
                min(current * 1.1, 0.9),
                min(current * 1.15, 0.85),
                min(current * 1.1, 0.8)
            ]
        elif trend == "decreasing":
            return [
                max(current * 0.9, 0.3),
                max(current * 0.85, 0.25),
                max(current * 0.8, 0.2)
            ]
        else:
            return [current, current * 0.95, current * 0.9]
    
    def _check_response_delays(
        self,
        conversation_history: List[Dict]
    ) -> Dict:
        """応答遅延をチェック"""
        
        # 簡易実装
        return {
            "max_delay_hours": 24,
            "avg_delay_hours": 12,
            "trend": "stable"
        }
    
    def _detect_competitor_mentions(
        self,
        conversation_history: List[Dict]
    ) -> int:
        """競合他社への言及を検出"""
        
        competitor_keywords = ["他社", "別の", "比較", "検討中", "オファー"]
        count = 0
        
        for msg in conversation_history:
            content = msg.get("content", "").lower()
            if any(keyword in content for keyword in competitor_keywords):
                count += 1
        
        return count
    
    def _calculate_avg_response_time(
        self,
        conversation_history: List[Dict]
    ) -> float:
        """平均応答時間を計算"""
        
        # 簡易実装
        return 12.0
    
    def _calculate_sentiment_trend(
        self,
        conversation_history: List[Dict]
    ) -> float:
        """感情トレンドを計算"""
        
        # 簡易実装：ポジティブ/ネガティブワードのカウント
        positive_words = ["いいね", "素晴らしい", "興味", "ぜひ", "楽しみ"]
        negative_words = ["難しい", "厳しい", "心配", "不安", "高い"]
        
        positive_count = 0
        negative_count = 0
        
        for msg in conversation_history:
            content = msg.get("content", "").lower()
            positive_count += sum(1 for word in positive_words if word in content)
            negative_count += sum(1 for word in negative_words if word in content)
        
        if positive_count + negative_count == 0:
            return 0.0
        
        return (positive_count - negative_count) / (positive_count + negative_count)
    
    def _calculate_budget_alignment(
        self,
        current_state: Dict
    ) -> float:
        """予算適合度を計算"""
        
        gap = current_state.get("budget_gap_percentage", 50)
        return max(0, 1 - (gap / 100))
    
    def _calculate_engagement_score(
        self,
        conversation_history: List[Dict]
    ) -> float:
        """エンゲージメントスコアを計算"""
        
        metrics = self._calculate_engagement_metrics(conversation_history)
        return metrics["overall_score"]
    
    def _analyze_message_length_trend(
        self,
        conversation_history: List[Dict]
    ) -> str:
        """メッセージ長のトレンドを分析"""
        
        if len(conversation_history) < 3:
            return "stable"
        
        lengths = [len(msg.get("content", "")) for msg in conversation_history]
        recent_avg = np.mean(lengths[-3:])
        overall_avg = np.mean(lengths)
        
        if recent_avg > overall_avg * 1.2:
            return "increasing"
        elif recent_avg < overall_avg * 0.8:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_question_ratio(
        self,
        conversation_history: List[Dict]
    ) -> float:
        """質問の割合を計算"""
        
        if not conversation_history:
            return 0.0
        
        question_count = sum(
            1 for msg in conversation_history 
            if "?" in msg.get("content", "")
        )
        
        return question_count / len(conversation_history)
    
    def _count_positive_signals(
        self,
        messages: List[Dict]
    ) -> int:
        """ポジティブシグナルをカウント"""
        
        positive_phrases = [
            "いいですね", "興味があります", "前向きに", "検討します",
            "ぜひ", "楽しみ", "素晴らしい", "ありがとう"
        ]
        
        count = 0
        for msg in messages:
            content = msg.get("content", "").lower()
            count += sum(1 for phrase in positive_phrases if phrase in content)
        
        return count