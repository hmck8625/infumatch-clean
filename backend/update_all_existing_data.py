#!/usr/bin/env python3
"""
全既存データのAI分析更新

@description BigQuery/Firestoreの全既存データ（24件）にAI分析を追加
安全に段階的に実行

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

class AllDataAIUpdater:
    """全データのAI分析更新器"""
    
    def __init__(self):
        self.project_id = PROJECT_ID
        self.bigquery_client = bigquery.Client(project=self.project_id)
        self.firestore_client = firestore.Client(project=self.project_id)
        self.ai_analyzer = AdvancedChannelAnalyzer()
        self.updated_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        
    def get_all_channels_status(self):
        """全チャンネルの更新状況を確認"""
        try:
            print("📊 全チャンネルの更新状況を確認中...")
            
            query = """
            SELECT 
                channel_id,
                channel_title,
                ai_analysis,
                updated_at
            FROM `hackathon-462905.infumatch_data.influencers`
            WHERE is_active = true
            ORDER BY subscriber_count DESC
            """
            
            query_job = self.bigquery_client.query(query)
            results = query_job.result()
            
            all_channels = []
            updated_channels = []
            old_format_channels = []
            
            for row in results:
                channel_info = {
                    'channel_id': row.channel_id,
                    'channel_title': row.channel_title,
                    'updated_at': row.updated_at
                }
                
                all_channels.append(channel_info)
                
                # AI分析の形式をチェック
                if row.ai_analysis:
                    try:
                        ai_data = json.loads(row.ai_analysis)
                        if 'advanced_analysis' in ai_data:
                            updated_channels.append(channel_info)
                        else:
                            old_format_channels.append(channel_info)
                    except:
                        old_format_channels.append(channel_info)
                else:
                    old_format_channels.append(channel_info)
            
            print(f"📊 全体状況:")
            print(f"  - 総チャンネル数: {len(all_channels)}")
            print(f"  - 新形式AI分析済み: {len(updated_channels)}")
            print(f"  - 旧形式/未分析: {len(old_format_channels)}")
            print()
            
            if updated_channels:
                print("✅ 新形式AI分析済みチャンネル:")
                for ch in updated_channels:
                    print(f"  - {ch['channel_title']}")
                print()
            
            print(f"🔄 更新が必要なチャンネル ({len(old_format_channels)}件):")
            for i, ch in enumerate(old_format_channels[:10], 1):  # 最初の10件表示
                print(f"  {i:2d}. {ch['channel_title']}")
            if len(old_format_channels) > 10:
                print(f"     ... 他 {len(old_format_channels) - 10} 件")
            print()
            
            return old_format_channels
            
        except Exception as e:
            print(f"❌ 状況確認エラー: {e}")
            return []
    
    def fetch_channels_for_update(self, channel_ids):
        """更新対象チャンネルの詳細データを取得"""
        try:
            print(f"📊 {len(channel_ids)} チャンネルの詳細データを取得中...")
            
            # チャンネルIDをクエリ用に準備
            channel_ids_str = "', '".join(channel_ids)
            
            query = f"""
            SELECT 
                influencer_id,
                channel_id,
                channel_title,
                description,
                subscriber_count,
                video_count,
                view_count,
                category,
                country,
                language,
                contact_email,
                social_links,
                ai_analysis,
                created_at,
                updated_at,
                is_active
            FROM `hackathon-462905.infumatch_data.influencers`
            WHERE channel_id IN ('{channel_ids_str}')
            AND is_active = true
            ORDER BY subscriber_count DESC
            """
            
            query_job = self.bigquery_client.query(query)
            results = query_job.result()
            
            channels = []
            for row in results:
                # social_linksからemailsを取得
                social_links = {}
                try:
                    if row.social_links:
                        social_links = json.loads(row.social_links)
                except:
                    social_links = {}
                
                emails = social_links.get('emails', [])
                if row.contact_email:
                    emails.append(row.contact_email)
                
                channel_data = {
                    'influencer_id': row.influencer_id,
                    'channel_id': row.channel_id,
                    'channel_title': row.channel_title,
                    'description': row.description or '',
                    'subscriber_count': int(row.subscriber_count),
                    'video_count': int(row.video_count),
                    'view_count': int(row.view_count),
                    'category': row.category,
                    'country': row.country or 'JP',
                    'language': row.language or 'ja',
                    'contact_email': row.contact_email or '',
                    'emails': emails,
                    'has_contact': len(emails) > 0 or bool(row.contact_email),
                    'social_links': social_links,
                    'old_ai_analysis': row.ai_analysis,
                    'created_at': row.created_at,
                    'updated_at': row.updated_at,
                    'is_active': row.is_active
                }
                
                # エンゲージメント推定値計算
                if channel_data['video_count'] > 0 and channel_data['subscriber_count'] > 0:
                    channel_data['engagement_estimate'] = round(
                        (channel_data['view_count'] / channel_data['video_count'] / channel_data['subscriber_count']) * 100, 2
                    )
                else:
                    channel_data['engagement_estimate'] = 0.0
                
                channels.append(channel_data)
            
            print(f"✅ {len(channels)} チャンネルの詳細データを取得しました")
            return channels
            
        except Exception as e:
            print(f"❌ 詳細データ取得エラー: {e}")
            return []
    
    async def process_channels_in_batches(self, channels, batch_size=3):
        """チャンネルをバッチ処理で更新"""
        total = len(channels)
        
        print(f"🚀 {total} チャンネルのバッチ処理開始（バッチサイズ: {batch_size}）")
        print("=" * 80)
        
        for i in range(0, total, batch_size):
            batch = channels[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total + batch_size - 1) // batch_size
            
            print(f"\n📦 バッチ {batch_num}/{total_batches} 処理中...")
            print(f"   チャンネル {i+1}-{min(i+batch_size, total)} / {total}")
            
            # バッチ内のチャンネルを並列処理
            tasks = []
            for channel in batch:
                task = self.enhance_channel_with_ai(channel)
                tasks.append(task)
            
            # 並列実行
            enhanced_channels = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 結果処理
            successful_channels = []
            for j, result in enumerate(enhanced_channels):
                if isinstance(result, Exception):
                    print(f"❌ {batch[j]['channel_title']}: {result}")
                    self.failed_count += 1
                elif result:
                    successful_channels.append(result)
                    self.updated_count += 1
                    print(f"✅ {result['channel_title']}: AI分析完了")
                else:
                    self.failed_count += 1
            
            # データベース更新
            if successful_channels:
                await self.update_databases_batch(successful_channels)
            
            # バッチ間の待機（レート制限対策）
            if i + batch_size < total:
                wait_time = 5
                print(f"⏸️ 次のバッチまで {wait_time} 秒待機...")
                await asyncio.sleep(wait_time)
        
        print(f"\n📊 全バッチ処理完了:")
        print(f"  - 成功: {self.updated_count} チャンネル")
        print(f"  - 失敗: {self.failed_count} チャンネル")
        print(f"  - 成功率: {self.updated_count/(self.updated_count+self.failed_count)*100:.1f}%")
    
    async def enhance_channel_with_ai(self, channel_data):
        """1つのチャンネルにAI分析を追加"""
        try:
            # AI分析実行
            advanced_ai_analysis = await self.ai_analyzer.analyze_channel_comprehensive(channel_data)
            
            # データ統合
            enhanced_data = {
                **channel_data,
                'advanced_ai_analysis': advanced_ai_analysis,
                'ai_category': advanced_ai_analysis.get('category_tags', {}).get('primary_category', channel_data['category']),
                'ai_sub_categories': advanced_ai_analysis.get('category_tags', {}).get('sub_categories', []),
                'ai_content_themes': advanced_ai_analysis.get('category_tags', {}).get('content_themes', []),
                'ai_target_age': advanced_ai_analysis.get('category_tags', {}).get('target_age_group', '不明'),
                'ai_confidence_score': advanced_ai_analysis.get('category_tags', {}).get('confidence_score', 0.5),
                'ai_brand_safety_score': advanced_ai_analysis.get('brand_safety', {}).get('overall_safety_score', 0.8),
                'ai_analysis_confidence': advanced_ai_analysis.get('analysis_confidence', 0.5),
                'ai_enhanced_at': datetime.now().isoformat()
            }
            
            # 商材マッチング情報
            product_matching = advanced_ai_analysis.get('product_matching', {})
            recommended_products = product_matching.get('recommended_products', [])
            
            if recommended_products:
                enhanced_data['ai_top_product_category'] = recommended_products[0].get('category', '不明')
                enhanced_data['ai_top_product_match_score'] = recommended_products[0].get('match_score', 0.0)
                enhanced_data['ai_collaboration_formats'] = product_matching.get('collaboration_formats', [])
            else:
                enhanced_data['ai_top_product_category'] = '不明'
                enhanced_data['ai_top_product_match_score'] = 0.0
                enhanced_data['ai_collaboration_formats'] = []
            
            return enhanced_data
            
        except Exception as e:
            return None
    
    async def update_databases_batch(self, enhanced_channels):
        """バッチでデータベースを更新"""
        # BigQuery更新
        bigquery_count = await self.update_bigquery_batch(enhanced_channels)
        
        # Firestore更新
        firestore_count = await self.update_firestore_batch(enhanced_channels)
        
        print(f"    📊 BigQuery更新: {bigquery_count} 件")
        print(f"    🔥 Firestore更新: {firestore_count} 件")
    
    async def update_bigquery_batch(self, enhanced_channels):
        """BigQueryをバッチ更新"""
        try:
            table_id = f"{self.project_id}.infumatch_data.influencers"
            updated_count = 0
            
            for channel in enhanced_channels:
                if channel:
                    # 新しいai_analysis作成
                    new_ai_analysis = {
                        "engagement_rate": channel['engagement_estimate'],
                        "content_quality_score": 0.8,
                        "brand_safety_score": channel['ai_brand_safety_score'],
                        "growth_potential": 0.7,
                        "advanced_analysis": {
                            "category_tags": {
                                "primary_category": channel['ai_category'],
                                "sub_categories": channel['ai_sub_categories'],
                                "content_themes": channel['ai_content_themes'],
                                "target_age_group": channel['ai_target_age'],
                                "confidence_score": channel['ai_confidence_score']
                            },
                            "product_matching": {
                                "top_category": channel['ai_top_product_category'],
                                "match_score": channel['ai_top_product_match_score'],
                                "collaboration_formats": channel['ai_collaboration_formats']
                            },
                            "analysis_meta": {
                                "confidence": channel['ai_analysis_confidence'],
                                "enhanced_at": channel['ai_enhanced_at'],
                                "version": "2.0"
                            }
                        },
                        "full_analysis": channel['advanced_ai_analysis']
                    }
                    
                    update_query = f"""
                    UPDATE `{table_id}`
                    SET 
                        ai_analysis = @ai_analysis,
                        updated_at = CURRENT_TIMESTAMP()
                    WHERE channel_id = @channel_id
                    """
                    
                    job_config = bigquery.QueryJobConfig(
                        query_parameters=[
                            bigquery.ScalarQueryParameter("ai_analysis", "STRING", json.dumps(new_ai_analysis, ensure_ascii=False)),
                            bigquery.ScalarQueryParameter("channel_id", "STRING", channel['channel_id'])
                        ]
                    )
                    
                    query_job = self.bigquery_client.query(update_query, job_config=job_config)
                    query_job.result()
                    updated_count += 1
            
            return updated_count
            
        except Exception as e:
            print(f"❌ BigQueryバッチ更新エラー: {e}")
            return 0
    
    async def update_firestore_batch(self, enhanced_channels):
        """Firestoreをバッチ更新"""
        try:
            collection_ref = self.firestore_client.collection('influencers')
            updated_count = 0
            
            # バッチ書き込み
            batch = self.firestore_client.batch()
            
            for channel in enhanced_channels:
                if channel:
                    firestore_data = {
                        'ai_analysis': {
                            "engagement_rate": channel['engagement_estimate'],
                            "content_quality_score": 0.8,
                            "brand_safety_score": channel['ai_brand_safety_score'],
                            "growth_potential": 0.7,
                            "advanced": {
                                "category": channel['ai_category'],
                                "sub_categories": channel['ai_sub_categories'],
                                "content_themes": channel['ai_content_themes'],
                                "target_age": channel['ai_target_age'],
                                "confidence": channel['ai_analysis_confidence'],
                                "safety_score": channel['ai_brand_safety_score'],
                                "top_product": channel['ai_top_product_category'],
                                "match_score": channel['ai_top_product_match_score'],
                                "enhanced_at": channel['ai_enhanced_at']
                            },
                            "full_analysis": channel['advanced_ai_analysis']
                        },
                        'updated_at': datetime.now()
                    }
                    
                    doc_ref = collection_ref.document(channel['channel_id'])
                    batch.update(doc_ref, firestore_data)
                    updated_count += 1
            
            # バッチ実行
            if updated_count > 0:
                batch.commit()
            
            return updated_count
            
        except Exception as e:
            print(f"❌ Firestoreバッチ更新エラー: {e}")
            return 0
    
    def save_final_report(self):
        """最終レポートを保存"""
        try:
            report = {
                "full_update_timestamp": datetime.now().isoformat(),
                "total_processed": self.updated_count + self.failed_count,
                "successful_updates": self.updated_count,
                "failed_updates": self.failed_count,
                "skipped_updates": self.skipped_count,
                "success_rate": self.updated_count/(self.updated_count+self.failed_count)*100 if (self.updated_count+self.failed_count) > 0 else 0,
                "update_method": "batch_processing",
                "version": "2.0"
            }
            
            with open('full_ai_update_report.json', 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"📄 最終レポートを full_ai_update_report.json に保存しました")
            
        except Exception as e:
            print(f"❌ レポート保存エラー: {e}")
    
    async def update_all_existing_data(self):
        """全既存データを更新"""
        print("🚀 全既存データのAI分析更新開始")
        print("=" * 80)
        
        # 1. 現在の状況確認
        channels_to_update = self.get_all_channels_status()
        
        if not channels_to_update:
            print("✅ 全てのチャンネルが既に最新のAI分析済みです")
            return
        
        print(f"🔄 {len(channels_to_update)} チャンネルを更新します")
        
        # 確認プロンプト
        response = input("\n続行しますか？ (y/N): ")
        if response.lower() != 'y':
            print("❌ キャンセルしました")
            return
        
        # 2. 詳細データ取得
        channel_ids = [ch['channel_id'] for ch in channels_to_update]
        detailed_channels = self.fetch_channels_for_update(channel_ids)
        
        if not detailed_channels:
            print("❌ 詳細データの取得に失敗しました")
            return
        
        # 3. バッチ処理で更新
        await self.process_channels_in_batches(detailed_channels, batch_size=3)
        
        # 4. 最終レポート
        self.save_final_report()
        
        print("\n" + "=" * 80)
        print("🎉 全既存データのAI分析更新完了！")
        print(f"📊 更新済み: {self.updated_count} チャンネル")
        print(f"❌ 失敗: {self.failed_count} チャンネル")
        print(f"📈 成功率: {self.updated_count/(self.updated_count+self.failed_count)*100:.1f}%")

async def main():
    """メイン実行関数"""
    updater = AllDataAIUpdater()
    
    try:
        await updater.update_all_existing_data()
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    asyncio.run(main())