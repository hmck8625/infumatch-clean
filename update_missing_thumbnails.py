#!/usr/bin/env python3
"""
サムネイル欠損チャンネルの再収集・更新スクリプト

@description Firestoreからサムネイルが欠損しているチャンネルを特定し、
YouTube APIで再取得してデータベースを更新
"""

import json
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.cloud import firestore
from google.cloud import bigquery

# 設定
YOUTUBE_API_KEY = "AIzaSyDtPl5WSRdxk744ha5Tlwno4iTBZVO96r4"
PROJECT_ID = "hackathon-462905"

class ThumbnailUpdater:
    """
    サムネイル更新システム
    
    機能:
    1. Firestoreからサムネイル欠損チャンネルを検索
    2. YouTube APIでサムネイルURL再取得
    3. Firestore・BigQueryの両方を更新
    """
    
    def __init__(self, api_key: str = YOUTUBE_API_KEY):
        self.api_key = api_key
        self.service = build('youtube', 'v3', developerKey=api_key)
        
        # データベースクライアント初期化
        self.firestore_db = firestore.Client(project=PROJECT_ID)
        self.bigquery_client = bigquery.Client(project=PROJECT_ID)
        
        # 統計情報
        self.stats = {
            'total_channels': 0,
            'missing_thumbnails': 0,
            'api_success': 0,
            'firestore_updated': 0,
            'bigquery_updated': 0,
            'errors': 0
        }
    
    def find_channels_without_thumbnails(self) -> List[Dict[str, Any]]:
        """Firestoreからサムネイルが欠損しているチャンネルを検索"""
        try:
            print("🔍 Firestoreからサムネイル欠損チャンネルを検索中...")
            
            collection_ref = self.firestore_db.collection('influencers')
            
            # 全チャンネルを取得
            all_docs = collection_ref.stream()
            channels_without_thumbnails = []
            
            for doc in all_docs:
                data = doc.to_dict()
                self.stats['total_channels'] += 1
                
                # サムネイルが欠損している条件をチェック
                thumbnail_url = data.get('thumbnail_url', '')
                
                is_missing_thumbnail = (
                    not thumbnail_url or 
                    thumbnail_url == '' or
                    thumbnail_url == 'null' or
                    thumbnail_url is None or
                    '/images/default-channel' in thumbnail_url or
                    'default_thumbnail' in thumbnail_url
                )
                
                if is_missing_thumbnail:
                    channel_data = {
                        'doc_id': doc.id,
                        'channel_id': data.get('channel_id', ''),
                        'channel_title': data.get('channel_title', 'Unknown'),
                        'current_thumbnail': thumbnail_url,
                        'category': data.get('category', 'Unknown'),
                        'subscriber_count': data.get('subscriber_count', 0)
                    }
                    channels_without_thumbnails.append(channel_data)
                    self.stats['missing_thumbnails'] += 1
            
            print(f"📊 検索完了:")
            print(f"  - 総チャンネル数: {self.stats['total_channels']}")
            print(f"  - サムネイル欠損: {self.stats['missing_thumbnails']}")
            
            if channels_without_thumbnails:
                print(f"\n📋 サムネイル欠損チャンネル一覧:")
                for i, channel in enumerate(channels_without_thumbnails[:10], 1):
                    print(f"  {i:2d}. {channel['channel_title']} (ID: {channel['channel_id']})")
                
                if len(channels_without_thumbnails) > 10:
                    print(f"  ... および他{len(channels_without_thumbnails) - 10}チャンネル")
            
            return channels_without_thumbnails
            
        except Exception as e:
            print(f"❌ Firestore検索エラー: {e}")
            self.stats['errors'] += 1
            return []
    
    def get_thumbnail_from_youtube(self, channel_id: str) -> str:
        """YouTube APIからサムネイルURLを取得"""
        try:
            if not channel_id:
                return ""
            
            # YouTube APIでチャンネル情報を取得
            response = self.service.channels().list(
                part='snippet',
                id=channel_id
            ).execute()
            
            items = response.get('items', [])
            if not items:
                print(f"  ⚠️ チャンネルが見つかりません: {channel_id}")
                return ""
            
            snippet = items[0].get('snippet', {})
            thumbnails = snippet.get('thumbnails', {})
            
            # 高品質順でサムネイルURLを取得
            for quality in ['maxres', 'high', 'medium', 'default']:
                if quality in thumbnails:
                    thumbnail_url = thumbnails[quality].get('url', '')
                    if thumbnail_url:
                        return thumbnail_url
            
            return ""
            
        except HttpError as e:
            print(f"  ❌ YouTube API エラー (channel_id: {channel_id}): {e}")
            return ""
        except Exception as e:
            print(f"  ❌ サムネイル取得エラー (channel_id: {channel_id}): {e}")
            return ""
    
    def update_channel_thumbnail(self, channel_data: Dict[str, Any], new_thumbnail_url: str) -> bool:
        """Firestoreのチャンネルサムネイルを更新"""
        try:
            if not new_thumbnail_url:
                return False
            
            doc_ref = self.firestore_db.collection('influencers').document(channel_data['doc_id'])
            
            update_data = {
                'thumbnail_url': new_thumbnail_url,
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'thumbnail_updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            doc_ref.update(update_data)
            self.stats['firestore_updated'] += 1
            return True
            
        except Exception as e:
            print(f"  ❌ Firestore更新エラー ({channel_data['channel_title']}): {e}")
            self.stats['errors'] += 1
            return False
    
    def update_bigquery_thumbnail(self, channel_id: str, new_thumbnail_url: str) -> bool:
        """BigQueryのチャンネルサムネイルを更新"""
        try:
            if not new_thumbnail_url or not channel_id:
                return False
            
            # BigQueryでUPDATE文を実行
            query = f"""
            UPDATE `{PROJECT_ID}.infumatch_data.influencers`
            SET 
                thumbnail_url = @thumbnail_url,
                updated_at = @updated_at
            WHERE channel_id = @channel_id
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("thumbnail_url", "STRING", new_thumbnail_url),
                    bigquery.ScalarQueryParameter("updated_at", "STRING", datetime.now(timezone.utc).isoformat()),
                    bigquery.ScalarQueryParameter("channel_id", "STRING", channel_id)
                ]
            )
            
            query_job = self.bigquery_client.query(query, job_config=job_config)
            query_job.result()  # 完了を待機
            
            self.stats['bigquery_updated'] += 1
            return True
            
        except Exception as e:
            print(f"  ❌ BigQuery更新エラー (channel_id: {channel_id}): {e}")
            self.stats['errors'] += 1
            return False
    
    def update_missing_thumbnails(self):
        """サムネイル欠損チャンネルの一括更新"""
        print("🚀 サムネイル欠損チャンネル更新開始")
        print("=" * 60)
        
        # 1. サムネイル欠損チャンネルを検索
        missing_channels = self.find_channels_without_thumbnails()
        
        if not missing_channels:
            print("✅ サムネイル欠損チャンネルはありません！")
            return
        
        print(f"\n📥 {len(missing_channels)} チャンネルのサムネイルを更新中...")
        print("-" * 60)
        
        # 2. 各チャンネルのサムネイルを取得・更新
        for i, channel in enumerate(missing_channels, 1):
            try:
                print(f"[{i}/{len(missing_channels)}] {channel['channel_title']}")
                
                # YouTube APIでサムネイルを取得
                new_thumbnail = self.get_thumbnail_from_youtube(channel['channel_id'])
                
                if new_thumbnail:
                    print(f"  ✅ サムネイル取得成功")
                    self.stats['api_success'] += 1
                    
                    # Firestoreを更新
                    firestore_success = self.update_channel_thumbnail(channel, new_thumbnail)
                    
                    # BigQueryを更新
                    bigquery_success = self.update_bigquery_thumbnail(channel['channel_id'], new_thumbnail)
                    
                    if firestore_success and bigquery_success:
                        print(f"  ✅ データベース更新完了")
                    elif firestore_success:
                        print(f"  ⚠️ Firestoreのみ更新成功")
                    elif bigquery_success:
                        print(f"  ⚠️ BigQueryのみ更新成功")
                    else:
                        print(f"  ❌ データベース更新失敗")
                        
                else:
                    print(f"  ❌ サムネイル取得失敗")
                    self.stats['errors'] += 1
                
            except Exception as e:
                print(f"  ❌ 処理エラー: {e}")
                self.stats['errors'] += 1
                continue
        
        # 3. 結果サマリー表示
        self.print_update_summary()
    
    def print_update_summary(self):
        """更新結果サマリーを表示"""
        print("\n" + "=" * 60)
        print("🎯 サムネイル更新完了サマリー")
        print("=" * 60)
        
        print(f"📊 処理統計:")
        print(f"  - 総チャンネル数: {self.stats['total_channels']}")
        print(f"  - サムネイル欠損: {self.stats['missing_thumbnails']}")
        print(f"  - API取得成功: {self.stats['api_success']}")
        print(f"  - Firestore更新: {self.stats['firestore_updated']}")
        print(f"  - BigQuery更新: {self.stats['bigquery_updated']}")
        print(f"  - エラー数: {self.stats['errors']}")
        
        success_rate = (self.stats['api_success'] / self.stats['missing_thumbnails'] * 100) if self.stats['missing_thumbnails'] > 0 else 0
        print(f"\n📈 成功率: {success_rate:.1f}%")
        
        if self.stats['api_success'] > 0:
            print("✅ サムネイル更新が完了しました！")
        else:
            print("⚠️ サムネイル更新に課題があります")

def main():
    """メイン実行関数"""
    updater = ThumbnailUpdater()
    
    try:
        updater.update_missing_thumbnails()
        
    except Exception as e:
        print(f"\n❌ 実行エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()