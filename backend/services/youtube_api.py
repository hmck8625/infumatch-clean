"""
YouTube Data API 連携サービス

@description YouTube Data API v3 を使用したチャンネル情報取得
インフルエンサー発見とデータ収集の中核機能

@author InfuMatch Development Team
@version 1.0.0
"""

import logging
import asyncio
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import time

import httpx
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google.auth
from google.oauth2 import service_account

from core.config import get_settings
from core.database import FirestoreClient, DatabaseHelper, DatabaseCollections

logger = logging.getLogger(__name__)
settings = get_settings()


class YouTubeAPIClient:
    """
    YouTube Data API クライアント
    
    API の呼び出し、レート制限管理、エラーハンドリングを提供
    """
    
    def __init__(self):
        """初期化"""
        self.api_key = settings.YOUTUBE_API_KEY
        self.quota_limit = settings.YOUTUBE_QUOTA_LIMIT
        self.rate_limit = settings.YOUTUBE_RATE_LIMIT_PER_SECOND
        self.service = None
        self._last_request_time = 0
        self._daily_quota_used = 0
        self._initialize_service()
    
    def _initialize_service(self) -> None:
        """YouTube API サービスの初期化"""
        try:
            self.service = build(
                'youtube',
                'v3',
                developerKey=self.api_key,
                cache_discovery=False  # キャッシュを無効化（メモリ使用量削減）
            )
            logger.info("✅ YouTube API service initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize YouTube API service: {e}")
            raise
    
    async def _rate_limit_check(self) -> None:
        """レート制限のチェック"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        # 秒あたりのレート制限
        min_interval = 1.0 / self.rate_limit
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            await asyncio.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def _check_quota(self, cost: int) -> bool:
        """クォータ使用量のチェック"""
        if self._daily_quota_used + cost > self.quota_limit:
            logger.warning(f"⚠️ Daily quota limit reached: {self._daily_quota_used}/{self.quota_limit}")
            return False
        return True
    
    async def search_channels(
        self,
        query: str,
        max_results: int = 50,
        order: str = 'relevance'
    ) -> List[Dict[str, Any]]:
        """
        チャンネル検索
        
        Args:
            query: 検索クエリ
            max_results: 最大取得件数（1-50）
            order: ソート順 ('relevance', 'date', 'rating', 'viewCount')
            
        Returns:
            List[Dict]: チャンネル情報のリスト
        """
        await self._rate_limit_check()
        
        # クォータチェック（検索は100ユニット消費）
        if not self._check_quota(100):
            raise Exception("Daily quota limit exceeded")
        
        try:
            logger.info(f"🔍 Searching channels for query: '{query}'")
            
            search_response = self.service.search().list(
                part='snippet',
                type='channel',
                q=query,
                maxResults=min(max_results, 50),  # API制限
                order=order,
                regionCode='JP',  # 日本のコンテンツを優先
                relevanceLanguage='ja'  # 日本語を優先
            ).execute()
            
            self._daily_quota_used += 100
            
            channels = []
            for item in search_response.get('items', []):
                channel_data = {
                    'channel_id': item['id']['channelId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'thumbnail_url': item['snippet']['thumbnails'].get('high', {}).get('url'),
                    'published_at': item['snippet']['publishedAt'],
                    'search_query': query
                }
                channels.append(channel_data)
            
            logger.info(f"✅ Found {len(channels)} channels for query: '{query}'")
            return channels
            
        except HttpError as e:
            logger.error(f"❌ YouTube API error: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Channel search failed: {e}")
            raise
    
    async def get_channel_details(self, channel_ids: List[str]) -> List[Dict[str, Any]]:
        """
        チャンネル詳細情報を取得
        
        Args:
            channel_ids: チャンネルIDのリスト（最大50件）
            
        Returns:
            List[Dict]: 詳細チャンネル情報のリスト
        """
        await self._rate_limit_check()
        
        # クォータチェック（チャンネル詳細は1ユニット消費）
        if not self._check_quota(1):
            raise Exception("Daily quota limit exceeded")
        
        try:
            # 最大50件に制限
            channel_ids = channel_ids[:50]
            
            logger.info(f"📊 Getting details for {len(channel_ids)} channels")
            
            channels_response = self.service.channels().list(
                part='snippet,statistics,contentDetails,topicDetails,brandingSettings',
                id=','.join(channel_ids)
            ).execute()
            
            self._daily_quota_used += 1
            
            channels = []
            for item in channels_response.get('items', []):
                channel_data = self._extract_channel_data(item)
                channels.append(channel_data)
            
            logger.info(f"✅ Retrieved details for {len(channels)} channels")
            return channels
            
        except HttpError as e:
            logger.error(f"❌ YouTube API error: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Channel details retrieval failed: {e}")
            raise
    
    def _extract_channel_data(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        API レスポンスからチャンネルデータを抽出
        
        Args:
            item: YouTube API のチャンネル項目
            
        Returns:
            Dict: 整理されたチャンネルデータ
        """
        snippet = item.get('snippet', {})
        statistics = item.get('statistics', {})
        content_details = item.get('contentDetails', {})
        topic_details = item.get('topicDetails', {})
        branding = item.get('brandingSettings', {})
        
        # 統計情報の安全な取得（hiddenの場合もある）
        subscriber_count = int(statistics.get('subscriberCount', 0))
        video_count = int(statistics.get('videoCount', 0))
        view_count = int(statistics.get('viewCount', 0))
        
        # エンゲージメント率の計算（概算）
        engagement_rate = 0.0
        if subscriber_count > 0 and video_count > 0:
            avg_views_per_video = view_count / video_count
            engagement_rate = (avg_views_per_video / subscriber_count) * 100
            engagement_rate = min(engagement_rate, 100.0)  # 上限設定
        
        return {
            'channel_id': item['id'],
            'channel_name': snippet.get('title', ''),
            'description': snippet.get('description', ''),
            'custom_url': snippet.get('customUrl', ''),
            'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url'),
            'published_at': snippet.get('publishedAt'),
            'country': snippet.get('country'),
            'default_language': snippet.get('defaultLanguage'),
            
            # 統計情報
            'subscriber_count': subscriber_count,
            'video_count': video_count,
            'view_count': view_count,
            'hidden_subscriber_count': statistics.get('hiddenSubscriberCount', False),
            'engagement_rate': round(engagement_rate, 2),
            
            # コンテンツ情報
            'uploads_playlist_id': content_details.get('relatedPlaylists', {}).get('uploads'),
            'topic_ids': topic_details.get('topicIds', []),
            'topic_categories': topic_details.get('topicCategories', []),
            
            # ブランディング情報
            'keywords': branding.get('channel', {}).get('keywords'),
            'banner_image_url': branding.get('image', {}).get('bannerExternalUrl'),
            
            # 取得日時
            'fetched_at': datetime.utcnow().isoformat(),
        }
    
    async def get_recent_videos(
        self,
        channel_id: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        チャンネルの最新動画を取得
        
        Args:
            channel_id: チャンネルID
            max_results: 最大取得件数
            
        Returns:
            List[Dict]: 動画情報のリスト
        """
        await self._rate_limit_check()
        
        if not self._check_quota(1):
            raise Exception("Daily quota limit exceeded")
        
        try:
            # まずチャンネルのアップロードプレイリストIDを取得
            channel_response = self.service.channels().list(
                part='contentDetails',
                id=channel_id
            ).execute()
            
            items = channel_response.get('items', [])
            if not items:
                return []
            
            uploads_playlist_id = items[0]['contentDetails']['relatedPlaylists']['uploads']
            
            # プレイリストから最新動画を取得
            playlist_response = self.service.playlistItems().list(
                part='snippet,contentDetails',
                playlistId=uploads_playlist_id,
                maxResults=max_results
            ).execute()
            
            self._daily_quota_used += 2  # 2回のAPI呼び出し
            
            videos = []
            for item in playlist_response.get('items', []):
                video_data = {
                    'video_id': item['contentDetails']['videoId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'thumbnail_url': item['snippet']['thumbnails'].get('high', {}).get('url'),
                    'published_at': item['snippet']['publishedAt'],
                    'channel_id': channel_id
                }
                videos.append(video_data)
            
            return videos
            
        except HttpError as e:
            logger.error(f"❌ YouTube API error: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Recent videos retrieval failed: {e}")
            raise


class EmailExtractor:
    """
    チャンネル説明文からメールアドレスを抽出
    
    正規表現とヒューリスティックを使用
    """
    
    # メールアドレスの正規表現パターン
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    )
    
    # ビジネス用メールの判定キーワード
    BUSINESS_KEYWORDS = [
        'お仕事', 'ビジネス', 'business', 'work', 'collaboration', 'collab',
        'コラボ', '仕事', '依頼', '相談', 'contact', 'inquiry', 'pr', 'プロモ'
    ]
    
    @classmethod
    def extract_emails(cls, text: str) -> List[Dict[str, Any]]:
        """
        テキストからメールアドレスを抽出
        
        Args:
            text: 対象テキスト
            
        Returns:
            List[Dict]: メールアドレス情報のリスト
        """
        if not text:
            return []
        
        # メールアドレスを抽出
        emails = cls.EMAIL_PATTERN.findall(text.lower())
        
        if not emails:
            return []
        
        # 重複除去と優先度判定
        unique_emails = []
        seen_emails = set()
        
        for email in emails:
            if email in seen_emails:
                continue
                
            seen_emails.add(email)
            priority = cls._calculate_priority(email, text)
            
            unique_emails.append({
                'email': email,
                'priority': priority,
                'context': cls._extract_context(email, text),
                'is_business': cls._is_business_email(email, text)
            })
        
        # 優先度順でソート
        unique_emails.sort(key=lambda x: x['priority'], reverse=True)
        
        return unique_emails
    
    @classmethod
    def _calculate_priority(cls, email: str, text: str) -> int:
        """
        メールアドレスの優先度を計算
        
        Args:
            email: メールアドレス
            text: 全体テキスト
            
        Returns:
            int: 優先度スコア（1-10）
        """
        priority = 1
        
        # 独自ドメインは高優先度
        if not any(domain in email for domain in ['gmail.com', 'yahoo.co.jp', 'hotmail.com']):
            priority += 3
        
        # ビジネス関連キーワードが近くにある
        email_index = text.lower().find(email)
        if email_index != -1:
            context_start = max(0, email_index - 50)
            context_end = min(len(text), email_index + len(email) + 50)
            context = text[context_start:context_end].lower()
            
            for keyword in cls.BUSINESS_KEYWORDS:
                if keyword in context:
                    priority += 2
                    break
        
        # メールアドレス自体にビジネス系キーワードが含まれる
        business_prefixes = ['business', 'contact', 'info', 'pr', 'collab', 'work']
        for prefix in business_prefixes:
            if prefix in email.split('@')[0]:
                priority += 1
                break
        
        return min(priority, 10)  # 最大10
    
    @classmethod
    def _extract_context(cls, email: str, text: str) -> str:
        """
        メールアドレス周辺のコンテキストを抽出
        
        Args:
            email: メールアドレス
            text: 全体テキスト
            
        Returns:
            str: コンテキスト文字列
        """
        email_index = text.find(email)
        if email_index == -1:
            return ""
        
        context_start = max(0, email_index - 30)
        context_end = min(len(text), email_index + len(email) + 30)
        
        return text[context_start:context_end].strip()
    
    @classmethod
    def _is_business_email(cls, email: str, text: str) -> bool:
        """
        ビジネス用メールかどうかの判定
        
        Args:
            email: メールアドレス
            text: 全体テキスト
            
        Returns:
            bool: ビジネス用の場合 True
        """
        # 独自ドメインは高確率でビジネス用
        if not any(domain in email for domain in ['gmail.com', 'yahoo.co.jp', 'hotmail.com']):
            return True
        
        # コンテキストにビジネスキーワードがある
        context = cls._extract_context(email, text)
        for keyword in cls.BUSINESS_KEYWORDS:
            if keyword in context.lower():
                return True
        
        return False


class YouTubeInfluencerService:
    """
    YouTube インフルエンサー関連のサービス
    
    検索、分析、データベース保存の統合機能
    """
    
    def __init__(self):
        self.api_client = YouTubeAPIClient()
        self.db_client = FirestoreClient()
        self.db_helper = DatabaseHelper(self.db_client)
        self.email_extractor = EmailExtractor()
    
    async def discover_influencers(
        self,
        search_queries: List[str],
        subscriber_min: int = 1000,
        subscriber_max: int = 100000,
        max_per_query: int = 20
    ) -> List[Dict[str, Any]]:
        """
        インフルエンサーを発見
        
        Args:
            search_queries: 検索クエリのリスト
            subscriber_min: 最小登録者数
            subscriber_max: 最大登録者数
            max_per_query: クエリあたりの最大取得数
            
        Returns:
            List[Dict]: 発見されたインフルエンサー情報
        """
        logger.info(f"🔍 Starting influencer discovery for {len(search_queries)} queries")
        
        all_influencers = []
        processed_channel_ids = set()
        
        for query in search_queries:
            try:
                # チャンネル検索
                channels = await self.api_client.search_channels(
                    query=query,
                    max_results=max_per_query
                )
                
                if not channels:
                    continue
                
                # 重複除去
                channel_ids = [
                    ch['channel_id'] for ch in channels 
                    if ch['channel_id'] not in processed_channel_ids
                ]
                
                if not channel_ids:
                    continue
                
                # 詳細情報取得
                detailed_channels = await self.api_client.get_channel_details(channel_ids)
                
                # フィルタリング（登録者数範囲）
                filtered_channels = [
                    ch for ch in detailed_channels
                    if subscriber_min <= ch['subscriber_count'] <= subscriber_max
                    and not ch['hidden_subscriber_count']
                ]
                
                # メールアドレス抽出
                for channel in filtered_channels:
                    emails = self.email_extractor.extract_emails(channel['description'])
                    channel['emails'] = emails
                    channel['has_business_email'] = any(e['is_business'] for e in emails)
                
                all_influencers.extend(filtered_channels)
                processed_channel_ids.update(channel_ids)
                
                logger.info(f"✅ Query '{query}': Found {len(filtered_channels)} matching influencers")
                
                # レート制限対応
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Failed to process query '{query}': {e}")
                continue
        
        logger.info(f"🎉 Discovery completed: {len(all_influencers)} total influencers found")
        return all_influencers
    
    async def save_influencers_to_db(self, influencers: List[Dict[str, Any]]) -> int:
        """
        インフルエンサー情報をデータベースに保存
        
        Args:
            influencers: インフルエンサー情報のリスト
            
        Returns:
            int: 保存成功件数
        """
        logger.info(f"💾 Saving {len(influencers)} influencers to database")
        
        saved_count = 0
        
        for influencer in influencers:
            try:
                # Firestore 用のドキュメントデータに変換
                doc_data = {
                    'channel_id': influencer['channel_id'],
                    'channel_name': influencer['channel_name'],
                    'description': influencer['description'],
                    'custom_url': influencer.get('custom_url', ''),
                    'thumbnail_url': influencer.get('thumbnail_url', ''),
                    'subscriber_count': influencer['subscriber_count'],
                    'video_count': influencer['video_count'],
                    'view_count': influencer['view_count'],
                    'engagement_rate': influencer['engagement_rate'],
                    'emails': influencer.get('emails', []),
                    'has_business_email': influencer.get('has_business_email', False),
                    'topic_categories': influencer.get('topic_categories', []),
                    'country': influencer.get('country', ''),
                    'fetched_at': influencer['fetched_at'],
                    'data_quality_score': self._calculate_quality_score(influencer),
                    'status': 'active'
                }
                
                # データベースに保存（チャンネルIDをドキュメントIDとして使用）
                await self.db_helper.create_document(
                    collection=DatabaseCollections.INFLUENCERS,
                    data=doc_data,
                    document_id=influencer['channel_id']
                )
                
                saved_count += 1
                
            except Exception as e:
                logger.error(f"❌ Failed to save influencer {influencer['channel_id']}: {e}")
                continue
        
        logger.info(f"✅ Saved {saved_count}/{len(influencers)} influencers to database")
        return saved_count
    
    def _calculate_quality_score(self, influencer: Dict[str, Any]) -> float:
        """
        データ品質スコアを計算
        
        Args:
            influencer: インフルエンサー情報
            
        Returns:
            float: 品質スコア (0.0-1.0)
        """
        score = 0.0
        
        # 基本情報の完全性
        if influencer.get('channel_name'):
            score += 0.2
        if influencer.get('description'):
            score += 0.2
        if influencer.get('thumbnail_url'):
            score += 0.1
        
        # 統計情報の妥当性
        if influencer['subscriber_count'] > 0:
            score += 0.2
        if influencer['video_count'] > 0:
            score += 0.1
        
        # メールアドレスの有無
        if influencer.get('has_business_email'):
            score += 0.2
        
        return round(score, 2)
    
    async def update_influencer_analytics(self, channel_id: str) -> bool:
        """
        インフルエンサーの分析情報を更新
        
        Args:
            channel_id: チャンネルID
            
        Returns:
            bool: 更新成功時 True
        """
        try:
            # 最新の詳細情報を取得
            channels = await self.api_client.get_channel_details([channel_id])
            
            if not channels:
                return False
            
            channel = channels[0]
            
            # 最新動画情報も取得
            recent_videos = await self.api_client.get_recent_videos(channel_id)
            
            # 更新データ
            update_data = {
                'subscriber_count': channel['subscriber_count'],
                'video_count': channel['video_count'],
                'view_count': channel['view_count'],
                'engagement_rate': channel['engagement_rate'],
                'recent_videos': recent_videos[:5],  # 最新5件
                'last_analyzed': datetime.utcnow().isoformat(),
                'data_quality_score': self._calculate_quality_score(channel)
            }
            
            # データベース更新
            success = await self.db_helper.update_document(
                collection=DatabaseCollections.INFLUENCERS,
                document_id=channel_id,
                data=update_data
            )
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to update analytics for {channel_id}: {e}")
            return False