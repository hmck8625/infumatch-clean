#!/usr/bin/env python3
"""
拡張版ビジネス系YouTubeチャンネル収集スクリプト

@description より多くのビジネス系チャンネルを収集し30個達成を目指す
"""

import json
import asyncio
import re
from datetime import datetime
from googleapiclient.discovery import build

# 設定
YOUTUBE_API_KEY = "AIzaSyDtPl5WSRdxk744ha5Tlwno4iTBZVO96r4"

def search_expanded_business_channels():
    """拡張ビジネス系チャンネル検索・収集"""
    service = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    
    # 拡張版ビジネス系検索クエリ（検索数を増やし、フィルタ条件を緩和）
    business_queries = [
        # 有名ビジネス系YouTuber（拡張）
        "両学長", "中田敦彦", "堀江貴文", "西野亮廣", "前澤友作",
        "竹花貴騎", "鴨頭嘉人", "マナブ", "迫佑樹", "イケハヤ",
        "与沢翼", "青汁王子", "ひろゆき", "DaiGo", "成田悠輔",
        "年商10億", "年商100億", "社長", "CEO", "経営者",
        
        # 投資・資産運用（拡張）
        "高橋ダン", "バフェット太郎", "投資の達人", "BANK ACADEMY", "つみたてシータ",
        "長期投資", "株式投資", "資産運用", "投資信託", "NISA",
        "iDeCo", "FX", "仮想通貨", "不動産投資", "節税",
        "資産形成", "お金", "投資", "株", "債券", "金融",
        
        # 起業・副業（拡張）
        "起業", "副業", "フリーランス", "独立", "スタートアップ",
        "ビジネスモデル", "マーケティング", "セールス", "営業",
        "コンサル", "せどり", "転売", "アフィリエイト", "ブログ",
        "YouTube 稼ぐ", "ネットビジネス", "MLM", "情報商材",
        
        # 自己啓発・スキルアップ（拡張）
        "自己啓発", "スキルアップ", "キャリア", "転職", "働き方",
        "プログラミング", "デザイン", "英語", "勉強法", "読書",
        "習慣", "時間術", "生産性", "効率化", "成功法則",
        
        # 業界・職種特化
        "IT ビジネス", "Web ビジネス", "EC ビジネス", "D2C", "SaaS",
        "AI ビジネス", "DX", "デジタル変革", "新規事業", "イノベーション",
        "コンサルティング", "会計", "税理士", "中小企業診断士"
    ]
    
    print("🚀 拡張版ビジネス系YouTubeチャンネル収集開始")
    print(f"🔍 {len(business_queries)} クエリで検索中...")
    
    all_channels = []
    channel_ids_seen = set()
    
    for i, query in enumerate(business_queries, 1):
        try:
            print(f"[{i}/{len(business_queries)}] 検索: '{query}'")
            
            # チャンネル検索（結果数を増やす）
            search_response = service.search().list(
                part='snippet',
                type='channel',
                q=query,
                maxResults=5,  # 2から5に増加
                order='relevance',
                regionCode='JP',
                relevanceLanguage='ja'
            ).execute()
            
            found_in_query = 0
            for item in search_response.get('items', []):
                channel_id = item['id']['channelId']
                if channel_id not in channel_ids_seen:
                    channel_ids_seen.add(channel_id)
                    
                    # サムネイルURL取得
                    thumbnail_url = None
                    thumbnails = item['snippet'].get('thumbnails', {})
                    if thumbnails:
                        for quality in ['maxres', 'high', 'medium', 'default']:
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
                    found_in_query += 1
                    print(f"  ✅ 発見: {item['snippet']['title']}")
            
            if found_in_query == 0:
                print(f"  📭 なし")
        
        except Exception as e:
            print(f"  ❌ エラー: {e}")
            continue
    
    print(f"\n📊 検索完了: {len(all_channels)} チャンネル発見")
    
    # 詳細データ取得（フィルタ条件を緩和）
    if all_channels:
        print("\n📊 詳細データ取得中...")
        detailed_channels = get_channel_details_relaxed(service, all_channels)
        
        # 30チャンネルまで選択
        if len(detailed_channels) > 30:
            # 登録者数順でソート
            detailed_channels = sorted(detailed_channels, key=lambda x: x['subscriber_count'], reverse=True)[:30]
        
        print(f"📊 最終選択: {len(detailed_channels)} チャンネル")
        
        # ファイル保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"business_channels_expanded_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(detailed_channels, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 保存完了: {filename}")
        print(f"🎉 収集成功: {len(detailed_channels)} チャンネル")
        
        # 統計表示
        print_stats(detailed_channels)
        
        return detailed_channels
    
    return []

def get_channel_details_relaxed(service, channels):
    """チャンネル詳細情報取得（条件緩和版）"""
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
                
                # 登録者数フィルタを5000人に緩和
                if subscriber_count < 5000:
                    continue
                
                # 元データからサムネイルURL取得
                original_channel = next((ch for ch in channels if ch['channel_id'] == item['id']), None)
                if not original_channel:
                    continue
                
                # メール抽出
                description = snippet.get('description', '')
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, description)
                
                # ビジネス系キーワードチェック（条件緩和）
                business_keywords = [
                    '投資', '起業', '副業', 'ビジネス', '経営', 'マーケティング', '資産運用', 'お金', 
                    '株式', 'FX', 'NISA', 'iDeCo', '不動産', 'フリーランス', '自己啓発', 'スキルアップ', 
                    'キャリア', '転職', '働き方', '成功', '稼ぐ', '収入', '売上', '利益', '節税',
                    '仮想通貨', 'せどり', '転売', 'アフィリエイト', 'ブログ', 'YouTube', 'SNS',
                    'コンサル', '社長', 'CEO', '経営者', '企業', '会社', '事業', 'プロジェクト',
                    'DX', 'IT', 'Web', 'デジタル', 'AI', 'プログラミング', 'デザイン', '英語'
                ]
                
                title_lower = snippet.get('title', '').lower()
                desc_lower = description.lower()
                
                is_business_related = (
                    any(keyword in desc_lower for keyword in business_keywords) or
                    any(keyword in title_lower for keyword in business_keywords) or
                    # チャンネル名でもチェック
                    any(word in title_lower for word in ['ビジネス', '投資', '起業', '副業', '経営', 'マネー', 'お金', 'アカデミー', '大学', '学校'])
                )
                
                # ビジネス関連チェックを緩和（疑わしいものも含める）
                if not is_business_related:
                    # 検索クエリがビジネス系なら含める
                    query = original_channel.get('search_query', '').lower()
                    business_query_words = ['投資', 'ビジネス', '起業', '副業', '経営', 'お金', '株式', '資産']
                    if any(word in query for word in business_query_words):
                        is_business_related = True
                
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
                    'search_query': original_channel.get('search_query'),
                    'category': 'ビジネス',
                    'is_business_verified': is_business_related
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
    
    print("\n" + "=" * 60)
    print("📊 拡張版ビジネス系チャンネル収集統計")
    print("=" * 60)
    
    total_subscribers = sum(ch['subscriber_count'] for ch in channels)
    total_videos = sum(ch['video_count'] for ch in channels)
    channels_with_email = sum(1 for ch in channels if ch['has_contact'])
    channels_with_thumbnail = sum(1 for ch in channels if ch['thumbnail_url'])
    business_verified = sum(1 for ch in channels if ch['is_business_verified'])
    
    print(f"📈 総登録者数: {total_subscribers:,}人")
    print(f"🎬 総動画数: {total_videos:,}本")
    print(f"📧 メール有り: {channels_with_email}/{len(channels)} ({channels_with_email/len(channels)*100:.1f}%)")
    print(f"🖼️ サムネイル有り: {channels_with_thumbnail}/{len(channels)} ({channels_with_thumbnail/len(channels)*100:.1f}%)")
    print(f"🏢 ビジネス系確認済み: {business_verified}/{len(channels)} ({business_verified/len(channels)*100:.1f}%)")
    
    # 上位チャンネル表示
    sorted_channels = sorted(channels, key=lambda x: x['subscriber_count'], reverse=True)
    print(f"\n🏆 登録者数TOP15:")
    for i, channel in enumerate(sorted_channels[:15], 1):
        verified_mark = "✅" if channel['is_business_verified'] else "⚠️"
        print(f"  {i:2d}. {channel['channel_title']}: {channel['subscriber_count']:,}人 {verified_mark}")

if __name__ == "__main__":
    search_expanded_business_channels()