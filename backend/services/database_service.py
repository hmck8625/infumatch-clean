"""
データベースサービス

@description Firestore と BigQuery からインフルエンサーデータを取得
@author InfuMatch Development Team  
@version 1.0.0
"""

import logging
import asyncio
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

try:
    from google.cloud import firestore
    from google.cloud import bigquery
    import google.auth
    from google.auth.exceptions import DefaultCredentialsError
except ImportError:
    firestore = None
    bigquery = None

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DatabaseService:
    """
    データベースアクセスサービス
    
    Firestore(リアルタイムデータ) と BigQuery(分析データ) から
    インフルエンサー情報を取得
    """
    
    def __init__(self):
        """データベースサービスの初期化"""
        self.firestore_client = None
        self.bigquery_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """データベースクライアントの初期化"""
        if not firestore or not bigquery:
            logger.warning("⚠️ Google Cloud libraries not available, using mock data")
            return
            
        try:
            # 環境変数確認
            creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
            logger.info(f"🔍 GOOGLE_APPLICATION_CREDENTIALS: {creds_path}")
            logger.info(f"🔍 Project ID: {settings.GOOGLE_CLOUD_PROJECT_ID}")
            
            # Firestore クライアント初期化
            if creds_path and os.path.exists(creds_path):
                logger.info("🔑 Using service account credentials")
                self.firestore_client = firestore.Client(
                    project=settings.GOOGLE_CLOUD_PROJECT_ID
                )
            else:
                logger.info("🔑 Using default credentials")
                # Cloud Run などで実行時はデフォルト認証を使用
                self.firestore_client = firestore.Client(
                    project=settings.GOOGLE_CLOUD_PROJECT_ID
                )
            
            # BigQuery クライアント初期化
            self.bigquery_client = bigquery.Client(
                project=settings.GOOGLE_CLOUD_PROJECT_ID
            )
            
            logger.info("✅ Database clients initialized successfully")
            
            # 接続テスト
            try:
                collection_ref = self.firestore_client.collection('youtube_influencers')
                docs = list(collection_ref.limit(1).stream())
                logger.info(f"🔥 Firestore test: Found {len(docs)} documents")
            except Exception as test_error:
                logger.error(f"🔥 Firestore test failed: {test_error}")
            
        except DefaultCredentialsError:
            logger.warning("⚠️ Google Cloud credentials not found, using mock data")
        except Exception as e:
            logger.error(f"❌ Failed to initialize database clients: {e}")
            import traceback
            logger.error(f"Stack trace: {traceback.format_exc()}")
    
    async def get_influencers(
        self, 
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        min_subscribers: Optional[int] = None,
        max_subscribers: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        インフルエンサーデータの検索
        
        Args:
            keyword: 検索キーワード
            category: カテゴリフィルタ
            min_subscribers: 最小登録者数
            max_subscribers: 最大登録者数
            limit: 取得件数上限
            
        Returns:
            List[Dict]: インフルエンサーデータのリスト
        """
        try:
            if self.firestore_client:
                return await self._get_influencers_from_firestore(
                    keyword, category, min_subscribers, max_subscribers, limit
                )
            else:
                logger.info("🔄 Using mock data (Firestore not available)")
                return await self._get_mock_influencers(
                    keyword, category, min_subscribers, max_subscribers, limit
                )
        except Exception as e:
            logger.error(f"❌ Failed to get influencers: {e}")
            return await self._get_mock_influencers(
                keyword, category, min_subscribers, max_subscribers, limit
            )
    
    async def _get_influencers_from_firestore(
        self,
        keyword: Optional[str],
        category: Optional[str], 
        min_subscribers: Optional[int],
        max_subscribers: Optional[int],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Firestore からインフルエンサーデータを取得"""
        
        def query_firestore():
            collection_ref = self.firestore_client.collection('youtube_influencers')
            query = collection_ref
            
            # カテゴリフィルタ
            if category and category != 'all':
                query = query.where('primary_category', '==', category)
            
            # 登録者数フィルタ
            if min_subscribers:
                query = query.where('subscriber_count', '>=', min_subscribers)
            if max_subscribers:
                query = query.where('subscriber_count', '<=', max_subscribers)
            
            # 取得件数制限
            query = query.limit(limit)
            
            # データ取得
            docs = query.stream()
            results = []
            
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                
                # キーワード検索（クライアントサイドフィルタ）
                if keyword:
                    keyword_lower = keyword.lower()
                    title = data.get('channel_title', '').lower()
                    description = data.get('description', '').lower()
                    
                    if keyword_lower not in title and keyword_lower not in description:
                        continue
                
                # API形式に変換
                converted_data = self._convert_firestore_to_api_format(data)
                results.append(converted_data)
            
            return results
        
        # 非同期実行
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, query_firestore)
    
    def _convert_firestore_to_api_format(self, firestore_data: Dict[str, Any]) -> Dict[str, Any]:
        """Firestore データを API レスポンス形式に変換"""
        return {
            "id": firestore_data.get('channel_id', firestore_data.get('id')),
            "name": firestore_data.get('channel_title', 'Unknown Channel'),
            "channelId": firestore_data.get('channel_id', ''),
            "subscriberCount": firestore_data.get('subscriber_count', 0),
            "viewCount": firestore_data.get('view_count', 0),
            "videoCount": firestore_data.get('video_count', 0),
            "category": firestore_data.get('primary_category', 'その他'),
            "description": firestore_data.get('description', ''),
            "thumbnailUrl": firestore_data.get('thumbnail_url', 'https://via.placeholder.com/120x120'),
            "engagementRate": firestore_data.get('engagement_rate', 0.0),
            "email": firestore_data.get('business_email'),
            # 追加のメタデータ
            "country": firestore_data.get('country', 'JP'),
            "language": firestore_data.get('default_language', 'ja'),
            "customUrl": firestore_data.get('custom_url'),
            "publishedAt": firestore_data.get('published_at'),
            "topicCategories": firestore_data.get('topic_categories', []),
            "avgViewCount": firestore_data.get('avg_view_count', 0),
            "estimatedEarnings": firestore_data.get('estimated_earnings', 0),
            "dataQualityScore": firestore_data.get('data_quality_score', 0.5),
            "fetchedAt": firestore_data.get('fetched_at'),
        }
    
    async def get_influencer_analytics(
        self, 
        channel_ids: List[str], 
        days: int = 30
    ) -> Dict[str, Dict[str, Any]]:
        """
        BigQuery から詳細分析データを取得
        
        Args:
            channel_ids: チャンネルIDリスト
            days: 分析期間（日数）
            
        Returns:
            Dict: チャンネルID -> 分析データ のマッピング
        """
        if not self.bigquery_client:
            logger.warning("⚠️ BigQuery not available, returning empty analytics")
            return {}
        
        try:
            # BigQuery クエリを構築
            query = f"""
            SELECT 
                channel_id,
                AVG(view_count) as avg_views_last_{days}d,
                AVG(like_count) as avg_likes_last_{days}d,
                AVG(comment_count) as avg_comments_last_{days}d,
                COUNT(*) as video_count_last_{days}d,
                AVG(like_count / NULLIF(view_count, 0) * 100) as avg_engagement_rate
            FROM `{settings.GOOGLE_CLOUD_PROJECT_ID}.{settings.BIGQUERY_DATASET}.video_analytics`
            WHERE channel_id IN ({','.join(f"'{cid}'" for cid in channel_ids)})
                AND published_at >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
            GROUP BY channel_id
            """
            
            def run_query():
                query_job = self.bigquery_client.query(query)
                results = query_job.result()
                
                analytics_data = {}
                for row in results:
                    analytics_data[row.channel_id] = {
                        f"avg_views_last_{days}d": row[f"avg_views_last_{days}d"] or 0,
                        f"avg_likes_last_{days}d": row[f"avg_likes_last_{days}d"] or 0, 
                        f"avg_comments_last_{days}d": row[f"avg_comments_last_{days}d"] or 0,
                        f"video_count_last_{days}d": row[f"video_count_last_{days}d"] or 0,
                        "avg_engagement_rate": row["avg_engagement_rate"] or 0,
                    }
                
                return analytics_data
            
            # 非同期実行
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, run_query)
            
        except Exception as e:
            logger.error(f"❌ Failed to get analytics from BigQuery: {e}")
            return {}
    
    async def get_influencer_by_id(self, influencer_id: str) -> Optional[Dict[str, Any]]:
        """
        特定のインフルエンサーの詳細データを取得
        
        Args:
            influencer_id: インフルエンサーID (channel_id)
            
        Returns:
            Optional[Dict]: インフルエンサーデータ、見つからない場合は None
        """
        if not self.firestore_client:
            return await self._get_mock_influencer_by_id(influencer_id)
        
        try:
            def get_doc():
                # まず channel_id で検索
                collection_ref = self.firestore_client.collection('youtube_influencers')
                query = collection_ref.where('channel_id', '==', influencer_id).limit(1)
                docs = list(query.stream())
                
                if docs:
                    data = docs[0].to_dict()
                    data['id'] = docs[0].id
                    return self._convert_firestore_to_api_format(data)
                
                # 見つからない場合はドキュメントIDで検索
                doc_ref = collection_ref.document(influencer_id)
                doc = doc_ref.get()
                
                if doc.exists:
                    data = doc.to_dict()
                    data['id'] = doc.id
                    return self._convert_firestore_to_api_format(data)
                
                return None
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, get_doc)
            
            if result:
                # BigQuery から詳細分析データも取得
                analytics = await self.get_influencer_analytics([result['channelId']])
                if result['channelId'] in analytics:
                    result.update(analytics[result['channelId']])
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to get influencer by ID: {e}")
            return await self._get_mock_influencer_by_id(influencer_id)
    
    async def _get_mock_influencers(
        self,
        keyword: Optional[str],
        category: Optional[str],
        min_subscribers: Optional[int], 
        max_subscribers: Optional[int],
        limit: int
    ) -> List[Dict[str, Any]]:
        """モックデータの取得（フォールバック用）"""
        mock_data = [
            {
                "id": "UC1234567890",
                "name": "Tech Review Japan",
                "channelId": "UC1234567890", 
                "subscriberCount": 8500,
                "viewCount": 1250000,
                "videoCount": 156,
                "category": "テクノロジー",
                "description": "最新のガジェットレビューと技術解説を行うチャンネル",
                "thumbnailUrl": "https://via.placeholder.com/120x120",
                "engagementRate": 4.5,
                "email": "techreview@example.com"
            },
            {
                "id": "UC2345678901",
                "name": "料理研究家ゆうこ",
                "channelId": "UC2345678901",
                "subscriberCount": 5200,
                "viewCount": 890000, 
                "videoCount": 243,
                "category": "料理",
                "description": "簡単で美味しい家庭料理のレシピを紹介",
                "thumbnailUrl": "https://via.placeholder.com/120x120",
                "engagementRate": 5.2,
                "email": "yuko.cooking@example.com"
            },
            {
                "id": "UC3456789012",
                "name": "Fitness Life Tokyo",
                "channelId": "UC3456789012",
                "subscriberCount": 3800,
                "viewCount": 567000,
                "videoCount": 89,
                "category": "フィットネス", 
                "description": "自宅でできるトレーニングとヘルシーライフスタイル",
                "thumbnailUrl": "https://via.placeholder.com/120x120",
                "engagementRate": 6.1,
                "email": "fitness.tokyo@example.com"
            },
            {
                "id": "UC4567890123",
                "name": "ビューティー研究所",
                "channelId": "UC4567890123",
                "subscriberCount": 9200,
                "viewCount": 2100000,
                "videoCount": 312,
                "category": "美容",
                "description": "メイクアップチュートリアルとスキンケア情報",
                "thumbnailUrl": "https://via.placeholder.com/120x120",
                "engagementRate": 3.8,
                "email": "beauty.lab@example.com"
            },
            {
                "id": "UC5678901234", 
                "name": "ゲーム実況チャンネル",
                "channelId": "UC5678901234",
                "subscriberCount": 7600,
                "viewCount": 1890000,
                "videoCount": 428,
                "category": "ゲーム",
                "description": "最新ゲームの実況プレイと攻略情報",
                "thumbnailUrl": "https://via.placeholder.com/120x120",
                "engagementRate": 4.2,
                "email": "game.channel@example.com"
            }
        ]
        
        # フィルタリング適用
        filtered = []
        for influencer in mock_data:
            # カテゴリフィルタ
            if category and category != 'all' and influencer['category'] != category:
                continue
                
            # キーワード検索
            if keyword:
                keyword_lower = keyword.lower()
                if (keyword_lower not in influencer['name'].lower() and 
                    keyword_lower not in influencer['description'].lower()):
                    continue
            
            # 登録者数フィルタ
            if min_subscribers and influencer['subscriberCount'] < min_subscribers:
                continue
            if max_subscribers and influencer['subscriberCount'] > max_subscribers:
                continue
                
            filtered.append(influencer)
        
        return filtered[:limit]
    
    async def _get_mock_influencer_by_id(self, influencer_id: str) -> Optional[Dict[str, Any]]:
        """モックデータから特定のインフルエンサーを取得"""
        mock_data = await self._get_mock_influencers(None, None, None, None, 100)
        for influencer in mock_data:
            if influencer['id'] == influencer_id or influencer['channelId'] == influencer_id:
                return influencer
        return None
    
    async def health_check(self) -> Dict[str, Any]:
        """データベース接続の健全性チェック"""
        status = {
            "firestore": "disconnected",
            "bigquery": "disconnected", 
            "status": "unhealthy"
        }
        
        # Firestore チェック
        if self.firestore_client:
            try:
                # 簡単なクエリでテスト
                collection_ref = self.firestore_client.collection('youtube_influencers')
                list(collection_ref.limit(1).stream())
                status["firestore"] = "connected"
            except Exception as e:
                logger.error(f"Firestore health check failed: {e}")
        
        # BigQuery チェック  
        if self.bigquery_client:
            try:
                # 簡単なクエリでテスト
                query = f"SELECT 1 as test"
                query_job = self.bigquery_client.query(query)
                list(query_job.result())
                status["bigquery"] = "connected"
            except Exception as e:
                logger.error(f"BigQuery health check failed: {e}")
        
        # 全体ステータス
        if status["firestore"] == "connected" or status["bigquery"] == "connected":
            status["status"] = "healthy"
        
        return status


# シングルトンインスタンス
database_service = DatabaseService()