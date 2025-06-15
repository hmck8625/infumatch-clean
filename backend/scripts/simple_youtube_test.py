#!/usr/bin/env python3
"""
YouTube API 簡単テスト

@description YouTube Data APIを直接使用してゲーム系YouTuberを検索
依存関係を最小限に抑えたテスト用スクリプト

@author InfuMatch Development Team
@version 1.0.0
"""

import os
import json
import asyncio
import re
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# 設定
YOUTUBE_API_KEY = "AIzaSyDtPl5WSRdxk744ha5Tlwno4iTBZVO96r4"
PROJECT_ID = "hackathon-462905"

class SimpleYouTubeCollector:
    """簡単なYouTube データ収集クラス"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.service = build('youtube', 'v3', developerKey=api_key)
        self.collected_data = []
    
    def extract_emails_from_description(self, description):
        """概要欄からメールアドレスを抽出"""
        if not description:
            return []
        
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, description)
        return list(set(emails))  # 重複除去
    
    def is_gaming_related(self, title, description):
        """ゲーム関連かどうかを判定"""
        gaming_keywords = [
            'ゲーム', 'game', 'gaming', '実況', 'プレイ', 'play',
            'マインクラフト', 'minecraft', 'フォートナイト', 'fortnite',
            'エーペックス', 'apex', 'スプラ', 'splatoon', 'ポケモン', 'pokemon'
        ]
        
        text = (title + ' ' + description).lower()
        return any(keyword.lower() in text for keyword in gaming_keywords)
    
    def search_gaming_channels(self, query, max_results=10):
        """ゲーム系チャンネルを検索"""
        try:
            print(f"🔍 Searching for: '{query}'")
            
            # チャンネル検索
            search_response = self.service.search().list(
                part='snippet',
                type='channel',
                q=query,
                maxResults=max_results,
                order='relevance',
                regionCode='JP',
                relevanceLanguage='ja'
            ).execute()
            
            channels = []
            for item in search_response.get('items', []):
                channel_data = {
                    'channel_id': item['id']['channelId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'thumbnail': item['snippet']['thumbnails'].get('high', {}).get('url'),
                    'search_query': query
                }
                channels.append(channel_data)
            
            print(f"✅ Found {len(channels)} channels")
            return channels
            
        except HttpError as e:
            print(f"❌ YouTube API error: {e}")
            return []
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []
    
    def get_channel_details(self, channel_ids):
        """チャンネル詳細情報を取得"""
        try:
            print(f"📊 Getting details for {len(channel_ids)} channels")
            
            channels_response = self.service.channels().list(
                part='snippet,statistics,contentDetails',
                id=','.join(channel_ids)
            ).execute()
            
            detailed_channels = []
            for item in channels_response.get('items', []):
                snippet = item.get('snippet', {})
                statistics = item.get('statistics', {})
                
                # 登録者数の安全な取得
                subscriber_count = int(statistics.get('subscriberCount', 0))
                video_count = int(statistics.get('videoCount', 0))
                view_count = int(statistics.get('viewCount', 0))
                
                # フィルタリング: 1万〜10万人
                if not (10000 <= subscriber_count <= 100000):
                    continue
                
                # ゲーム関連かチェック
                if not self.is_gaming_related(snippet.get('title', ''), snippet.get('description', '')):
                    continue
                
                # メールアドレス抽出
                emails = self.extract_emails_from_description(snippet.get('description', ''))
                
                channel_data = {
                    'channel_id': item['id'],
                    'channel_title': snippet.get('title', ''),
                    'description': snippet.get('description', ''),
                    'subscriber_count': subscriber_count,
                    'video_count': video_count,
                    'view_count': view_count,
                    'country': snippet.get('country', 'JP'),
                    'emails': emails,
                    'has_contact': len(emails) > 0,
                    'engagement_estimate': round((view_count / video_count / subscriber_count) * 100, 2) if video_count > 0 and subscriber_count > 0 else 0,
                    'collected_at': datetime.now().isoformat()
                }
                
                detailed_channels.append(channel_data)
                print(f"✅ {snippet.get('title', 'Unknown')}: {subscriber_count:,} subscribers, {len(emails)} emails")
            
            return detailed_channels
            
        except HttpError as e:
            print(f"❌ YouTube API error: {e}")
            return []
        except Exception as e:
            print(f"❌ Details retrieval failed: {e}")
            return []
    
    def collect_gaming_youtubers(self):
        """ゲーム系YouTuberデータを収集"""
        print("🎮 日本のゲーム系YouTuber データ収集開始")
        print("="*60)
        
        # 検索クエリ
        search_queries = [
            "ゲーム実況",
            "実況プレイ", 
            "ゲーム配信",
            "マインクラフト 実況",
            "フォートナイト 実況"
        ]
        
        all_channels = []
        channel_ids_seen = set()
        
        # 各クエリで検索
        for query in search_queries:
            channels = self.search_gaming_channels(query, max_results=5)
            
            for channel in channels:
                channel_id = channel['channel_id']
                if channel_id not in channel_ids_seen:
                    channel_ids_seen.add(channel_id)
                    all_channels.append(channel)
        
        print(f"\n📋 Found {len(all_channels)} unique channels")
        
        if not all_channels:
            print("❌ No channels found")
            return []
        
        # 詳細情報を取得
        channel_ids = [ch['channel_id'] for ch in all_channels]
        detailed_channels = self.get_channel_details(channel_ids)
        
        self.collected_data = detailed_channels
        
        # 結果表示
        self.print_results()
        
        return detailed_channels
    
    def print_results(self):
        """収集結果を表示"""
        if not self.collected_data:
            print("❌ No data collected")
            return
        
        print("\n" + "="*80)
        print("🎯 収集結果サマリー")
        print("="*80)
        
        total_channels = len(self.collected_data)
        channels_with_email = sum(1 for ch in self.collected_data if ch['has_contact'])
        total_subscribers = sum(ch['subscriber_count'] for ch in self.collected_data)
        avg_engagement = sum(ch['engagement_estimate'] for ch in self.collected_data) / total_channels if total_channels > 0 else 0
        
        print(f"📊 統計:")
        print(f"  - 収集チャンネル数: {total_channels}")
        print(f"  - 連絡可能チャンネル: {channels_with_email} ({channels_with_email/total_channels*100:.1f}%)")
        print(f"  - 総登録者数: {total_subscribers:,}")
        print(f"  - 平均エンゲージメント推定値: {avg_engagement:.2f}%")
        
        print(f"\n📋 収集チャンネル一覧:")
        print("-"*80)
        
        # 登録者数でソート
        sorted_channels = sorted(self.collected_data, key=lambda x: x['subscriber_count'], reverse=True)
        
        for i, channel in enumerate(sorted_channels, 1):
            print(f"{i:2d}. {channel['channel_title']}")
            print(f"     登録者: {channel['subscriber_count']:,}人")
            print(f"     エンゲージメント推定: {channel['engagement_estimate']:.2f}%")
            print(f"     メールアドレス: {len(channel['emails'])}件")
            if channel['emails']:
                print(f"     連絡先: {', '.join(channel['emails'][:2])}")  # 最初の2件表示
            print()
        
        print("="*80)
        print("🎉 データ収集完了！")
    
    def save_to_json(self, filename="gaming_youtubers.json"):
        """結果をJSONファイルに保存"""
        if not self.collected_data:
            print("❌ No data to save")
            return
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.collected_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 データを {filename} に保存しました")
            
        except Exception as e:
            print(f"❌ Failed to save data: {e}")


def main():
    """メイン実行関数"""
    collector = SimpleYouTubeCollector(YOUTUBE_API_KEY)
    
    try:
        # データ収集実行
        channels = collector.collect_gaming_youtubers()
        
        if channels:
            # JSONファイルに保存
            collector.save_to_json()
            
            # 成功メッセージ
            print(f"\n✅ 成功: {len(channels)} 件のゲーム系YouTuberデータを収集しました")
            print("📄 結果は gaming_youtubers.json に保存されました")
            
        else:
            print("❌ データ収集に失敗しました")
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")


if __name__ == "__main__":
    main()