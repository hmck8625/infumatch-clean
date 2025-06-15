#!/usr/bin/env python3
"""
全既存データの自動AI分析更新

@description 確認なしで全データを自動更新
"""

import asyncio
import json
from datetime import datetime
from google.cloud import firestore, bigquery
from services.ai_channel_analyzer import AdvancedChannelAnalyzer

# 設定
PROJECT_ID = "hackathon-462905"

class AutoAllDataUpdater:
    """全データの自動AI分析更新器"""
    
    def __init__(self):
        self.project_id = PROJECT_ID
        self.bigquery_client = bigquery.Client(project=self.project_id)
        self.firestore_client = firestore.Client(project=self.project_id)
        self.ai_analyzer = AdvancedChannelAnalyzer()
        self.updated_count = 0
        self.failed_count = 0
        
    def get_channels_needing_update(self):
        """更新が必要なチャンネルを取得"""
        try:
            print("📊 更新が必要なチャンネルを確認中...")
            
            query = """
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
            WHERE is_active = true
            ORDER BY subscriber_count DESC
            """
            
            query_job = self.bigquery_client.query(query)
            results = query_job.result()
            
            channels_to_update = []
            already_updated = []
            
            for row in results:
                # AI分析の形式をチェック
                needs_update = True
                if row.ai_analysis:
                    try:
                        ai_data = json.loads(row.ai_analysis)
                        if 'advanced_analysis' in ai_data:
                            needs_update = False
                            already_updated.append(row.channel_title)
                    except:
                        pass
                
                if needs_update:
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
                    
                    channels_to_update.append(channel_data)
            
            print(f"📊 状況:")
            print(f"  - 既に更新済み: {len(already_updated)} チャンネル")
            print(f"  - 更新が必要: {len(channels_to_update)} チャンネル")
            
            if already_updated:
                print(f"\n✅ 更新済みチャンネル:")
                for ch in already_updated:
                    print(f"  - {ch}")
            
            return channels_to_update
            
        except Exception as e:
            print(f"❌ チャンネル取得エラー: {e}")
            return []
    
    async def process_channel(self, channel_data):
        """1つのチャンネルを処理"""
        try:
            print(f"🤖 AI分析中: {channel_data['channel_title']}")
            
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
            
            # データベース更新
            await self.update_databases(enhanced_data)
            
            print(f"✅ 完了: {channel_data['channel_title']}")
            print(f"   🎯 AIカテゴリ: {enhanced_data['ai_category']}")
            print(f"   🛡️ 安全性: {enhanced_data['ai_brand_safety_score']:.2f}")
            print(f"   💼 推奨商材: {enhanced_data['ai_top_product_category']}")
            
            self.updated_count += 1
            return True
            
        except Exception as e:
            print(f"❌ エラー ({channel_data['channel_title']}): {e}")
            self.failed_count += 1
            return False
    
    async def update_databases(self, enhanced_channel):
        """データベースを更新"""
        # BigQuery更新
        await self.update_bigquery_single(enhanced_channel)
        
        # Firestore更新
        await self.update_firestore_single(enhanced_channel)
    
    async def update_bigquery_single(self, channel):
        """BigQueryを単体更新"""
        try:
            table_id = f"{self.project_id}.infumatch_data.influencers"
            
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
            
        except Exception as e:
            print(f"❌ BigQuery更新エラー: {e}")
    
    async def update_firestore_single(self, channel):
        """Firestoreを単体更新"""
        try:
            collection_ref = self.firestore_client.collection('influencers')
            
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
            doc_ref.update(firestore_data)
            
        except Exception as e:
            print(f"❌ Firestore更新エラー: {e}")
    
    async def auto_update_all_data(self):
        """全データを自動更新"""
        print("🚀 全既存データの自動AI分析更新開始")
        print("=" * 80)
        
        # 1. 更新が必要なチャンネル取得
        channels_to_update = self.get_channels_needing_update()
        
        if not channels_to_update:
            print("✅ 全てのチャンネルが既に最新のAI分析済みです")
            return
        
        print(f"\n🔄 {len(channels_to_update)} チャンネルを自動更新します")
        print()
        
        # 2. 順次処理
        for i, channel in enumerate(channels_to_update, 1):
            print(f"⏳ 進捗: {i}/{len(channels_to_update)} ({i/len(channels_to_update)*100:.1f}%)")
            
            await self.process_channel(channel)
            
            # レート制限対策
            if i < len(channels_to_update):
                print("⏸️ 3秒待機...")
                await asyncio.sleep(3)
            
            print()
        
        # 3. 最終レポート
        self.save_final_report()
        
        print("=" * 80)
        print("🎉 全既存データの自動AI分析更新完了！")
        print(f"📊 更新済み: {self.updated_count} チャンネル")
        print(f"❌ 失敗: {self.failed_count} チャンネル")
        if self.updated_count + self.failed_count > 0:
            print(f"📈 成功率: {self.updated_count/(self.updated_count+self.failed_count)*100:.1f}%")
    
    def save_final_report(self):
        """最終レポートを保存"""
        try:
            report = {
                "auto_update_timestamp": datetime.now().isoformat(),
                "total_processed": self.updated_count + self.failed_count,
                "successful_updates": self.updated_count,
                "failed_updates": self.failed_count,
                "success_rate": self.updated_count/(self.updated_count+self.failed_count)*100 if (self.updated_count+self.failed_count) > 0 else 0,
                "update_method": "sequential_auto_processing",
                "version": "2.0"
            }
            
            with open('auto_ai_update_report.json', 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"📄 最終レポートを auto_ai_update_report.json に保存しました")
            
        except Exception as e:
            print(f"❌ レポート保存エラー: {e}")

async def main():
    """メイン実行関数"""
    updater = AutoAllDataUpdater()
    
    try:
        await updater.auto_update_all_data()
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    asyncio.run(main())