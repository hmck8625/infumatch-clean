#!/usr/bin/env python3
"""
AI分析統合YouTube収集システム

@description データ取得時にリアルタイムでAI分析を実行
- カテゴリタグ自動付与
- チャンネル概要の構造化 
- 商材マッチング分析

@author InfuMatch Development Team
@version 2.0.0
"""

import os
import json
import asyncio
import re
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# AI分析サービスをインポート
from services.ai_channel_analyzer import AdvancedChannelAnalyzer

# 設定
YOUTUBE_API_KEY = "AIzaSyDtPl5WSRdxk744ha5Tlwno4iTBZVO96r4"
PROJECT_ID = "hackathon-462905"


class EnhancedYouTubeCollector:
    """
    AI分析統合YouTubeデータ収集クラス
    
    データ取得と同時にAI分析を実行し、
    高付加価値なインフルエンサーデータを生成
    """
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.service = build('youtube', 'v3', developerKey=api_key)
        self.ai_analyzer = AdvancedChannelAnalyzer()
        self.collected_data = []
    
    def extract_emails_from_description(self, description):
        """概要欄からメールアドレスを抽出"""
        if not description:
            return []
        
        email_pattern = r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b'
        emails = re.findall(email_pattern, description)
        return list(set(emails))
    
    def search_channels_by_keywords(self, search_queries, max_results=5):
        """キーワードベースのチャンネル検索"""
        try:
            print(f"🔍 AI分析統合チャンネル検索開始")
            
            all_channels = []
            channel_ids_seen = set()
            
            for query in search_queries:
                print(f"   検索クエリ: '{query}'")
                
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
                            'search_query': query
                        }
                        all_channels.append(channel_data)
            
            print(f"   ✅ 発見: {len(all_channels)} チャンネル")
            return all_channels
            
        except HttpError as e:
            print(f"❌ YouTube API エラー: {e}")
            return []
        except Exception as e:
            print(f"❌ 検索失敗: {e}")
            return []
    
    async def get_channel_details_with_ai(self, channels):
        """チャンネル詳細取得 + AI分析"""
        try:
            channel_ids = [ch['channel_id'] for ch in channels]
            print(f"📊 {len(channel_ids)} チャンネルの詳細取得 + AI分析中...")
            
            # YouTube API でチャンネル詳細取得
            channels_response = self.service.channels().list(
                part='snippet,statistics,contentDetails',
                id=','.join(channel_ids)
            ).execute()
            
            enhanced_channels = []
            
            for item in channels_response.get('items', []):
                try:
                    snippet = item.get('snippet', {})
                    statistics = item.get('statistics', {})
                    
                    # 基本データ取得
                    subscriber_count = int(statistics.get('subscriberCount', 0))
                    video_count = int(statistics.get('videoCount', 0))
                    view_count = int(statistics.get('viewCount', 0))
                    
                    # フィルタリング: 1万〜50万人
                    if not (10000 <= subscriber_count <= 500000):
                        continue
                    
                    # サムネイルURL取得
                    thumbnail_url = None
                    thumbnails = snippet.get('thumbnails', {})
                    if thumbnails:
                        # 高画質から順に取得を試みる
                        for quality in ['maxres', 'high', 'medium', 'default']:
                            if quality in thumbnails:
                                thumbnail_url = thumbnails[quality].get('url')
                                break
                    
                    # 基本チャンネルデータ
                    channel_data = {
                        'channel_id': item['id'],
                        'channel_title': snippet.get('title', ''),
                        'description': snippet.get('description', ''),
                        'subscriber_count': subscriber_count,
                        'video_count': video_count,
                        'view_count': view_count,
                        'country': snippet.get('country', 'JP'),
                        'thumbnail_url': thumbnail_url,
                        'emails': self.extract_emails_from_description(snippet.get('description', '')),
                        'has_contact': len(self.extract_emails_from_description(snippet.get('description', ''))) > 0,
                        'engagement_estimate': round((view_count / video_count / subscriber_count) * 100, 2) if video_count > 0 and subscriber_count > 0 else 0,
                        'collected_at': datetime.now().isoformat()
                    }
                    
                    # 🤖 AI分析実行
                    print(f"🤖 AI分析中: {channel_data['channel_title']}")
                    ai_analysis = await self.ai_analyzer.analyze_channel_comprehensive(channel_data)
                    
                    # AI分析結果を統合
                    enhanced_channel = {
                        **channel_data,
                        'ai_analysis': ai_analysis,
                        'category': ai_analysis.get('category_tags', {}).get('primary_category', '未分類'),
                        'sub_categories': ai_analysis.get('category_tags', {}).get('sub_categories', []),
                        'content_themes': ai_analysis.get('category_tags', {}).get('content_themes', []),
                        'recommended_products': ai_analysis.get('product_matching', {}).get('recommended_products', []),
                        'brand_safety_score': ai_analysis.get('brand_safety', {}).get('overall_safety_score', 0.8),
                        'analysis_confidence': ai_analysis.get('analysis_confidence', 0.5)
                    }
                    
                    enhanced_channels.append(enhanced_channel)
                    
                    # 結果表示
                    print(f"✅ 完了: {channel_data['channel_title']}")
                    print(f"   📊 登録者: {subscriber_count:,}")
                    print(f"   🎯 カテゴリ: {enhanced_channel['category']}")
                    print(f"   🛡️ 安全性: {enhanced_channel['brand_safety_score']:.2f}")
                    print(f"   📈 信頼度: {enhanced_channel['analysis_confidence']:.2f}")
                    if enhanced_channel['recommended_products']:
                        top_product = enhanced_channel['recommended_products'][0]
                        print(f"   💼 推奨商材: {top_product.get('category', 'N/A')}")
                    print()
                    
                except Exception as e:
                    print(f"❌ チャンネル処理エラー ({item.get('id', 'Unknown')}): {e}")
                    continue
            
            return enhanced_channels
            
        except HttpError as e:
            print(f"❌ YouTube API エラー: {e}")
            return []
        except Exception as e:
            print(f"❌ 詳細取得失敗: {e}")
            return []
    
    async def collect_ai_enhanced_channels(self, search_queries, target_count=10):
        """AI分析統合チャンネル収集"""
        print("🚀 AI分析統合YouTuberデータ収集開始")
        print("=" * 80)
        
        print("🔧 実行内容:")
        print("  1. YouTube APIでチャンネル検索")
        print("  2. 基本データ取得・フィルタリング")
        print("  3. Gemini AIによる包括的分析")
        print("     - カテゴリタグ自動付与")
        print("     - チャンネル概要構造化")
        print("     - 商材マッチング分析")
        print("     - オーディエンス分析")
        print("     - ブランドセーフティ評価")
        print()
        
        # チャンネル検索
        all_channels = self.search_channels_by_keywords(search_queries, max_results=5)
        
        if not all_channels:
            print("❌ チャンネルが見つかりません")
            return []
        
        # AI分析付き詳細取得
        enhanced_channels = await self.get_channel_details_with_ai(all_channels)
        
        # 結果を制限
        self.collected_data = enhanced_channels[:target_count]
        
        # 結果表示
        self.print_enhanced_results()
        
        return self.collected_data
    
    def print_enhanced_results(self):
        """AI分析結果を含む詳細表示"""
        if not self.collected_data:
            print("❌ 収集データがありません")
            return
        
        print("\\n" + "=" * 100)
        print("🎯 AI分析統合収集結果")
        print("=" * 100)
        
        total_channels = len(self.collected_data)
        channels_with_email = sum(1 for ch in self.collected_data if ch['has_contact'])
        total_subscribers = sum(ch['subscriber_count'] for ch in self.collected_data)
        avg_confidence = sum(ch['analysis_confidence'] for ch in self.collected_data) / total_channels if total_channels > 0 else 0
        avg_safety = sum(ch['brand_safety_score'] for ch in self.collected_data) / total_channels if total_channels > 0 else 0
        
        print(f"📊 統計情報:")
        print(f"  - 収集チャンネル数: {total_channels}")
        print(f"  - 連絡可能チャンネル: {channels_with_email} ({channels_with_email/total_channels*100:.1f}%)")
        print(f"  - 総登録者数: {total_subscribers:,}")
        print(f"  - 平均AI信頼度: {avg_confidence:.2f}")
        print(f"  - 平均ブランド安全性: {avg_safety:.2f}")
        
        # カテゴリ別統計
        categories = {}
        for ch in self.collected_data:
            cat = ch['category']
            if cat not in categories:
                categories[cat] = 0
            categories[cat] += 1
        
        print(f"\\n📋 カテゴリ分布:")
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {category}: {count}チャンネル")
        
        print(f"\\n📋 詳細結果:")
        print("-" * 100)
        
        # 信頼度順でソート
        sorted_channels = sorted(self.collected_data, key=lambda x: x['analysis_confidence'], reverse=True)
        
        for i, channel in enumerate(sorted_channels, 1):
            print(f"{i:2d}. {channel['channel_title']}")
            print(f"     📊 登録者: {channel['subscriber_count']:,}人")
            print(f"     🎯 カテゴリ: {channel['category']}")
            if channel['sub_categories']:
                print(f"     🏷️ サブカテゴリ: {', '.join(channel['sub_categories'])}")
            if channel['content_themes']:
                print(f"     📝 テーマ: {', '.join(channel['content_themes'][:3])}")
            print(f"     🛡️ 安全性: {channel['brand_safety_score']:.2f}")
            print(f"     📈 AI信頼度: {channel['analysis_confidence']:.2f}")
            
            if channel['recommended_products']:
                top_products = channel['recommended_products'][:2]
                products_str = ', '.join([p.get('category', 'N/A') for p in top_products])
                print(f"     💼 推奨商材: {products_str}")
            
            if channel['emails']:
                print(f"     📧 連絡先: {', '.join(channel['emails'][:1])}")
            print()
        
        print("=" * 100)
        print("🎉 AI分析統合データ収集完了！")
    
    def save_enhanced_data(self, filename="ai_enhanced_youtubers.json"):
        """AI分析結果を含むデータ保存"""
        if not self.collected_data:
            print("❌ 保存するデータがありません")
            return
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.collected_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 AI分析結果を {filename} に保存しました")
            
            # サマリーファイルも作成
            summary = {
                "collection_timestamp": datetime.now().isoformat(),
                "total_channels": len(self.collected_data),
                "analysis_summary": {
                    "avg_confidence": sum(ch['analysis_confidence'] for ch in self.collected_data) / len(self.collected_data),
                    "avg_brand_safety": sum(ch['brand_safety_score'] for ch in self.collected_data) / len(self.collected_data),
                    "categories": list(set(ch['category'] for ch in self.collected_data)),
                    "contact_rate": sum(1 for ch in self.collected_data if ch['has_contact']) / len(self.collected_data)
                }
            }
            
            with open('ai_analysis_summary.json', 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            print(f"📊 分析サマリーを ai_analysis_summary.json に保存しました")
            
        except Exception as e:
            print(f"❌ データ保存失敗: {e}")


async def main():
    """メイン実行関数"""
    collector = EnhancedYouTubeCollector(YOUTUBE_API_KEY)
    
    # ゲーム系チャンネル検索クエリ
    test_queries = [
        "ゲーム実況",
        "実況プレイ",
        "ゲーム配信",
        "マインクラフト 実況",
        "フォートナイト 実況",
        "エーペックス 実況",
        "ゲーム攻略",
        "gaming japan",
        "日本 ゲーム実況",
        "ゲーム実況者"
    ]
    
    try:
        print("🤖 AI分析統合YouTuber収集システム")
        print("=" * 60)
        print("実行内容: 検索 → 詳細取得 → AI分析 → 結果保存")
        print()
        
        # AI分析付きデータ収集
        channels = await collector.collect_ai_enhanced_channels(test_queries, target_count=33)
        
        if channels:
            # データ保存
            collector.save_enhanced_data()
            
            print(f"\\n✅ 成功: {len(channels)} 件のAI分析済みYouTuberデータを収集")
            print("📄 結果は ai_enhanced_youtubers.json に保存されました")
            print("📊 サマリーは ai_analysis_summary.json に保存されました")
            
        else:
            print("❌ データ収集に失敗しました")
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")


if __name__ == "__main__":
    asyncio.run(main())