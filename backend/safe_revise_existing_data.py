#!/usr/bin/env python3
"""
既存データの安全なAI分析リバイズ

@description 既存データに新しい列を追加してAI分析結果を安全に更新
バックアップを取りながら段階的に実行

@author InfuMatch Development Team
@version 1.0.0
"""

import asyncio
import json
from datetime import datetime
from google.cloud import firestore, bigquery
from services.ai_channel_analyzer import AdvancedChannelAnalyzer

# 設定
PROJECT_ID = "hackathon-462905"

class SafeExistingDataReviser:
    """既存データの安全なAI分析リバイザー"""
    
    def __init__(self):
        self.project_id = PROJECT_ID
        self.bigquery_client = bigquery.Client(project=self.project_id)
        self.firestore_client = firestore.Client(project=self.project_id)
        self.ai_analyzer = AdvancedChannelAnalyzer()
        self.revised_count = 0
        self.failed_count = 0
        
    def fetch_existing_channels(self, limit=5):
        """既存チャンネルデータを取得（テスト用に少数）"""
        try:
            print(f"📊 BigQueryから既存データを取得中（最大{limit}件）...")
            
            query = f"""
            SELECT 
                channel_id,
                channel_title,
                description,
                subscriber_count,
                video_count,
                view_count,
                country,
                category,
                emails,
                has_contact,
                engagement_estimate,
                collected_at
            FROM `hackathon-462905.infumatch_data.influencers`
            ORDER BY subscriber_count DESC
            LIMIT {limit}
            """
            
            query_job = self.bigquery_client.query(query)
            results = query_job.result()
            
            channels = []
            for row in results:
                channel_data = {
                    'channel_id': row.channel_id,
                    'channel_title': row.channel_title,
                    'description': row.description or '',
                    'subscriber_count': int(row.subscriber_count),
                    'video_count': int(row.video_count),
                    'view_count': int(row.view_count),
                    'country': row.country,
                    'category': row.category,
                    'emails': row.emails or [],
                    'has_contact': bool(row.has_contact),
                    'engagement_estimate': float(row.engagement_estimate),
                    'collected_at': row.collected_at
                }
                channels.append(channel_data)
            
            print(f"✅ {len(channels)} チャンネルのデータを取得しました")
            return channels
            
        except Exception as e:
            print(f"❌ BigQueryデータ取得エラー: {e}")
            return []
    
    async def add_ai_analysis_to_channel(self, channel_data):
        """1つのチャンネルにAI分析を追加"""
        try:
            print(f"🤖 AI分析中: {channel_data['channel_title']}")
            
            # AI分析実行
            ai_analysis = await self.ai_analyzer.analyze_channel_comprehensive(channel_data)
            
            # AI分析結果を統合
            enhanced_data = {
                **channel_data,
                'ai_analysis': ai_analysis,
                'ai_category': ai_analysis.get('category_tags', {}).get('primary_category', channel_data['category']),
                'ai_sub_categories': ai_analysis.get('category_tags', {}).get('sub_categories', []),
                'ai_content_themes': ai_analysis.get('category_tags', {}).get('content_themes', []),
                'ai_target_age': ai_analysis.get('category_tags', {}).get('target_age_group', '不明'),
                'ai_brand_safety_score': ai_analysis.get('brand_safety', {}).get('overall_safety_score', 0.8),
                'ai_analysis_confidence': ai_analysis.get('analysis_confidence', 0.5),
                'ai_revised_at': datetime.now().isoformat()
            }
            
            # 推奨商材情報を簡潔に
            recommended_products = ai_analysis.get('product_matching', {}).get('recommended_products', [])
            if recommended_products:
                enhanced_data['ai_top_product_category'] = recommended_products[0].get('category', '不明')
                enhanced_data['ai_top_product_match_score'] = recommended_products[0].get('match_score', 0.0)
            else:
                enhanced_data['ai_top_product_category'] = '不明'
                enhanced_data['ai_top_product_match_score'] = 0.0
            
            print(f"✅ AI分析完了: {channel_data['channel_title']}")
            print(f"   🎯 AIカテゴリ: {enhanced_data['ai_category']}")
            print(f"   🛡️ 安全性: {enhanced_data['ai_brand_safety_score']:.2f}")
            print(f"   📈 信頼度: {enhanced_data['ai_analysis_confidence']:.2f}")
            print(f"   💼 推奨商材: {enhanced_data['ai_top_product_category']}")
            
            return enhanced_data
            
        except Exception as e:
            print(f"❌ AI分析エラー ({channel_data['channel_title']}): {e}")
            return None
    
    def create_ai_enhanced_table(self, enhanced_channels):
        """AI分析結果を含む新しいテーブルを作成"""
        try:
            print("🏗️ AI拡張テーブルを作成中...")
            
            # 新しいテーブルID
            table_id = f"{self.project_id}.infumatch_data.influencers_ai_enhanced"
            
            # スキーマ定義
            schema = [
                # 既存フィールド
                bigquery.SchemaField("channel_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("channel_title", "STRING"),
                bigquery.SchemaField("description", "STRING"),
                bigquery.SchemaField("subscriber_count", "INTEGER"),
                bigquery.SchemaField("video_count", "INTEGER"),
                bigquery.SchemaField("view_count", "INTEGER"),
                bigquery.SchemaField("country", "STRING"),
                bigquery.SchemaField("category", "STRING"),
                bigquery.SchemaField("emails", "STRING", mode="REPEATED"),
                bigquery.SchemaField("has_contact", "BOOLEAN"),
                bigquery.SchemaField("engagement_estimate", "FLOAT"),
                bigquery.SchemaField("collected_at", "STRING"),
                # AI分析フィールド
                bigquery.SchemaField("ai_category", "STRING"),
                bigquery.SchemaField("ai_sub_categories", "STRING", mode="REPEATED"),
                bigquery.SchemaField("ai_content_themes", "STRING", mode="REPEATED"),
                bigquery.SchemaField("ai_target_age", "STRING"),
                bigquery.SchemaField("ai_top_product_category", "STRING"),
                bigquery.SchemaField("ai_top_product_match_score", "FLOAT"),
                bigquery.SchemaField("ai_brand_safety_score", "FLOAT"),
                bigquery.SchemaField("ai_analysis_confidence", "FLOAT"),
                bigquery.SchemaField("ai_revised_at", "STRING"),
                bigquery.SchemaField("ai_analysis_json", "STRING"),  # 完全なAI分析結果
            ]
            
            # テーブル作成
            table = bigquery.Table(table_id, schema=schema)
            
            # 既存テーブルがあれば削除
            try:
                self.bigquery_client.delete_table(table_id)
                print(f"🗑️ 既存のAI拡張テーブルを削除しました")
            except:
                pass
            
            table = self.bigquery_client.create_table(table)
            print(f"✅ AI拡張テーブル作成完了: {table_id}")
            
            # データ挿入
            rows_to_insert = []
            for channel in enhanced_channels:
                if channel:
                    row = {
                        'channel_id': channel['channel_id'],
                        'channel_title': channel['channel_title'],
                        'description': channel['description'],
                        'subscriber_count': channel['subscriber_count'],
                        'video_count': channel['video_count'],
                        'view_count': channel['view_count'],
                        'country': channel['country'],
                        'category': channel['category'],
                        'emails': channel['emails'],
                        'has_contact': channel['has_contact'],
                        'engagement_estimate': channel['engagement_estimate'],
                        'collected_at': channel['collected_at'],
                        'ai_category': channel['ai_category'],
                        'ai_sub_categories': channel['ai_sub_categories'],
                        'ai_content_themes': channel['ai_content_themes'],
                        'ai_target_age': channel['ai_target_age'],
                        'ai_top_product_category': channel['ai_top_product_category'],
                        'ai_top_product_match_score': channel['ai_top_product_match_score'],
                        'ai_brand_safety_score': channel['ai_brand_safety_score'],
                        'ai_analysis_confidence': channel['ai_analysis_confidence'],
                        'ai_revised_at': channel['ai_revised_at'],
                        'ai_analysis_json': json.dumps(channel['ai_analysis'], ensure_ascii=False)
                    }
                    rows_to_insert.append(row)
            
            if rows_to_insert:
                errors = self.bigquery_client.insert_rows_json(table, rows_to_insert)
                if errors:
                    print(f"❌ BigQuery挿入エラー: {errors}")
                    return 0
                else:
                    print(f"✅ AI拡張テーブルに {len(rows_to_insert)} 件のデータを挿入しました")
                    return len(rows_to_insert)
            
            return 0
            
        except Exception as e:
            print(f"❌ AI拡張テーブル作成エラー: {e}")
            return 0
    
    def update_firestore_with_ai(self, enhanced_channels):
        """FirestoreにAI分析結果を追加"""
        try:
            print("🔥 FirestoreにAI分析結果を追加中...")
            
            collection_ref = self.firestore_client.collection('influencers_ai_enhanced')
            updated_count = 0
            
            for channel in enhanced_channels:
                if channel:
                    try:
                        # Firestore用データ準備
                        firestore_data = {
                            'channel_id': channel['channel_id'],
                            'channel_title': channel['channel_title'],
                            'description': channel['description'],
                            'subscriber_count': channel['subscriber_count'],
                            'video_count': channel['video_count'],
                            'view_count': channel['view_count'],
                            'country': channel['country'],
                            'category': channel['category'],
                            'emails': channel['emails'],
                            'has_contact': channel['has_contact'],
                            'engagement_estimate': channel['engagement_estimate'],
                            'collected_at': channel['collected_at'],
                            # AI分析結果
                            'ai_category': channel['ai_category'],
                            'ai_sub_categories': channel['ai_sub_categories'],
                            'ai_content_themes': channel['ai_content_themes'],
                            'ai_target_age': channel['ai_target_age'],
                            'ai_top_product_category': channel['ai_top_product_category'],
                            'ai_top_product_match_score': channel['ai_top_product_match_score'],
                            'ai_brand_safety_score': channel['ai_brand_safety_score'],
                            'ai_analysis_confidence': channel['ai_analysis_confidence'],
                            'ai_revised_at': channel['ai_revised_at'],
                            'ai_analysis': channel['ai_analysis']  # 完全なAI分析結果
                        }
                        
                        # ドキュメント追加
                        doc_ref = collection_ref.document(channel['channel_id'])
                        doc_ref.set(firestore_data)
                        updated_count += 1
                        
                    except Exception as e:
                        print(f"❌ Firestore追加エラー ({channel['channel_title']}): {e}")
                        continue
            
            print(f"✅ Firestoreに {updated_count} 件のAI拡張データを追加しました")
            return updated_count
            
        except Exception as e:
            print(f"❌ Firestore追加エラー: {e}")
            return 0
    
    async def safe_revise_existing_data(self, limit=5):
        """既存データを安全にAI分析拡張"""
        print("🚀 既存データの安全なAI分析拡張開始")
        print("=" * 80)
        
        print("🔧 実行内容:")
        print("  1. 既存データを少数取得（テスト用）")
        print("  2. 各チャンネルにAI分析を実行")
        print("  3. AI拡張テーブルを新規作成")
        print("  4. AI拡張Firestoreコレクションを作成")
        print("  5. 元データは保持（安全性確保）")
        print()
        
        # 1. 既存データ取得
        existing_channels = self.fetch_existing_channels(limit)
        if not existing_channels:
            print("❌ 既存データが見つかりません")
            return
        
        print(f"📊 {len(existing_channels)} チャンネルのAI分析を開始...")
        print()
        
        # 2. AI分析実行
        enhanced_channels = []
        for i, channel in enumerate(existing_channels, 1):
            print(f"⏳ 進捗: {i}/{len(existing_channels)} ({i/len(existing_channels)*100:.1f}%)")
            
            try:
                enhanced_channel = await self.add_ai_analysis_to_channel(channel)
                if enhanced_channel:
                    enhanced_channels.append(enhanced_channel)
                    self.revised_count += 1
                else:
                    self.failed_count += 1
                    
                print()
                
                # レート制限回避
                if i < len(existing_channels):
                    print("⏸️ レート制限回避のため3秒待機...")
                    await asyncio.sleep(3)
                    
            except Exception as e:
                print(f"❌ チャンネル処理エラー: {e}")
                self.failed_count += 1
                continue
        
        print(f"\n📊 AI分析完了:")
        print(f"  - 成功: {self.revised_count} チャンネル")
        print(f"  - 失敗: {self.failed_count} チャンネル")
        print()
        
        if enhanced_channels:
            # 3. AI拡張テーブル作成
            bigquery_count = self.create_ai_enhanced_table(enhanced_channels)
            
            # 4. AI拡張Firestoreコレクション作成
            firestore_count = self.update_firestore_with_ai(enhanced_channels)
            
            # 5. 結果保存
            self.save_enhanced_data(enhanced_channels)
            
            print("\n" + "=" * 80)
            print("🎉 既存データのAI分析拡張完了！")
            print(f"📊 BigQuery AI拡張テーブル: {bigquery_count} 件")
            print(f"🔥 Firestore AI拡張コレクション: {firestore_count} 件")
            print(f"📈 AI分析成功率: {self.revised_count/(self.revised_count+self.failed_count)*100:.1f}%")
            print()
            print("💡 確認方法:")
            print("  - BigQuery: `hackathon-462905.infumatch_data.influencers_ai_enhanced`")
            print("  - Firestore: `influencers_ai_enhanced` コレクション")
            
        else:
            print("❌ AI分析済みデータがありません")
    
    def save_enhanced_data(self, enhanced_channels):
        """AI拡張データを保存"""
        try:
            # 拡張データ保存
            with open('existing_data_ai_enhanced.json', 'w', encoding='utf-8') as f:
                json.dump(enhanced_channels, f, ensure_ascii=False, indent=2)
            
            # レポート作成
            report = {
                "enhancement_timestamp": datetime.now().isoformat(),
                "total_processed": len(enhanced_channels),
                "successful_enhancements": self.revised_count,
                "failed_enhancements": self.failed_count,
                "success_rate": self.revised_count/(self.revised_count+self.failed_count)*100 if (self.revised_count+self.failed_count) > 0 else 0,
                "enhanced_channels_summary": [
                    {
                        "channel_id": ch["channel_id"],
                        "channel_title": ch["channel_title"],
                        "original_category": ch["category"],
                        "ai_category": ch["ai_category"],
                        "ai_confidence": ch["ai_analysis_confidence"],
                        "ai_safety_score": ch["ai_brand_safety_score"],
                        "ai_top_product": ch["ai_top_product_category"]
                    }
                    for ch in enhanced_channels if ch
                ]
            }
            
            with open('ai_enhancement_report.json', 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"📄 AI拡張データを existing_data_ai_enhanced.json に保存しました")
            print(f"📊 拡張レポートを ai_enhancement_report.json に保存しました")
            
        except Exception as e:
            print(f"❌ データ保存エラー: {e}")

async def main():
    """メイン実行関数"""
    reviser = SafeExistingDataReviser()
    
    try:
        # テスト用に5件から開始
        await reviser.safe_revise_existing_data(limit=5)
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    asyncio.run(main())