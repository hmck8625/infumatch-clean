#!/usr/bin/env python3
"""
既存データのAI分析強化

@description 既存のBigQuery/Firestoreデータに新しいAI分析結果を追加
既存のai_analysis列を新しい高度なAI分析で置き換え

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

class ExistingDataAIEnhancer:
    """既存データのAI分析強化器"""
    
    def __init__(self):
        self.project_id = PROJECT_ID
        self.bigquery_client = bigquery.Client(project=self.project_id)
        self.firestore_client = firestore.Client(project=self.project_id)
        self.ai_analyzer = AdvancedChannelAnalyzer()
        self.enhanced_count = 0
        self.failed_count = 0
        
    def fetch_existing_channels(self, limit=5):
        """既存チャンネルデータを取得"""
        try:
            print(f"📊 BigQueryから既存データを取得中（最大{limit}件）...")
            
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
            WHERE is_active = true
            ORDER BY subscriber_count DESC
            LIMIT {limit}
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
                    'is_active': row.is_active,
                    'engagement_estimate': 0.0  # 計算する
                }
                
                # エンゲージメント推定値計算
                if channel_data['video_count'] > 0 and channel_data['subscriber_count'] > 0:
                    channel_data['engagement_estimate'] = round(
                        (channel_data['view_count'] / channel_data['video_count'] / channel_data['subscriber_count']) * 100, 2
                    )
                
                channels.append(channel_data)
            
            print(f"✅ {len(channels)} チャンネルのデータを取得しました")
            return channels
            
        except Exception as e:
            print(f"❌ BigQueryデータ取得エラー: {e}")
            return []
    
    async def enhance_channel_with_advanced_ai(self, channel_data):
        """1つのチャンネルに高度なAI分析を追加"""
        try:
            print(f"🤖 高度AI分析中: {channel_data['channel_title']}")
            
            # 新しいAI分析実行
            advanced_ai_analysis = await self.ai_analyzer.analyze_channel_comprehensive(channel_data)
            
            # 既存データと新AI分析を統合
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
            
            # チャンネル概要情報
            channel_summary = advanced_ai_analysis.get('channel_summary', {})
            enhanced_data['ai_content_style'] = channel_summary.get('content_style', '不明')
            enhanced_data['ai_expertise_level'] = channel_summary.get('expertise_level', '中')
            enhanced_data['ai_entertainment_value'] = channel_summary.get('entertainment_value', '中')
            enhanced_data['ai_educational_value'] = channel_summary.get('educational_value', '中')
            
            # オーディエンス情報
            audience_profile = advanced_ai_analysis.get('audience_profile', {})
            enhanced_data['ai_audience_size'] = audience_profile.get('audience_size', '不明')
            enhanced_data['ai_engagement_level'] = audience_profile.get('engagement_level', '中')
            enhanced_data['ai_reach_potential'] = audience_profile.get('reach_potential', '中程度')
            
            demographics = audience_profile.get('estimated_demographics', {})
            enhanced_data['ai_target_demographics'] = {
                'age': demographics.get('age', '20-40歳'),
                'gender': demographics.get('gender', '男女半々'),
                'income': demographics.get('income', '中')
            }
            
            print(f"✅ 高度AI分析完了: {channel_data['channel_title']}")
            print(f"   🎯 AIカテゴリ: {enhanced_data['ai_category']}")
            print(f"   🎭 サブカテゴリ: {', '.join(enhanced_data['ai_sub_categories'][:2])}")
            print(f"   🛡️ 安全性: {enhanced_data['ai_brand_safety_score']:.2f}")
            print(f"   📈 信頼度: {enhanced_data['ai_analysis_confidence']:.2f}")
            print(f"   💼 推奨商材: {enhanced_data['ai_top_product_category']}")
            print(f"   👥 対象年齢: {enhanced_data['ai_target_age']}")
            
            return enhanced_data
            
        except Exception as e:
            print(f"❌ 高度AI分析エラー ({channel_data['channel_title']}): {e}")
            return None
    
    def update_bigquery_with_enhanced_ai(self, enhanced_channels):
        """BigQueryにAI強化データを更新"""
        try:
            print("📊 BigQueryにAI強化データを更新中...")
            
            table_id = f"{self.project_id}.infumatch_data.influencers"
            updated_count = 0
            
            for channel in enhanced_channels:
                if channel:
                    try:
                        # 更新用クエリ
                        update_query = f"""
                        UPDATE `{table_id}`
                        SET 
                            ai_analysis = @ai_analysis,
                            updated_at = CURRENT_TIMESTAMP()
                        WHERE channel_id = @channel_id
                        """
                        
                        # ai_analysisを更新（新しい高度分析で置き換え）
                        new_ai_analysis = {
                            # 既存の簡易分析情報
                            "engagement_rate": channel['engagement_estimate'],
                            "content_quality_score": 0.8,
                            "brand_safety_score": channel['ai_brand_safety_score'],
                            "growth_potential": 0.7,
                            
                            # 新しい高度AI分析情報
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
                                "content_analysis": {
                                    "content_style": channel['ai_content_style'],
                                    "expertise_level": channel['ai_expertise_level'],
                                    "entertainment_value": channel['ai_entertainment_value'],
                                    "educational_value": channel['ai_educational_value']
                                },
                                "audience_profile": {
                                    "audience_size": channel['ai_audience_size'],
                                    "engagement_level": channel['ai_engagement_level'],
                                    "reach_potential": channel['ai_reach_potential'],
                                    "demographics": channel['ai_target_demographics']
                                },
                                "analysis_meta": {
                                    "confidence": channel['ai_analysis_confidence'],
                                    "enhanced_at": channel['ai_enhanced_at'],
                                    "version": "2.0"
                                }
                            },
                            
                            # 完全な分析結果
                            "full_analysis": channel['advanced_ai_analysis']
                        }
                        
                        job_config = bigquery.QueryJobConfig(
                            query_parameters=[
                                bigquery.ScalarQueryParameter("ai_analysis", "STRING", json.dumps(new_ai_analysis, ensure_ascii=False)),
                                bigquery.ScalarQueryParameter("channel_id", "STRING", channel['channel_id'])
                            ]
                        )
                        
                        query_job = self.bigquery_client.query(update_query, job_config=job_config)
                        query_job.result()
                        
                        updated_count += 1
                        print(f"  ✅ {channel['channel_title']} 更新完了")
                        
                    except Exception as e:
                        print(f"  ❌ {channel['channel_title']} 更新エラー: {e}")
                        continue
            
            print(f"✅ BigQueryに {updated_count} 件のAI強化データを更新しました")
            return updated_count
            
        except Exception as e:
            print(f"❌ BigQuery更新エラー: {e}")
            return 0
    
    def update_firestore_with_enhanced_ai(self, enhanced_channels):
        """FirestoreにAI強化データを更新"""
        try:
            print("🔥 FirestoreにAI強化データを更新中...")
            
            collection_ref = self.firestore_client.collection('influencers')
            updated_count = 0
            
            for channel in enhanced_channels:
                if channel:
                    try:
                        # Firestore用データ準備
                        firestore_data = {
                            'influencer_id': channel['influencer_id'],
                            'channel_id': channel['channel_id'],
                            'channel_title': channel['channel_title'],
                            'description': channel['description'],
                            'subscriber_count': channel['subscriber_count'],
                            'video_count': channel['video_count'],
                            'view_count': channel['view_count'],
                            'category': channel['category'],
                            'country': channel['country'],
                            'language': channel['language'],
                            'contact_email': channel['contact_email'],
                            'emails': channel['emails'],
                            'has_contact': channel['has_contact'],
                            'social_links': channel['social_links'],
                            'engagement_estimate': channel['engagement_estimate'],
                            'created_at': channel['created_at'],
                            'updated_at': datetime.now(),
                            'is_active': channel['is_active'],
                            
                            # AI強化情報
                            'ai_analysis': {
                                # 既存の簡易分析
                                "engagement_rate": channel['engagement_estimate'],
                                "content_quality_score": 0.8,
                                "brand_safety_score": channel['ai_brand_safety_score'],
                                "growth_potential": 0.7,
                                
                                # 新しい高度分析
                                "advanced": {
                                    "category": channel['ai_category'],
                                    "sub_categories": channel['ai_sub_categories'],
                                    "content_themes": channel['ai_content_themes'],
                                    "target_age": channel['ai_target_age'],
                                    "confidence": channel['ai_analysis_confidence'],
                                    "safety_score": channel['ai_brand_safety_score'],
                                    "top_product": channel['ai_top_product_category'],
                                    "match_score": channel['ai_top_product_match_score'],
                                    "audience_size": channel['ai_audience_size'],
                                    "demographics": channel['ai_target_demographics'],
                                    "enhanced_at": channel['ai_enhanced_at']
                                },
                                
                                # 完全な分析結果
                                "full_analysis": channel['advanced_ai_analysis']
                            }
                        }
                        
                        # ドキュメント更新
                        doc_ref = collection_ref.document(channel['channel_id'])
                        doc_ref.set(firestore_data, merge=True)
                        updated_count += 1
                        
                    except Exception as e:
                        print(f"❌ Firestore更新エラー ({channel['channel_title']}): {e}")
                        continue
            
            print(f"✅ Firestoreに {updated_count} 件のAI強化データを更新しました")
            return updated_count
            
        except Exception as e:
            print(f"❌ Firestore更新エラー: {e}")
            return 0
    
    async def enhance_existing_data_with_advanced_ai(self, limit=5):
        """既存データを高度AI分析で強化"""
        print("🚀 既存データの高度AI分析強化開始")
        print("=" * 80)
        
        print("🔧 実行内容:")
        print("  1. BigQueryから既存データを取得")
        print("  2. 各チャンネルに高度AI分析を実行")
        print("  3. BigQueryのai_analysis列を更新")
        print("  4. Firestoreのai_analysis情報を更新")
        print("  5. 既存データは保持し、AI分析のみ強化")
        print()
        
        # 1. 既存データ取得
        existing_channels = self.fetch_existing_channels(limit)
        if not existing_channels:
            print("❌ 既存データが見つかりません")
            return
        
        print(f"📊 {len(existing_channels)} チャンネルの高度AI分析を開始...")
        print()
        
        # 2. 高度AI分析実行
        enhanced_channels = []
        for i, channel in enumerate(existing_channels, 1):
            print(f"⏳ 進捗: {i}/{len(existing_channels)} ({i/len(existing_channels)*100:.1f}%)")
            
            try:
                enhanced_channel = await self.enhance_channel_with_advanced_ai(channel)
                if enhanced_channel:
                    enhanced_channels.append(enhanced_channel)
                    self.enhanced_count += 1
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
        
        print(f"\n📊 高度AI分析完了:")
        print(f"  - 成功: {self.enhanced_count} チャンネル")
        print(f"  - 失敗: {self.failed_count} チャンネル")
        print()
        
        if enhanced_channels:
            # 3. BigQuery更新
            bigquery_count = self.update_bigquery_with_enhanced_ai(enhanced_channels)
            
            # 4. Firestore更新
            firestore_count = self.update_firestore_with_enhanced_ai(enhanced_channels)
            
            # 5. 結果保存
            self.save_enhancement_report(enhanced_channels)
            
            print("\n" + "=" * 80)
            print("🎉 既存データの高度AI分析強化完了！")
            print(f"📊 BigQuery更新: {bigquery_count} 件")
            print(f"🔥 Firestore更新: {firestore_count} 件")
            print(f"📈 AI分析成功率: {self.enhanced_count/(self.enhanced_count+self.failed_count)*100:.1f}%")
            print()
            print("💡 確認方法:")
            print("  - BigQuery: ai_analysis列の'advanced_analysis'フィールド")
            print("  - Firestore: ai_analysis.advanced フィールド")
            
        else:
            print("❌ AI強化済みデータがありません")
    
    def save_enhancement_report(self, enhanced_channels):
        """AI強化レポートを保存"""
        try:
            # 強化データ保存
            enhancement_data = []
            for channel in enhanced_channels:
                if channel:
                    enhancement_data.append({
                        "channel_id": channel["channel_id"],
                        "channel_title": channel["channel_title"],
                        "original_category": channel["category"],
                        "ai_category": channel["ai_category"],
                        "ai_sub_categories": channel["ai_sub_categories"],
                        "ai_content_themes": channel["ai_content_themes"],
                        "ai_target_age": channel["ai_target_age"],
                        "ai_confidence": channel["ai_analysis_confidence"],
                        "ai_safety_score": channel["ai_brand_safety_score"],
                        "ai_top_product": channel["ai_top_product_category"],
                        "ai_match_score": channel["ai_top_product_match_score"],
                        "ai_enhanced_at": channel["ai_enhanced_at"]
                    })
            
            with open('existing_data_enhanced.json', 'w', encoding='utf-8') as f:
                json.dump(enhancement_data, f, ensure_ascii=False, indent=2)
            
            # レポート作成
            report = {
                "enhancement_timestamp": datetime.now().isoformat(),
                "total_processed": len(enhanced_channels),
                "successful_enhancements": self.enhanced_count,
                "failed_enhancements": self.failed_count,
                "success_rate": self.enhanced_count/(self.enhanced_count+self.failed_count)*100 if (self.enhanced_count+self.failed_count) > 0 else 0,
                "enhancement_summary": {
                    "categories_enhanced": len(set(ch["ai_category"] for ch in enhanced_channels if ch)),
                    "avg_confidence": sum(ch["ai_analysis_confidence"] for ch in enhanced_channels if ch) / len(enhanced_channels),
                    "avg_safety_score": sum(ch["ai_brand_safety_score"] for ch in enhanced_channels if ch) / len(enhanced_channels),
                    "product_categories": list(set(ch["ai_top_product_category"] for ch in enhanced_channels if ch))
                },
                "enhanced_channels": enhancement_data
            }
            
            with open('ai_enhancement_report.json', 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"📄 AI強化データを existing_data_enhanced.json に保存しました")
            print(f"📊 強化レポートを ai_enhancement_report.json に保存しました")
            
        except Exception as e:
            print(f"❌ レポート保存エラー: {e}")

async def main():
    """メイン実行関数"""
    enhancer = ExistingDataAIEnhancer()
    
    try:
        # テスト用に5件から開始
        await enhancer.enhance_existing_data_with_advanced_ai(limit=5)
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    asyncio.run(main())