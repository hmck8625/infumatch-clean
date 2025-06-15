#!/usr/bin/env python3
"""
既存データのスキーマ確認

@description BigQueryの既存テーブルスキーマを確認してAI分析追加の準備
"""

from google.cloud import bigquery

def check_bigquery_schema():
    """BigQueryテーブルのスキーマを確認"""
    try:
        client = bigquery.Client(project="hackathon-462905")
        
        # テーブル一覧確認
        print("📊 データセット内のテーブル一覧:")
        dataset_ref = client.dataset("infumatch_data")
        tables = client.list_tables(dataset_ref)
        
        for table in tables:
            print(f"  - {table.table_id}")
        print()
        
        # influencersテーブルのスキーマ確認
        table_id = "hackathon-462905.infumatch_data.influencers"
        table = client.get_table(table_id)
        
        print(f"📋 {table.table_id} のスキーマ:")
        print("-" * 50)
        for field in table.schema:
            print(f"  - {field.name}: {field.field_type} ({field.mode})")
        
        print(f"\n📊 行数: {table.num_rows:,}")
        print()
        
        # サンプルデータ取得
        print("📄 サンプルデータ（最初の3行）:")
        query = f"""
        SELECT *
        FROM `{table_id}`
        LIMIT 3
        """
        
        query_job = client.query(query)
        results = query_job.result()
        
        for i, row in enumerate(results, 1):
            print(f"\n{i}. チャンネル:")
            for field in table.schema:
                value = getattr(row, field.name, None)
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                print(f"   {field.name}: {value}")
        
    except Exception as e:
        print(f"❌ スキーマ確認エラー: {e}")

if __name__ == "__main__":
    check_bigquery_schema()