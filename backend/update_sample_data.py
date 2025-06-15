#!/usr/bin/env python3
"""
サンプルデータの名前を変更
"""

import os
from google.cloud import firestore

# 環境変数設定
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/hamazakidaisuke/Desktop/プロジェクト/250614_hac_iftool/hackathon-462905-7d72a76d3742.json'

def update_sample_data():
    try:
        print("🔄 Updating sample data names...")
        
        # Firestoreクライアント初期化
        db = firestore.Client(project="hackathon-462905")
        
        # youtube_influencersコレクションのデータを更新
        collection_ref = db.collection('youtube_influencers')
        docs = list(collection_ref.stream())
        
        for doc in docs:
            data = doc.to_dict()
            # 名前にSAMPLEプレフィックスを追加
            if not data.get('channel_title', '').startswith('[SAMPLE]'):
                updated_data = data.copy()
                updated_data['channel_title'] = f"[SAMPLE] {data.get('channel_title', '')}"
                
                # ドキュメントを更新
                doc.reference.set(updated_data)
                print(f"✅ Updated: {updated_data['channel_title']}")
        
        print(f"🎉 Updated {len(docs)} sample documents")
        return True
        
    except Exception as e:
        print(f"❌ Error updating sample data: {e}")
        return False

if __name__ == "__main__":
    update_sample_data()