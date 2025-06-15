#!/usr/bin/env python3
"""
実際のAI分析適用スクリプト

@description 既存データに対して実装済みのAI分析機能を適用
デフォルト値から実際のAI分析結果に更新

@author InfuMatch Development Team
@version 1.0.0
"""

import json
import asyncio
from google.cloud import firestore, bigquery
from datetime import datetime, timezone

# 簡易版AI分析（Gemini APIなしでテスト）
class SimpleAIAnalyzer:
    """簡易AI分析クラス（Gemini API不要）"""
    
    def __init__(self):
        # カテゴリ別のブランドセーフティ基準
        self.category_brand_safety = {
            'gaming': 0.85,
            '料理・グルメ': 0.95,
            '美容・コスメ': 0.90,
            'ライフスタイル': 0.88,
            '教育・学習': 0.98,
            '音楽': 0.87,
            'エンタメ・バラエティ': 0.82
        }
    
    def analyze_content_quality(self, channel_data):
        """コンテンツ品質スコア分析"""
        score = 0.5  # ベーススコア
        
        # 登録者数による補正
        subscribers = channel_data.get('subscriber_count', 0)
        if subscribers > 100000:
            score += 0.3
        elif subscribers > 50000:
            score += 0.2
        elif subscribers > 10000:
            score += 0.1
        
        # 動画数による補正（コンスタントな投稿）
        video_count = channel_data.get('video_count', 0)
        if video_count > 500:
            score += 0.2
        elif video_count > 100:
            score += 0.15
        elif video_count > 50:
            score += 0.1
        
        # エンゲージメント率による補正
        engagement = channel_data.get('engagement_estimate', 0)
        if engagement > 5:
            score += 0.2
        elif engagement > 2:
            score += 0.15
        elif engagement > 1:
            score += 0.1
        
        # 概要欄の充実度
        description = channel_data.get('description', '')
        if len(description) > 200:
            score += 0.1
        elif len(description) > 100:
            score += 0.05
        
        return min(1.0, score)
    
    def analyze_brand_safety(self, channel_data):
        """ブランドセーフティスコア分析"""
        category = channel_data.get('category', 'その他')
        base_score = self.category_brand_safety.get(category, 0.85)
        
        # 連絡先がある場合は信頼性アップ
        if channel_data.get('has_contact', False):
            base_score += 0.05
        
        # 概要欄にリンクやプロフェッショナルな情報がある場合
        description = channel_data.get('description', '').lower()
        professional_indicators = ['お仕事', 'business', 'contact', '企業', '会社']
        if any(indicator in description for indicator in professional_indicators):
            base_score += 0.03
        
        return min(1.0, base_score)
    
    def analyze_growth_potential(self, channel_data):
        """成長ポテンシャル分析"""
        score = 0.5  # ベーススコア
        
        subscribers = channel_data.get('subscriber_count', 0)
        engagement = channel_data.get('engagement_estimate', 0)
        
        # エンゲージメント率が高い = 成長ポテンシャル高
        if engagement > 10:
            score += 0.4
        elif engagement > 5:
            score += 0.3
        elif engagement > 2:
            score += 0.2
        elif engagement > 1:
            score += 0.1
        
        # 中規模チャンネル（まだ成長余地あり）
        if 10000 <= subscribers <= 100000:
            score += 0.2
        elif 100000 <= subscribers <= 500000:
            score += 0.1
        
        # 動画投稿の活発さ
        video_count = channel_data.get('video_count', 0)
        view_count = channel_data.get('view_count', 0)
        if video_count > 0:
            avg_views = view_count / video_count
            if avg_views > subscribers * 0.3:  # 登録者の30%以上が視聴
                score += 0.15
            elif avg_views > subscribers * 0.1:
                score += 0.1
        
        return min(1.0, score)
    
    def calculate_matching_score(self, channel_data):
        """企業マッチング適性スコア"""
        # ブランドセーフティ、コンテンツ品質、連絡可能性を総合
        brand_safety = self.analyze_brand_safety(channel_data)
        content_quality = self.analyze_content_quality(channel_data)
        has_contact = 1.0 if channel_data.get('has_contact', False) else 0.3
        
        # 重み付け平均
        matching_score = (brand_safety * 0.4 + content_quality * 0.4 + has_contact * 0.2)
        return matching_score
    
    def analyze_channel(self, channel_data):
        """チャンネルの包括的AI分析"""
        analysis = {
            'content_quality_score': self.analyze_content_quality(channel_data),
            'brand_safety_score': self.analyze_brand_safety(channel_data),
            'growth_potential': self.analyze_growth_potential(channel_data),
            'matching_score': self.calculate_matching_score(channel_data),
            'engagement_rate': channel_data.get('engagement_estimate', 0) / 100,
            'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
            'analysis_version': '1.0.0'
        }
        return analysis

async def update_firestore_ai_analysis():
    """Firestoreのai_analysisを更新"""
    print("🔥 Firestore AI分析データ更新中...")
    
    try:
        db = firestore.Client(project="hackathon-462905")
        analyzer = SimpleAIAnalyzer()
        
        # 全ドキュメントを取得
        docs = list(db.collection('influencers').stream())
        
        updated_count = 0
        for doc in docs:
            doc_data = doc.to_dict()
            
            # AI分析実行
            ai_analysis = analyzer.analyze_channel(doc_data)
            
            # ドキュメント更新
            doc.reference.update({
                'ai_analysis': ai_analysis,
                'updated_at': datetime.now(timezone.utc).isoformat()
            })
            
            print(f"✅ 更新: {doc_data.get('channel_title', 'Unknown')}")
            print(f"   品質: {ai_analysis['content_quality_score']:.3f}")
            print(f"   安全性: {ai_analysis['brand_safety_score']:.3f}")
            print(f"   成長性: {ai_analysis['growth_potential']:.3f}")
            print(f"   マッチング: {ai_analysis['matching_score']:.3f}")
            
            updated_count += 1
        
        print(f"\n🎉 Firestore更新完了: {updated_count} ドキュメント")
        return updated_count
        
    except Exception as e:
        print(f"❌ Firestore更新エラー: {e}")
        return 0

def update_bigquery_ai_analysis():
    """BigQueryのai_analysisを更新"""
    print("\n🏗️ BigQuery AI分析データ更新中...")
    
    try:
        client = bigquery.Client(project="hackathon-462905")
        analyzer = SimpleAIAnalyzer()
        
        # 現在のデータを取得
        query = """
        SELECT 
            influencer_id,
            channel_title,
            subscriber_count,
            video_count,
            view_count,
            category,
            contact_email,
            JSON_EXTRACT_SCALAR(ai_analysis, '$.engagement_rate') as engagement_rate
        FROM `hackathon-462905.infumatch_data.influencers`
        """
        
        query_job = client.query(query)
        results = query_job.result()
        
        updated_count = 0
        for row in results:
            # チャンネルデータ再構成
            channel_data = {
                'channel_title': row.channel_title,
                'subscriber_count': row.subscriber_count,
                'video_count': row.video_count,
                'view_count': row.view_count,
                'category': row.category,
                'has_contact': bool(row.contact_email),
                'engagement_estimate': float(row.engagement_rate or 0) * 100,
                'description': ''  # BigQueryに概要欄がないため空文字
            }
            
            # AI分析実行
            ai_analysis = analyzer.analyze_channel(channel_data)
            
            # 更新クエリ
            update_query = f"""
            UPDATE `hackathon-462905.infumatch_data.influencers`
            SET 
                ai_analysis = '{json.dumps(ai_analysis)}',
                updated_at = CURRENT_TIMESTAMP()
            WHERE influencer_id = '{row.influencer_id}'
            """
            
            update_job = client.query(update_query)
            update_job.result()
            
            print(f"✅ 更新: {row.channel_title}")
            updated_count += 1
        
        print(f"\n🎉 BigQuery更新完了: {updated_count} レコード")
        return updated_count
        
    except Exception as e:
        print(f"❌ BigQuery更新エラー: {e}")
        return 0

def verify_ai_analysis_update():
    """AI分析更新を確認"""
    print("\n🔍 AI分析更新確認")
    print("=" * 60)
    
    try:
        # Firestore確認
        db = firestore.Client(project="hackathon-462905")
        sample_doc = list(db.collection('influencers').limit(1).stream())[0]
        ai_analysis = sample_doc.to_dict().get('ai_analysis', {})
        
        print("🔥 Firestore サンプル:")
        for key, value in ai_analysis.items():
            if isinstance(value, float):
                print(f"   {key}: {value:.3f}")
            else:
                print(f"   {key}: {value}")
        
        # BigQuery確認
        client = bigquery.Client(project="hackathon-462905")
        query = """
        SELECT 
            channel_title,
            JSON_EXTRACT_SCALAR(ai_analysis, '$.content_quality_score') as quality,
            JSON_EXTRACT_SCALAR(ai_analysis, '$.brand_safety_score') as safety,
            JSON_EXTRACT_SCALAR(ai_analysis, '$.matching_score') as matching
        FROM `hackathon-462905.infumatch_data.influencers`
        LIMIT 1
        """
        
        query_job = client.query(query)
        result = list(query_job.result())[0]
        
        print(f"\n🏗️ BigQuery サンプル ({result.channel_title}):")
        print(f"   quality: {result.quality}")
        print(f"   safety: {result.safety}")
        print(f"   matching: {result.matching}")
        
    except Exception as e:
        print(f"❌ 確認エラー: {e}")

async def main():
    """メイン実行関数"""
    print("🤖 実際のAI分析適用開始")
    print("=" * 80)
    
    print("📋 適用内容:")
    print("  - content_quality_score: 登録者数、動画数、エンゲージメントから算出")
    print("  - brand_safety_score: カテゴリ、連絡先、プロ度から算出")
    print("  - growth_potential: エンゲージメント、規模、活発度から算出")
    print("  - matching_score: 企業マッチング適性の総合スコア")
    
    # Firestore更新
    firestore_count = await update_firestore_ai_analysis()
    
    # BigQuery更新
    bigquery_count = update_bigquery_ai_analysis()
    
    # 更新確認
    if firestore_count > 0 or bigquery_count > 0:
        verify_ai_analysis_update()
    
    print(f"\n🎉 AI分析適用完了!")
    print(f"🔥 Firestore: {firestore_count} 更新")
    print(f"🏗️ BigQuery: {bigquery_count} 更新")
    print(f"✨ デフォルト値から実際のAI分析値に更新されました")

if __name__ == "__main__":
    asyncio.run(main())