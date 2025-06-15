#!/usr/bin/env python3
"""
Firestore認証と接続テスト
"""

import os
import sys

# 環境変数設定
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/hamazakidaisuke/Desktop/プロジェクト/250614_hac_iftool/hackathon-462905-7d72a76d3742.json'

def test_firestore_auth():
    try:
        print("🔍 Testing Firestore authentication...")
        
        # Google Cloudライブラリのインポート
        from google.cloud import firestore
        from google.auth import default
        
        print("✅ Google Cloud libraries imported successfully")
        
        # 認証情報を確認
        try:
            credentials, project = default()
            print(f"📋 Project ID from credentials: {project}")
            print(f"🔑 Credentials type: {type(credentials).__name__}")
        except Exception as auth_error:
            print(f"❌ Authentication error: {auth_error}")
            return False
        
        # Firestoreクライアント初期化
        try:
            db = firestore.Client(project="hackathon-462905")
            print("✅ Firestore client initialized")
        except Exception as client_error:
            print(f"❌ Firestore client error: {client_error}")
            return False
        
        # 簡単な操作テスト
        try:
            # テストドキュメントの作成
            test_ref = db.collection('connection_test').document('test')
            test_ref.set({
                'timestamp': firestore.SERVER_TIMESTAMP,
                'test': True
            })
            print("✅ Test document created")
            
            # テストドキュメントの読み取り
            doc = test_ref.get()
            if doc.exists:
                print("✅ Test document read successfully")
                print(f"📄 Document data: {doc.to_dict()}")
            else:
                print("❌ Test document not found")
                return False
                
            # テストドキュメントの削除
            test_ref.delete()
            print("✅ Test document deleted")
            
        except Exception as operation_error:
            print(f"❌ Firestore operation error: {operation_error}")
            return False
        
        # youtube_influencersコレクションの確認
        try:
            collection_ref = db.collection('youtube_influencers')
            docs = list(collection_ref.limit(1).stream())
            print(f"📊 youtube_influencers collection: {len(docs)} documents found")
            
            if docs:
                sample_doc = docs[0]
                print(f"📄 Sample document ID: {sample_doc.id}")
                data = sample_doc.to_dict()
                print(f"📋 Sample document keys: {list(data.keys())}")
        except Exception as collection_error:
            print(f"❌ Collection access error: {collection_error}")
            return False
        
        print("🎉 All Firestore tests passed!")
        return True
        
    except ImportError as import_error:
        print(f"❌ Import error: {import_error}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_firestore_auth()
    sys.exit(0 if success else 1)