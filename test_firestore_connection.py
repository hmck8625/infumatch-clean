#!/usr/bin/env python3
"""
Firestore接続テストスクリプト
"""

import os
import sys
sys.path.append('./backend')

# 環境変数設定
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/hamazakidaisuke/Desktop/プロジェクト/250614_hac_iftool/hackathon-462905-fd4f661125e5.json'

def test_firestore_connection():
    """Firestoreの接続とデータ確認"""
    try:
        from google.cloud import firestore
        
        # Firestoreクライアント初期化
        db = firestore.Client(project="hackathon-462905")
        print("✅ Firestore接続成功")
        
        # youtube_influencers コレクションからデータを取得
        collection_ref = db.collection('youtube_influencers')
        docs = collection_ref.limit(5).stream()
        
        print("\n📊 Firestore内のデータ:")
        count = 0
        for doc in docs:
            count += 1
            data = doc.to_dict()
            print(f"{count}. {data.get('channel_title', 'タイトル不明')} (ID: {doc.id})")
            print(f"   登録者数: {data.get('subscriber_count', 0):,}")
            print(f"   カテゴリ: {data.get('primary_category', '不明')}")
        
        if count == 0:
            print("❌ データが見つかりません")
        else:
            print(f"\n✅ {count}件のデータを確認")
            
        return count > 0
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

if __name__ == "__main__":
    test_firestore_connection()