#!/usr/bin/env python3
"""
既存のinfluencersコレクションのデータ構造を確認
"""

import os
from google.cloud import firestore

# 環境変数設定
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/hamazakidaisuke/Desktop/プロジェクト/250614_hac_iftool/hackathon-462905-7d72a76d3742.json'

def check_influencers_collection():
    try:
        print("🔍 Checking influencers collection...")
        
        # Firestoreクライアント初期化
        db = firestore.Client(project="hackathon-462905")
        
        # influencersコレクションを確認
        collection_ref = db.collection('influencers')
        docs = list(collection_ref.limit(3).stream())
        
        print(f"📊 Found {len(docs)} documents in 'influencers' collection")
        
        if docs:
            for i, doc in enumerate(docs):
                print(f"\n📄 Document {i+1}: {doc.id}")
                data = doc.to_dict()
                print(f"📋 Keys: {list(data.keys())}")
                
                # サンプルデータの内容を表示
                for key, value in data.items():
                    if isinstance(value, str) and len(value) > 100:
                        print(f"  {key}: {value[:100]}...")
                    else:
                        print(f"  {key}: {value}")
        else:
            print("❌ No documents found in 'influencers' collection")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking collection: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_influencers_collection()