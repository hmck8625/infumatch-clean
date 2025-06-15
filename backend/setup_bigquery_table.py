#!/usr/bin/env python3
"""
BigQuery テーブル作成スクリプト

@description BigQuery データセットとテーブルを作成する
@author InfuMatch Development Team
@version 1.0.0
"""

import os
from google.cloud import bigquery

def initialize_bigquery():
    """BigQuery クライアントを初期化"""
    try:
        # プロジェクトIDを設定
        project_id = "hackathon-462905"
        
        # デフォルト認証を使用（gcloud auth loginの認証情報）
        # os.environ['GOOGLE_APPLICATION_CREDENTIALS'] は使用しない
        
        # BigQueryクライアントを初期化
        client = bigquery.Client(project=project_id)
        print(f"✅ BigQuery クライアント初期化完了 (プロジェクト: {project_id})")
        return client
        
    except Exception as e:
        print(f"❌ BigQuery クライアント初期化エラー: {e}")
        return None

def create_dataset(client, dataset_id):
    """データセットを作成"""
    try:
        # データセット参照を作成
        dataset_ref = client.dataset(dataset_id)
        
        # データセット存在確認
        try:
            dataset = client.get_dataset(dataset_ref)
            print(f"✅ データセット '{dataset_id}' は既に存在します")
            return dataset
        except Exception:
            # データセットが存在しない場合は作成
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"  # BigQueryのデフォルトロケーション
            dataset.description = "InfuMatch - YouTuber Influencer Data Platform"
            
            dataset = client.create_dataset(dataset)
            print(f"✅ データセット '{dataset_id}' を作成しました")
            return dataset
            
    except Exception as e:
        print(f"❌ データセット作成エラー: {e}")
        return None

def create_influencers_table(client, dataset_id, table_id):
    """influencers テーブルを作成"""
    try:
        # テーブル参照を作成
        table_ref = client.dataset(dataset_id).table(table_id)
        
        # テーブル存在確認
        try:
            table = client.get_table(table_ref)
            print(f"✅ テーブル '{dataset_id}.{table_id}' は既に存在します")
            return table
        except Exception:
            pass
        
        # テーブルスキーマを定義
        schema = [
            bigquery.SchemaField("influencer_id", "STRING", mode="REQUIRED", description="Unique influencer identifier"),
            bigquery.SchemaField("channel_id", "STRING", mode="REQUIRED", description="YouTube channel ID"),
            bigquery.SchemaField("channel_title", "STRING", mode="REQUIRED", description="Channel title"),
            bigquery.SchemaField("description", "STRING", mode="NULLABLE", description="Channel description"),
            bigquery.SchemaField("subscriber_count", "INTEGER", mode="REQUIRED", description="Number of subscribers"),
            bigquery.SchemaField("video_count", "INTEGER", mode="REQUIRED", description="Number of videos"),
            bigquery.SchemaField("view_count", "INTEGER", mode="REQUIRED", description="Total view count"),
            bigquery.SchemaField("category", "STRING", mode="REQUIRED", description="Content category"),
            bigquery.SchemaField("country", "STRING", mode="NULLABLE", description="Country code"),
            bigquery.SchemaField("language", "STRING", mode="NULLABLE", description="Primary language"),
            bigquery.SchemaField("contact_email", "STRING", mode="NULLABLE", description="Contact email address"),
            bigquery.SchemaField("social_links", "STRING", mode="NULLABLE", description="Social media links (JSON)"),
            bigquery.SchemaField("ai_analysis", "STRING", mode="NULLABLE", description="AI analysis results (JSON)"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED", description="Record creation timestamp"),
            bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED", description="Last update timestamp"),
            bigquery.SchemaField("is_active", "BOOLEAN", mode="REQUIRED", description="Active status flag"),
        ]
        
        # テーブルを作成
        table = bigquery.Table(table_ref, schema=schema)
        table.description = "YouTube Influencer profiles and metrics"
        
        table = client.create_table(table)
        print(f"✅ テーブル '{dataset_id}.{table_id}' を作成しました")
        
        # テーブル情報を表示
        print(f"   📄 テーブル情報:")
        print(f"      - スキーマフィールド数: {len(table.schema)}")
        print(f"      - レコード数: {table.num_rows}")
        print(f"      - 作成日時: {table.created}")
        
        return table
        
    except Exception as e:
        print(f"❌ テーブル作成エラー: {e}")
        return None

def main():
    """メイン実行関数"""
    print("🏗️ BigQuery データセット・テーブル作成")
    print("=" * 60)
    
    # BigQueryクライアント初期化
    client = initialize_bigquery()
    if not client:
        print("❌ BigQuery初期化失敗 - 処理を終了")
        return
    
    # データセット作成
    dataset_id = "infumatch_data"
    dataset = create_dataset(client, dataset_id)
    if not dataset:
        print("❌ データセット作成失敗 - 処理を終了")
        return
    
    # influencersテーブル作成
    table_id = "influencers"
    table = create_influencers_table(client, dataset_id, table_id)
    if not table:
        print("❌ テーブル作成失敗 - 処理を終了")
        return
    
    print("\n🎉 BigQuery セットアップ完了！")
    print(f"📊 データセット: {dataset_id}")
    print(f"📄 テーブル: {table_id}")
    print(f"🔗 BigQuery URL: https://console.cloud.google.com/bigquery?project=hackathon-462905")

if __name__ == "__main__":
    main()