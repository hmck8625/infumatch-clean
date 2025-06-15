#!/usr/bin/env python3
"""
10チャンネル追加スクリプト（重複チェック付き）

@description channel_idによる重複チェックを行いながら10チャンネルを追加
@author InfuMatch Development Team
@version 1.0.0
"""

import os
import json
import asyncio
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.cloud import firestore
from google.cloud import bigquery

# AI分析サービスをインポート
from services.ai_channel_analyzer import AdvancedChannelAnalyzer

# 設定
YOUTUBE_API_KEY = "AIzaSyDtPl5WSRdxk744ha5Tlwno4iTBZVO96r4"
PROJECT_ID = "hackathon-462905"

class TenChannelAdder:
    """
    10チャンネル追加システム（重複チェック付き）
    """
    
    def __init__(self, api_key: str = YOUTUBE_API_KEY):
        self.api_key = api_key
        self.service = build('youtube', 'v3', developerKey=api_key)
        self.ai_analyzer = AdvancedChannelAnalyzer()
        
        # データベースクライアント初期化
        self.firestore_db = firestore.Client(project=PROJECT_ID)
        self.bigquery_client = bigquery.Client(project=PROJECT_ID)
        
        # 既存チャンネルID追跡
        self.existing_channel_ids: Set[str] = set()
        
        # 収集データ
        self.added_channels = []
        self.stats = {
            'searched': 0,
            'duplicates_skipped': 0,
            'analyzed': 0,
            'saved_firestore': 0,
            'saved_bigquery': 0,
            'errors': 0
        }
    
    async def load_existing_channel_ids(self):
        """既存チャンネルIDを読み込み"""
        print("🔍 既存チャンネルID読み込み中...")
        
        try:
            # Firestoreから既存チャンネルID取得
            collection_ref = self.firestore_db.collection('influencers')
            docs = collection_ref.get()
            
            for doc in docs:
                data = doc.to_dict()
                channel_id = data.get('channel_id')
                if channel_id:
                    self.existing_channel_ids.add(channel_id)
            
            print(f"✅ 既存チャンネルID読み込み完了: {len(self.existing_channel_ids)} 件")
            
        except Exception as e:
            print(f"❌ 既存チャンネルID読み込みエラー: {e}")
    
    def extract_emails_from_description(self, description: str) -> List[str]:
        """概要欄からメールアドレスを抽出"""
        if not description:
            return []
        
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, description)
        return list(set(emails))  # 重複除去
    
    async def search_additional_channels(self, target_count: int = 20) -> List[Dict[str, Any]]:
        """追加チャンネル検索（重複チェック付き）"""
        print(f"\n🔍 追加チャンネル検索開始（目標: {target_count} 件発見）")
        
        # 追加検索クエリ（既存とは異なるキーワード）
        additional_queries = [
            "健康 ダイエット", "筋トレ フィットネス", "ヨガ エクササイズ",
            "DIY 手作り", "ガーデニング 園芸", "ペット 動物",
            "アニメ レビュー", "映画 感想", "本 読書",
            "旅行 観光", "温泉 グルメ", "カフェ スイーツ",
            "プログラミング 技術", "英語 学習", "資格 勉強"
        ]
        
        found_channels = []
        seen_in_search = set()
        
        for i, query in enumerate(additional_queries, 1):
            try:
                print(f"  {i:2d}. '{query}' 検索中...")
                
                search_request = self.service.search().list(
                    part='snippet',
                    q=query,
                    type='channel',
                    regionCode='JP',
                    relevanceLanguage='ja',
                    order='relevance',
                    maxResults=10
                )
                
                search_response = search_request.execute()
                new_found = 0
                
                for item in search_response.get('items', []):
                    channel_id = item['id']['channelId']
                    
                    # 重複チェック（既存 + 今回検索分）
                    if channel_id not in self.existing_channel_ids and channel_id not in seen_in_search:
                        seen_in_search.add(channel_id)
                        found_channels.append({
                            'channel_id': channel_id,
                            'channel_title': item['snippet']['title'],
                            'description': item['snippet']['description'],
                            'query_source': query
                        })
                        new_found += 1
                
                print(f"     ✅ 新規発見: {new_found} 件")
                self.stats['searched'] += len(search_response.get('items', []))
                
                # 目標数に達したら終了
                if len(found_channels) >= target_count:
                    break
                
                # レート制限対応
                await asyncio.sleep(0.5)
                
            except HttpError as e:
                print(f"     ❌ 検索エラー: {e}")
                self.stats['errors'] += 1
                continue
        
        print(f"\n📊 検索結果: {len(found_channels)} 件の新規チャンネル発見")
        return found_channels[:target_count]
    
    async def get_channel_details_with_ai(self, channels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """チャンネル詳細取得 + AI分析（重複チェック付き）"""
        print(f"\n🤖 {len(channels)} チャンネルの詳細取得 + AI分析中...")
        
        enhanced_channels = []
        channel_ids = [ch['channel_id'] for ch in channels]
        
        try:
            # バッチで詳細取得
            details_request = self.service.channels().list(
                part='snippet,statistics',
                id=','.join(channel_ids[:50])
            )
            details_response = details_request.execute()
            
            for item in details_response.get('items', []):
                try:
                    channel_id = item['id']
                    
                    # 最終重複チェック
                    if channel_id in self.existing_channel_ids:
                        print(f"⚠️ 重複スキップ: {item['snippet']['title']}")
                        self.stats['duplicates_skipped'] += 1
                        continue
                    
                    snippet = item['snippet']
                    statistics = item['statistics']
                    
                    subscriber_count = int(statistics.get('subscriberCount', 0))
                    video_count = int(statistics.get('videoCount', 0))
                    view_count = int(statistics.get('viewCount', 0))
                    
                    # フィルタリング（マイクロインフルエンサー: 10K-500K）
                    if not (10000 <= subscriber_count <= 500000):
                        print(f"📊 範囲外スキップ: {snippet['title']} (登録者: {subscriber_count:,})")
                        continue
                    
                    description = snippet.get('description', '')
                    emails = self.extract_emails_from_description(description)
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
                    self.existing_channel_ids.add(channel_id)  # 追加済みとしてマーク
                    self.stats['analyzed'] += 1
                    
                    # 結果表示
                    print(f"✅ 完了: {channel_data['channel_title']}")
                    print(f"   📊 登録者: {subscriber_count:,}")
                    print(f"   🎯 カテゴリ: {enhanced_channel['category']}")
                    print(f"   🛡️ 安全性: {enhanced_channel['brand_safety_score']:.2f}")
                    print()
                    
                    # 目標の10チャンネルに達したら終了
                    if len(enhanced_channels) >= 10:
                        break
                    
                except Exception as e:
                    print(f"❌ チャンネル処理エラー ({item.get('id', 'Unknown')}): {e}")
                    self.stats['errors'] += 1
                    continue
            
            return enhanced_channels
            
        except HttpError as e:
            print(f"❌ YouTube API エラー: {e}")
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
            'collection_method': 'additional_10_channels'
        }
    
    async def save_to_firestore(self, channels: List[Dict[str, Any]]) -> bool:
        """Firestoreに保存（重複チェック付き）"""
        print(f"\n🔥 Firestoreに {len(channels)} チャンネルを保存中...")
        
        success_count = 0
        
        for i, channel_data in enumerate(channels, 1):
            try:
                firestore_doc = self.convert_to_firestore_format(channel_data)
                
                # 既存チェック（最終確認）
                doc_ref = self.firestore_db.collection('influencers').document(firestore_doc['channel_id'])
                existing_doc = doc_ref.get()
                
                if existing_doc.exists:
                    print(f"⚠️  {i:2d}. {firestore_doc['channel_title']} (既存データをスキップ)")
                    self.stats['duplicates_skipped'] += 1
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
        """BigQuery形式に変換（現在のスキーマに合わせて）"""
        ai_analysis = channel_data.get('ai_analysis', {})
        
        # AI分析情報をsocial_linksフィールドに含める（JSON形式）
        extended_social_links = {
            'emails': channel_data.get('emails', []),
            'ai_analysis': ai_analysis,
            'brand_safety_score': ai_analysis.get('brand_safety', {}).get('overall_safety_score', 0.8),
            'analysis_confidence': ai_analysis.get('analysis_confidence', 0.5)
        }
        
        return {
            'influencer_id': channel_data['channel_id'],
            'channel_id': channel_data['channel_id'],
            'channel_title': channel_data['channel_title'],
            'description': channel_data['description'][:1000] if channel_data.get('description') else '',
            'subscriber_count': channel_data['subscriber_count'],
            'video_count': channel_data['video_count'],
            'view_count': channel_data['view_count'],
            'category': channel_data.get('category', '未分類'),
            'country': channel_data.get('country', 'JP'),
            'language': 'ja',
            'contact_email': channel_data.get('emails', [None])[0] if channel_data.get('emails') else None,
            'social_links': json.dumps(extended_social_links),
            'ai_analysis': json.dumps(ai_analysis),  # 専用のai_analysisフィールドを使用
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'is_active': True
        }
    
    async def save_to_bigquery(self, channels: List[Dict[str, Any]]) -> bool:
        """BigQueryに保存"""
        print(f"\n🏗️ BigQueryに {len(channels)} チャンネルを保存中...")
        
        try:
            dataset_id = "infumatch_data"
            table_id = "influencers"
            
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
        """JSONファイルに保存"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(channels, f, ensure_ascii=False, indent=2)
            print(f"💾 JSONバックアップ保存: {filename}")
        except Exception as e:
            print(f"❌ JSON保存失敗: {e}")
    
    def print_results_summary(self):
        """結果サマリー表示"""
        print(f"\n{'='*80}")
        print(f"🎯 10チャンネル追加結果")
        print(f"{'='*80}")
        
        print(f"📊 統計情報:")
        print(f"  - 検索実行: {self.stats['searched']} チャンネル")
        print(f"  - 重複スキップ: {self.stats['duplicates_skipped']} チャンネル")
        print(f"  - AI分析完了: {self.stats['analyzed']} チャンネル")
        print(f"  - Firestore保存: {self.stats['saved_firestore']} チャンネル")
        print(f"  - BigQuery保存: {self.stats['saved_bigquery']} チャンネル")
        print(f"  - エラー数: {self.stats['errors']}")
        
        if self.added_channels:
            print(f"\n📋 追加チャンネル:")
            for i, channel in enumerate(self.added_channels, 1):
                print(f"{i:2d}. {channel['channel_title']} (登録者: {channel['subscriber_count']:,}, カテゴリ: {channel.get('category', '未分類')})")

async def main():
    """メイン実行関数"""
    adder = TenChannelAdder()
    
    print("🤖 10チャンネル追加システム（重複チェック付き）")
    print("=" * 60)
    print("機能: channel_id重複チェック + AI分析 + 自動登録")
    print()
    
    try:
        # 1. 既存チャンネルID読み込み
        await adder.load_existing_channel_ids()
        
        # 2. 追加チャンネル検索
        channels = await adder.search_additional_channels(target_count=20)
        
        if not channels:
            print("❌ 新規チャンネルが見つかりません")
            return
        
        # 3. 詳細取得 + AI分析（10チャンネルまで）
        enhanced_channels = await adder.get_channel_details_with_ai(channels)
        
        if not enhanced_channels:
            print("❌ 条件に合うチャンネルが見つかりません")
            return
        
        adder.added_channels = enhanced_channels
        
        # 4. データベース保存
        await adder.save_to_firestore(enhanced_channels)
        await adder.save_to_bigquery(enhanced_channels)
        
        # 5. JSONバックアップ
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"additional_10_channels_{timestamp}.json"
        adder.save_to_json(enhanced_channels, filename)
        
        # 6. 結果表示
        adder.print_results_summary()
        
        print(f"\n🎉 10チャンネル追加が完了しました！")
        
    except Exception as e:
        print(f"❌ 追加処理エラー: {e}")
        adder.print_results_summary()

if __name__ == "__main__":
    asyncio.run(main())