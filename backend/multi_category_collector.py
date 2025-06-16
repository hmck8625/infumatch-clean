#!/usr/bin/env python3
"""
多カテゴリYouTuber収集スクリプト

@description 複数カテゴリから20チャンネル程度のYouTuberを収集
ゲーム以外のカテゴリも含めて多様性のあるデータを取得

@author InfuMatch Development Team
@version 1.0.0
"""

import os
import json
import re
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# 設定
YOUTUBE_API_KEY = "AIzaSyDtPl5WSRdxk744ha5Tlwno4iTBZVO96r4"
PROJECT_ID = "hackathon-462905"

class MultiCategoryYouTubeCollector:
    """多カテゴリYouTube データ収集クラス"""
    
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
    
    def is_category_related(self, title, description, category_keywords):
        """カテゴリ関連かどうかを判定"""
        text = (title + ' ' + description).lower()
        return any(keyword.lower() in text for keyword in category_keywords)
    
    def search_channels_by_category(self, category_name, search_queries, max_results=5):
        """カテゴリ別チャンネル検索"""
        try:
            print(f"\n🔍 {category_name} カテゴリの検索開始")
            
            all_channels = []
            channel_ids_seen = set()
            
            for query in search_queries:
                print(f"   検索クエリ: '{query}'")
                
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
                
                for item in search_response.get('items', []):
                    channel_id = item['id']['channelId']
                    if channel_id not in channel_ids_seen:
                        channel_ids_seen.add(channel_id)
                        channel_data = {
                            'channel_id': channel_id,
                            'title': item['snippet']['title'],
                            'description': item['snippet']['description'],
                            'thumbnail': item['snippet']['thumbnails'].get('high', {}).get('url'),
                            'search_query': query,
                            'category': category_name
                        }
                        all_channels.append(channel_data)
            
            print(f"   ✅ {category_name}: {len(all_channels)} チャンネル発見")
            return all_channels
            
        except HttpError as e:
            print(f"   ❌ {category_name} 検索エラー: {e}")
            return []
        except Exception as e:
            print(f"   ❌ {category_name} 検索失敗: {e}")
            return []
    
    def get_channel_details(self, channels, category_keywords):
        """チャンネル詳細情報を取得"""
        try:
            channel_ids = [ch['channel_id'] for ch in channels]
            print(f"📊 {len(channel_ids)} チャンネルの詳細情報を取得中...")
            
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
                
                # フィルタリング: 1万〜50万人（範囲を拡大）
                if not (10000 <= subscriber_count <= 500000):
                    continue
                
                # 元のカテゴリ情報を取得
                original_channel = next(ch for ch in channels if ch['channel_id'] == item['id'])
                category_name = original_channel['category']
                
                # カテゴリ関連かチェック（緩い条件）
                if category_keywords and not self.is_category_related(
                    snippet.get('title', ''), 
                    snippet.get('description', ''), 
                    category_keywords
                ):
                    continue
                
                # メールアドレス抽出
                emails = self.extract_emails_from_description(snippet.get('description', ''))
                
                # サムネイルURL取得
                thumbnail_url = original_channel.get('thumbnail')  # 検索時に取得したサムネイル使用
                if not thumbnail_url:
                    # フォールバック: 詳細データからサムネイル取得
                    thumbnails = snippet.get('thumbnails', {})
                    if thumbnails:
                        for quality in ['maxres', 'high', 'medium', 'default']:
                            if quality in thumbnails:
                                thumbnail_url = thumbnails[quality].get('url')
                                break
                
                channel_data = {
                    'channel_id': item['id'],
                    'channel_title': snippet.get('title', ''),
                    'description': snippet.get('description', ''),
                    'subscriber_count': subscriber_count,
                    'video_count': video_count,
                    'view_count': view_count,
                    'country': snippet.get('country', 'JP'),
                    'category': category_name,
                    'thumbnail_url': thumbnail_url,
                    'emails': emails,
                    'has_contact': len(emails) > 0,
                    'engagement_estimate': round((view_count / video_count / subscriber_count) * 100, 2) if video_count > 0 and subscriber_count > 0 else 0,
                    'collected_at': datetime.now().isoformat()
                }
                
                detailed_channels.append(channel_data)
                print(f"✅ {snippet.get('title', 'Unknown')}: {subscriber_count:,} 登録者, {len(emails)} メール")
            
            return detailed_channels
            
        except HttpError as e:
            print(f"❌ YouTube API エラー: {e}")
            return []
        except Exception as e:
            print(f"❌ 詳細取得失敗: {e}")
            return []
    
    def collect_multi_category_youtubers(self):
        """複数カテゴリのYouTuberデータを収集"""
        print("🎯 多カテゴリYouTuber データ収集開始")
        print("=" * 80)
        
        # カテゴリ定義
        categories = {
            "料理・グルメ": {
                "queries": ["料理", "レシピ", "グルメ", "お菓子作り", "料理チャンネル"],
                "keywords": ["料理", "レシピ", "cooking", "グルメ", "お菓子", "food"]
            },
            "美容・コスメ": {
                "queries": ["メイク", "コスメ", "美容", "スキンケア", "ヘアアレンジ"],
                "keywords": ["メイク", "コスメ", "beauty", "美容", "スキンケア", "化粧"]
            },
            "ライフスタイル": {
                "queries": ["日常", "ライフスタイル", "暮らし", "ルーティン", "生活"],
                "keywords": ["日常", "ライフスタイル", "暮らし", "ルーティン", "生活", "lifestyle"]
            },
            "教育・学習": {
                "queries": ["勉強", "学習", "教育", "解説", "講座"],
                "keywords": ["勉強", "学習", "教育", "解説", "講座", "tutorial"]
            },
            "音楽": {
                "queries": ["歌ってみた", "演奏", "音楽", "カバー", "弾いてみた"],
                "keywords": ["歌", "演奏", "音楽", "music", "カバー", "弾いてみた"]
            },
            "エンタメ・バラエティ": {
                "queries": ["バラエティ", "エンタメ", "面白", "コメディ", "企画"],
                "keywords": ["バラエティ", "エンタメ", "面白", "comedy", "企画", "entertainment"]
            }
        }
        
        all_channels = []
        
        # 各カテゴリからチャンネルを検索
        for category_name, category_info in categories.items():
            channels = self.search_channels_by_category(
                category_name, 
                category_info["queries"], 
                max_results=4
            )
            
            if channels:
                # 詳細情報を取得
                detailed_channels = self.get_channel_details(channels, category_info["keywords"])
                all_channels.extend(detailed_channels)
                
                # 目標の20チャンネルに近づいたら停止
                if len(all_channels) >= 20:
                    break
        
        # 重複除去（念のため）
        seen_ids = set()
        unique_channels = []
        for channel in all_channels:
            if channel['channel_id'] not in seen_ids:
                seen_ids.add(channel['channel_id'])
                unique_channels.append(channel)
        
        self.collected_data = unique_channels[:20]  # 最大20チャンネル
        
        # 結果表示
        self.print_collection_results()
        
        return self.collected_data
    
    def print_collection_results(self):
        """収集結果を表示"""
        if not self.collected_data:
            print("❌ データ収集できませんでした")
            return
        
        print("\n" + "=" * 100)
        print("🎯 多カテゴリ収集結果サマリー")
        print("=" * 100)
        
        total_channels = len(self.collected_data)
        channels_with_email = sum(1 for ch in self.collected_data if ch['has_contact'])
        total_subscribers = sum(ch['subscriber_count'] for ch in self.collected_data)
        avg_engagement = sum(ch['engagement_estimate'] for ch in self.collected_data) / total_channels if total_channels > 0 else 0
        
        # カテゴリ別集計
        category_stats = {}
        for channel in self.collected_data:
            cat = channel['category']
            if cat not in category_stats:
                category_stats[cat] = {'count': 0, 'with_email': 0}
            category_stats[cat]['count'] += 1
            if channel['has_contact']:
                category_stats[cat]['with_email'] += 1
        
        print(f"📊 統計情報:")
        print(f"  - 収集チャンネル数: {total_channels}")
        print(f"  - 連絡可能チャンネル: {channels_with_email} ({channels_with_email/total_channels*100:.1f}%)")
        print(f"  - 総登録者数: {total_subscribers:,}")
        print(f"  - 平均エンゲージメント推定値: {avg_engagement:.2f}%")
        
        print(f"\n📋 カテゴリ別統計:")
        for category, stats in category_stats.items():
            print(f"  - {category}: {stats['count']}チャンネル (連絡可能: {stats['with_email']})")
        
        print(f"\n📋 収集チャンネル一覧:")
        print("-" * 100)
        
        # カテゴリ別にソート、その後登録者数順
        sorted_channels = sorted(
            self.collected_data, 
            key=lambda x: (x['category'], -x['subscriber_count'])
        )
        
        current_category = None
        for i, channel in enumerate(sorted_channels, 1):
            if current_category != channel['category']:
                current_category = channel['category']
                print(f"\n🎭 {current_category}")
                print("-" * 60)
            
            print(f"{i:2d}. {channel['channel_title']}")
            print(f"     登録者: {channel['subscriber_count']:,}人")
            print(f"     エンゲージメント推定: {channel['engagement_estimate']:.2f}%")
            print(f"     メールアドレス: {len(channel['emails'])}件")
            if channel['emails']:
                print(f"     連絡先: {', '.join(channel['emails'][:2])}")  # 最初の2件表示
            print()
        
        print("=" * 100)
        print("🎉 多カテゴリデータ収集完了！")
    
    def save_to_json(self, filename="multi_category_youtubers.json"):
        """結果をJSONファイルに保存"""
        if not self.collected_data:
            print("❌ 保存するデータがありません")
            return
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.collected_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 データを {filename} に保存しました")
            
        except Exception as e:
            print(f"❌ データ保存失敗: {e}")

def main():
    """メイン実行関数"""
    collector = MultiCategoryYouTubeCollector(YOUTUBE_API_KEY)
    
    try:
        # データ収集実行
        channels = collector.collect_multi_category_youtubers()
        
        if channels:
            # JSONファイルに保存
            collector.save_to_json()
            
            # 成功メッセージ
            print(f"\n✅ 成功: {len(channels)} 件の多カテゴリYouTuberデータを収集しました")
            print("📄 結果は multi_category_youtubers.json に保存されました")
            
        else:
            print("❌ データ収集に失敗しました")
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    main()