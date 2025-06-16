#!/usr/bin/env python3
"""
収集データをFirestore・BigQueryに保存
"""

import json
import os
from datetime import datetime, timezone
from google.cloud import firestore
from google.cloud import bigquery

# 設定
PROJECT_ID = "hackathon-462905"

def save_to_firestore(channels):
    """Firestoreに保存"""
    try:
        print(f"🔥 Firestoreに {len(channels)} チャンネルを保存中...")
        
        db = firestore.Client(project=PROJECT_ID)
        collection_ref = db.collection('influencers')
        
        saved_count = 0
        updated_count = 0
        
        for i, channel in enumerate(channels, 1):
            try:
                # 既存データ確認
                existing_query = collection_ref.where('channel_id', '==', channel['channel_id']).limit(1)
                existing_docs = list(existing_query.stream())
                
                # データ準備
                channel_data = {
                    **channel,
                    'updated_at': datetime.now(timezone.utc).isoformat(),
                    'data_source': 'famous_channels_collection',
                    'status': 'active'
                }
                
                if existing_docs:
                    # 更新
                    doc_ref = existing_docs[0].reference
                    doc_ref.update(channel_data)
                    print(f"🔄 更新: {i}. {channel['channel_title']} (登録者: {channel['subscriber_count']:,})")
                    updated_count += 1
                else:
                    # 新規作成
                    channel_data['created_at'] = datetime.now(timezone.utc).isoformat()
                    doc_ref = collection_ref.document(channel['channel_id'])
                    doc_ref.set(channel_data)
                    print(f"✅ 新規: {i}. {channel['channel_title']} (登録者: {channel['subscriber_count']:,})")
                    saved_count += 1
                
            except Exception as e:
                print(f"❌ Firestore保存エラー ({channel.get('channel_title', 'Unknown')}): {e}")
                continue
        
        print(f"✅ Firestore保存完了: 新規 {saved_count} 件, 更新 {updated_count} 件")
        return True
        
    except Exception as e:
        print(f"❌ Firestore保存失敗: {e}")
        return False

def save_to_bigquery(channels):
    """BigQueryに保存"""
    try:
        print(f"🏗️ BigQueryに {len(channels)} チャンネルを保存中...")
        
        client = bigquery.Client(project=PROJECT_ID)
        dataset_ref = client.dataset('infumatch_data')
        table_ref = dataset_ref.table('influencers')
        
        # データ変換
        rows_to_insert = []
        for channel in channels:
            try:
                row = {
                    'influencer_id': channel['channel_id'],
                    'channel_id': channel['channel_id'],
                    'channel_title': channel['channel_title'],
                    'description': channel.get('description', '')[:1000],  # BigQuery制限対応
                    'subscriber_count': channel['subscriber_count'],
                    'video_count': channel['video_count'],
                    'view_count': channel['view_count'],
                    'category': 'エンタメ',  # デフォルトカテゴリ
                    'country': channel.get('country', 'JP'),
                    'language': 'ja',
                    'contact_email': channel['emails'][0] if channel['emails'] else None,
                    'social_links': '',
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat(),
                    'is_active': True
                }
                rows_to_insert.append(row)
                
            except Exception as e:
                print(f"❌ BigQuery行変換エラー ({channel.get('channel_title', 'Unknown')}): {e}")
                continue
        
        # バッチ挿入
        errors = client.insert_rows_json(table_ref, rows_to_insert)
        
        if errors:
            print(f"❌ BigQuery挿入エラー: {errors}")
            return False
        else:
            print(f"✅ BigQuery保存成功: {len(rows_to_insert)} 件")
            return True
            
    except Exception as e:
        print(f"❌ BigQuery保存失敗: {e}")
        return False

def main():
    """メイン実行関数"""
    # Vlog・カップル系JSONファイルを優先的に探す
    vlog_files = [f for f in os.listdir('.') if f.startswith('vlog_couple_channels_') and f.endswith('.json')]
    
    if vlog_files:
        # 最新Vlog系ファイルを選択
        latest_file = sorted(vlog_files)[-1]
        print(f"📁 読み込み: {latest_file}")
    else:
        # 芸人系JSONファイルを次に探す
        comedian_files = [f for f in os.listdir('.') if f.startswith('comedian_channels_') and f.endswith('.json')]
        
        if comedian_files:
            # 最新芸人系ファイルを選択
            latest_file = sorted(comedian_files)[-1]
            print(f"📁 読み込み: {latest_file}")
        else:
            # ビジネス系JSONファイルを次に探す
            business_files = [f for f in os.listdir('.') if f.startswith('business_channels_') and f.endswith('.json')]
            
            if business_files:
                # 最新ビジネス系ファイルを選択
                latest_file = sorted(business_files)[-1]
                print(f"📁 読み込み: {latest_file}")
            else:
                # その他のJSONファイル
                json_files = [f for f in os.listdir('.') if f.endswith('.json') and ('channels_' in f or 'famous_' in f)]
                
                if not json_files:
                    print("❌ JSONファイルが見つかりません")
                    return
                
                latest_file = sorted(json_files)[-1]
                print(f"📁 読み込み: {latest_file}")
    
    # データ読み込み
    with open(latest_file, 'r', encoding='utf-8') as f:
        channels = json.load(f)
    
    print(f"📊 読み込み完了: {len(channels)} チャンネル")
    
    # データベース保存
    print("\\n💾 データベース保存開始...")
    
    firestore_success = save_to_firestore(channels)
    bigquery_success = save_to_bigquery(channels)
    
    # 結果表示
    print("\\n" + "=" * 60)
    print("🎯 データベース保存結果")
    print("=" * 60)
    print(f"🔥 Firestore: {'✅ 成功' if firestore_success else '❌ 失敗'}")
    print(f"🏗️ BigQuery: {'✅ 成功' if bigquery_success else '❌ 失敗'}")
    
    if firestore_success and bigquery_success:
        print("\\n🎉 すべてのデータベースに正常に保存されました！")
    else:
        print("\\n⚠️ 一部のデータベース保存に失敗しました")

if __name__ == "__main__":
    main()