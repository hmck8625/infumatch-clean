#!/usr/bin/env python3
"""
Firestore 直接データ挿入スクリプト

@description Google Cloud Firestore Client Libraryを使用してデータを直接挿入
gcloud CLIではなくPythonライブラリを使用

@author InfuMatch Development Team
@version 1.0.0
"""

import json
import os
from datetime import datetime, timezone
from google.cloud import firestore

def initialize_firestore():
    """Firestore クライアントを初期化"""
    try:
        # プロジェクトIDを設定
        project_id = "hackathon-462905"
        
        # デフォルト認証を使用（gcloud auth application-default loginの認証情報）
        # os.environ['GOOGLE_APPLICATION_CREDENTIALS'] は使用しない
        
        # Firestoreクライアントを初期化
        db = firestore.Client(project=project_id)
        print(f"✅ Firestore クライアント初期化完了 (プロジェクト: {project_id})")
        return db
        
    except Exception as e:
        print(f"❌ Firestore クライアント初期化エラー: {e}")
        return None

def load_formatted_data():
    """整形済みデータを読み込み"""
    try:
        with open('firestore_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ {len(data)} 件の整形済みデータを読み込みました")
        return data
    except FileNotFoundError:
        print("❌ firestore_data.json が見つかりません")
        return []
    except Exception as e:
        print(f"❌ データ読み込みエラー: {e}")
        return []

def insert_to_firestore(db, formatted_data):
    """Firestoreにデータを挿入"""
    print("\n🔥 Firestore にデータを挿入中...")
    
    collection_ref = db.collection('influencers')
    
    success_count = 0
    for i, doc_data in enumerate(formatted_data, 1):
        try:
            # channel_idをドキュメントIDとして使用
            doc_id = doc_data['channel_id']
            
            # ドキュメントを作成
            doc_ref = collection_ref.document(doc_id)
            doc_ref.set(doc_data)
            
            print(f"✅ {i}/{len(formatted_data)} 完了: {doc_data['channel_title']}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ {i}/{len(formatted_data)} 失敗: {doc_data.get('channel_title', 'Unknown')} - {e}")
    
    print(f"\n🎉 Firestore 挿入完了: {success_count}/{len(formatted_data)} 件成功")
    return success_count

def verify_firestore_data(db):
    """Firestoreのデータを確認"""
    print("\n🔍 Firestore データ確認中...")
    
    try:
        collection_ref = db.collection('influencers')
        docs = collection_ref.stream()
        
        doc_count = 0
        for doc in docs:
            doc_data = doc.to_dict()
            print(f"📄 {doc.id}: {doc_data.get('channel_title', 'Unknown')}")
            doc_count += 1
        
        print(f"\n✅ Firestore確認完了: {doc_count} 件のドキュメントが存在")
        return doc_count
        
    except Exception as e:
        print(f"❌ Firestore確認エラー: {e}")
        return 0

def main():
    """メイン実行関数"""
    print("🔥 Firestore 直接データ挿入")
    print("=" * 60)
    
    # Firestoreクライアント初期化
    db = initialize_firestore()
    if not db:
        print("❌ Firestore初期化失敗 - 処理を終了")
        return
    
    # 整形済みデータ読み込み
    formatted_data = load_formatted_data()
    if not formatted_data:
        print("❌ データ読み込み失敗 - 処理を終了")
        return
    
    # Firestoreにデータ挿入
    success_count = insert_to_firestore(db, formatted_data)
    
    # データ確認
    if success_count > 0:
        verify_firestore_data(db)
    
    print("\n🎉 Firestore データ挿入処理完了！")

if __name__ == "__main__":
    main()