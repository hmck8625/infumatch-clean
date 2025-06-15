#!/usr/bin/env python3
"""
Quick Firestore データ挿入
"""

import json
import os
import sys
from google.cloud import firestore

# 環境変数設定
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/hamazakidaisuke/Desktop/プロジェクト/250614_hac_iftool/hackathon-462905-fd4f661125e5.json'

def quick_insert():
    """実データをFirestoreに素早く挿入"""
    try:
        # Firestoreクライアント初期化
        db = firestore.Client(project="hackathon-462905")
        print("✅ Firestore接続成功")
        
        # データファイル読み込み
        with open('firestore_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📊 {len(data)} 件のデータを読み込み")
        
        # 最初の3件だけ挿入（テスト用）
        collection_ref = db.collection('youtube_influencers')
        
        for i, influencer in enumerate(data[:10]):  # 最初の10件だけ
            # データをFirestore形式に変換
            doc_data = {
                'channel_id': influencer['channel_id'],
                'channel_title': influencer['channel_title'],
                'description': influencer.get('description', ''),
                'subscriber_count': influencer.get('subscriber_count', 0),
                'video_count': influencer.get('video_count', 0),
                'view_count': influencer.get('view_count', 0),
                'primary_category': influencer.get('category', 'その他'),
                'country': influencer.get('country', 'JP'),
                'default_language': influencer.get('language', 'ja'),
                'engagement_rate': influencer.get('engagement_metrics', {}).get('engagement_rate', 0.0),
                'business_email': influencer.get('contact_info', {}).get('primary_email'),
                'thumbnail_url': f"https://yt3.ggpht.com/a/default-user=s88-c-k-c0x00ffffff-no-rj",
                'fetched_at': firestore.SERVER_TIMESTAMP,
                'data_quality_score': 0.8 if influencer.get('contact_info', {}).get('primary_email') else 0.5
            }
            
            # ドキュメントを追加
            doc_ref = collection_ref.document(influencer['channel_id'])
            doc_ref.set(doc_data)
            print(f"   {i+1}. {influencer['channel_title']} - 登録完了")
        
        print("✅ Firestore登録完了")
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

if __name__ == "__main__":
    quick_insert()