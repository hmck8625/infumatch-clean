#!/usr/bin/env python3
"""
50ビジネス系チャンネル追加スクリプト

@description ビジネス・経済・起業系チャンネルを50件追加（重複チェック付き）
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

class BusinessChannelAdder:
    """
    50ビジネス系チャンネル追加システム（重複チェック付き）
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
        """既存チャンネルID読み込み"""
        print("🔍 既存チャンネルID読み込み中...")
        
        try:
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
        return list(set(emails))
    
    async def search_business_channels(self, target_count: int = 80) -> List[Dict[str, Any]]:
        """ビジネス系チャンネル検索（拡張版）"""
        print(f"\n🔍 ビジネス系チャンネル検索開始（目標: {target_count} 件発見）")
        
        # ビジネス系検索クエリ（大幅拡張）
        business_queries = [
            # 起業・経営系
            "起業 経営", "スタートアップ ベンチャー", "経営者 CEO", "ビジネス戦略",
            "会社経営 社長", "起業家 創業", "経営コンサルタント", "ビジネスモデル",
            
            # 投資・資産運用系
            "投資 株式", "資産運用 投資信託", "不動産投資", "FX 為替", 
            "仮想通貨 ビットコイン", "積立投資 NISA", "米国株投資", "個別株分析",
            
            # 副業・フリーランス系
            "副業 在宅ワーク", "フリーランス 独立", "ネットビジネス", "アフィリエイト",
            "YouTube収益化", "ブログ収益", "せどり 転売", "ウェブデザイン",
            
            # マーケティング・セールス系
            "マーケティング戦略", "デジタルマーケティング", "SNSマーケティング", "セールス営業",
            "ブランディング", "広告運用", "コンテンツマーケティング", "顧客獲得",
            
            # 自己啓発・スキルアップ系
            "自己啓発 成功法則", "時間管理 生産性", "読書 ビジネス書", "プレゼンテーション",
            "コミュニケーション", "リーダーシップ", "目標達成", "習慣化",
            
            # IT・テクノロジー系
            "プログラミング ビジネス", "AI ビジネス活用", "DX デジタル変革", "ITコンサルタント",
            "システム開発", "アプリ開発", "ウェブ開発", "データ分析",
            
            # 経済・金融系
            "経済解説 ニュース", "金融市場分析", "マクロ経済", "企業分析",
            "業界動向", "経済政策", "金融リテラシー", "保険 ライフプラン",
            
            # 転職・キャリア系
            "転職 キャリア", "就職活動 面接", "キャリアアップ", "スキル転職",
            "外資系転職", "IT転職", "管理職 昇進", "キャリアチェンジ",
            
            # 会計・税務系
            "会計 簿記", "税務 確定申告", "法人税", "相続税", "節税対策",
            "財務管理", "資金調達", "事業計画",
            
            # 英語ビジネス系
            "ビジネス英語", "英会話 仕事", "TOEIC ビジネス", "国際ビジネス",
            "海外進出", "グローバルビジネス", "外国人 ビジネス"
        ]
        
        found_channels = []
        seen_in_search = set()
        
        for i, query in enumerate(business_queries, 1):
            try:
                print(f"  {i:3d}. '{query}' 検索中...")
                
                search_request = self.service.search().list(
                    part='snippet',
                    q=query,
                    type='channel',
                    regionCode='JP',
                    relevanceLanguage='ja',
                    order='relevance',
                    maxResults=15  # より多くの候補を取得
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
                
                print(f"       ✅ 新規発見: {new_found} 件")
                self.stats['searched'] += len(search_response.get('items', []))
                
                # 目標数に達したら終了
                if len(found_channels) >= target_count:
                    print(f"🎯 目標数 {target_count} 件に到達！検索を終了します")
                    break
                
                # レート制限対応
                await asyncio.sleep(0.3)
                
            except HttpError as e:
                if "quotaExceeded" in str(e):
                    print(f"⚠️ YouTube APIクォータ制限に到達。現在 {len(found_channels)} 件取得済み")
                    break
                else:
                    print(f"     ❌ 検索エラー: {e}")
                    self.stats['errors'] += 1
                    continue
        
        print(f"\n📊 検索結果: {len(found_channels)} 件の新規ビジネス系チャンネル発見")
        return found_channels[:target_count]
    
    async def get_channel_details_with_ai(self, channels: List[Dict[str, Any]], target_final: int = 50) -> List[Dict[str, Any]]:
        """チャンネル詳細取得 + AI分析（ビジネス系特化）"""
        print(f"\n🤖 {len(channels)} チャンネルの詳細取得 + AI分析中（目標: {target_final} 件）...")
        
        enhanced_channels = []
        processed = 0
        
        # バッチサイズ調整（API制限対応）
        batch_size = 50
        
        for batch_start in range(0, len(channels), batch_size):
            batch_channels = channels[batch_start:batch_start + batch_size]
            channel_ids = [ch['channel_id'] for ch in batch_channels]
            
            try:
                # バッチで詳細取得
                details_request = self.service.channels().list(
                    part='snippet,statistics',
                    id=','.join(channel_ids)
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
                        
                        # ビジネス系カテゴリフィルタリング
                        detected_category = ai_analysis.get('category_tags', {}).get('primary_category', '').lower()
                        business_keywords = [
                            'ビジネス', 'business', '経済', '投資', '起業', '経営', 
                            '教育', 'education', 'howto', 'finance', 'マーケティング',
                            'コンサルティング', 'キャリア', '自己啓発'
                        ]
                        
                        is_business_related = any(keyword in detected_category for keyword in business_keywords)
                        
                        if not is_business_related:
                            # チャンネル説明からもビジネス関連性をチェック
                            description_lower = description.lower()
                            title_lower = channel_data['channel_title'].lower()
                            combined_text = f"{description_lower} {title_lower}"
                            
                            business_check_keywords = [
                                'ビジネス', 'business', '起業', '経営', '投資', '副業', 
                                'フリーランス', 'マーケティング', '経済', 'コンサル',
                                '資産運用', '転職', 'キャリア', '自己啓発', '成功'
                            ]
                            
                            is_business_related = any(keyword in combined_text for keyword in business_check_keywords)
                        
                        if not is_business_related:
                            print(f"📝 非ビジネス系スキップ: {channel_data['channel_title']} (カテゴリ: {detected_category})")
                            continue
                        
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
                        self.existing_channel_ids.add(channel_id)
                        self.stats['analyzed'] += 1
                        processed += 1
                        
                        # 結果表示
                        print(f"✅ 完了 {len(enhanced_channels):2d}: {channel_data['channel_title']}")
                        print(f"     📊 登録者: {subscriber_count:,}")
                        print(f"     🎯 カテゴリ: {enhanced_channel['category']}")
                        print(f"     🛡️ 安全性: {enhanced_channel['brand_safety_score']:.2f}")
                        if enhanced_channel['recommended_products']:
                            top_product = enhanced_channel['recommended_products'][0]
                            print(f"     💼 推奨商材: {top_product.get('category', 'N/A')}")
                        print()
                        
                        # 目標の50チャンネルに達したら終了
                        if len(enhanced_channels) >= target_final:
                            print(f"🎯 目標 {target_final} チャンネルに到達！分析を終了します")
                            return enhanced_channels
                        
                    except Exception as e:
                        print(f"❌ チャンネル処理エラー ({item.get('id', 'Unknown')}): {e}")
                        self.stats['errors'] += 1
                        continue
                
                # バッチ間の休憩
                if len(enhanced_channels) < target_final and batch_start + batch_size < len(channels):
                    print(f"⏱️ バッチ処理完了。3秒休憩...")
                    await asyncio.sleep(3)
                
            except HttpError as e:
                if "quotaExceeded" in str(e):
                    print(f"⚠️ YouTube APIクォータ制限。現在 {len(enhanced_channels)} 件分析済み")
                    break
                else:
                    print(f"❌ YouTube API エラー: {e}")
                    self.stats['errors'] += 1
                    continue
        
        print(f"\n📊 最終分析結果: {len(enhanced_channels)} 件のビジネス系チャンネル")
        return enhanced_channels
    
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
            'collection_method': 'business_50_channels'
        }
    
    async def save_to_firestore(self, channels: List[Dict[str, Any]]) -> bool:
        """Firestoreに保存"""
        print(f"\n🔥 Firestoreに {len(channels)} チャンネルを保存中...")
        
        success_count = 0
        
        for i, channel_data in enumerate(channels, 1):
            try:
                firestore_doc = self.convert_to_firestore_format(channel_data)
                
                # 既存チェック
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
        """BigQuery形式に変換"""
        ai_analysis = channel_data.get('ai_analysis', {})
        
        # AI分析情報をsocial_linksフィールドに含める
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
            'ai_analysis': json.dumps(ai_analysis),
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
        print(f"🎯 50ビジネス系チャンネル追加結果")
        print(f"{'='*80}")
        
        print(f"📊 統計情報:")
        print(f"  - 検索実行: {self.stats['searched']} チャンネル")
        print(f"  - 重複スキップ: {self.stats['duplicates_skipped']} チャンネル")
        print(f"  - AI分析完了: {self.stats['analyzed']} チャンネル")
        print(f"  - Firestore保存: {self.stats['saved_firestore']} チャンネル")
        print(f"  - BigQuery保存: {self.stats['saved_bigquery']} チャンネル")
        print(f"  - エラー数: {self.stats['errors']}")
        
        if self.added_channels:
            # カテゴリ分布
            categories = {}
            total_subscribers = 0
            avg_safety = 0
            avg_confidence = 0
            contact_count = 0
            
            for channel in self.added_channels:
                cat = channel.get('category', '未分類')
                categories[cat] = categories.get(cat, 0) + 1
                total_subscribers += channel.get('subscriber_count', 0)
                avg_safety += channel.get('brand_safety_score', 0)
                avg_confidence += channel.get('analysis_confidence', 0)
                if channel.get('has_contact', False):
                    contact_count += 1
            
            total_count = len(self.added_channels)
            avg_safety = avg_safety / total_count if total_count > 0 else 0
            avg_confidence = avg_confidence / total_count if total_count > 0 else 0
            
            print(f"\n📋 カテゴリ分布:")
            for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                print(f"  - {category}: {count} チャンネル")
            
            print(f"\n📈 品質指標:")
            print(f"  - 総登録者数: {total_subscribers:,} 人")
            print(f"  - 平均安全性スコア: {avg_safety:.2f}")
            print(f"  - 平均AI信頼度: {avg_confidence:.2f}")
            print(f"  - 連絡先有りチャンネル: {contact_count} / {total_count} ({contact_count/total_count*100:.1f}%)")
            
            print(f"\n📋 追加チャンネル:")
            for i, channel in enumerate(self.added_channels[:10], 1):  # 最初の10件のみ表示
                print(f"{i:2d}. {channel['channel_title']} (登録者: {channel['subscriber_count']:,}, カテゴリ: {channel.get('category', '未分類')})")
            if len(self.added_channels) > 10:
                print(f"    ... 他 {len(self.added_channels) - 10} チャンネル")

async def main():
    """メイン実行関数"""
    adder = BusinessChannelAdder()
    
    print("🤖 50ビジネス系チャンネル追加システム")
    print("=" * 60)
    print("機能: ビジネス・経済・起業系特化 + AI分析 + 自動登録")
    print()
    
    try:
        # 1. 既存チャンネルID読み込み
        await adder.load_existing_channel_ids()
        
        # 2. ビジネス系チャンネル検索
        channels = await adder.search_business_channels(target_count=100)  # 多めに検索
        
        if not channels:
            print("❌ 新規ビジネス系チャンネルが見つかりません")
            return
        
        # 3. 詳細取得 + AI分析（50チャンネル目標）
        enhanced_channels = await adder.get_channel_details_with_ai(channels, target_final=50)
        
        if not enhanced_channels:
            print("❌ 条件に合うビジネス系チャンネルが見つかりません")
            return
        
        adder.added_channels = enhanced_channels
        
        # 4. データベース保存
        await adder.save_to_firestore(enhanced_channels)
        await adder.save_to_bigquery(enhanced_channels)
        
        # 5. JSONバックアップ
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"business_50_channels_{timestamp}.json"
        adder.save_to_json(enhanced_channels, filename)
        
        # 6. 結果表示
        adder.print_results_summary()
        
        print(f"\n🎉 ビジネス系50チャンネル追加が完了しました！")
        print(f"📈 合計登録チャンネル数: {102 + len(enhanced_channels)} 件")
        
    except Exception as e:
        print(f"❌ 追加処理エラー: {e}")
        adder.print_results_summary()

if __name__ == "__main__":
    asyncio.run(main())