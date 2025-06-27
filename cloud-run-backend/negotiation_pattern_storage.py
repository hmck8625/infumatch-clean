"""
交渉パターンストレージシステム
成功・失敗パターンの記録と学習データの管理
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging
from google.cloud import firestore
import hashlib

class PatternType(Enum):
    """パターンタイプの定義"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    ESCALATION = "escalation"

class NegotiationOutcome(Enum):
    """交渉結果の定義"""
    DEAL_CLOSED = "deal_closed"
    NEGOTIATION_FAILED = "negotiation_failed"
    PRICE_AGREED = "price_agreed"
    TERMS_AGREED = "terms_agreed"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"

class NegotiationPatternStorage:
    """交渉パターンストレージマネージャー"""
    
    def __init__(self, db_client=None):
        self.db = db_client  # Firestoreクライアント
        self.collection_name = "negotiation_patterns"
        self.analytics_collection = "pattern_analytics"
        self.cache = {}  # メモリキャッシュ
        
    async def record_negotiation_pattern(
        self,
        thread_id: str,
        pattern_data: Dict,
        outcome: NegotiationOutcome,
        success_metrics: Dict
    ) -> Dict:
        """交渉パターンを記録"""
        
        pattern_id = self._generate_pattern_id(pattern_data)
        
        # パターンタイプを判定
        pattern_type = self._determine_pattern_type(outcome, success_metrics)
        
        # パターンドキュメントを作成
        pattern_doc = {
            "pattern_id": pattern_id,
            "thread_id": thread_id,
            "pattern_type": pattern_type.value,
            "outcome": outcome.value,
            "recorded_at": datetime.now().isoformat(),
            
            # パターンデータ
            "conversation_summary": pattern_data.get("conversation_summary", {}),
            "key_phrases": pattern_data.get("key_phrases", []),
            "negotiation_flow": pattern_data.get("negotiation_flow", []),
            "decision_points": pattern_data.get("decision_points", []),
            
            # 成功指標
            "success_metrics": {
                "deal_value": success_metrics.get("deal_value", 0),
                "negotiation_duration_hours": success_metrics.get("duration_hours", 0),
                "rounds_count": success_metrics.get("rounds_count", 0),
                "satisfaction_score": success_metrics.get("satisfaction_score", 0),
                "budget_efficiency": success_metrics.get("budget_efficiency", 0)
            },
            
            # コンテキスト情報
            "context": {
                "influencer_category": pattern_data.get("influencer_category", "unknown"),
                "product_category": pattern_data.get("product_category", "unknown"),
                "initial_budget_range": pattern_data.get("initial_budget_range", {}),
                "final_agreed_amount": pattern_data.get("final_agreed_amount", 0),
                "negotiation_tone": pattern_data.get("negotiation_tone", "balanced"),
                "custom_instructions": pattern_data.get("custom_instructions", "")
            },
            
            # 学習用フィーチャー
            "features": self._extract_learning_features(pattern_data, outcome),
            
            # 統計情報
            "usage_count": 0,
            "success_rate": 0.0,
            "last_used": None
        }
        
        # DBに保存
        if self.db:
            try:
                # 既存パターンの確認
                existing = self._get_existing_pattern(pattern_id)
                if existing:
                    # 既存パターンを更新
                    pattern_doc = self._merge_patterns(existing, pattern_doc)
                
                self.db.collection(self.collection_name).document(pattern_id).set(
                    pattern_doc, merge=True
                )
                
                # 分析データも更新
                await self._update_pattern_analytics(pattern_id, outcome, success_metrics)
                
            except Exception as e:
                logging.error(f"パターン記録エラー: {e}")
        
        # キャッシュに保存
        self.cache[pattern_id] = pattern_doc
        
        print(f"✅ 交渉パターン記録: {pattern_type.value} - {outcome.value}")
        
        return pattern_doc
    
    async def find_similar_patterns(
        self,
        current_context: Dict,
        min_similarity: float = 0.7
    ) -> List[Dict]:
        """類似パターンを検索"""
        
        similar_patterns = []
        
        # 現在のコンテキストから特徴を抽出
        current_features = self._extract_context_features(current_context)
        
        # パターンコレクションから検索
        if self.db:
            try:
                # カテゴリでフィルタ
                query = self.db.collection(self.collection_name)
                
                if current_context.get("influencer_category"):
                    query = query.where(
                        "context.influencer_category", "==", 
                        current_context["influencer_category"]
                    )
                
                # 成功パターンを優先
                query = query.where("pattern_type", "in", ["success", "partial"])
                query = query.order_by("success_metrics.satisfaction_score", direction=firestore.Query.DESCENDING)
                query = query.limit(20)
                
                docs = query.stream()
                
                for doc in docs:
                    pattern = doc.to_dict()
                    
                    # 類似度を計算
                    similarity = self._calculate_similarity(
                        current_features, 
                        pattern.get("features", {})
                    )
                    
                    if similarity >= min_similarity:
                        pattern["similarity_score"] = similarity
                        similar_patterns.append(pattern)
                
            except Exception as e:
                logging.error(f"類似パターン検索エラー: {e}")
        
        # 類似度でソート
        similar_patterns.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
        
        return similar_patterns[:5]  # 上位5件
    
    async def get_best_strategy(
        self,
        negotiation_context: Dict
    ) -> Dict:
        """最適な戦略を取得"""
        
        # 類似パターンを検索
        similar_patterns = await self.find_similar_patterns(negotiation_context)
        
        if not similar_patterns:
            return self._get_default_strategy()
        
        # 最も成功率の高いパターンを選択
        best_pattern = max(
            similar_patterns,
            key=lambda p: p.get("success_metrics", {}).get("satisfaction_score", 0) * p.get("similarity_score", 0)
        )
        
        # 戦略を生成
        strategy = {
            "approach": best_pattern.get("context", {}).get("negotiation_tone", "balanced"),
            "key_phrases": best_pattern.get("key_phrases", []),
            "recommended_flow": best_pattern.get("negotiation_flow", []),
            "avoid_topics": self._extract_failure_points(best_pattern),
            "budget_flexibility": self._calculate_budget_flexibility(best_pattern),
            "expected_rounds": best_pattern.get("success_metrics", {}).get("rounds_count", 3),
            "confidence": best_pattern.get("similarity_score", 0.5),
            "based_on_pattern": best_pattern.get("pattern_id")
        }
        
        return strategy
    
    async def update_pattern_performance(
        self,
        pattern_id: str,
        performance_data: Dict
    ) -> None:
        """パターンのパフォーマンスを更新"""
        
        if self.db:
            try:
                # 使用回数と成功率を更新
                pattern_ref = self.db.collection(self.collection_name).document(pattern_id)
                pattern = pattern_ref.get()
                
                if pattern.exists:
                    current_data = pattern.to_dict()
                    usage_count = current_data.get("usage_count", 0) + 1
                    
                    # 成功率を再計算
                    if performance_data.get("success"):
                        success_count = current_data.get("success_count", 0) + 1
                    else:
                        success_count = current_data.get("success_count", 0)
                    
                    success_rate = success_count / usage_count if usage_count > 0 else 0
                    
                    # 更新
                    pattern_ref.update({
                        "usage_count": usage_count,
                        "success_count": success_count,
                        "success_rate": success_rate,
                        "last_used": datetime.now().isoformat(),
                        "recent_performance": performance_data
                    })
                    
            except Exception as e:
                logging.error(f"パフォーマンス更新エラー: {e}")
    
    async def get_pattern_analytics(
        self,
        time_range_days: int = 30
    ) -> Dict:
        """パターン分析データを取得"""
        
        analytics = {
            "total_patterns": 0,
            "success_patterns": 0,
            "failure_patterns": 0,
            "average_success_rate": 0.0,
            "most_effective_approaches": [],
            "category_performance": {},
            "trend_analysis": []
        }
        
        if self.db:
            try:
                # 指定期間のパターンを取得
                cutoff_date = datetime.now() - timedelta(days=time_range_days)
                
                query = self.db.collection(self.collection_name)
                query = query.where("recorded_at", ">=", cutoff_date.isoformat())
                
                patterns = query.stream()
                
                success_rates = []
                approach_stats = {}
                category_stats = {}
                
                for pattern_doc in patterns:
                    pattern = pattern_doc.to_dict()
                    analytics["total_patterns"] += 1
                    
                    # パターンタイプ別カウント
                    if pattern.get("pattern_type") == "success":
                        analytics["success_patterns"] += 1
                    elif pattern.get("pattern_type") == "failure":
                        analytics["failure_patterns"] += 1
                    
                    # 成功率収集
                    if pattern.get("success_rate") is not None:
                        success_rates.append(pattern["success_rate"])
                    
                    # アプローチ別統計
                    approach = pattern.get("context", {}).get("negotiation_tone", "unknown")
                    if approach not in approach_stats:
                        approach_stats[approach] = {"count": 0, "success_rate": 0}
                    approach_stats[approach]["count"] += 1
                    
                    # カテゴリ別統計
                    category = pattern.get("context", {}).get("influencer_category", "unknown")
                    if category not in category_stats:
                        category_stats[category] = {"count": 0, "avg_deal_value": 0}
                    category_stats[category]["count"] += 1
                
                # 平均成功率
                if success_rates:
                    analytics["average_success_rate"] = sum(success_rates) / len(success_rates)
                
                # 最も効果的なアプローチ
                analytics["most_effective_approaches"] = sorted(
                    approach_stats.items(),
                    key=lambda x: x[1]["count"],
                    reverse=True
                )[:3]
                
                # カテゴリ別パフォーマンス
                analytics["category_performance"] = category_stats
                
            except Exception as e:
                logging.error(f"分析データ取得エラー: {e}")
        
        return analytics
    
    def _generate_pattern_id(self, pattern_data: Dict) -> str:
        """パターンIDを生成"""
        # 主要な特徴からハッシュを生成
        key_elements = [
            pattern_data.get("influencer_category", ""),
            pattern_data.get("product_category", ""),
            pattern_data.get("negotiation_tone", ""),
            str(pattern_data.get("initial_budget_range", {}))
        ]
        
        pattern_string = "|".join(key_elements)
        return hashlib.sha256(pattern_string.encode()).hexdigest()[:16]
    
    def _determine_pattern_type(
        self,
        outcome: NegotiationOutcome,
        success_metrics: Dict
    ) -> PatternType:
        """パターンタイプを判定"""
        
        if outcome in [NegotiationOutcome.DEAL_CLOSED, NegotiationOutcome.PRICE_AGREED]:
            if success_metrics.get("satisfaction_score", 0) >= 0.8:
                return PatternType.SUCCESS
            else:
                return PatternType.PARTIAL
        elif outcome == NegotiationOutcome.NEGOTIATION_FAILED:
            return PatternType.FAILURE
        else:
            return PatternType.ESCALATION
    
    def _extract_learning_features(self, pattern_data: Dict, outcome: NegotiationOutcome) -> Dict:
        """学習用の特徴を抽出"""
        
        features = {
            # カテゴリカル特徴
            "influencer_category": pattern_data.get("influencer_category", "unknown"),
            "product_category": pattern_data.get("product_category", "unknown"),
            "negotiation_tone": pattern_data.get("negotiation_tone", "balanced"),
            "outcome": outcome.value,
            
            # 数値特徴
            "initial_budget": pattern_data.get("initial_budget_range", {}).get("min", 0),
            "budget_flexibility": pattern_data.get("budget_flexibility", 0),
            "round_count": len(pattern_data.get("negotiation_flow", [])),
            "message_count": pattern_data.get("message_count", 0),
            
            # テキスト特徴（簡略化）
            "key_phrase_count": len(pattern_data.get("key_phrases", [])),
            "positive_signals": pattern_data.get("positive_signals", 0),
            "negative_signals": pattern_data.get("negative_signals", 0),
            
            # 時系列特徴
            "response_time_avg": pattern_data.get("response_time_avg", 0),
            "momentum_score": pattern_data.get("momentum_score", 0.5)
        }
        
        return features
    
    def _extract_context_features(self, context: Dict) -> Dict:
        """コンテキストから特徴を抽出"""
        
        return {
            "influencer_category": context.get("influencer_category", "unknown"),
            "product_category": context.get("product_category", "unknown"),
            "budget_range": context.get("budget_range", {}),
            "urgency_level": context.get("urgency_level", "normal"),
            "current_stage": context.get("negotiation_stage", "initial_contact")
        }
    
    def _calculate_similarity(self, features1: Dict, features2: Dict) -> float:
        """特徴間の類似度を計算"""
        
        similarity_scores = []
        
        # カテゴリの一致
        if features1.get("influencer_category") == features2.get("influencer_category"):
            similarity_scores.append(1.0)
        else:
            similarity_scores.append(0.0)
        
        if features1.get("product_category") == features2.get("product_category"):
            similarity_scores.append(0.8)
        else:
            similarity_scores.append(0.2)
        
        # 予算範囲の類似性
        budget1 = features1.get("initial_budget", 0)
        budget2 = features2.get("initial_budget", 0)
        if budget1 > 0 and budget2 > 0:
            budget_similarity = 1 - abs(budget1 - budget2) / max(budget1, budget2)
            similarity_scores.append(budget_similarity * 0.6)
        
        # 全体の類似度
        return sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0
    
    def _get_existing_pattern(self, pattern_id: str) -> Optional[Dict]:
        """既存パターンを取得"""
        
        if pattern_id in self.cache:
            return self.cache[pattern_id]
        
        if self.db:
            try:
                doc = self.db.collection(self.collection_name).document(pattern_id).get()
                if doc.exists:
                    return doc.to_dict()
            except Exception:
                pass
        
        return None
    
    def _merge_patterns(self, existing: Dict, new: Dict) -> Dict:
        """パターンをマージ"""
        
        # 使用回数を増やす
        existing["usage_count"] = existing.get("usage_count", 0) + 1
        
        # キーフレーズを統合
        existing_phrases = set(existing.get("key_phrases", []))
        new_phrases = set(new.get("key_phrases", []))
        existing["key_phrases"] = list(existing_phrases.union(new_phrases))[:20]
        
        # 成功指標を更新
        for key, value in new.get("success_metrics", {}).items():
            if key in existing.get("success_metrics", {}):
                # 平均を取る
                existing["success_metrics"][key] = (
                    existing["success_metrics"][key] + value
                ) / 2
            else:
                existing["success_metrics"][key] = value
        
        return existing
    
    async def _update_pattern_analytics(
        self,
        pattern_id: str,
        outcome: NegotiationOutcome,
        success_metrics: Dict
    ) -> None:
        """パターン分析データを更新"""
        
        if self.db:
            try:
                analytics_doc = {
                    "pattern_id": pattern_id,
                    "timestamp": datetime.now().isoformat(),
                    "outcome": outcome.value,
                    "metrics": success_metrics,
                    "date": datetime.now().date().isoformat()
                }
                
                self.db.collection(self.analytics_collection).add(analytics_doc)
                
            except Exception as e:
                logging.error(f"分析データ更新エラー: {e}")
    
    def _extract_failure_points(self, pattern: Dict) -> List[str]:
        """失敗ポイントを抽出"""
        
        # パターンから避けるべきトピックを抽出
        avoid_topics = []
        
        if pattern.get("pattern_type") == "failure":
            # 失敗パターンからネガティブな要素を抽出
            if pattern.get("decision_points"):
                for point in pattern["decision_points"]:
                    if point.get("outcome") == "negative":
                        avoid_topics.append(point.get("topic", ""))
        
        return [topic for topic in avoid_topics if topic]
    
    def _calculate_budget_flexibility(self, pattern: Dict) -> float:
        """予算柔軟性を計算"""
        
        context = pattern.get("context", {})
        initial_range = context.get("initial_budget_range", {})
        final_amount = context.get("final_agreed_amount", 0)
        
        if initial_range and final_amount:
            initial_min = initial_range.get("min", 0)
            initial_max = initial_range.get("max", 0)
            
            if initial_min > 0 and initial_max > 0:
                # 最終合意額が初期範囲のどこに位置するか
                if final_amount <= initial_min:
                    return 0.0  # 柔軟性なし
                elif final_amount >= initial_max:
                    return 1.0  # 高い柔軟性
                else:
                    return (final_amount - initial_min) / (initial_max - initial_min)
        
        return 0.5  # デフォルト
    
    def _get_default_strategy(self) -> Dict:
        """デフォルト戦略を取得"""
        
        return {
            "approach": "balanced",
            "key_phrases": [
                "ご提案ありがとうございます",
                "詳細についてご相談させてください",
                "win-winの関係を築きたい"
            ],
            "recommended_flow": [
                "挨拶と感謝",
                "提案内容の確認",
                "条件の調整",
                "合意形成"
            ],
            "avoid_topics": [],
            "budget_flexibility": 0.15,
            "expected_rounds": 3,
            "confidence": 0.5,
            "based_on_pattern": None
        }