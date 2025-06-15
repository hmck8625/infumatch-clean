"""
統合マッチングサービス

@description Firebaseデータベースと統合した集権化マッチングエンジン
- リアルタイムデータベース検索
- 高度なフィルタリング
- AI分析統合
- 履歴学習機能

@author InfuMatch Development Team
@version 2.0.0
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from services.database_service import database_service
from services.ai_agents.recommendation_agent import RecommendationAgent
from services.ai_channel_analyzer import AdvancedChannelAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class MatchingRequest:
    """統合マッチングリクエスト"""
    
    # 基本検索条件
    keyword: Optional[str] = None
    category: Optional[str] = None
    min_subscribers: Optional[int] = None
    max_subscribers: Optional[int] = None
    min_engagement_rate: Optional[float] = None
    
    # AI推薦条件
    product_name: Optional[str] = None
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    target_audience: List[str] = None
    campaign_goals: Optional[str] = None
    
    # マッチング設定
    use_ai_analysis: bool = True
    include_analytics: bool = True
    max_results: int = 20
    sort_by: str = "overall_score"  # overall_score, subscribers, engagement
    
    # ユーザー設定統合
    user_preferences: Optional[Dict[str, Any]] = None


@dataclass
class MatchingResponse:
    """統合マッチングレスポンス"""
    
    success: bool
    results: List[Dict[str, Any]]
    ai_analysis: Optional[Dict[str, Any]] = None
    search_metadata: Optional[Dict[str, Any]] = None
    user_context: Optional[Dict[str, Any]] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


class CentralizedMatchingService:
    """
    統合マッチングサービス
    
    Firebaseデータベースと連携した高度なマッチングエンジン
    - リアルタイムデータ検索
    - AI分析統合
    - ユーザー設定考慮
    - 履歴学習
    """
    
    def __init__(self):
        """初期化"""
        self.database_service = database_service
        self.recommendation_agent = RecommendationAgent()
        self.ai_analyzer = AdvancedChannelAnalyzer()
        
        # キャッシュ設定
        self._cache = {}
        self._cache_ttl = timedelta(minutes=5)
    
    async def execute_matching(self, request: MatchingRequest) -> MatchingResponse:
        """
        統合マッチング実行
        
        Args:
            request: マッチングリクエスト
            
        Returns:
            MatchingResponse: マッチング結果
        """
        try:
            logger.info(f"🎯 Executing centralized matching: {request}")
            
            # 1. 基本データ検索（Firebase）
            base_results = await self._search_database(request)
            
            if not base_results:
                return MatchingResponse(
                    success=True,
                    results=[],
                    search_metadata={"message": "条件に合致するインフルエンサーが見つかりませんでした"}
                )
            
            # 2. AI分析統合（オプション）
            if request.use_ai_analysis:
                enhanced_results = await self._enhance_with_ai_analysis(base_results, request)
            else:
                enhanced_results = base_results
            
            # 3. ユーザー設定適用
            personalized_results = await self._apply_user_preferences(enhanced_results, request)
            
            # 4. 最終スコアリング・ソート
            final_results = await self._calculate_final_scores(personalized_results, request)
            
            # 5. 結果制限
            limited_results = final_results[:request.max_results]
            
            # 6. メタデータ生成
            search_metadata = self._generate_search_metadata(base_results, limited_results, request)
            
            return MatchingResponse(
                success=True,
                results=limited_results,
                search_metadata=search_metadata
            )
            
        except Exception as e:
            logger.error(f"❌ Centralized matching failed: {e}")
            return MatchingResponse(
                success=False,
                results=[],
                search_metadata={"error": str(e)}
            )
    
    async def _search_database(self, request: MatchingRequest) -> List[Dict[str, Any]]:
        """
        Firebaseデータベースから基本検索
        
        Args:
            request: マッチングリクエスト
            
        Returns:
            List[Dict]: 基本検索結果
        """
        try:
            # 検索条件の準備
            search_params = {
                "keyword": request.keyword,
                "category": request.category,
                "min_subscribers": request.min_subscribers,
                "max_subscribers": request.max_subscribers,
                "limit": request.max_results * 2  # AI分析でフィルタされることを考慮
            }
            
            # キャッシュキー生成
            cache_key = f"search_{hash(frozenset(search_params.items()))}"
            
            # キャッシュチェック
            if cache_key in self._cache:
                cache_entry = self._cache[cache_key]
                if datetime.utcnow() - cache_entry["timestamp"] < self._cache_ttl:
                    logger.info("📦 Using cached search results")
                    return cache_entry["data"]
            
            # データベース検索実行
            logger.info(f"🔍 Searching database with params: {search_params}")
            results = await self.database_service.get_influencers(**search_params)
            
            # エンゲージメント率フィルタ（データベースクエリ後）
            if request.min_engagement_rate:
                results = [
                    r for r in results 
                    if r.get("engagementRate", 0) >= request.min_engagement_rate
                ]
            
            # キャッシュ保存
            self._cache[cache_key] = {
                "data": results,
                "timestamp": datetime.utcnow()
            }
            
            logger.info(f"✅ Found {len(results)} influencers from database")
            return results
            
        except Exception as e:
            logger.error(f"❌ Database search failed: {e}")
            return []
    
    async def _enhance_with_ai_analysis(
        self, 
        results: List[Dict[str, Any]], 
        request: MatchingRequest
    ) -> List[Dict[str, Any]]:
        """
        AI分析による結果拡張
        
        Args:
            results: 基本検索結果
            request: マッチングリクエスト
            
        Returns:
            List[Dict]: AI分析拡張済み結果
        """
        try:
            logger.info(f"🤖 Enhancing {len(results)} results with AI analysis")
            
            enhanced_results = []
            
            for result in results:
                try:
                    # AI分析実行（並列処理で高速化）
                    ai_analysis = await self.ai_analyzer.analyze_channel_comprehensive({
                        "channel_id": result.get("channelId"),
                        "channel_title": result.get("name"),
                        "description": result.get("description"),
                        "subscriber_count": result.get("subscriberCount"),
                        "video_count": result.get("videoCount"),
                        "category": result.get("category")
                    })
                    
                    # AI分析結果を結果に統合
                    enhanced_result = result.copy()
                    enhanced_result["aiAnalysis"] = ai_analysis
                    enhanced_result["brandSafetyScore"] = ai_analysis.get("brand_safety", {}).get("overall_safety_score", 0.8)
                    enhanced_result["matchScore"] = ai_analysis.get("analysis_confidence", 0.5)
                    
                    enhanced_results.append(enhanced_result)
                    
                except Exception as e:
                    logger.warning(f"⚠️ AI analysis failed for {result.get('name')}: {e}")
                    # AI分析失敗時も結果に含める
                    enhanced_results.append(result)
            
            logger.info(f"✅ AI analysis completed for {len(enhanced_results)} results")
            return enhanced_results
            
        except Exception as e:
            logger.error(f"❌ AI enhancement failed: {e}")
            return results  # 失敗時は元の結果を返す
    
    async def _apply_user_preferences(
        self, 
        results: List[Dict[str, Any]], 
        request: MatchingRequest
    ) -> List[Dict[str, Any]]:
        """
        ユーザー設定の適用
        
        Args:
            results: AI分析済み結果
            request: マッチングリクエスト
            
        Returns:
            List[Dict]: ユーザー設定適用済み結果
        """
        if not request.user_preferences:
            return results
        
        try:
            logger.info("👤 Applying user preferences")
            
            preferences = request.user_preferences
            filtered_results = []
            
            for result in results:
                # 優先カテゴリチェック
                preferred_categories = preferences.get("preferredCategories", [])
                if preferred_categories:
                    if result.get("category") in preferred_categories:
                        result["userPreferenceBonus"] = 0.1
                
                # ブランドセーフティ要件
                min_safety_score = preferences.get("minBrandSafetyScore", 0.5)
                if result.get("brandSafetyScore", 0.8) >= min_safety_score:
                    filtered_results.append(result)
                else:
                    logger.debug(f"Filtered out {result.get('name')} due to brand safety score")
            
            logger.info(f"✅ User preferences applied, {len(filtered_results)} results remain")
            return filtered_results
            
        except Exception as e:
            logger.error(f"❌ User preference application failed: {e}")
            return results
    
    async def _calculate_final_scores(
        self, 
        results: List[Dict[str, Any]], 
        request: MatchingRequest
    ) -> List[Dict[str, Any]]:
        """
        最終スコア計算とソート
        
        Args:
            results: ユーザー設定適用済み結果
            request: マッチングリクエスト
            
        Returns:
            List[Dict]: 最終スコア計算・ソート済み結果
        """
        try:
            logger.info(f"📊 Calculating final scores for {len(results)} results")
            
            for result in results:
                # 基本スコア要素
                engagement_score = min(result.get("engagementRate", 0) / 10.0, 1.0)
                subscriber_score = min(result.get("subscriberCount", 0) / 100000.0, 1.0)
                ai_score = result.get("matchScore", 0.5)
                safety_score = result.get("brandSafetyScore", 0.8)
                user_bonus = result.get("userPreferenceBonus", 0.0)
                
                # 重み付き総合スコア
                final_score = (
                    engagement_score * 0.25 +
                    subscriber_score * 0.20 +
                    ai_score * 0.30 +
                    safety_score * 0.15 +
                    user_bonus * 0.10
                )
                
                result["finalScore"] = round(final_score, 3)
                result["scoreBreakdown"] = {
                    "engagement": round(engagement_score, 3),
                    "subscriber": round(subscriber_score, 3),
                    "ai_analysis": round(ai_score, 3),
                    "brand_safety": round(safety_score, 3),
                    "user_bonus": round(user_bonus, 3)
                }
            
            # ソート
            sort_key = "finalScore"
            if request.sort_by == "subscribers":
                sort_key = "subscriberCount"
            elif request.sort_by == "engagement":
                sort_key = "engagementRate"
            
            sorted_results = sorted(
                results, 
                key=lambda x: x.get(sort_key, 0), 
                reverse=True
            )
            
            logger.info(f"✅ Final scoring completed, sorted by {sort_key}")
            return sorted_results
            
        except Exception as e:
            logger.error(f"❌ Final scoring failed: {e}")
            return results
    
    def _generate_search_metadata(
        self, 
        base_results: List[Dict[str, Any]], 
        final_results: List[Dict[str, Any]], 
        request: MatchingRequest
    ) -> Dict[str, Any]:
        """
        検索メタデータ生成
        
        Args:
            base_results: 基本検索結果
            final_results: 最終結果
            request: マッチングリクエスト
            
        Returns:
            Dict: 検索メタデータ
        """
        return {
            "total_found": len(base_results),
            "final_results": len(final_results),
            "search_params": {
                "keyword": request.keyword,
                "category": request.category,
                "min_subscribers": request.min_subscribers,
                "max_subscribers": request.max_subscribers,
                "min_engagement_rate": request.min_engagement_rate
            },
            "ai_analysis_enabled": request.use_ai_analysis,
            "user_preferences_applied": request.user_preferences is not None,
            "sort_by": request.sort_by,
            "execution_time": datetime.utcnow().isoformat()
        }
    
    async def get_real_time_recommendations(
        self, 
        campaign_id: str,
        refresh_interval: int = 300  # 5分
    ) -> MatchingResponse:
        """
        リアルタイム推薦更新
        
        Args:
            campaign_id: キャンペーンID
            refresh_interval: 更新間隔（秒）
            
        Returns:
            MatchingResponse: リアルタイム推薦結果
        """
        # 実装はキャンペーンデータ取得後に行う
        # 現在はプレースホルダー
        return MatchingResponse(
            success=True,
            results=[],
            search_metadata={"message": "Real-time recommendations feature coming soon"}
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        サービス正常性チェック
        
        Returns:
            Dict: ヘルスチェック結果
        """
        status = {
            "service": "CentralizedMatchingService",
            "status": "healthy",
            "components": {}
        }
        
        try:
            # データベースサービスチェック
            db_health = await self.database_service.health_check()
            status["components"]["database"] = db_health
            
            # AI分析サービスチェック
            status["components"]["ai_analyzer"] = {
                "status": "available" if self.ai_analyzer else "unavailable"
            }
            
            # 推薦エージェントチェック
            status["components"]["recommendation_agent"] = {
                "status": "available" if self.recommendation_agent else "unavailable",
                "capabilities": self.recommendation_agent.get_capabilities() if self.recommendation_agent else []
            }
            
            # 全体ステータス判定
            unhealthy_components = [
                comp for comp, details in status["components"].items()
                if details.get("status") not in ["healthy", "connected", "available"]
            ]
            
            if unhealthy_components:
                status["status"] = "degraded"
                status["issues"] = unhealthy_components
            
        except Exception as e:
            status["status"] = "unhealthy"
            status["error"] = str(e)
        
        return status


# シングルトンインスタンス
centralized_matching_service = CentralizedMatchingService()