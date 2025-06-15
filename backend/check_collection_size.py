#!/usr/bin/env python3
"""
Firestoreコレクション詳細確認スクリプト

@description influencersコレクションの全ドキュメント数とサンプルを確認
"""

from google.cloud import firestore

def check_influencers_collection():
    """influencersコレクション詳細確認"""
    print("🔍 influencersコレクション詳細確認...")
    
    try:
        # Firestoreクライアント初期化
        db = firestore.Client(project="hackathon-462905")
        
        # 全ドキュメント取得（制限なし）
        collection_ref = db.collection('influencers')
        docs = list(collection_ref.get())
        
        print(f"📊 総ドキュメント数: {len(docs)}")
        
        if docs:
            print(f"\n📋 チャンネルリスト:")
            for i, doc in enumerate(docs, 1):
                data = doc.to_dict()
                title = data.get('channel_title', 'Unknown')
                subscribers = data.get('subscriber_count', 0)
                category = data.get('category', 'Unknown')
                collection_method = data.get('collection_method', 'Unknown')
                
                print(f"{i:2d}. {title}")
                print(f"    登録者: {subscribers:,} | カテゴリ: {category} | 収集方法: {collection_method}")
        
        # カテゴリ別統計
        categories = {}
        collection_methods = {}
        
        for doc in docs:
            data = doc.to_dict()
            cat = data.get('category', 'Unknown')
            method = data.get('collection_method', 'Unknown')
            
            categories[cat] = categories.get(cat, 0) + 1
            collection_methods[method] = collection_methods.get(method, 0) + 1
        
        print(f"\n📈 カテゴリ別統計:")
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {category}: {count} チャンネル")
        
        print(f"\n🔧 収集方法別統計:")
        for method, count in sorted(collection_methods.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {method}: {count} チャンネル")
        
        return len(docs)
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return 0

def main():
    total_count = check_influencers_collection()
    print(f"\n🎯 最終結果: {total_count} チャンネルがFirestoreに登録されています")

if __name__ == "__main__":
    main()