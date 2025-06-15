#!/usr/bin/env python3
"""
データベース接続診断スクリプト

@description Firestore、BigQueryの接続状況と書き込み権限をテスト
@author InfuMatch Development Team
@version 1.0.0
"""

import json
import os
from datetime import datetime, timezone
from google.cloud import firestore
from google.cloud import bigquery

# プロジェクト設定
PROJECT_ID = "hackathon-462905"

def test_firestore_connection():
    """Firestore接続テスト"""
    print("🔥 Firestoreテスト開始...")
    
    try:
        # Firestoreクライアント初期化
        db = firestore.Client(project=PROJECT_ID)
        print(f"✅ Firestoreクライアント初期化成功")
        
        # influencersコレクション確認
        collection_ref = db.collection('influencers')
        docs = list(collection_ref.limit(5).get())
        print(f"📊 influencersコレクション: {len(docs)} 件取得")
        
        # テストドキュメント作成
        test_doc_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        test_data = {
            'test_field': 'test_value',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'test_type': 'connection_test'
        }
        
        doc_ref = collection_ref.document(test_doc_id)
        doc_ref.set(test_data)
        print(f"✅ テストドキュメント作成成功: {test_doc_id}")
        
        # 読み込みテスト
        doc = doc_ref.get()
        if doc.exists:
            print(f"✅ テストドキュメント読み込み成功")
        else:
            print(f"❌ テストドキュメント読み込み失敗")
        
        # テストドキュメント削除
        doc_ref.delete()
        print(f"✅ テストドキュメント削除成功")
        
        return True
        
    except Exception as e:
        print(f"❌ Firestoreテストエラー: {e}")
        return False

def test_bigquery_connection():
    """BigQuery接続テスト"""
    print("\n🏗️ BigQueryテスト開始...")
    
    try:
        # BigQueryクライアント初期化
        client = bigquery.Client(project=PROJECT_ID)
        print(f"✅ BigQueryクライアント初期化成功")
        
        # データセット確認
        datasets = list(client.list_datasets())
        print(f"📊 利用可能データセット: {len(datasets)} 件")
        for dataset in datasets:
            print(f"  - {dataset.dataset_id}")
        
        # infumatch_dataデータセットとinfluencersテーブル確認
        try:
            dataset_id = "infumatch_data"
            table_id = "influencers"
            table_ref = client.dataset(dataset_id).table(table_id)
            table = client.get_table(table_ref)
            print(f"✅ テーブル確認: {dataset_id}.{table_id} (行数: {table.num_rows})")
            
            # スキーマ情報表示
            print("📋 テーブルスキーマ:")
            for field in table.schema[:5]:  # 最初の5フィールドのみ表示
                print(f"  - {field.name}: {field.field_type}")
            
        except Exception as e:
            print(f"⚠️ influencersテーブル確認エラー: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ BigQueryテストエラー: {e}")
        return False

def check_service_account():
    """サービスアカウント確認"""
    print("\n🔑 認証情報確認...")
    
    # 環境変数確認
    creds_env = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if creds_env:
        print(f"✅ GOOGLE_APPLICATION_CREDENTIALS: {creds_env}")
    else:
        print("⚠️ GOOGLE_APPLICATION_CREDENTIALS 未設定 (デフォルト認証を使用)")
    
    # サービスアカウントファイル確認
    service_account_files = [
        "hackathon-462905-7d72a76d3742.json",
        "hackathon-462905-fd4f661125e5.json"
    ]
    
    for filename in service_account_files:
        if os.path.exists(filename):
            print(f"✅ サービスアカウントファイル発見: {filename}")
            # ファイル内容の簡易確認
            try:
                with open(filename, 'r') as f:
                    creds_data = json.load(f)
                print(f"  - プロジェクトID: {creds_data.get('project_id', 'N/A')}")
                print(f"  - クライアントID: {creds_data.get('client_id', 'N/A')}")
            except Exception as e:
                print(f"  - ファイル読み込みエラー: {e}")
        else:
            print(f"❌ サービスアカウントファイル未発見: {filename}")

def main():
    """メイン診断処理"""
    print("🔧 データベース接続診断開始")
    print("=" * 60)
    
    # 認証情報確認
    check_service_account()
    
    # Firestore接続テスト
    firestore_ok = test_firestore_connection()
    
    # BigQuery接続テスト
    bigquery_ok = test_bigquery_connection()
    
    # 結果サマリー
    print("\n📋 診断結果サマリー")
    print("=" * 60)
    print(f"Firestore接続: {'✅ 正常' if firestore_ok else '❌ 異常'}")
    print(f"BigQuery接続: {'✅ 正常' if bigquery_ok else '❌ 異常'}")
    
    if firestore_ok and bigquery_ok:
        print("\n🎉 すべてのデータベース接続が正常です")
        return True
    else:
        print("\n⚠️ データベース接続に問題があります")
        return False

if __name__ == "__main__":
    main()