#!/usr/bin/env python3
"""
残りチャンネルの更新

@description 未更新の5チャンネルを更新
"""

import asyncio
import json
from datetime import datetime
from google.cloud import firestore, bigquery
from services.ai_channel_analyzer import AdvancedChannelAnalyzer

# 残り5チャンネルのチャンネルID
REMAINING_CHANNEL_IDS = [
    "UCgokOIWB73ZUg5NdYU9zIUQ",  # リカルガ【ゆっくり実況】
    "UCZ9baV335FyJiNa4IExtoQw",  # ほとんどホラーゲーム実況ですが何か?
    "UC4KXxp8JMm-NtfMXG-wbvdw",  # ノノムラ猫の考えるゲーム配信
    "UCrp9JdBWuMrkwbGwmfaZtsA",  # DECORTÉ Concierge Channel
    "UCQSn0XEy6Nz52vKH6n-GCKw"   # りお
]

class RemainingChannelsUpdater:
    """残りチャンネルの更新器"""
    
    def __init__(self):
        self.project_id = "hackathon-462905"
        self.bigquery_client = bigquery.Client(project=self.project_id)
        self.firestore_client = firestore.Client(project=self.project_id)
        self.ai_analyzer = AdvancedChannelAnalyzer()
        self.updated_count = 0
        self.failed_count = 0
    
    def fetch_remaining_channels(self):
        """残りチャンネルのデータを取得"""
        try:
            print("📊 残りチャンネルのデータを取得中...")
            
            channel_ids_str = "', '".join(REMAINING_CHANNEL_IDS)
            
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
            
            print(f"✅ {len(channels)} チャンネルのデータを取得しました")
            for ch in channels:
                print(f"  - {ch['channel_title']}")
            
            return channels
            
        except Exception as e:
            print(f"❌ データ取得エラー: {e}")
            return []
    
    async def process_channel(self, channel_data):
        """1つのチャンネルを処理"""
        try:
            print(f"\n🤖 AI分析中: {channel_data['channel_title']}")
            print(f"   カテゴリ: {channel_data['category']}")
            print(f"   登録者: {channel_data['subscriber_count']:,}人")
            
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
            print(f"   🎭 サブカテゴリ: {', '.join(enhanced_data['ai_sub_categories'][:2])}")
            print(f"   🛡️ 安全性: {enhanced_data['ai_brand_safety_score']:.2f}")
            print(f"   💼 推奨商材: {enhanced_data['ai_top_product_category']}")
            print(f"   👥 対象年齢: {enhanced_data['ai_target_age']}")
            
            self.updated_count += 1
            return True
            
        except Exception as e:
            print(f"❌ エラー ({channel_data['channel_title']}): {e}")
            self.failed_count += 1
            return False
    
    async def update_databases(self, enhanced_channel):
        """データベースを更新"""
        await self.update_bigquery_single(enhanced_channel)
        await self.update_firestore_single(enhanced_channel)
    
    async def update_bigquery_single(self, channel):
        """BigQueryを単体更新"""
        try:
            table_id = f"{self.project_id}.infumatch_data.influencers"
            
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
    
    async def update_remaining_channels(self):
        """残りチャンネルを更新"""
        print("🚀 残り5チャンネルのAI分析更新開始")
        print("=" * 80)
        
        # データ取得
        channels = self.fetch_remaining_channels()
        
        if not channels:
            print("❌ チャンネルデータが取得できませんでした")
            return
        
        print(f"\n🔄 {len(channels)} チャンネルを更新します")
        
        # 順次処理
        for i, channel in enumerate(channels, 1):
            print(f"\n⏳ 進捗: {i}/{len(channels)} ({i/len(channels)*100:.1f}%)")
            
            await self.process_channel(channel)
            
            # レート制限対策
            if i < len(channels):
                print("⏸️ 3秒待機...")
                await asyncio.sleep(3)
        
        print("\n" + "=" * 80)
        print("🎉 残りチャンネルの更新完了！")
        print(f"📊 更新済み: {self.updated_count} チャンネル")
        print(f"❌ 失敗: {self.failed_count} チャンネル")
        if self.updated_count + self.failed_count > 0:
            print(f"📈 成功率: {self.updated_count/(self.updated_count+self.failed_count)*100:.1f}%")

async def main():
    """メイン実行関数"""
    updater = RemainingChannelsUpdater()
    
    try:
        await updater.update_remaining_channels()
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    asyncio.run(main())