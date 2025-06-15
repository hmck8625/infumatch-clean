#!/usr/bin/env python3
"""
日本のゲーム系YouTuber実データ収集スクリプト

@description YouTube Data APIを使用して実際のゲーム系YouTuberを検索・取得し、
Firestore + BigQueryに登録する

@author InfuMatch Development Team
@version 1.0.0
"""

import sys
import os
import asyncio
import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import json

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.config import get_settings
from core.database import DatabaseHelper, DatabaseCollections
from services.data_integration import get_data_integration_service

# YouTube API クライアント（実装済み）
from services.youtube_api import YouTubeAPIClient

# YouTubeInfluencerServiceの簡易実装
class YouTubeInfluencerService:
    def __init__(self, api_client):
        self.api_client = api_client
    
    async def save_influencers_to_db(self, influencers):
        """インフルエンサーデータをDBに保存"""
        return len(influencers)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RealGamingYouTuberCollector:
    """実際のゲーム系YouTuber収集クラス"""
    
    def __init__(self):
        self.settings = get_settings()
        self.db_helper = DatabaseHelper()
        self.integration = get_data_integration_service()
        
        # YouTube API クライアント初期化
        self.youtube_client = YouTubeAPIClient()  # APIキーは設定から自動取得
        self.youtube_service = YouTubeInfluencerService(self.youtube_client)
        
        # 検索条件
        self.search_queries = [
            "ゲーム実況",
            "実況プレイ",
            "ゲーム配信",
            "gaming japan",
            "ゲーム実況者",
            "日本 ゲーム実況",
            "マインクラフト 実況",
            "フォートナイト 実況",
            "エーペックス 実況",
            "ゲーム攻略"
        ]
        
        # 統計情報
        self.stats = {
            'channels_found': 0,
            'channels_filtered': 0,
            'channels_saved': 0,
            'errors': 0,
            'processing_time': 0
        }
    
    def extract_contact_info_from_description(self, description: str) -> Dict[str, Any]:
        """概要欄からコンタクト情報を抽出"""
        if not description:
            return {'emails': [], 'social_links': {}, 'full_description': ''}
        
        # メールアドレス抽出
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, description)
        
        # SNSリンク抽出
        social_links = {}
        
        # Twitter
        twitter_patterns = [
            r'twitter\.com/([a-zA-Z0-9_]+)',
            r'@([a-zA-Z0-9_]+)',
            r'ツイッター[：:\s]*@?([a-zA-Z0-9_]+)'
        ]
        for pattern in twitter_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            if matches:
                social_links['twitter'] = f"@{matches[0]}"
                break
        
        # Instagram
        instagram_patterns = [
            r'instagram\.com/([a-zA-Z0-9_.]+)',
            r'インスタ[：:\s]*@?([a-zA-Z0-9_.]+)',
            r'Instagram[：:\s]*@?([a-zA-Z0-9_.]+)'
        ]
        for pattern in instagram_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            if matches:
                social_links['instagram'] = f"@{matches[0]}"
                break
        
        # TikTok
        tiktok_patterns = [
            r'tiktok\.com/@([a-zA-Z0-9_.]+)',
            r'TikTok[：:\s]*@?([a-zA-Z0-9_.]+)',
            r'ティックトック[：:\s]*@?([a-zA-Z0-9_.]+)'
        ]
        for pattern in tiktok_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            if matches:
                social_links['tiktok'] = f"@{matches[0]}"
                break
        
        # Twitch
        twitch_patterns = [
            r'twitch\.tv/([a-zA-Z0-9_]+)',
            r'Twitch[：:\s]*([a-zA-Z0-9_]+)'
        ]
        for pattern in twitch_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            if matches:
                social_links['twitch'] = matches[0]
                break
        
        # その他のウェブサイト
        url_pattern = r'https?://[^\s\)）\]】」\>\｝]+'
        websites = re.findall(url_pattern, description)
        if websites:
            social_links['websites'] = websites
        
        return {
            'emails': list(set(emails)),  # 重複除去
            'social_links': social_links,
            'full_description': description.strip()
        }
    
    def is_gaming_channel(self, channel_info: Dict[str, Any]) -> bool:
        """チャンネルがゲーム系かどうかを判定"""
        gaming_keywords = [
            'ゲーム', 'game', 'gaming', '実況', 'プレイ', 'play',
            'マインクラフト', 'minecraft', 'フォートナイト', 'fortnite',
            'エーペックス', 'apex', 'フォール', 'fall', 'guys',
            'スプラ', 'splatoon', 'ポケモン', 'pokemon', 'モンハン',
            'valorant', 'バロラント', 'lol', 'リーグ', 'league',
            'pubg', 'cod', 'コール', 'call', 'duty', 'fps',
            'mmo', 'rpg', 'アクション', 'シューティング', 'レーシング',
            'ストラテジー', 'シミュレーション', 'パズル', 'アドベンチャー'
        ]
        
        # チャンネル名とdescriptionでチェック
        text_to_check = (
            channel_info.get('title', '') + ' ' +
            channel_info.get('description', '')
        ).lower()
        
        return any(keyword.lower() in text_to_check for keyword in gaming_keywords)
    
    def filter_by_subscriber_range(self, channel_info: Dict[str, Any]) -> bool:
        """登録者数でフィルタリング（1万〜10万人）"""
        subscriber_count = channel_info.get('subscriber_count', 0)
        return 10000 <= subscriber_count <= 100000
    
    async def search_gaming_channels(self, max_results: int = 20) -> List[Dict[str, Any]]:
        """ゲーム系チャンネルを検索"""
        logger.info("🔍 Searching for gaming channels...")
        
        all_channels = []
        channel_ids_seen = set()
        
        for query in self.search_queries:
            logger.info(f"🔍 Searching with query: '{query}'")
            
            try:
                # チャンネル検索
                search_results = await self.youtube_client.search_channels(
                    query=query,
                    max_results=max_results // len(self.search_queries),
                    order='relevance',
                    region='JP',
                    relevance_language='ja'
                )
                
                for result in search_results:
                    channel_id = result.get('channel_id')
                    if channel_id and channel_id not in channel_ids_seen:
                        channel_ids_seen.add(channel_id)
                        all_channels.append(result)
                
                # API制限対応の待機
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Search failed for query '{query}': {str(e)}")
                self.stats['errors'] += 1
                continue
        
        self.stats['channels_found'] = len(all_channels)
        logger.info(f"✅ Found {len(all_channels)} unique channels")
        
        return all_channels
    
    async def get_detailed_channel_info(self, channels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """詳細なチャンネル情報を取得"""
        logger.info("📊 Getting detailed channel information...")
        
        detailed_channels = []
        
        # チャンネルIDを抽出
        channel_ids = [ch.get('channel_id') for ch in channels if ch.get('channel_id')]
        
        if not channel_ids:
            logger.warning("⚠️ No channel IDs found")
            return []
        
        try:
            # 詳細情報を一括取得
            detailed_info = await self.youtube_client.get_channel_details(channel_ids)
            
            for channel in detailed_info:
                # 概要欄から連絡先情報を抽出
                description = channel.get('description', '')
                contact_info = self.extract_contact_info_from_description(description)
                
                # チャンネル情報を拡張
                enhanced_channel = {
                    **channel,
                    'contact_emails': contact_info['emails'],
                    'social_links': contact_info['social_links'],
                    'full_description': contact_info['full_description']
                }
                
                detailed_channels.append(enhanced_channel)
                
        except Exception as e:
            logger.error(f"❌ Failed to get detailed channel info: {str(e)}")
            self.stats['errors'] += 1
        
        logger.info(f"✅ Retrieved detailed info for {len(detailed_channels)} channels")
        return detailed_channels
    
    async def get_recent_videos(self, channel_id: str) -> List[Dict[str, Any]]:
        """最近の動画情報を取得"""
        try:
            videos = await self.youtube_client.get_recent_videos(
                channel_id=channel_id,
                max_results=5
            )
            return videos
        except Exception as e:
            logger.warning(f"⚠️ Failed to get videos for channel {channel_id}: {str(e)}")
            return []
    
    def calculate_engagement_metrics(self, channel_info: Dict[str, Any], videos: List[Dict[str, Any]]) -> Dict[str, float]:
        """エンゲージメント指標を計算"""
        if not videos:
            return {'engagement_rate': 0.0, 'avg_views': 0.0, 'avg_likes': 0.0}
        
        subscriber_count = channel_info.get('subscriber_count', 1)
        
        # 動画の統計を計算
        total_views = sum(video.get('view_count', 0) for video in videos)
        total_likes = sum(video.get('like_count', 0) for video in videos)
        total_comments = sum(video.get('comment_count', 0) for video in videos)
        
        avg_views = total_views / len(videos)
        avg_likes = total_likes / len(videos)
        avg_comments = total_comments / len(videos)
        
        # エンゲージメント率 = (平均いいね数 + 平均コメント数) / 登録者数
        engagement_rate = (avg_likes + avg_comments) / subscriber_count if subscriber_count > 0 else 0
        
        return {
            'engagement_rate': round(engagement_rate, 4),
            'avg_views': round(avg_views, 0),
            'avg_likes': round(avg_likes, 0),
            'avg_comments': round(avg_comments, 0),
            'video_count_analyzed': len(videos)
        }
    
    def generate_ai_analysis_score(self, channel_info: Dict[str, Any], engagement_metrics: Dict[str, float]) -> Dict[str, float]:
        """AI分析スコアを生成（簡易版）"""
        # 基本スコア計算
        subscriber_score = min(channel_info.get('subscriber_count', 0) / 100000, 1.0)
        engagement_score = min(engagement_metrics.get('engagement_rate', 0) * 100, 1.0)
        activity_score = 0.8  # デフォルト値（実際は投稿頻度から計算）
        
        # コンテンツ品質スコア（概要欄の充実度から推定）
        description_length = len(channel_info.get('full_description', ''))
        content_quality_score = min(description_length / 500, 1.0)
        
        # ブランド安全性スコア（キーワードベース）
        brand_safety_score = 0.9  # デフォルト高値
        
        return {
            'engagement_rate': engagement_metrics.get('engagement_rate', 0),
            'content_quality_score': round(content_quality_score, 2),
            'brand_safety_score': round(brand_safety_score, 2),
            'activity_score': round(activity_score, 2),
            'overall_score': round((subscriber_score + engagement_score + activity_score + content_quality_score) / 4, 2)
        }
    
    async def process_and_filter_channels(self, channels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """チャンネルを処理・フィルタリング"""
        logger.info("🔄 Processing and filtering channels...")
        
        processed_channels = []
        
        for channel in channels:
            try:
                # ゲームチャンネルかチェック
                if not self.is_gaming_channel(channel):
                    logger.debug(f"Skipping non-gaming channel: {channel.get('title', 'Unknown')}")
                    continue
                
                # 登録者数でフィルタリング
                if not self.filter_by_subscriber_range(channel):
                    logger.debug(f"Skipping channel outside subscriber range: {channel.get('title', 'Unknown')} "
                               f"({channel.get('subscriber_count', 0):,} subscribers)")
                    continue
                
                # 最近の動画を取得
                recent_videos = await self.get_recent_videos(channel.get('channel_id'))
                
                # エンゲージメント指標を計算
                engagement_metrics = self.calculate_engagement_metrics(channel, recent_videos)
                
                # AI分析スコアを生成
                ai_analysis = self.generate_ai_analysis_score(channel, engagement_metrics)
                
                # データベース用フォーマットに変換
                processed_channel = {
                    'channel_id': channel.get('channel_id'),
                    'channel_title': channel.get('channel_name', channel.get('title', '')),
                    'description': channel.get('full_description', channel.get('description', '')),
                    'subscriber_count': channel.get('subscriber_count', 0),
                    'view_count': channel.get('view_count', 0),
                    'video_count': channel.get('video_count', 0),
                    'category': 'gaming',
                    'country': 'JP',
                    'language': 'ja',
                    'contact_info': {
                        'emails': channel.get('contact_emails', []),
                        'primary_email': channel.get('contact_emails', [None])[0] if channel.get('contact_emails') else None
                    },
                    'social_links': channel.get('social_links', {}),
                    'recent_videos': recent_videos,
                    'engagement_metrics': engagement_metrics,
                    'ai_analysis': ai_analysis,
                    'status': 'active',
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat(),
                    'last_analyzed': datetime.now(timezone.utc).isoformat(),
                    'fetched_at': datetime.now(timezone.utc).isoformat()
                }
                
                processed_channels.append(processed_channel)
                self.stats['channels_filtered'] += 1
                
                logger.info(f"✅ Processed: {channel.get('title', 'Unknown')} "
                           f"({channel.get('subscriber_count', 0):,} subscribers, "
                           f"{engagement_metrics.get('engagement_rate', 0):.3f} engagement)")
                
                # レート制限対応
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"❌ Failed to process channel {channel.get('title', 'Unknown')}: {str(e)}")
                self.stats['errors'] += 1
                continue
        
        # 登録者数でソート（降順）
        processed_channels.sort(key=lambda x: x.get('subscriber_count', 0), reverse=True)
        
        logger.info(f"✅ Filtered to {len(processed_channels)} gaming channels in target range")
        return processed_channels
    
    async def save_to_database(self, channels: List[Dict[str, Any]]) -> bool:
        """データベースに保存"""
        logger.info("💾 Saving channels to database...")
        
        try:
            saved_count = 0
            
            for channel in channels:
                # Firestoreに保存
                await self.db_helper.create_document(
                    collection=DatabaseCollections.INFLUENCERS,
                    document_id=channel['channel_id'],
                    data=channel
                )
                saved_count += 1
                
            self.stats['channels_saved'] = saved_count
            logger.info(f"✅ Saved {saved_count} channels to Firestore")
            
            # BigQueryに同期
            logger.info("🔄 Syncing to BigQuery...")
            sync_result = await self.integration.sync_influencers_to_bigquery()
            
            if sync_result.get('error'):
                logger.warning(f"⚠️ BigQuery sync warning: {sync_result['error']}")
            else:
                logger.info(f"✅ Synced {sync_result.get('synced_count', 0)} records to BigQuery")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save to database: {str(e)}")
            return False
    
    def print_summary(self, channels: List[Dict[str, Any]]):
        """収集結果のサマリーを表示"""
        print("\n" + "="*80)
        print("🎮 日本のゲーム系YouTuber収集結果")
        print("="*80)
        
        print(f"📊 統計:")
        print(f"  - 検索で発見: {self.stats['channels_found']} チャンネル")
        print(f"  - 条件に合致: {self.stats['channels_filtered']} チャンネル")
        print(f"  - データベース保存: {self.stats['channels_saved']} チャンネル")
        print(f"  - エラー数: {self.stats['errors']}")
        
        if channels:
            print(f"\n📋 取得したチャンネル一覧:")
            print("-"*80)
            
            for i, channel in enumerate(channels[:15], 1):  # 上位15件表示
                title = channel.get('channel_title', 'Unknown')
                subscribers = channel.get('subscriber_count', 0)
                engagement = channel.get('engagement_metrics', {}).get('engagement_rate', 0)
                emails = len(channel.get('contact_info', {}).get('emails', []))
                
                print(f"{i:2d}. {title}")
                print(f"     登録者: {subscribers:,}人 | エンゲージメント: {engagement:.3f} | メール: {emails}件")
                
                if i % 5 == 0:
                    print("-"*80)
        
        print("\n🎉 データ収集完了！")
        print("="*80)
    
    async def run_collection(self, max_results: int = 20) -> List[Dict[str, Any]]:
        """メイン収集処理"""
        start_time = datetime.now()
        
        logger.info("🚀 Starting real gaming YouTuber data collection...")
        
        try:
            # 1. チャンネル検索
            channels = await self.search_gaming_channels(max_results)
            
            if not channels:
                logger.warning("⚠️ No channels found")
                return []
            
            # 2. 詳細情報取得
            detailed_channels = await self.get_detailed_channel_info(channels)
            
            # 3. 処理・フィルタリング
            processed_channels = await self.process_and_filter_channels(detailed_channels)
            
            if not processed_channels:
                logger.warning("⚠️ No channels passed filtering")
                return []
            
            # 4. データベース保存
            await self.save_to_database(processed_channels)
            
            # 5. 結果表示
            end_time = datetime.now()
            self.stats['processing_time'] = (end_time - start_time).total_seconds()
            
            self.print_summary(processed_channels)
            
            return processed_channels
            
        except Exception as e:
            logger.error(f"❌ Collection failed: {str(e)}")
            return []


async def main():
    """メイン実行関数"""
    collector = RealGamingYouTuberCollector()
    
    print("\n🎮 日本のゲーム系YouTuber実データ収集ツール")
    print("="*60)
    print("\n収集条件:")
    print("- 対象: マイクロインフルエンサー（1万〜10万人）")
    print("- ジャンル: ゲーム全般")
    print("- 地域: 日本")
    print("- 件数: 10-20件")
    print("- 概要欄: 全内容取得")
    print("-"*60)
    
    try:
        # データ収集実行
        channels = await collector.run_collection(max_results=20)
        
        if channels:
            print(f"\n✅ 成功: {len(channels)} 件のゲーム系YouTuberデータを収集・保存しました")
            
            # 簡易レポート
            total_subscribers = sum(ch.get('subscriber_count', 0) for ch in channels)
            avg_engagement = sum(ch.get('engagement_metrics', {}).get('engagement_rate', 0) for ch in channels) / len(channels)
            channels_with_email = sum(1 for ch in channels if ch.get('contact_info', {}).get('emails'))
            
            print(f"\n📈 分析サマリー:")
            print(f"  - 総登録者数: {total_subscribers:,} 人")
            print(f"  - 平均エンゲージメント率: {avg_engagement:.3f}")
            print(f"  - 連絡可能チャンネル: {channels_with_email}/{len(channels)} 件")
            
        else:
            print("❌ データ収集に失敗しました")
            
    except Exception as e:
        logger.error(f"❌ Execution failed: {str(e)}")
        print(f"❌ エラーが発生しました: {str(e)}")


if __name__ == "__main__":
    # スクリプト実行
    asyncio.run(main())