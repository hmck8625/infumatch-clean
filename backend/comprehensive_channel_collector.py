#!/usr/bin/env python3
"""
包括的YouTubeチャンネル収集・登録システム

@description AI分析付きでYouTubeチャンネルを収集し、Firestore・BigQueryに自動登録
@author InfuMatch Development Team
@version 3.0.0
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

class ComprehensiveChannelCollector:
    """
    包括的YouTubeチャンネル収集・登録システム
    
    機能:
    1. YouTube API経由でチャンネル検索・取得
    2. AI分析による高度な分析
    3. Firestore自動登録
    4. BigQuery自動同期
    5. 進捗管理・エラーハンドリング
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
    
    def extract_emails_from_description(self, description: str) -> List[str]:
        """概要欄からメールアドレスを抽出"""
        if not description:
            return []
        
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, description)
        return list(set(emails))  # 重複除去
    
    async def search_channels_by_category(self, category: str, search_queries: List[str], target_count: int = 35) -> List[Dict[str, Any]]:
        """カテゴリ別チャンネル検索"""
        print(f"\n🔍 {category}系チャンネル検索開始")
        print(f"📋 検索クエリ: {len(search_queries)} 件")
        print(f"🎯 目標収集数: {target_count} チャンネル")
        
        all_channels = []
        seen_channel_ids = set()
        
        for i, query in enumerate(search_queries, 1):
            try:
                print(f"  {i:2d}. '{query}' 検索中...")
                
                search_request = self.service.search().list(
                    part='snippet',
                    q=query,
                    type='channel',
                    regionCode='JP',
                    relevanceLanguage='ja',
                    order='relevance',
                    maxResults=min(50, target_count // len(search_queries) + 10)
                )
                
                search_response = search_request.execute()
                
                for item in search_response.get('items', []):
                    channel_id = item['id']['channelId']
                    if channel_id not in seen_channel_ids:
                        seen_channel_ids.add(channel_id)
                        all_channels.append({
                            'channel_id': channel_id,
                            'channel_title': item['snippet']['title'],
                            'description': item['snippet']['description'],
                            'query_source': query
                        })
                
                print(f"     ✅ {len(search_response.get('items', []))} 件発見")
                
                # レート制限対応
                await asyncio.sleep(0.5)
                
            except HttpError as e:
                print(f"     ❌ 検索エラー: {e}")
                self.stats['errors'] += 1
                continue
        
        self.stats['searched'] = len(all_channels)
        print(f"\n📊 検索結果: {len(all_channels)} チャンネル発見")
        
        return all_channels[:target_count]
    
    async def get_channel_details_with_ai(self, channels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """チャンネル詳細取得 + AI分析"""
        print(f"\n🤖 {len(channels)} チャンネルの詳細取得 + AI分析中...")
        
        enhanced_channels = []
        
        # チャンネルIDを抽出
        channel_ids = [ch['channel_id'] for ch in channels]
        
        try:
            # バッチで詳細取得
            details_request = self.service.channels().list(
                part='snippet,statistics',
                id=','.join(channel_ids[:50])  # API制限対応
            )
            details_response = details_request.execute()
            
            for item in details_response.get('items', []):
                try:
                    # 基本データ抽出
                    channel_id = item['id']
                    snippet = item['snippet']
                    statistics = item['statistics']
                    
                    subscriber_count = int(statistics.get('subscriberCount', 0))
                    video_count = int(statistics.get('videoCount', 0))
                    view_count = int(statistics.get('viewCount', 0))
                    
                    # フィルタリング（マイクロインフルエンサー: 10K-500K）
                    if not (10000 <= subscriber_count <= 500000):
                        continue
                    
                    # メール抽出
                    description = snippet.get('description', '')
                    emails = self.extract_emails_from_description(description)
                    
                    # エンゲージメント推定
                    engagement_estimate = (subscriber_count / video_count * 100) if video_count > 0 else 0
                    
                    # 基本チャンネルデータ
                    channel_data = {
                        'channel_id': channel_id,
                        'channel_title': snippet.get('title', ''),
                        'description': description,
                        'subscriber_count': subscriber_count,
                        'video_count': video_count,
                        'view_count': view_count,
                        'country': snippet.get('country', 'JP'),
                        'emails': emails,
                        'has_contact': len(emails) > 0,
                        'engagement_estimate': round(engagement_estimate, 2),
                        'collected_at': datetime.now(timezone.utc).isoformat()
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
                    self.stats['analyzed'] += 1
                    
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
    
    def convert_to_firestore_format(self, channel_data: Dict[str, Any]) -> Dict[str, Any]:
        """Firestore形式に変換"""
        ai_analysis = channel_data.get('ai_analysis', {})
        brand_safety = ai_analysis.get('brand_safety', {})
        category_tags = ai_analysis.get('category_tags', {})
        product_matching = ai_analysis.get('product_matching', {})
        
        return {
            'channel_id': channel_data['channel_id'],
            'channel_title': channel_data['channel_title'],
            'description': channel_data['description'],
            'subscriber_count': channel_data['subscriber_count'],
            'video_count': channel_data['video_count'],
            'view_count': channel_data['view_count'],
            'category': channel_data.get('category', '未分類'),
            'country': channel_data.get('country', 'JP'),
            'language': 'ja',
            'contact_info': {
                'emails': channel_data.get('emails', []),
                'primary_email': channel_data.get('emails', [None])[0] if channel_data.get('emails') else None
            },
            'engagement_metrics': {
                'engagement_rate': channel_data.get('engagement_estimate', 0) / 100,
                'avg_views_per_video': channel_data['view_count'] / channel_data['video_count'] if channel_data['video_count'] > 0 else 0,
                'has_contact': channel_data.get('has_contact', False)
            },
            'ai_analysis': {
                'engagement_rate': channel_data.get('engagement_estimate', 0) / 100,
                'content_quality_score': 0.8,
                'brand_safety_score': brand_safety.get('overall_safety_score', 0.8),
                'growth_potential': 0.7,
                'full_analysis': ai_analysis,
                'advanced': {
                    'enhanced_at': datetime.now(timezone.utc).isoformat(),
                    'category': category_tags.get('primary_category', '未分類'),
                    'sub_categories': category_tags.get('sub_categories', []),
                    'content_themes': category_tags.get('content_themes', []),
                    'safety_score': brand_safety.get('overall_safety_score', 0.8),
                    'confidence': ai_analysis.get('analysis_confidence', 0.5),
                    'target_age': category_tags.get('target_age_group', '不明'),
                    'top_product': product_matching.get('recommended_products', [{}])[0].get('category', '未定') if product_matching.get('recommended_products') else '未定',
                    'match_score': product_matching.get('recommended_products', [{}])[0].get('match_score', 0.5) if product_matching.get('recommended_products') else 0.5
                }
            },
            'status': 'active',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'last_analyzed': channel_data.get('collected_at', datetime.now(timezone.utc).isoformat()),
            'fetched_at': channel_data.get('collected_at', datetime.now(timezone.utc).isoformat()),
            'data_source': 'youtube_api',
            'collection_method': 'comprehensive_ai_enhanced'
        }
    
    async def save_to_firestore(self, channels: List[Dict[str, Any]]) -> bool:
        """Firestoreに保存"""
        print(f"\n🔥 Firestoreに {len(channels)} チャンネルを保存中...")
        
        success_count = 0
        
        for i, channel_data in enumerate(channels, 1):
            try:
                # Firestore形式に変換
                firestore_doc = self.convert_to_firestore_format(channel_data)
                
                # 既存チェック
                doc_ref = self.firestore_db.collection('influencers').document(firestore_doc['channel_id'])
                existing_doc = doc_ref.get()
                
                if existing_doc.exists:
                    print(f"⚠️  {i:2d}. {firestore_doc['channel_title']} (既存データをスキップ)")
                    continue
                
                # Firestoreに保存
                doc_ref.set(firestore_doc)
                
                print(f"✅ {i:2d}. {firestore_doc['channel_title']} (登録者: {firestore_doc['subscriber_count']:,})")
                success_count += 1
                
            except Exception as e:
                print(f"❌ {i:2d}. Firestore保存失敗 ({channel_data.get('channel_title', 'Unknown')}): {e}")
                self.stats['errors'] += 1
                continue
        
        self.stats['saved_firestore'] = success_count
        print(f"\n📊 Firestore保存結果: {success_count}/{len(channels)} 件成功")
        
        return success_count > 0
    
    def convert_to_bigquery_format(self, channel_data: Dict[str, Any]) -> Dict[str, Any]:
        """BigQuery形式に変換"""
        ai_analysis = channel_data.get('ai_analysis', {})
        
        return {
            'influencer_id': channel_data['channel_id'],
            'channel_id': channel_data['channel_id'],
            'channel_title': channel_data['channel_title'],
            'description': channel_data['description'][:1000],  # BigQuery文字列長制限
            'subscriber_count': channel_data['subscriber_count'],
            'video_count': channel_data['video_count'],
            'view_count': channel_data['view_count'],
            'category': channel_data.get('category', '未分類'),
            'country': channel_data.get('country', 'JP'),
            'language': 'ja',
            'contact_email': channel_data.get('emails', [None])[0] if channel_data.get('emails') else None,
            'social_links': json.dumps({'emails': channel_data.get('emails', [])}),
            'ai_analysis_json': json.dumps(ai_analysis),
            'brand_safety_score': ai_analysis.get('brand_safety', {}).get('overall_safety_score', 0.8),
            'analysis_confidence': ai_analysis.get('analysis_confidence', 0.5),
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'is_active': True
        }
    
    async def save_to_bigquery(self, channels: List[Dict[str, Any]]) -> bool:
        """BigQueryに保存"""
        print(f"\n🏗️ BigQueryに {len(channels)} チャンネルを保存中...")
        
        try:
            # テーブル参照を取得
            dataset_id = "infumatch_data"  # 実際に使用中のデータセット
            table_id = "influencers"
            
            # テーブル存在確認・作成
            table_ref = self.bigquery_client.dataset(dataset_id).table(table_id)
            
            try:
                table = self.bigquery_client.get_table(table_ref)
                print(f"✅ BigQueryテーブル確認: {dataset_id}.{table_id}")
            except Exception:
                print(f"⚠️ BigQueryテーブル {dataset_id}.{table_id} が存在しません。スキップします。")
                return False
            
            # データ変換
            rows_to_insert = []
            for channel_data in channels:
                bq_row = self.convert_to_bigquery_format(channel_data)
                rows_to_insert.append(bq_row)
            
            # BigQueryに挿入
            errors = self.bigquery_client.insert_rows_json(table, rows_to_insert)
            
            if not errors:
                self.stats['saved_bigquery'] = len(rows_to_insert)
                print(f"✅ BigQuery保存成功: {len(rows_to_insert)} 件")
                return True
            else:
                print(f"❌ BigQuery保存エラー: {errors}")
                self.stats['errors'] += 1
                return False
                
        except Exception as e:
            print(f"❌ BigQuery保存失敗: {e}")
            self.stats['errors'] += 1
            return False
    
    def save_to_json(self, channels: List[Dict[str, Any]], filename: str):
        """JSONファイルに保存（バックアップ用）"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(channels, f, ensure_ascii=False, indent=2)
            print(f"💾 JSONバックアップ保存: {filename}")
        except Exception as e:
            print(f"❌ JSON保存失敗: {e}")
    
    async def collect_category_channels(self, category: str, search_queries: List[str], target_count: int = 35) -> List[Dict[str, Any]]:
        """カテゴリ別チャンネル収集"""
        print(f"\n{'='*80}")
        print(f"🚀 {category}系チャンネル収集開始")
        print(f"{'='*80}")
        
        # 1. チャンネル検索
        channels = await self.search_channels_by_category(category, search_queries, target_count)
        
        if not channels:
            print(f"❌ {category}系チャンネルが見つかりません")
            return []
        
        # 2. 詳細取得 + AI分析
        enhanced_channels = await self.get_channel_details_with_ai(channels)
        
        if not enhanced_channels:
            print(f"❌ {category}系チャンネルの詳細取得に失敗")
            return []
        
        # 3. データベース保存
        await self.save_to_firestore(enhanced_channels)
        await self.save_to_bigquery(enhanced_channels)
        
        # 4. JSONバックアップ
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{category.lower()}_channels_{timestamp}.json"
        self.save_to_json(enhanced_channels, filename)
        
        self.collected_channels.extend(enhanced_channels)
        
        return enhanced_channels
    
    def print_results_summary(self):
        """結果サマリー表示"""
        print(f"\n{'='*80}")
        print(f"🎯 収集結果サマリー")
        print(f"{'='*80}")
        
        print(f"📊 統計情報:")
        print(f"  - 検索発見: {self.stats['searched']} チャンネル")
        print(f"  - フィルタ後: {self.stats['filtered']} チャンネル") 
        print(f"  - AI分析完了: {self.stats['analyzed']} チャンネル")
        print(f"  - Firestore保存: {self.stats['saved_firestore']} チャンネル")
        print(f"  - BigQuery保存: {self.stats['saved_bigquery']} チャンネル")
        print(f"  - エラー数: {self.stats['errors']}")
        
        if self.collected_channels:
            # カテゴリ分布
            categories = {}
            total_subscribers = 0
            avg_safety = 0
            avg_confidence = 0
            
            for channel in self.collected_channels:
                cat = channel.get('category', '未分類')
                categories[cat] = categories.get(cat, 0) + 1
                total_subscribers += channel.get('subscriber_count', 0)
                avg_safety += channel.get('brand_safety_score', 0)
                avg_confidence += channel.get('analysis_confidence', 0)
            
            total_count = len(self.collected_channels)
            avg_safety = avg_safety / total_count if total_count > 0 else 0
            avg_confidence = avg_confidence / total_count if total_count > 0 else 0
            
            print(f"\n📋 カテゴリ分布:")
            for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                print(f"  - {category}: {count} チャンネル")
            
            print(f"\n📈 品質指標:")
            print(f"  - 総登録者数: {total_subscribers:,} 人")
            print(f"  - 平均安全性スコア: {avg_safety:.2f}")
            print(f"  - 平均AI信頼度: {avg_confidence:.2f}")

# カテゴリ別検索クエリ定義
SEARCH_QUERIES = {
    'ゲーム': [
        "ゲーム実況", "実況プレイ", "ゲーム配信", "マインクラフト 実況",
        "フォートナイト 実況", "エーペックス 実況", "ゲーム攻略",
        "gaming japan", "日本 ゲーム実況", "ゲーム実況者"
    ],
    'ビジネス': [
        "ビジネス 起業", "経営 コンサル", "投資 株式", "副業 稼ぐ",
        "マーケティング 戦略", "経済 解説", "フリーランス 独立",
        "business japan", "転職 キャリア", "資産運用 投資"
    ],
    '料理': [
        "料理 レシピ", "クッキング 簡単", "グルメ 食べ物", "お弁当 作り方",
        "お菓子作り スイーツ", "和食 日本料理", "家庭料理 時短",
        "cooking japan", "ベーキング パン", "食材 節約"
    ]
}

async def main():
    """メイン実行関数"""
    collector = ComprehensiveChannelCollector()
    
    print("🤖 包括的YouTubeチャンネル収集・登録システム")
    print("=" * 60)
    print("機能: AI分析 + Firestore + BigQuery自動登録")
    print()
    
    try:
        # 各カテゴリのチャンネルを収集
        for category, queries in SEARCH_QUERIES.items():
            await collector.collect_category_channels(category, queries, target_count=35)
            
            # カテゴリ間の休憩
            print(f"\n⏱️ 次のカテゴリまで5秒休憩...")
            await asyncio.sleep(5)
        
        # 最終結果表示
        collector.print_results_summary()
        
        print(f"\n🎉 すべての収集が完了しました！")
        
    except Exception as e:
        print(f"❌ 収集処理エラー: {e}")
        collector.print_results_summary()

if __name__ == "__main__":
    asyncio.run(main())