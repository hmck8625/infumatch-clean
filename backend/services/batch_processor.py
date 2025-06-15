"""
YouTube データ バッチ処理サービス

@description 大規模なYouTubeデータ収集・更新のバッチ処理
アーキテクチャ設計書のPhase 1要件に対応

@author InfuMatch Development Team
@version 1.0.0
"""

import logging
import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import time

# from services.youtube_api import YouTubeInfluencerService, YouTubeAPIClient  # テスト用にコメントアウト
from core.config import get_settings
from core.database import FirestoreClient, DatabaseHelper, DatabaseCollections

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class BatchConfig:
    """バッチ処理設定"""
    max_channels_per_batch: int = 100
    max_concurrent_requests: int = 5
    delay_between_batches: float = 2.0
    quota_safety_margin: int = 1000
    retry_attempts: int = 3
    retry_delay: float = 5.0


class YouTubeBatchProcessor:
    """
    YouTube データの大規模バッチ処理
    
    定期的なデータ収集、更新、分析処理を効率的に実行
    """
    
    def __init__(self):
        """初期化"""
        self.config = BatchConfig()
        self.youtube_service = YouTubeInfluencerService()
        self.api_client = YouTubeAPIClient()
        self.db_client = FirestoreClient()
        self.db_helper = DatabaseHelper(self.db_client)
        
        # 処理統計
        self.stats = {
            'channels_processed': 0,
            'channels_failed': 0,
            'api_calls_made': 0,
            'start_time': None,
            'end_time': None
        }
    
    async def discover_influencers_batch(
        self,
        categories: List[str],
        subscriber_ranges: List[tuple] = None,
        max_per_category: int = 50
    ) -> Dict[str, Any]:
        """
        カテゴリベースでインフルエンサーを大規模発見
        
        Args:
            categories: 検索カテゴリリスト
            subscriber_ranges: 登録者数範囲のリスト [(min, max), ...]
            max_per_category: カテゴリあたりの最大取得数
            
        Returns:
            Dict: 処理結果統計
        """
        logger.info(f"🚀 Starting batch influencer discovery for {len(categories)} categories")
        self.stats['start_time'] = datetime.utcnow()
        
        if subscriber_ranges is None:
            subscriber_ranges = [
                (1000, 10000),      # マイクロインフルエンサー
                (10000, 100000),    # ミドルインフルエンサー  
                (100000, 1000000),  # マクロインフルエンサー
            ]
        
        all_results = []
        
        for category in categories:
            logger.info(f"📂 Processing category: {category}")
            
            try:
                # カテゴリごとの検索クエリ生成
                search_queries = self._generate_search_queries(category)
                
                for min_subs, max_subs in subscriber_ranges:
                    logger.info(f"👥 Subscriber range: {min_subs:,} - {max_subs:,}")
                    
                    # インフルエンサー発見
                    influencers = await self.youtube_service.discover_influencers(
                        search_queries=search_queries,
                        subscriber_min=min_subs,
                        subscriber_max=max_subs,
                        max_per_query=max_per_category // len(search_queries)
                    )
                    
                    if influencers:
                        # カテゴリ情報を追加
                        for influencer in influencers:
                            influencer['discovered_category'] = category
                            influencer['subscriber_range'] = f"{min_subs}-{max_subs}"
                        
                        all_results.extend(influencers)
                        self.stats['channels_processed'] += len(influencers)
                        
                        logger.info(f"✅ Found {len(influencers)} influencers in {category} ({min_subs:,}-{max_subs:,})")
                    
                    # レート制限対応
                    await asyncio.sleep(self.config.delay_between_batches)
                
            except Exception as e:
                logger.error(f"❌ Failed to process category {category}: {e}")
                self.stats['channels_failed'] += 1
                continue
        
        # データベースに一括保存
        if all_results:
            saved_count = await self.youtube_service.save_influencers_to_db(all_results)
            logger.info(f"💾 Saved {saved_count}/{len(all_results)} to database")
        
        self.stats['end_time'] = datetime.utcnow()
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        return {
            'total_discovered': len(all_results),
            'categories_processed': len(categories),
            'processing_time_seconds': duration,
            'channels_per_minute': len(all_results) / (duration / 60) if duration > 0 else 0,
            'stats': self.stats
        }
    
    def _generate_search_queries(self, category: str) -> List[str]:
        """
        カテゴリに基づいて検索クエリを生成
        
        Args:
            category: カテゴリ名
            
        Returns:
            List[str]: 検索クエリのリスト
        """
        # カテゴリ別検索クエリマップ
        query_map = {
            'beauty': [
                'メイク', 'コスメ', 'スキンケア', 'beauty', 'makeup tutorial',
                'cosmetics review', 'skincare routine'
            ],
            'gaming': [
                'ゲーム実況', 'gaming', 'gameplay', 'ゲーム攻略', 'esports',
                'game review', 'lets play'
            ],
            'cooking': [
                '料理', 'レシピ', 'cooking', 'recipe', '手料理', 'baking',
                'food', 'おうちごはん'
            ],
            'tech': [
                'テクノロジー', 'ガジェット', 'technology', 'tech review',
                'gadget', 'iPhone', 'Android', 'PC'
            ],
            'fitness': [
                'フィットネス', 'トレーニング', 'fitness', 'workout', 'yoga',
                'diet', 'ダイエット', '筋トレ'
            ],
            'fashion': [
                'ファッション', 'fashion', 'outfit', 'style', 'coordinate',
                'ブランド', 'shopping'
            ],
            'travel': [
                '旅行', 'travel', 'trip', '観光', 'vlog', '海外旅行',
                'domestic travel', '温泉'
            ],
            'education': [
                '教育', 'education', '学習', 'tutorial', 'how to',
                '英語', 'language learning', 'study'
            ]
        }
        
        # カテゴリに対応するクエリを取得、なければカテゴリ名をそのまま使用
        queries = query_map.get(category.lower(), [category])
        
        # 日本語と英語の両方でカバー
        if category.lower() not in query_map:
            queries.extend([f"{category} japan", f"{category} japanese", f"{category} tutorial"])
        
        return queries[:5]  # 最大5つのクエリに制限
    
    async def update_existing_influencers(
        self,
        batch_size: int = 50,
        days_since_last_update: int = 7
    ) -> Dict[str, Any]:
        """
        既存インフルエンサーデータの一括更新
        
        Args:
            batch_size: バッチサイズ
            days_since_last_update: 最終更新からの日数
            
        Returns:
            Dict: 更新結果統計
        """
        logger.info(f"🔄 Starting batch update for existing influencers")
        self.stats['start_time'] = datetime.utcnow()
        
        # 更新対象の取得
        cutoff_date = datetime.utcnow() - timedelta(days=days_since_last_update)
        
        try:
            # データベースから更新対象を取得
            query_conditions = [
                ('last_analyzed', '<', cutoff_date.isoformat()),
                ('status', '==', 'active')
            ]
            
            influencers = await self.db_helper.query_documents(
                collection=DatabaseCollections.INFLUENCERS,
                conditions=query_conditions,
                limit=1000  # 一度に最大1000件
            )
            
            logger.info(f"📊 Found {len(influencers)} influencers to update")
            
            updated_count = 0
            failed_count = 0
            
            # バッチごとに処理
            for i in range(0, len(influencers), batch_size):
                batch = influencers[i:i + batch_size]
                
                logger.info(f"🔄 Processing batch {i//batch_size + 1}/{(len(influencers) + batch_size - 1)//batch_size}")
                
                # 並行処理で更新
                update_tasks = [
                    self.youtube_service.update_influencer_analytics(inf['channel_id'])
                    for inf in batch
                ]
                
                results = await asyncio.gather(*update_tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Exception):
                        failed_count += 1
                        logger.error(f"❌ Update failed: {result}")
                    elif result:
                        updated_count += 1
                    else:
                        failed_count += 1
                
                # レート制限対応
                await asyncio.sleep(self.config.delay_between_batches)
            
            self.stats['end_time'] = datetime.utcnow()
            duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
            
            return {
                'total_checked': len(influencers),
                'successfully_updated': updated_count,
                'failed_updates': failed_count,
                'processing_time_seconds': duration,
                'updates_per_minute': updated_count / (duration / 60) if duration > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Batch update failed: {e}")
            return {
                'error': str(e),
                'total_checked': 0,
                'successfully_updated': 0,
                'failed_updates': 0
            }
    
    async def analyze_trending_channels(
        self,
        region: str = 'JP',
        max_results: int = 100
    ) -> Dict[str, Any]:
        """
        トレンドチャンネルの分析
        
        Args:
            region: 地域コード
            max_results: 最大取得数
            
        Returns:
            Dict: 分析結果
        """
        logger.info(f"📈 Analyzing trending channels in {region}")
        
        try:
            # 人気カテゴリでの検索
            trending_queries = [
                'バズった', 'viral', 'trending', '話題', 'popular',
                '急上昇', 'おすすめ', 'ランキング'
            ]
            
            all_channels = []
            
            for query in trending_queries:
                # 最新の人気チャンネルを検索
                channels = await self.api_client.search_channels(
                    query=query,
                    max_results=max_results // len(trending_queries),
                    order='viewCount'
                )
                
                if channels:
                    # 詳細情報を取得
                    channel_ids = [ch['channel_id'] for ch in channels]
                    detailed_channels = await self.api_client.get_channel_details(channel_ids)
                    
                    # メールアドレス抽出
                    for channel in detailed_channels:
                        emails = self.youtube_service.email_extractor.extract_emails(
                            channel['description']
                        )
                        channel['emails'] = emails
                        channel['trending_query'] = query
                    
                    all_channels.extend(detailed_channels)
                
                await asyncio.sleep(1)  # レート制限
            
            # 重複除去
            unique_channels = {}
            for channel in all_channels:
                if channel['channel_id'] not in unique_channels:
                    unique_channels[channel['channel_id']] = channel
            
            trending_channels = list(unique_channels.values())
            
            # トレンド分析
            analysis = self._analyze_trends(trending_channels)
            
            return {
                'total_channels_analyzed': len(trending_channels),
                'trending_analysis': analysis,
                'top_channels': sorted(
                    trending_channels,
                    key=lambda x: x['engagement_rate'],
                    reverse=True
                )[:10]
            }
            
        except Exception as e:
            logger.error(f"❌ Trending analysis failed: {e}")
            return {'error': str(e)}
    
    def _analyze_trends(self, channels: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        チャンネルリストからトレンド分析
        
        Args:
            channels: チャンネルリスト
            
        Returns:
            Dict: トレンド分析結果
        """
        if not channels:
            return {}
        
        # 統計計算
        subscriber_counts = [ch['subscriber_count'] for ch in channels]
        engagement_rates = [ch['engagement_rate'] for ch in channels]
        
        # カテゴリ分布
        category_distribution = {}
        for channel in channels:
            categories = channel.get('topic_categories', [])
            for category in categories:
                category_distribution[category] = category_distribution.get(category, 0) + 1
        
        # メール連絡可能率
        contactable_count = sum(1 for ch in channels if ch.get('emails'))
        contactable_rate = contactable_count / len(channels) if channels else 0
        
        return {
            'average_subscriber_count': sum(subscriber_counts) / len(subscriber_counts) if subscriber_counts else 0,
            'median_subscriber_count': sorted(subscriber_counts)[len(subscriber_counts)//2] if subscriber_counts else 0,
            'average_engagement_rate': sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0,
            'category_distribution': sorted(
                category_distribution.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            'contactable_rate': round(contactable_rate * 100, 2),
            'total_channels': len(channels)
        }
    
    async def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, Any]:
        """
        古いデータのクリーンアップ
        
        Args:
            days_to_keep: 保持日数
            
        Returns:
            Dict: クリーンアップ結果
        """
        logger.info(f"🧹 Starting data cleanup (keeping last {days_to_keep} days)")
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        try:
            # 非アクティブなインフルエンサーを特定
            query_conditions = [
                ('fetched_at', '<', cutoff_date.isoformat()),
                ('status', '==', 'inactive')
            ]
            
            old_influencers = await self.db_helper.query_documents(
                collection=DatabaseCollections.INFLUENCERS,
                conditions=query_conditions
            )
            
            # 削除実行
            deleted_count = 0
            for influencer in old_influencers:
                try:
                    await self.db_helper.delete_document(
                        collection=DatabaseCollections.INFLUENCERS,
                        document_id=influencer['channel_id']
                    )
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"❌ Failed to delete {influencer['channel_id']}: {e}")
            
            return {
                'deleted_count': deleted_count,
                'cutoff_date': cutoff_date.isoformat(),
                'cleanup_completed': True
            }
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            return {'error': str(e), 'cleanup_completed': False}


# バッチ処理用のヘルパー関数
async def run_daily_batch():
    """日次バッチ処理"""
    processor = YouTubeBatchProcessor()
    
    # 1. 新規インフルエンサー発見
    discovery_result = await processor.discover_influencers_batch(
        categories=['beauty', 'gaming', 'cooking', 'tech', 'fitness'],
        max_per_category=20
    )
    
    # 2. 既存データの更新
    update_result = await processor.update_existing_influencers(
        batch_size=50,
        days_since_last_update=7
    )
    
    # 3. トレンド分析
    trend_result = await processor.analyze_trending_channels()
    
    logger.info(f"📊 Daily batch completed:")
    logger.info(f"  - Discovered: {discovery_result.get('total_discovered', 0)} new influencers")
    logger.info(f"  - Updated: {update_result.get('successfully_updated', 0)} existing influencers")
    logger.info(f"  - Analyzed: {trend_result.get('total_channels_analyzed', 0)} trending channels")
    
    return {
        'discovery': discovery_result,
        'updates': update_result,
        'trends': trend_result
    }


if __name__ == "__main__":
    # バッチ処理のテスト実行
    asyncio.run(run_daily_batch())