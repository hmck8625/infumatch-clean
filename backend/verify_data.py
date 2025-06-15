#!/usr/bin/env python3
"""
データベース確認スクリプト

@description Firestore と BigQuery のデータを確認・表示
@author InfuMatch Development Team
@version 1.0.0
"""

from google.cloud import firestore, bigquery
import json

def check_firestore_data():
    """Firestore データを確認"""
    print("🔥 Firestore データ確認")
    print("=" * 50)
    
    try:
        db = firestore.Client(project="hackathon-462905")
        collection_ref = db.collection('influencers')
        docs = collection_ref.stream()
        
        doc_count = 0
        for doc in docs:
            doc_data = doc.to_dict()
            doc_count += 1
            
            print(f"\n📄 ドキュメント {doc_count}: {doc.id}")
            print(f"   チャンネル名: {doc_data.get('channel_title', 'N/A')}")
            print(f"   登録者数: {doc_data.get('subscriber_count', 0):,}")
            print(f"   連絡先: {doc_data.get('contact_info', {}).get('primary_email', 'なし')}")
            print(f"   エンゲージメント率: {doc_data.get('engagement_metrics', {}).get('engagement_rate', 0):.4f}")
        
        print(f"\n✅ Firestore 合計: {doc_count} ドキュメント")
        return doc_count
        
    except Exception as e:
        print(f"❌ Firestore 確認エラー: {e}")
        return 0

def check_bigquery_data():
    """BigQuery データを確認"""
    print("\n🏗️ BigQuery データ確認")
    print("=" * 50)
    
    try:
        client = bigquery.Client(project="hackathon-462905")
        
        # データ一覧クエリ
        query = """
        SELECT 
            channel_id,
            channel_title,
            subscriber_count,
            contact_email,
            JSON_EXTRACT_SCALAR(ai_analysis, '$.engagement_rate') as engagement_rate,
            created_at
        FROM `hackathon-462905.infumatch_data.influencers`
        ORDER BY subscriber_count DESC
        """
        
        query_job = client.query(query)
        results = query_job.result()
        
        row_count = 0
        for row in results:
            row_count += 1
            print(f"\n📊 レコード {row_count}: {row.channel_id}")
            print(f"   チャンネル名: {row.channel_title}")
            print(f"   登録者数: {row.subscriber_count:,}")
            print(f"   連絡先: {row.contact_email or 'なし'}")
            print(f"   エンゲージメント率: {row.engagement_rate or '0'}")
            print(f"   作成日時: {row.created_at}")
        
        print(f"\n✅ BigQuery 合計: {row_count} レコード")
        return row_count
        
    except Exception as e:
        print(f"❌ BigQuery 確認エラー: {e}")
        return 0

def check_data_consistency():
    """データ整合性チェック"""
    print("\n🔍 データ整合性チェック")
    print("=" * 50)
    
    try:
        # Firestore データ取得
        db = firestore.Client(project="hackathon-462905")
        firestore_docs = list(db.collection('influencers').stream())
        firestore_ids = {doc.id for doc in firestore_docs}
        
        # BigQuery データ取得
        client = bigquery.Client(project="hackathon-462905")
        query = "SELECT channel_id FROM `hackathon-462905.infumatch_data.influencers`"
        query_job = client.query(query)
        bigquery_results = query_job.result()
        bigquery_ids = {row.channel_id for row in bigquery_results}
        
        # 整合性チェック
        print(f"📊 Firestore ドキュメント数: {len(firestore_ids)}")
        print(f"📊 BigQuery レコード数: {len(bigquery_ids)}")
        
        if firestore_ids == bigquery_ids:
            print("✅ データ整合性: 両データベースのIDが一致しています")
        else:
            print("❌ データ整合性: IDに差異があります")
            only_firestore = firestore_ids - bigquery_ids
            only_bigquery = bigquery_ids - firestore_ids
            
            if only_firestore:
                print(f"   Firestoreのみ: {only_firestore}")
            if only_bigquery:
                print(f"   BigQueryのみ: {only_bigquery}")
        
        return len(firestore_ids) == len(bigquery_ids)
        
    except Exception as e:
        print(f"❌ 整合性チェックエラー: {e}")
        return False

def main():
    """メイン実行関数"""
    print("📊 データベース確認ツール")
    print("=" * 60)
    
    # Firestore 確認
    firestore_count = check_firestore_data()
    
    # BigQuery 確認
    bigquery_count = check_bigquery_data()
    
    # 整合性チェック
    is_consistent = check_data_consistency()
    
    # サマリー
    print("\n📈 確認結果サマリー")
    print("=" * 60)
    print(f"🔥 Firestore: {firestore_count} ドキュメント")
    print(f"🏗️ BigQuery: {bigquery_count} レコード")
    print(f"🔍 整合性: {'✅ 一致' if is_consistent else '❌ 不一致'}")
    
    if firestore_count > 0 and bigquery_count > 0:
        print("\n🎉 データ登録が正常に完了しています！")
    else:
        print("\n❌ データ登録に問題があります")

if __name__ == "__main__":
    main()