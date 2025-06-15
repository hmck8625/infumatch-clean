#!/usr/bin/env python3
"""
収集されたYouTuberデータのデータベース登録スクリプト

@description 収集されたJSONファイルのデータをFirestoreとBigQueryに登録
実データをデータベースに統合する

@author InfuMatch Development Team
@version 1.0.0
"""

import json
import sys
import os
from datetime import datetime, timezone

# 簡易版の登録処理（Google Cloudライブラリを使用しない）
def load_collected_data():
    """収集されたデータを読み込み"""
    try:
        with open('gaming_youtubers.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ {len(data)} 件のデータを読み込みました")
        return data
    except FileNotFoundError:
        print("❌ gaming_youtubers.json が見つかりません")
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
            'category': 'gaming',
            'country': 'JP',
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
            'collection_method': 'manual_search'
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
            'category': 'gaming',
            'country': 'JP',
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

def create_firestore_commands(formatted_data):
    """Firestore登録用のコマンドを生成"""
    commands = []
    
    print("\n🔥 Firestore登録コマンド:")
    print("=" * 60)
    
    for i, data in enumerate(formatted_data, 1):
        firestore_doc = data['firestore']
        channel_id = firestore_doc['channel_id']
        channel_title = firestore_doc['channel_title']
        
        # gcloud firestore コマンド生成
        command = f"""# {i}. {channel_title}
gcloud firestore documents create --project=hackathon-462905 \\
  --collection=influencers \\
  --document-id="{channel_id}" \\
  --data='{json.dumps(firestore_doc, ensure_ascii=False, separators=(",", ":"))}'
"""
        commands.append(command)
        print(command)
    
    return commands

def create_bigquery_commands(formatted_data):
    """BigQuery登録用のSQLを生成"""
    print("\n🏗️ BigQuery登録SQL:")
    print("=" * 60)
    
    # SQLのINSERT文を生成
    sql_values = []
    
    for data in formatted_data:
        bq_row = data['bigquery']
        
        # 値をSQLエスケープ
        values = f"""(
  '{bq_row["influencer_id"]}',
  '{bq_row["channel_id"]}',  
  '{bq_row["channel_title"].replace("'", "''")}',
  '{bq_row["description"].replace("'", "''")}',
  {bq_row["subscriber_count"]},
  {bq_row["video_count"]},
  {bq_row["view_count"]},
  '{bq_row["category"]}',
  '{bq_row["country"]}',
  '{bq_row["language"]}',
  '{bq_row["contact_email"]}',
  '{bq_row["social_links"].replace("'", "''")}',
  '{bq_row["ai_analysis"].replace("'", "''")}',
  TIMESTAMP('{bq_row["created_at"]}'),
  TIMESTAMP('{bq_row["updated_at"]}'),
  {str(bq_row["is_active"]).lower()}
)"""
        sql_values.append(values)
    
    sql = f"""INSERT INTO `hackathon-462905.infumatch_data.influencers` (
  influencer_id,
  channel_id,
  channel_title,
  description,
  subscriber_count,
  video_count,
  view_count,
  category,
  country,
  language,
  contact_email,
  social_links,
  ai_analysis,
  created_at,
  updated_at,
  is_active
) VALUES
{','.join(sql_values)};"""
    
    print(sql)
    
    # ファイルに保存
    with open('bigquery_insert.sql', 'w', encoding='utf-8') as f:
        f.write(sql)
    
    print("\n💾 BigQuery SQLを bigquery_insert.sql に保存しました")
    
    return sql

def create_summary_report(formatted_data):
    """データサマリーレポートを生成"""
    print("\n📊 データ登録サマリー:")
    print("=" * 80)
    
    total_channels = len(formatted_data)
    channels_with_email = sum(1 for data in formatted_data if data['original']['has_contact'])
    total_subscribers = sum(data['original']['subscriber_count'] for data in formatted_data)
    avg_engagement = sum(data['original']['engagement_estimate'] for data in formatted_data) / total_channels if total_channels > 0 else 0
    
    print(f"📈 統計情報:")
    print(f"  - 登録対象チャンネル数: {total_channels}")
    print(f"  - 連絡可能チャンネル数: {channels_with_email} ({channels_with_email/total_channels*100:.1f}%)")
    print(f"  - 総登録者数: {total_subscribers:,} 人")
    print(f"  - 平均エンゲージメント率: {avg_engagement:.2f}%")
    
    print(f"\n📋 登録チャンネル詳細:")
    print("-" * 80)
    
    sorted_data = sorted(formatted_data, key=lambda x: x['original']['subscriber_count'], reverse=True)
    
    for i, data in enumerate(sorted_data, 1):
        original = data['original']
        print(f"{i:2d}. {original['channel_title']}")
        print(f"     ID: {original['channel_id']}")
        print(f"     登録者: {original['subscriber_count']:,} 人")
        print(f"     動画数: {original['video_count']:,} 本")
        print(f"     エンゲージメント: {original['engagement_estimate']:.2f}%")
        print(f"     連絡先: {len(original['emails'])} 件")
        if original['emails']:
            print(f"     メール: {', '.join(original['emails'])}")
        print()
    
    print("=" * 80)

def save_formatted_data(formatted_data):
    """整形されたデータをファイルに保存"""
    # Firestore用データ
    firestore_data = [data['firestore'] for data in formatted_data]
    with open('firestore_data.json', 'w', encoding='utf-8') as f:
        json.dump(firestore_data, f, ensure_ascii=False, indent=2)
    
    # BigQuery用データ
    bigquery_data = [data['bigquery'] for data in formatted_data]
    with open('bigquery_data.json', 'w', encoding='utf-8') as f:
        json.dump(bigquery_data, f, ensure_ascii=False, indent=2)
    
    print("💾 整形データを以下のファイルに保存:")
    print("  - firestore_data.json (Firestore用)")
    print("  - bigquery_data.json (BigQuery用)")
    print("  - bigquery_insert.sql (BigQueryインサート文)")

def main():
    """メイン実行関数"""
    print("🎮 収集されたゲーム系YouTuberデータのデータベース登録")
    print("=" * 70)
    
    # データ読み込み
    youtuber_data = load_collected_data()
    if not youtuber_data:
        print("❌ 登録するデータがありません")
        return
    
    # データ変換
    print("\n🔄 データベース用フォーマットに変換中...")
    formatted_data = format_for_database(youtuber_data)
    
    # Firestoreコマンド生成
    create_firestore_commands(formatted_data)
    
    # BigQueryコマンド生成
    create_bigquery_commands(formatted_data)
    
    # サマリーレポート
    create_summary_report(formatted_data)
    
    # ファイル保存
    save_formatted_data(formatted_data)
    
    print("\n🎉 データベース登録準備完了！")
    print("\n📝 次のステップ:")
    print("1. gcloud コマンドでFirestoreに登録")
    print("2. BigQuery コンソールでSQLを実行")
    print("3. データ同期の確認")

if __name__ == "__main__":
    main()