#!/usr/bin/env python3
"""
Firestoreにテストデータを追加
"""

import os
from google.cloud import firestore

# 環境変数設定
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/hamazakidaisuke/Desktop/プロジェクト/250614_hac_iftool/hackathon-462905-7d72a76d3742.json'

def add_test_data():
    try:
        print("🔥 Adding test data to Firestore...")
        
        # Firestoreクライアント初期化
        db = firestore.Client(project="hackathon-462905")
        
        # テストデータ
        test_influencers = [
            {
                'channel_id': 'UC1234567890',
                'channel_title': 'Tech Review Japan',
                'subscriber_count': 85000,
                'view_count': 12500000,
                'video_count': 156,
                'primary_category': 'テクノロジー',
                'description': '最新のガジェットレビューと技術解説を行うチャンネル',
                'thumbnail_url': 'https://via.placeholder.com/120x120?text=Tech+Review',
                'engagement_rate': 4.5,
                'business_email': 'techreview@example.com',
                'country': 'JP',
                'default_language': 'ja',
                'fetched_at': firestore.SERVER_TIMESTAMP
            },
            {
                'channel_id': 'UC2345678901',
                'channel_title': '料理研究家ゆうこ',
                'subscriber_count': 52000,
                'view_count': 8900000,
                'video_count': 243,
                'primary_category': '料理',
                'description': '簡単で美味しい家庭料理のレシピを紹介',
                'thumbnail_url': 'https://via.placeholder.com/120x120?text=料理',
                'engagement_rate': 5.2,
                'business_email': 'yuko.cooking@example.com',
                'country': 'JP',
                'default_language': 'ja',
                'fetched_at': firestore.SERVER_TIMESTAMP
            },
            {
                'channel_id': 'UC3456789012',
                'channel_title': 'Fitness Life Tokyo',
                'subscriber_count': 38000,
                'view_count': 5670000,
                'video_count': 89,
                'primary_category': 'フィットネス',
                'description': '自宅でできるトレーニングとヘルシーライフスタイル',
                'thumbnail_url': 'https://via.placeholder.com/120x120?text=Fitness',
                'engagement_rate': 6.1,
                'business_email': 'fitness.tokyo@example.com',
                'country': 'JP',
                'default_language': 'ja',
                'fetched_at': firestore.SERVER_TIMESTAMP
            },
            {
                'channel_id': 'UC4567890123',
                'channel_title': 'ビューティー研究所',
                'subscriber_count': 92000,
                'view_count': 21000000,
                'video_count': 312,
                'primary_category': '美容',
                'description': 'メイクアップチュートリアルとスキンケア情報',
                'thumbnail_url': 'https://via.placeholder.com/120x120?text=Beauty',
                'engagement_rate': 3.8,
                'business_email': 'beauty.lab@example.com',
                'country': 'JP',
                'default_language': 'ja',
                'fetched_at': firestore.SERVER_TIMESTAMP
            },
            {
                'channel_id': 'UC5678901234',
                'channel_title': 'ゲーム実況チャンネル',
                'subscriber_count': 76000,
                'view_count': 18900000,
                'video_count': 428,
                'primary_category': 'ゲーム',
                'description': '最新ゲームの実況プレイと攻略情報',
                'thumbnail_url': 'https://via.placeholder.com/120x120?text=Gaming',
                'engagement_rate': 4.2,
                'business_email': 'game.channel@example.com',
                'country': 'JP',
                'default_language': 'ja',
                'fetched_at': firestore.SERVER_TIMESTAMP
            }
        ]
        
        # データをFirestoreに追加
        collection_ref = db.collection('youtube_influencers')
        
        for influencer in test_influencers:
            doc_ref = collection_ref.document(influencer['channel_id'])
            doc_ref.set(influencer)
            print(f"✅ Added: {influencer['channel_title']}")
        
        print(f"🎉 Successfully added {len(test_influencers)} test influencers to Firestore!")
        
        # 確認
        docs = list(collection_ref.limit(10).stream())
        print(f"📊 Total documents in collection: {len(docs)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding test data: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    add_test_data()