#!/usr/bin/env python3
"""
既存データのAI分析リバイズ

@description BigQuery/Firestoreの既存データにAI分析結果を追加
既存のYouTuberデータを取得し、AI分析を実行して更新

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

class ExistingDataAIReviser:
    """既存データのAI分析リバイザー"""
    
    def __init__(self):
        self.project_id = PROJECT_ID
        self.bigquery_client = bigquery.Client(project=self.project_id)
        self.firestore_client = firestore.Client(project=self.project_id)
        self.ai_analyzer = AdvancedChannelAnalyzer()
        self.revised_count = 0
        self.failed_count = 0
        
    def fetch_existing_data_from_bigquery(self):
        """BigQueryから既存データを取得"""
        try:
            print("📊 BigQueryから既存データを取得中...")
            
            query = """
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
    
    async def revise_channel_with_ai(self, channel_data):
        """1つのチャンネルにAI分析を追加"""
        try:
            print(f"🤖 AI分析中: {channel_data['channel_title']}")
            
            # AI分析実行
            ai_analysis = await self.ai_analyzer.analyze_channel_comprehensive(channel_data)
            
            # AI分析結果を統合
            revised_data = {
                **channel_data,
                'ai_analysis': ai_analysis,
                'ai_category': ai_analysis.get('category_tags', {}).get('primary_category', channel_data['category']),
                'ai_sub_categories': ai_analysis.get('category_tags', {}).get('sub_categories', []),
                'ai_content_themes': ai_analysis.get('category_tags', {}).get('content_themes', []),
                'ai_target_age': ai_analysis.get('category_tags', {}).get('target_age_group', '不明'),
                'ai_recommended_products': ai_analysis.get('product_matching', {}).get('recommended_products', []),
                'ai_brand_safety_score': ai_analysis.get('brand_safety', {}).get('overall_safety_score', 0.8),
                'ai_analysis_confidence': ai_analysis.get('analysis_confidence', 0.5),
                'ai_revised_at': datetime.now().isoformat()
            }
            
            print(f"✅ AI分析完了: {channel_data['channel_title']}")
            print(f"   🎯 カテゴリ: {revised_data['ai_category']}")
            print(f"   🛡️ 安全性: {revised_data['ai_brand_safety_score']:.2f}")
            print(f"   📈 信頼度: {revised_data['ai_analysis_confidence']:.2f}")
            
            return revised_data
            
        except Exception as e:
            print(f"❌ AI分析エラー ({channel_data['channel_title']}): {e}")
            return None
    
    async def update_bigquery_with_ai_data(self, revised_channels):
        """BigQueryにAI分析結果を更新"""
        try:
            print(f"📊 BigQueryにAI分析結果を更新中...")
            
            # テーブル参照
            table_id = f"{self.project_id}.infumatch_data.influencers"
            table = self.bigquery_client.get_table(table_id)
            
            # 更新用データを準備
            rows_to_update = []
            for channel in revised_channels:
                if channel:  # AI分析が成功したもののみ
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
                        # AI分析結果を追加
                        'ai_analysis': json.dumps(channel['ai_analysis'], ensure_ascii=False),
                        'ai_category': channel['ai_category'],
                        'ai_sub_categories': channel['ai_sub_categories'],
                        'ai_content_themes': channel['ai_content_themes'],
                        'ai_target_age': channel['ai_target_age'],
                        'ai_recommended_products': json.dumps(channel['ai_recommended_products'], ensure_ascii=False),
                        'ai_brand_safety_score': channel['ai_brand_safety_score'],
                        'ai_analysis_confidence': channel['ai_analysis_confidence'],
                        'ai_revised_at': channel['ai_revised_at']
                    }
                    rows_to_update.append(row)
            
            if rows_to_update:
                # 既存テーブルをドロップして再作成（AI列追加のため）
                print("🔄 BigQueryテーブル構造を更新...")
                
                # 新しいスキーマ定義
                schema = [
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
                    # AI分析結果フィールド追加
                    bigquery.SchemaField("ai_analysis", "STRING"),
                    bigquery.SchemaField("ai_category", "STRING"),
                    bigquery.SchemaField("ai_sub_categories", "STRING", mode="REPEATED"),
                    bigquery.SchemaField("ai_content_themes", "STRING", mode="REPEATED"),
                    bigquery.SchemaField("ai_target_age", "STRING"),
                    bigquery.SchemaField("ai_recommended_products", "STRING"),
                    bigquery.SchemaField("ai_brand_safety_score", "FLOAT"),
                    bigquery.SchemaField("ai_analysis_confidence", "FLOAT"),
                    bigquery.SchemaField("ai_revised_at", "STRING"),
                ]
                
                # バックアップテーブル作成
                backup_table_id = f"{table_id}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                print(f"💾 バックアップテーブル作成: {backup_table_id}")
                
                backup_query = f"""
                CREATE TABLE `{backup_table_id}` AS
                SELECT * FROM `{table_id}`
                """
                self.bigquery_client.query(backup_query).result()
                
                # 元テーブル削除
                self.bigquery_client.delete_table(table_id)
                print(f"🗑️ 元テーブル削除完了")
                
                # 新テーブル作成
                new_table = bigquery.Table(table_id, schema=schema)
                new_table = self.bigquery_client.create_table(new_table)
                print(f"🆕 新テーブル作成完了")
                
                # データ挿入
                errors = self.bigquery_client.insert_rows_json(new_table, rows_to_update)
                
                if errors:
                    print(f"❌ BigQuery挿入エラー: {errors}")
                else:
                    print(f"✅ BigQueryに {len(rows_to_update)} 件のAI分析済みデータを更新しました")
                    
            return len(rows_to_update)
            
        except Exception as e:
            print(f"❌ BigQuery更新エラー: {e}")
            return 0
    
    async def update_firestore_with_ai_data(self, revised_channels):
        """FirestoreにAI分析結果を更新"""
        try:
            print(f"🔥 FirestoreにAI分析結果を更新中...")
            
            collection_ref = self.firestore_client.collection('influencers')
            updated_count = 0
            
            for channel in revised_channels:
                if channel:  # AI分析が成功したもののみ
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
                            # AI分析結果追加
                            'ai_analysis': channel['ai_analysis'],
                            'ai_category': channel['ai_category'],
                            'ai_sub_categories': channel['ai_sub_categories'],
                            'ai_content_themes': channel['ai_content_themes'],
                            'ai_target_age': channel['ai_target_age'],
                            'ai_recommended_products': channel['ai_recommended_products'],
                            'ai_brand_safety_score': channel['ai_brand_safety_score'],
                            'ai_analysis_confidence': channel['ai_analysis_confidence'],
                            'ai_revised_at': channel['ai_revised_at']
                        }
                        
                        # ドキュメント更新
                        doc_ref = collection_ref.document(channel['channel_id'])
                        doc_ref.set(firestore_data, merge=True)
                        updated_count += 1
                        
                    except Exception as e:
                        print(f"❌ Firestore更新エラー ({channel['channel_title']}): {e}")
                        continue
            
            print(f"✅ Firestoreに {updated_count} 件のAI分析済みデータを更新しました")
            return updated_count
            
        except Exception as e:
            print(f"❌ Firestore更新エラー: {e}")
            return 0
    
    async def revise_all_existing_data(self):
        """既存データ全てにAI分析を追加"""
        print("🚀 既存データのAI分析リバイズ開始")
        print("=" * 80)
        
        print("🔧 実行内容:")
        print("  1. BigQueryから既存データを取得")
        print("  2. 各チャンネルにAI分析を実行")
        print("  3. AI分析結果をBigQueryに更新")
        print("  4. AI分析結果をFirestoreに更新")
        print()
        
        # 1. 既存データ取得
        existing_channels = self.fetch_existing_data_from_bigquery()
        if not existing_channels:
            print("❌ 既存データが見つかりません")
            return
        
        total_channels = len(existing_channels)
        print(f"📊 {total_channels} チャンネルのAI分析を開始...")
        print()
        
        # 2. AI分析実行
        revised_channels = []
        for i, channel in enumerate(existing_channels, 1):
            print(f"⏳ 進捗: {i}/{total_channels} ({i/total_channels*100:.1f}%)")
            
            try:
                revised_channel = await self.revise_channel_with_ai(channel)
                if revised_channel:
                    revised_channels.append(revised_channel)
                    self.revised_count += 1
                else:
                    self.failed_count += 1
                    
                print()
                
                # 3つずつ処理してレート制限を避ける
                if i % 3 == 0:
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
        
        if revised_channels:
            # 3. BigQuery更新
            bigquery_updated = await self.update_bigquery_with_ai_data(revised_channels)
            
            # 4. Firestore更新
            firestore_updated = await self.update_firestore_with_ai_data(revised_channels)
            
            print("\n" + "=" * 80)
            print("🎉 既存データのAI分析リバイズ完了！")
            print(f"📊 BigQuery更新: {bigquery_updated} 件")
            print(f"🔥 Firestore更新: {firestore_updated} 件")
            print(f"📈 AI分析成功率: {self.revised_count/(self.revised_count+self.failed_count)*100:.1f}%")
            
        else:
            print("❌ AI分析済みデータがありません")
    
    def save_revision_report(self, revised_channels):
        """リバイズレポートを保存"""
        try:
            report = {
                "revision_timestamp": datetime.now().isoformat(),
                "total_processed": len(revised_channels),
                "successful_revisions": self.revised_count,
                "failed_revisions": self.failed_count,
                "success_rate": self.revised_count/(self.revised_count+self.failed_count)*100 if (self.revised_count+self.failed_count) > 0 else 0,
                "revised_channels": [
                    {
                        "channel_id": ch["channel_id"],
                        "channel_title": ch["channel_title"],
                        "ai_category": ch["ai_category"],
                        "ai_confidence": ch["ai_analysis_confidence"],
                        "ai_safety_score": ch["ai_brand_safety_score"]
                    }
                    for ch in revised_channels if ch
                ]
            }
            
            with open('ai_revision_report.json', 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"📄 リバイズレポートを ai_revision_report.json に保存しました")
            
        except Exception as e:
            print(f"❌ レポート保存エラー: {e}")

async def main():
    """メイン実行関数"""
    reviser = ExistingDataAIReviser()
    
    try:
        await reviser.revise_all_existing_data()
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    asyncio.run(main())