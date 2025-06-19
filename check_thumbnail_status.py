#!/usr/bin/env python3
"""
全チャンネルのサムネイル状況詳細確認スクリプト

@description 363チャンネルのサムネイル欠損状況を詳細に確認
@author InfuMatch Development Team
@version 1.0.0
"""

from google.cloud import firestore
from datetime import datetime

PROJECT_ID = "hackathon-462905"

class ThumbnailStatusChecker:
    """
    サムネイル状況詳細確認システム
    """
    
    def __init__(self):
        self.firestore_db = firestore.Client(project=PROJECT_ID)
        self.total_channels = 0
        self.missing_thumbnails = []
        self.valid_thumbnails = []
        self.invalid_thumbnails = []
    
    def check_all_thumbnails(self):
        """全チャンネルのサムネイル状況を確認"""
        print("🔍 全チャンネルのサムネイル状況を詳細確認中...")
        print("=" * 60)
        
        try:
            collection_ref = self.firestore_db.collection('influencers')
            all_docs = collection_ref.stream()
            
            for doc in all_docs:
                data = doc.to_dict()
                self.total_channels += 1
                
                channel_id = data.get('channel_id', '')
                channel_title = data.get('channel_title', 'Unknown')
                thumbnail_url = data.get('thumbnail_url', '')
                
                # サムネイル状況の分類
                if self.is_missing_thumbnail(thumbnail_url):
                    self.missing_thumbnails.append({
                        'doc_id': doc.id,
                        'channel_id': channel_id,
                        'channel_title': channel_title,
                        'current_thumbnail': thumbnail_url,
                        'category': data.get('category', 'Unknown'),
                        'subscriber_count': data.get('subscriber_count', 0)
                    })
                elif self.is_invalid_thumbnail(thumbnail_url):
                    self.invalid_thumbnails.append({
                        'doc_id': doc.id,
                        'channel_id': channel_id,
                        'channel_title': channel_title,
                        'current_thumbnail': thumbnail_url,
                        'category': data.get('category', 'Unknown'),
                        'subscriber_count': data.get('subscriber_count', 0)
                    })
                else:
                    self.valid_thumbnails.append({
                        'doc_id': doc.id,
                        'channel_id': channel_id,
                        'channel_title': channel_title,
                        'current_thumbnail': thumbnail_url[:50] + "..." if len(thumbnail_url) > 50 else thumbnail_url,
                        'category': data.get('category', 'Unknown')
                    })
            
            self.print_detailed_report()
            
        except Exception as e:
            print(f"❌ Firestore検索エラー: {e}")
    
    def is_missing_thumbnail(self, thumbnail_url):
        """サムネイルが欠損しているかチェック"""
        if not thumbnail_url or thumbnail_url == '' or thumbnail_url == 'null' or thumbnail_url is None:
            return True
        
        invalid_patterns = [
            '/images/default-channel',
            'default_thumbnail',
            'placeholder',
            'via.placeholder.com',
            'text=ERROR'
        ]
        
        return any(pattern in thumbnail_url for pattern in invalid_patterns)
    
    def is_invalid_thumbnail(self, thumbnail_url):
        """サムネイルが無効（アクセス不可など）かチェック"""
        if not thumbnail_url:
            return False
        
        # 明らかに無効なURL形式
        invalid_patterns = [
            'http://example.com',
            'https://example.com',
            'localhost',
            'test.jpg',
            '.svg'  # SVGアイコンは無効扱い
        ]
        
        return any(pattern in thumbnail_url for pattern in invalid_patterns)
    
    def print_detailed_report(self):
        """詳細レポートを表示"""
        print("📊 サムネイル状況詳細レポート")
        print("=" * 60)
        
        print(f"📈 総計:")
        print(f"  - 総チャンネル数: {self.total_channels}")
        print(f"  - 有効なサムネイル: {len(self.valid_thumbnails)} ({len(self.valid_thumbnails)/self.total_channels*100:.1f}%)")
        print(f"  - 欠損サムネイル: {len(self.missing_thumbnails)} ({len(self.missing_thumbnails)/self.total_channels*100:.1f}%)")
        print(f"  - 無効サムネイル: {len(self.invalid_thumbnails)} ({len(self.invalid_thumbnails)/self.total_channels*100:.1f}%)")
        
        if self.missing_thumbnails:
            print(f"\\n❌ サムネイル欠損チャンネル ({len(self.missing_thumbnails)}件):")
            for i, channel in enumerate(self.missing_thumbnails[:20], 1):
                print(f"  {i:2d}. {channel['channel_title']} (ID: {channel['channel_id'][:20]}...)")
                print(f"      現在の値: '{channel['current_thumbnail']}'")
            
            if len(self.missing_thumbnails) > 20:
                print(f"  ... および他{len(self.missing_thumbnails) - 20}チャンネル")
        
        if self.invalid_thumbnails:
            print(f"\\n⚠️ 無効サムネイルチャンネル ({len(self.invalid_thumbnails)}件):")
            for i, channel in enumerate(self.invalid_thumbnails[:10], 1):
                print(f"  {i:2d}. {channel['channel_title']}")
                print(f"      現在の値: '{channel['current_thumbnail'][:50]}...'")
            
            if len(self.invalid_thumbnails) > 10:
                print(f"  ... および他{len(self.invalid_thumbnails) - 10}チャンネル")
        
        print(f"\\n📂 カテゴリ別欠損状況:")
        category_missing = {}
        for channel in self.missing_thumbnails + self.invalid_thumbnails:
            category = channel['category']
            category_missing[category] = category_missing.get(category, 0) + 1
        
        for category, count in sorted(category_missing.items()):
            print(f"  - {category}: {count}件")
        
        print(f"\\n💡 推奨アクション:")
        total_need_update = len(self.missing_thumbnails) + len(self.invalid_thumbnails)
        if total_need_update > 0:
            print(f"  1. python3 update_missing_thumbnails.py でサムネイル更新")
            print(f"     → {total_need_update}チャンネルが更新対象")
            print(f"  2. API使用量: 約{total_need_update} units")
        else:
            print(f"  ✅ すべてのチャンネルで有効なサムネイルが設定済み")
        
        print(f"\\n🕒 確認完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    """メイン実行関数"""
    checker = ThumbnailStatusChecker()
    
    try:
        checker.check_all_thumbnails()
        
    except Exception as e:
        print(f"\\n❌ 実行エラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()