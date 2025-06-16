#!/usr/bin/env python3
"""
有名日本YouTubeチャンネル収集スクリプト

@description 日本で人気の高い有名チャンネルを収集してDB保存
サムネイル付きAI分析データとしてFirestore・BigQueryに蓄積

@author InfuMatch Development Team
@version 1.0.0
"""

import os
import json
import asyncio
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.cloud import firestore
from google.cloud import bigquery

# AI分析サービスをインポート
from services.ai_channel_analyzer import AdvancedChannelAnalyzer

# 設定
YOUTUBE_API_KEY = "AIzaSyDtPl5WSRdxk744ha5Tlwno4iTBZVO96r4"
PROJECT_ID = "hackathon-462905"

class FamousJapaneseChannelCollector:
    """
    有名日本チャンネル収集・登録システム
    
    機能:
    1. 有名チャンネルの戦略的検索
    2. AI分析による高度な分析
    3. サムネイル付きデータ収集
    4. Firestore・BigQuery自動登録
    """
    
    def __init__(self, api_key: str = YOUTUBE_API_KEY):
        self.api_key = api_key
        self.service = build('youtube', 'v3', developerKey=api_key)
        self.ai_analyzer = AdvancedChannelAnalyzer()
        
        # データベースクライアント初期化
        self.firestore_db = firestore.Client(project=PROJECT_ID)
        self.bigquery_client = bigquery.Client(project=PROJECT_ID)
        
        # 収集データ
        self.collected_channels = []
        self.stats = {
            'searched': 0,
            'filtered': 0,
            'analyzed': 0,
            'saved_firestore': 0,
            'saved_bigquery': 0,
            'errors': 0
        }
    
    def get_famous_search_queries(self) -> List[Dict[str, Any]]:
        """有名チャンネル収集用の戦略的検索クエリ"""
        return [
            # メガ級YouTuber
            {"queries": ["ヒカキン", "はじめしゃちょー", "フィッシャーズ", "東海オンエア"], "category": "エンタメ"},
            {"queries": ["水溜りボンド", "すしらーめん", "コムドット"], "category": "エンタメ"},
            
            # ゲーム系有名チャンネル  
            {"queries": ["ポッキー", "マインクラフト 実況", "加藤純一", "もこう"], "category": "ゲーム"},
            {"queries": ["兄者弟者", "キヨ", "レトルト"], "category": "ゲーム"},
            
            # 料理・グルメ有名チャンネル
            {"queries": ["リュウジ バズレシピ", "きまぐれクック", "谷やん", "料理研究家"], "category": "料理"},
            {"queries": ["大食い", "木下ゆうか", "大胃王"], "category": "料理"},
            
            # 美容・ファッション
            {"queries": ["佐々木あさひ", "美容系", "メイク", "スキンケア"], "category": "美容"},
            {"queries": ["コスメ レビュー", "化粧品", "美容"], "category": "美容"},
            
            # ビジネス・教育
            {"queries": ["中田敞彦", "オリラジ", "両学長", "投資"], "category": "教育"},
            {"queries": ["ビジネス", "副業", "起業", "経済"], "category": "教育"},
            
            # 音楽・エンタメ
            {"queries": ["Official髭男dism", "あいみょん", "米津玄師", "YOASOBI"], "category": "音楽"},
            {"queries": ["歌ってみた", "踊ってみた", "ボカロ"], "category": "音楽"},
            
            # テクノロジー・レビュー
            {"queries": ["瀬戸弘司", "カズ", "iPhone", "ガジェット"], "category": "テクノロジー"},
            {"queries": ["レビュー", "開封", "Apple", "Android"], "category": "テクノロジー"},
            
            # ライフスタイル・VLOG
            {"queries": ["kemio", "古川優香", "関根理沙", "ライフスタイル"], "category": "ライフスタイル"},
            {"queries": ["vlog", "日常", "ルーティン"], "category": "ライフスタイル"}
        ]
    
    def extract_emails_from_description(self, description: str) -> List[str]:
        """概要欄からメールアドレスを抽出"""
        if not description:
            return []
        
        email_pattern = r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b'
        emails = re.findall(email_pattern, description)
        return list(set(emails))
    
    def search_famous_channels(self, search_queries: List[str], category: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """有名チャンネル検索"""
        try:
            print(f"🔍 {category} 有名チャンネル検索開始")
            
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
                            'search_query': query,
                            'category': category
                        }
                        all_channels.append(channel_data)
            
            print(f"   ✅ {category}: {len(all_channels)} チャンネル発見")
            self.stats['searched'] += len(all_channels)
            return all_channels
            
        except HttpError as e:
            print(f"❌ {category} 検索エラー: {e}")
            self.stats['errors'] += 1
            return []
        except Exception as e:
            print(f"❌ {category} 検索失敗: {e}")
            self.stats['errors'] += 1
            return []
    
    async def get_channel_details_with_ai(self, channels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
                    
                    # フィルタリング: 1万人以上（有名チャンネルなので下限引き下げ）
                    if subscriber_count < 10000:
                        continue
                    
                    # 元のカテゴリ情報を取得
                    original_channel = next(ch for ch in channels if ch['channel_id'] == item['id'])
                    category_name = original_channel['category']
                    
                    # サムネイルURL（詳細データから再取得）
                    thumbnail_url = original_channel.get('thumbnail_url')
                    if not thumbnail_url:
                        thumbnails = snippet.get('thumbnails', {})
                        if thumbnails:
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
                        'collected_at': datetime.now().isoformat(),
                        'collection_method': 'famous_channels_targeted'
                    }
                    
                    # 🤖 AI分析実行
                    print(f"🤖 AI分析中: {channel_data['channel_title']}")
                    ai_analysis = await self.ai_analyzer.analyze_channel_comprehensive(channel_data)
                    
                    # AI分析結果を統合
                    enhanced_channel = {
                        **channel_data,
                        'ai_analysis': ai_analysis,
                        'category': ai_analysis.get('category_tags', {}).get('primary_category', category_name),
                        'sub_categories': ai_analysis.get('category_tags', {}).get('sub_categories', []),
                        'content_themes': ai_analysis.get('category_tags', {}).get('content_themes', []),
                        'recommended_products': ai_analysis.get('product_matching', {}).get('recommended_products', []),
                        'brand_safety_score': ai_analysis.get('brand_safety', {}).get('overall_safety_score', 0.8),
                        'analysis_confidence': ai_analysis.get('analysis_confidence', 0.5)
                    }
                    
                    enhanced_channels.append(enhanced_channel)
                    self.stats['analyzed'] += 1
                    
                    # 結果表示
                    print(f"✅ 完了: {channel_data['channel_title']}")
                    print(f"   📊 登録者: {subscriber_count:,}")
                    print(f"   🎯 カテゴリ: {enhanced_channel['category']}")
                    print(f"   🛡️ 安全性: {enhanced_channel['brand_safety_score']:.2f}")
                    print(f"   📈 信頼度: {enhanced_channel['analysis_confidence']:.2f}")
                    if enhanced_channel['thumbnail_url']:
                        print(f"   🖼️ サムネイル: ✅")
                    if enhanced_channel['recommended_products']:
                        top_product = enhanced_channel['recommended_products'][0]
                        print(f"   💼 推奨商材: {top_product.get('category', 'N/A')}")
                    print()
                    
                except Exception as e:
                    print(f"❌ チャンネル処理エラー ({item.get('id', 'Unknown')}): {e}")
                    self.stats['errors'] += 1
                    continue
            
            self.stats['filtered'] = len(enhanced_channels)
            return enhanced_channels
            
        except HttpError as e:
            print(f"❌ YouTube API エラー: {e}")
            self.stats['errors'] += 1
            return []
        except Exception as e:
            print(f"❌ 詳細取得失敗: {e}")
            self.stats['errors'] += 1
            return []
    
    async def save_to_firestore(self, channels: List[Dict[str, Any]]) -> bool:
        """Firestoreに保存"""
        try:
            print(f"🔥 Firestoreに {len(channels)} チャンネルを保存中...")
            
            collection_ref = self.firestore_db.collection('influencers')
            
            for i, channel in enumerate(channels, 1):
                try:
                    # 既存データ確認
                    existing_query = collection_ref.where('channel_id', '==', channel['channel_id']).limit(1)
                    existing_docs = list(existing_query.stream())
                    
                    if existing_docs:
                        # 更新
                        doc_ref = existing_docs[0].reference
                        doc_ref.update({
                            **channel,
                            'updated_at': datetime.now(timezone.utc).isoformat(),
                            'data_source': 'famous_channels_collection'
                        })
                        print(f"🔄 更新: {i}. {channel['channel_title']} (登録者: {channel['subscriber_count']:,})")
                    else:
                        # 新規作成
                        doc_ref = collection_ref.document(channel['channel_id'])
                        doc_ref.set({
                            **channel,
                            'created_at': datetime.now(timezone.utc).isoformat(),
                            'updated_at': datetime.now(timezone.utc).isoformat(),
                            'data_source': 'famous_channels_collection',
                            'status': 'active'
                        })
                        print(f"✅ 新規: {i}. {channel['channel_title']} (登録者: {channel['subscriber_count']:,})")
                    
                    self.stats['saved_firestore'] += 1
                    
                except Exception as e:
                    print(f"❌ Firestore保存エラー ({channel.get('channel_title', 'Unknown')}): {e}")
                    self.stats['errors'] += 1
                    continue
            
            print(f"✅ Firestore保存完了: {self.stats['saved_firestore']} 件")
            return True
            
        except Exception as e:
            print(f"❌ Firestore保存失敗: {e}")
            self.stats['errors'] += 1
            return False
    
    async def save_to_bigquery(self, channels: List[Dict[str, Any]]) -> bool:
        """BigQueryに保存"""
        try:
            print(f"🏗️ BigQueryに {len(channels)} チャンネルを保存中...")
            
            # テーブル参照
            dataset_ref = self.bigquery_client.dataset('infumatch_data')
            table_ref = dataset_ref.table('influencers')
            
            # データ変換
            rows_to_insert = []
            for channel in channels:
                try:
                    row = {
                        'influencer_id': channel['channel_id'],
                        'channel_id': channel['channel_id'],
                        'channel_title': channel['channel_title'],
                        'description': channel.get('description', '')[:1000],  # BigQuery制限対応
                        'subscriber_count': channel['subscriber_count'],
                        'video_count': channel['video_count'],
                        'view_count': channel['view_count'],
                        'category': channel.get('category', ''),
                        'country': channel.get('country', 'JP'),
                        'language': 'ja',
                        'contact_email': channel['emails'][0] if channel['emails'] else None,
                        'thumbnail_url': channel.get('thumbnail_url'),
                        'ai_analysis_json': json.dumps(channel.get('ai_analysis', {}), ensure_ascii=False),
                        'brand_safety_score': channel.get('brand_safety_score', 0.0),
                        'analysis_confidence': channel.get('analysis_confidence', 0.0),
                        'created_at': datetime.now(timezone.utc),
                        'updated_at': datetime.now(timezone.utc),
                        'is_active': True
                    }
                    rows_to_insert.append(row)
                    
                except Exception as e:
                    print(f"❌ BigQuery行変換エラー ({channel.get('channel_title', 'Unknown')}): {e}")
                    self.stats['errors'] += 1
                    continue
            
            # バッチ挿入
            errors = self.bigquery_client.insert_rows_json(table_ref, rows_to_insert)
            
            if errors:
                print(f"❌ BigQuery挿入エラー: {errors}")
                self.stats['errors'] += len(errors)
                return False
            else:
                self.stats['saved_bigquery'] = len(rows_to_insert)
                print(f"✅ BigQuery保存成功: {self.stats['saved_bigquery']} 件")
                return True
                
        except Exception as e:
            print(f"❌ BigQuery保存失敗: {e}")
            self.stats['errors'] += 1
            return False
    
    def save_backup_file(self, channels: List[Dict[str, Any]], filename: str = None) -> str:
        """バックアップファイル保存"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"famous_japanese_channels_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(channels, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"💾 バックアップ保存: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ バックアップ保存失敗: {e}")
            return ""
    
    def print_final_stats(self):
        """最終統計表示"""
        print("\\n" + "=" * 80)
        print("🎯 有名日本チャンネル収集完了サマリー")
        print("=" * 80)
        
        print(f"📊 統計情報:")
        print(f"  - 検索発見: {self.stats['searched']} チャンネル")
        print(f"  - フィルタ後: {self.stats['filtered']} チャンネル")
        print(f"  - AI分析完了: {self.stats['analyzed']} チャンネル")
        print(f"  - Firestore保存: {self.stats['saved_firestore']} チャンネル")
        print(f"  - BigQuery保存: {self.stats['saved_bigquery']} チャンネル")
        print(f"  - エラー数: {self.stats['errors']}")
        
        if self.collected_channels:
            print(f"\\n📋 収集チャンネル概要:")
            categories = {}
            total_subscribers = 0
            channels_with_thumbnails = 0
            
            for channel in self.collected_channels:
                cat = channel.get('category', '未分類')
                if cat not in categories:
                    categories[cat] = 0
                categories[cat] += 1
                
                total_subscribers += channel.get('subscriber_count', 0)
                if channel.get('thumbnail_url'):
                    channels_with_thumbnails += 1
            
            print(f"  - 総登録者数: {total_subscribers:,}人")
            print(f"  - サムネイル取得率: {channels_with_thumbnails}/{len(self.collected_channels)} ({channels_with_thumbnails/len(self.collected_channels)*100:.1f}%)")
            
            print(f"\\n📂 カテゴリ分布:")
            for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                print(f"  - {category}: {count} チャンネル")
        
        print("\\n🎉 有名チャンネル収集・DB保存が完了しました！")
        print("=" * 80)

    async def collect_famous_channels(self, target_count: int = 30) -> List[Dict[str, Any]]:
        """有名日本チャンネル包括収集"""
        print("🚀 有名日本YouTubeチャンネル収集開始")
        print("=" * 80)
        
        print("🎯 実行内容:")
        print("  1. 戦略的キーワードで有名チャンネル検索")
        print("  2. サムネイル付き詳細データ取得")
        print("  3. Gemini AIによる包括的分析")
        print("  4. Firestore・BigQuery自動保存")
        print("  5. 品質管理・統計表示")
        print()
        
        # 検索クエリ取得
        search_categories = self.get_famous_search_queries()
        
        all_channels = []
        collected_count = 0
        
        for category_data in search_categories:
            if collected_count >= target_count:
                break
                
            queries = category_data["queries"]
            category = category_data["category"]
            
            # チャンネル検索
            found_channels = self.search_famous_channels(queries, category, max_results=3)
            all_channels.extend(found_channels)
            
            collected_count = len(all_channels)
            print(f"   進捗: {collected_count}/{target_count} チャンネル")
        
        if not all_channels:
            print("❌ チャンネルが見つかりません")
            return []
        
        # 上位チャンネルに絞り込み
        selected_channels = all_channels[:target_count]
        print(f"\\n📊 選択: {len(selected_channels)} チャンネル（目標: {target_count}）")
        
        # AI分析付き詳細取得
        enhanced_channels = await self.get_channel_details_with_ai(selected_channels)
        
        if not enhanced_channels:
            print("❌ 有効なチャンネルが見つかりません")
            return []
        
        self.collected_channels = enhanced_channels
        
        # データベース保存
        print(f"\\n💾 データベース保存開始...")
        firestore_success = await self.save_to_firestore(enhanced_channels)
        bigquery_success = await self.save_to_bigquery(enhanced_channels)
        
        # バックアップ保存
        backup_file = self.save_backup_file(enhanced_channels)
        
        # 統計表示
        self.print_final_stats()
        
        return enhanced_channels


async def main():
    """メイン実行関数"""
    collector = FamousJapaneseChannelCollector()
    
    try:
        # 30チャンネル収集実行
        channels = await collector.collect_famous_channels(target_count=30)
        
        if channels:
            print(f"\\n🎉 収集成功: {len(channels)} チャンネル")
            print("データベース保存完了！")
        else:
            print("\\n❌ 収集失敗")
            
    except Exception as e:
        print(f"\\n❌ 実行エラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())