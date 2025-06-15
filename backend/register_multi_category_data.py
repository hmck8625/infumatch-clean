#!/usr/bin/env python3
"""
多カテゴリYouTuberデータのデータベース登録スクリプト

@description 収集された多カテゴリJSONファイルのデータをFirestoreとBigQueryに登録
@author InfuMatch Development Team
@version 1.0.0
"""

import json
import os
from datetime import datetime, timezone
from google.cloud import firestore, bigquery

def load_multi_category_data():
    """多カテゴリデータを読み込み"""
    try:
        with open('multi_category_youtubers.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ {len(data)} 件の多カテゴリデータを読み込みました")
        return data
    except FileNotFoundError:
        print("❌ multi_category_youtubers.json が見つかりません")
        return []
    except Exception as e:
        print(f"❌ データ読み込みエラー: {e}")
        return []

def format_for_database(youtuber_data):
    """データベース用にデータを変換"""
    formatted_data = []
    
    for channel in youtuber_data:
        # Firestore用フォーマット
        firestore_doc = {
            'channel_id': channel['channel_id'],
            'channel_title': channel['channel_title'],
            'description': channel['description'],
            'subscriber_count': channel['subscriber_count'],
            'video_count': channel['video_count'],
            'view_count': channel['view_count'],
            'category': channel['category'],
            'country': channel.get('country', 'JP'),
            'language': 'ja',
            'contact_info': {
                'emails': channel['emails'],
                'primary_email': channel['emails'][0] if channel['emails'] else None
            },
            'engagement_metrics': {
                'engagement_rate': channel['engagement_estimate'] / 100,  # 小数に変換
                'avg_views_per_video': channel['view_count'] / channel['video_count'] if channel['video_count'] > 0 else 0,
                'has_contact': channel['has_contact']
            },
            'ai_analysis': {
                'content_quality_score': 0.8,  # デフォルト値
                'brand_safety_score': 0.9,     # デフォルト値
                'growth_potential': 0.7        # デフォルト値
            },
            'status': 'active',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'last_analyzed': channel['collected_at'],
            'fetched_at': channel['collected_at'],
            'data_source': 'youtube_api',
            'collection_method': 'multi_category_search'
        }
        
        # BigQuery用フォーマット
        bigquery_row = {
            'influencer_id': channel['channel_id'],
            'channel_id': channel['channel_id'],
            'channel_title': channel['channel_title'],
            'description': channel['description'],
            'subscriber_count': channel['subscriber_count'],
            'video_count': channel['video_count'],
            'view_count': channel['view_count'],
            'category': channel['category'],
            'country': channel.get('country', 'JP'),
            'language': 'ja',
            'contact_email': channel['emails'][0] if channel['emails'] else '',
            'social_links': json.dumps({
                'emails': channel['emails']
            }),
            'ai_analysis': json.dumps({
                'engagement_rate': channel['engagement_estimate'] / 100,
                'content_quality_score': 0.8,
                'brand_safety_score': 0.9,
                'growth_potential': 0.7
            }),
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'is_active': True
        }
        
        formatted_data.append({
            'firestore': firestore_doc,
            'bigquery': bigquery_row,
            'original': channel
        })
    
    return formatted_data

def insert_to_firestore(formatted_data):
    """Firestoreにデータを挿入"""
    print("\n🔥 Firestore にデータを挿入中...")
    
    try:
        db = firestore.Client(project="hackathon-462905")
        collection_ref = db.collection('influencers')
        
        success_count = 0
        for i, data in enumerate(formatted_data, 1):
            try:
                firestore_doc = data['firestore']
                doc_id = firestore_doc['channel_id']
                
                # ドキュメントを作成
                doc_ref = collection_ref.document(doc_id)
                doc_ref.set(firestore_doc)
                
                print(f"✅ {i}/{len(formatted_data)} 完了: {firestore_doc['channel_title']}")
                success_count += 1
                
            except Exception as e:
                print(f"❌ {i}/{len(formatted_data)} 失敗: {data['original'].get('channel_title', 'Unknown')} - {e}")
        
        print(f"\n🎉 Firestore 挿入完了: {success_count}/{len(formatted_data)} 件成功")
        return success_count
        
    except Exception as e:
        print(f"❌ Firestore 挿入エラー: {e}")
        return 0

def insert_to_bigquery(formatted_data):
    """BigQueryにデータを挿入"""
    print("\n🏗️ BigQuery にデータを挿入中...")
    
    try:
        client = bigquery.Client(project="hackathon-462905")
        table_ref = client.dataset("infumatch_data").table("influencers")
        table = client.get_table(table_ref)
        
        # BigQuery用データを準備
        bigquery_rows = [data['bigquery'] for data in formatted_data]
        
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

def verify_data_insertion():
    """データ挿入を確認"""
    print("\n🔍 データ挿入確認中...")
    
    try:
        # Firestore確認
        db = firestore.Client(project="hackathon-462905")
        firestore_docs = list(db.collection('influencers').stream())
        firestore_count = len(firestore_docs)
        
        # BigQuery確認
        client = bigquery.Client(project="hackathon-462905")
        query = "SELECT COUNT(*) as total FROM `hackathon-462905.infumatch_data.influencers`"
        query_job = client.query(query)
        result = list(query_job.result())[0]
        bigquery_count = result.total
        
        print(f"📊 Firestore: {firestore_count} ドキュメント")
        print(f"📊 BigQuery: {bigquery_count} レコード")
        
        # カテゴリ別集計
        category_query = """
        SELECT 
            category,
            COUNT(*) as count,
            SUM(CASE WHEN contact_email != '' THEN 1 ELSE 0 END) as with_email
        FROM `hackathon-462905.infumatch_data.influencers`
        GROUP BY category
        ORDER BY count DESC
        """
        
        query_job = client.query(category_query)
        results = query_job.result()
        
        print(f"\n📈 カテゴリ別統計:")
        for row in results:
            print(f"  - {row.category}: {row.count}チャンネル (連絡可能: {row.with_email})")
        
        return firestore_count, bigquery_count
        
    except Exception as e:
        print(f"❌ 確認エラー: {e}")
        return 0, 0

def create_summary_report(formatted_data):
    """データサマリーレポートを生成"""
    print("\n📊 多カテゴリデータ登録サマリー:")
    print("=" * 100)
    
    total_channels = len(formatted_data)
    channels_with_email = sum(1 for data in formatted_data if data['original']['has_contact'])
    total_subscribers = sum(data['original']['subscriber_count'] for data in formatted_data)
    avg_engagement = sum(data['original']['engagement_estimate'] for data in formatted_data) / total_channels if total_channels > 0 else 0
    
    # カテゴリ別統計
    category_stats = {}
    for data in formatted_data:
        cat = data['original']['category']
        if cat not in category_stats:
            category_stats[cat] = {'count': 0, 'with_email': 0, 'subscribers': 0}
        category_stats[cat]['count'] += 1
        category_stats[cat]['subscribers'] += data['original']['subscriber_count']
        if data['original']['has_contact']:
            category_stats[cat]['with_email'] += 1
    
    print(f"📈 全体統計情報:")
    print(f"  - 登録対象チャンネル数: {total_channels}")
    print(f"  - 連絡可能チャンネル数: {channels_with_email} ({channels_with_email/total_channels*100:.1f}%)")
    print(f"  - 総登録者数: {total_subscribers:,} 人")
    print(f"  - 平均エンゲージメント率: {avg_engagement:.2f}%")
    
    print(f"\n📋 カテゴリ別詳細:")
    print("-" * 100)
    for category, stats in sorted(category_stats.items(), key=lambda x: x[1]['count'], reverse=True):
        print(f"🎭 {category}")
        print(f"   チャンネル数: {stats['count']}")
        print(f"   連絡可能: {stats['with_email']} ({stats['with_email']/stats['count']*100:.1f}%)")
        print(f"   総登録者数: {stats['subscribers']:,}")
        print()
    
    print("=" * 100)

def main():
    """メイン実行関数"""
    print("🎭 多カテゴリYouTuberデータのデータベース登録")
    print("=" * 80)
    
    # データ読み込み
    youtuber_data = load_multi_category_data()
    if not youtuber_data:
        print("❌ 登録するデータがありません")
        return
    
    # データ変換
    print(f"\n🔄 {len(youtuber_data)}件のデータをデータベース用フォーマットに変換中...")
    formatted_data = format_for_database(youtuber_data)
    
    # Firestoreに挿入
    firestore_success = insert_to_firestore(formatted_data)
    
    # BigQueryに挿入
    bigquery_success = insert_to_bigquery(formatted_data)
    
    # データ確認
    if firestore_success > 0 or bigquery_success > 0:
        verify_data_insertion()
    
    # サマリーレポート
    create_summary_report(formatted_data)
    
    # 最終結果
    print(f"\n🎉 多カテゴリデータベース登録完了！")
    print(f"🔥 Firestore: {firestore_success} 件成功")
    print(f"🏗️ BigQuery: {bigquery_success} 件成功")
    
    if firestore_success > 0 and bigquery_success > 0:
        print("✅ 両データベースへの登録が正常に完了しました！")
    else:
        print("❌ 一部のデータベース登録に問題があります")

if __name__ == "__main__":
    main()