#!/usr/bin/env python3
"""
BigQuery 直接データ挿入スクリプト

@description Google Cloud BigQuery Client Libraryを使用してデータを直接挿入
BigQuery SQLではなくPythonライブラリを使用

@author InfuMatch Development Team
@version 1.0.0
"""

import json
import os
from datetime import datetime, timezone
from google.cloud import bigquery

def initialize_bigquery():
    """BigQuery クライアントを初期化"""
    try:
        # プロジェクトIDを設定
        project_id = "hackathon-462905"
        
        # デフォルト認証を使用（gcloud auth application-default loginの認証情報）
        # os.environ['GOOGLE_APPLICATION_CREDENTIALS'] は使用しない
        
        # BigQueryクライアントを初期化
        client = bigquery.Client(project=project_id)
        print(f"✅ BigQuery クライアント初期化完了 (プロジェクト: {project_id})")
        return client
        
    except Exception as e:
        print(f"❌ BigQuery クライアント初期化エラー: {e}")
        return None

def load_formatted_data():
    """整形済みデータを読み込み"""
    try:
        with open('bigquery_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ {len(data)} 件の整形済みデータを読み込みました")
        return data
    except FileNotFoundError:
        print("❌ bigquery_data.json が見つかりません")
        return []
    except Exception as e:
        print(f"❌ データ読み込みエラー: {e}")
        return []

def setup_bigquery_table(client):
    """BigQuery テーブルを確認・作成"""
    dataset_id = "infumatch_data"
    table_id = "influencers"
    
    try:
        # データセット参照
        dataset_ref = client.dataset(dataset_id)
        table_ref = dataset_ref.table(table_id)
        
        # テーブル存在確認
        try:
            table = client.get_table(table_ref)
            print(f"✅ テーブル確認完了: {dataset_id}.{table_id}")
            return table
        except Exception:
            print(f"❌ テーブル {dataset_id}.{table_id} が存在しません")
            return None
            
    except Exception as e:
        print(f"❌ BigQuery テーブル確認エラー: {e}")
        return None

def convert_data_for_bigquery(formatted_data):
    """BigQuery用にデータを変換"""
    bigquery_rows = []
    
    for data in formatted_data:
        # 必要に応じてデータ型変換
        row = {
            'influencer_id': data['influencer_id'],
            'channel_id': data['channel_id'],
            'channel_title': data['channel_title'],
            'description': data['description'],
            'subscriber_count': int(data['subscriber_count']),
            'video_count': int(data['video_count']),
            'view_count': int(data['view_count']),
            'category': data['category'],
            'country': data['country'],
            'language': data['language'],
            'contact_email': data['contact_email'],
            'social_links': data['social_links'],
            'ai_analysis': data['ai_analysis'],
            'created_at': data['created_at'],
            'updated_at': data['updated_at'],
            'is_active': bool(data['is_active'])
        }
        bigquery_rows.append(row)
    
    return bigquery_rows

def insert_to_bigquery(client, table, bigquery_rows):
    """BigQueryにデータを挿入"""
    print("\n🏗️ BigQuery にデータを挿入中...")
    
    try:
        # データを挿入
        errors = client.insert_rows_json(table, bigquery_rows)
        
        if errors:
            print(f"❌ BigQuery 挿入エラー:")
            for error in errors:
                print(f"   {error}")
            return 0
        else:
            print(f"✅ BigQuery 挿入成功: {len(bigquery_rows)} 件")
            return len(bigquery_rows)
            
    except Exception as e:
        print(f"❌ BigQuery 挿入例外: {e}")
        return 0

def verify_bigquery_data(client):
    """BigQueryのデータを確認"""
    print("\n🔍 BigQuery データ確認中...")
    
    try:
        query = """
        SELECT 
            influencer_id,
            channel_title,
            subscriber_count,
            contact_email,
            created_at
        FROM `hackathon-462905.infumatch_data.influencers`
        ORDER BY subscriber_count DESC
        """
        
        query_job = client.query(query)
        results = query_job.result()
        
        row_count = 0
        for row in results:
            print(f"📄 {row.influencer_id}: {row.channel_title} ({row.subscriber_count:,} 登録者)")
            row_count += 1
        
        print(f"\n✅ BigQuery確認完了: {row_count} 件のレコードが存在")
        return row_count
        
    except Exception as e:
        print(f"❌ BigQuery確認エラー: {e}")
        return 0

def main():
    """メイン実行関数"""
    print("🏗️ BigQuery 直接データ挿入")
    print("=" * 60)
    
    # BigQueryクライアント初期化
    client = initialize_bigquery()
    if not client:
        print("❌ BigQuery初期化失敗 - 処理を終了")
        return
    
    # テーブル確認
    table = setup_bigquery_table(client)
    if not table:
        print("❌ テーブル確認失敗 - 処理を終了")
        return
    
    # 整形済みデータ読み込み
    formatted_data = load_formatted_data()
    if not formatted_data:
        print("❌ データ読み込み失敗 - 処理を終了")
        return
    
    # BigQuery用データ変換
    bigquery_rows = convert_data_for_bigquery(formatted_data)
    
    # BigQueryにデータ挿入
    success_count = insert_to_bigquery(client, table, bigquery_rows)
    
    # データ確認
    if success_count > 0:
        verify_bigquery_data(client)
    
    print("\n🎉 BigQuery データ挿入処理完了！")

if __name__ == "__main__":
    main()