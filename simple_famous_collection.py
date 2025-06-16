#!/usr/bin/env python3
"""
簡単版：有名日本YouTubeチャンネル収集
"""

import json
import asyncio
import re
from datetime import datetime
from googleapiclient.discovery import build

# 設定
YOUTUBE_API_KEY = "AIzaSyDtPl5WSRdxk744ha5Tlwno4iTBZVO96r4"

def search_famous_channels():
    """有名チャンネル検索・収集"""
    service = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    
    # 有名チャンネル検索クエリ
    famous_queries = [
        "ヒカキン", "はじめしゃちょー", "フィッシャーズ", "東海オンエア",
        "水溜りボンド", "コムドット", "リュウジ バズレシピ", "きまぐれクック",
        "佐々木あさひ", "中田敞彦", "瀬戸弘司", "兄者弟者",
        "木下ゆうか", "kemio", "古川優香", "Official髭男dism",
        "米津玄師", "YOASOBI", "ポッキー", "加藤純一"
    ]
    
    print("🚀 有名日本YouTubeチャンネル収集開始")
    print(f"🔍 {len(famous_queries)} クエリで検索中...")
    
    all_channels = []
    channel_ids_seen = set()
    
    for i, query in enumerate(famous_queries, 1):
        try:
            print(f"[{i}/{len(famous_queries)}] 検索: '{query}'")
            
            # チャンネル検索
            search_response = service.search().list(
                part='snippet',
                type='channel',
                q=query,
                maxResults=2,
                order='relevance',
                regionCode='JP',
                relevanceLanguage='ja'
            ).execute()
            
            for item in search_response.get('items', []):
                channel_id = item['id']['channelId']
                if channel_id not in channel_ids_seen:
                    channel_ids_seen.add(channel_id)
                    
                    # サムネイルURL取得
                    thumbnail_url = None
                    thumbnails = item['snippet'].get('thumbnails', {})
                    if thumbnails:
                        for quality in ['high', 'medium', 'default']:
                            if quality in thumbnails:
                                thumbnail_url = thumbnails[quality].get('url')
                                break
                    
                    channel_data = {
                        'channel_id': channel_id,
                        'title': item['snippet']['title'],
                        'description': item['snippet']['description'],
                        'thumbnail_url': thumbnail_url,
                        'search_query': query
                    }
                    all_channels.append(channel_data)
                    print(f"  ✅ 発見: {item['snippet']['title']}")
            
        except Exception as e:
            print(f"  ❌ エラー: {e}")
            continue
    
    print(f"\\n📊 検索完了: {len(all_channels)} チャンネル発見")
    
    # 詳細データ取得
    if all_channels:
        print("\\n📊 詳細データ取得中...")
        detailed_channels = get_channel_details(service, all_channels)
        
        # ファイル保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"famous_channels_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(detailed_channels, f, ensure_ascii=False, indent=2)
        
        print(f"\\n💾 保存完了: {filename}")
        print(f"🎉 収集成功: {len(detailed_channels)} チャンネル")
        
        # 統計表示
        print_stats(detailed_channels)
        
        return detailed_channels
    
    return []

def get_channel_details(service, channels):
    """チャンネル詳細情報取得"""
    channel_ids = [ch['channel_id'] for ch in channels]
    
    try:
        channels_response = service.channels().list(
            part='snippet,statistics,contentDetails',
            id=','.join(channel_ids)
        ).execute()
        
        detailed_channels = []
        
        for item in channels_response.get('items', []):
            try:
                snippet = item.get('snippet', {})
                statistics = item.get('statistics', {})
                
                subscriber_count = int(statistics.get('subscriberCount', 0))
                video_count = int(statistics.get('videoCount', 0))
                view_count = int(statistics.get('viewCount', 0))
                
                # 1万人以上のチャンネルのみ
                if subscriber_count < 10000:
                    continue
                
                # 元データからサムネイルURL取得
                original_channel = next(ch for ch in channels if ch['channel_id'] == item['id'])
                
                # メール抽出
                description = snippet.get('description', '')
                email_pattern = r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b'
                emails = re.findall(email_pattern, description)
                
                channel_data = {
                    'channel_id': item['id'],
                    'channel_title': snippet.get('title', ''),
                    'description': description,
                    'subscriber_count': subscriber_count,
                    'video_count': video_count,
                    'view_count': view_count,
                    'country': snippet.get('country', 'JP'),
                    'thumbnail_url': original_channel.get('thumbnail_url'),
                    'emails': emails,
                    'has_contact': len(emails) > 0,
                    'engagement_estimate': round((view_count / video_count / subscriber_count) * 100, 2) if video_count > 0 and subscriber_count > 0 else 0,
                    'collected_at': datetime.now().isoformat(),
                    'search_query': original_channel.get('search_query')
                }
                
                detailed_channels.append(channel_data)
                print(f"✅ {snippet.get('title', 'Unknown')}: {subscriber_count:,} 登録者")
                
            except Exception as e:
                print(f"❌ 処理エラー: {e}")
                continue
        
        return detailed_channels
        
    except Exception as e:
        print(f"❌ 詳細取得エラー: {e}")
        return []

def print_stats(channels):
    """統計情報表示"""
    if not channels:
        return
    
    print("\\n" + "=" * 60)
    print("📊 収集統計")
    print("=" * 60)
    
    total_subscribers = sum(ch['subscriber_count'] for ch in channels)
    total_videos = sum(ch['video_count'] for ch in channels)
    channels_with_email = sum(1 for ch in channels if ch['has_contact'])
    channels_with_thumbnail = sum(1 for ch in channels if ch['thumbnail_url'])
    
    print(f"📈 総登録者数: {total_subscribers:,}人")
    print(f"🎬 総動画数: {total_videos:,}本")
    print(f"📧 メール有り: {channels_with_email}/{len(channels)} ({channels_with_email/len(channels)*100:.1f}%)")
    print(f"🖼️ サムネイル有り: {channels_with_thumbnail}/{len(channels)} ({channels_with_thumbnail/len(channels)*100:.1f}%)")
    
    # 上位チャンネル表示
    sorted_channels = sorted(channels, key=lambda x: x['subscriber_count'], reverse=True)
    print(f"\\n🏆 登録者数TOP10:")
    for i, channel in enumerate(sorted_channels[:10], 1):
        print(f"  {i:2d}. {channel['channel_title']}: {channel['subscriber_count']:,}人")

if __name__ == "__main__":
    search_famous_channels()