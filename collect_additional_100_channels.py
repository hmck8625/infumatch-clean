#!/usr/bin/env python3
"""
追加100チャンネル収集スクリプト

@description 既存の263チャンネルに加えて、100チャンネルを追加収集
@author InfuMatch Development Team
@version 1.0.0
"""

import json
import os
import re
from datetime import datetime, timezone
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# 設定
YOUTUBE_API_KEY = "AIzaSyDtPl5WSRdxk744ha5Tlwno4iTBZVO96r4"
PROJECT_ID = "hackathon-462905"

class AdditionalChannelCollector:
    """
    追加100チャンネル収集システム
    
    目標:
    - 多様なカテゴリから100チャンネルを収集
    - 高品質なデータを効率的に取得
    - APIクォータを効率的に使用
    """
    
    def __init__(self, api_key=YOUTUBE_API_KEY):
        self.api_key = api_key
        self.service = build('youtube', 'v3', developerKey=api_key)
        self.collected_channels = []
        self.api_calls_used = 0
        
        # 収集ターゲット (カテゴリ別)
        self.collection_targets = {
            'ライフスタイル・暮らし': {
                'keywords': ['暮らし', 'ライフスタイル', '日常', '生活', '一人暮らし', 'インテリア', '掃除', '整理収納'],
                'target_count': 20
            },
            '教育・学習': {
                'keywords': ['勉強', '学習', '資格', '英語', '数学', '歴史', '科学', '読書'],
                'target_count': 15
            },
            '音楽・エンターテイメント': {
                'keywords': ['音楽', 'カバー', '弾いてみた', '歌ってみた', 'アニメ', '映画レビュー'],
                'target_count': 15
            },
            'DIY・クラフト': {
                'keywords': ['DIY', 'ハンドメイド', '手作り', '工作', 'クラフト', '手芸'],
                'target_count': 10
            },
            'ペット・動物': {
                'keywords': ['犬', '猫', 'ペット', '動物', 'ハムスター', '鳥', '熱帯魚'],
                'target_count': 10
            },
            '旅行・観光': {
                'keywords': ['旅行', '観光', '海外旅行', '国内旅行', 'グルメ旅', '温泉'],
                'target_count': 10
            },
            'スポーツ・アウトドア': {
                'keywords': ['スポーツ', 'サッカー', '野球', 'キャンプ', 'アウトドア', '登山'],
                'target_count': 10
            },
            '家族・育児': {
                'keywords': ['育児', '子育て', '家族', 'ママ', 'パパ', '赤ちゃん', '妊娠'],
                'target_count': 10
            }
        }
    
    def extract_emails_from_description(self, description):
        """概要欄からメールアドレスを抽出"""
        if not description:
            return []
        
        email_pattern = r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b'
        emails = re.findall(email_pattern, description)
        return emails[:3]  # 最大3つまで
    
    def collect_channels_by_category(self, category, config):
        """カテゴリ別にチャンネルを収集"""
        print(f"\\n📂 {category} カテゴリの収集開始 (目標: {config['target_count']}チャンネル)")
        
        collected_for_category = []
        
        for keyword in config['keywords']:
            if len(collected_for_category) >= config['target_count']:
                break
            
            try:
                print(f"  🔍 キーワード: '{keyword}' で検索中...")
                
                # YouTube検索APIを実行
                search_response = self.service.search().list(
                    q=f"{keyword} 日本",
                    part='snippet',
                    type='channel',
                    regionCode='JP',
                    relevanceLanguage='ja',
                    maxResults=5,
                    order='relevance'
                ).execute()
                
                self.api_calls_used += 1
                print(f"    API使用: {self.api_calls_used} calls")
                
                # 検索結果を処理
                for item in search_response.get('items', []):
                    if len(collected_for_category) >= config['target_count']:
                        break
                    
                    channel_id = item['id']['channelId']
                    
                    # 重複チェック
                    if any(ch['channel_id'] == channel_id for ch in self.collected_channels):
                        continue
                    if any(ch['channel_id'] == channel_id for ch in collected_for_category):
                        continue
                    
                    # チャンネル詳細情報を取得
                    channel_data = self.get_channel_details(channel_id)
                    if channel_data:
                        channel_data['category'] = category
                        channel_data['discovery_keyword'] = keyword
                        collected_for_category.append(channel_data)
                        print(f"    ✅ {channel_data['channel_title']} ({channel_data['subscriber_count']:,}人)")
                
            except HttpError as e:
                print(f"    ❌ API エラー (keyword: {keyword}): {e}")
                if 'quotaExceeded' in str(e):
                    print("⚠️ APIクォータに達しました")
                    return collected_for_category
                continue
            except Exception as e:
                print(f"    ❌ エラー (keyword: {keyword}): {e}")
                continue
        
        print(f"  📊 {category}: {len(collected_for_category)}チャンネル収集完了")
        return collected_for_category
    
    def get_channel_details(self, channel_id):
        """チャンネル詳細情報を取得"""
        try:
            # チャンネル情報取得
            channel_response = self.service.channels().list(
                part='snippet,statistics',
                id=channel_id
            ).execute()
            
            self.api_calls_used += 1
            
            items = channel_response.get('items', [])
            if not items:
                return None
            
            channel = items[0]
            snippet = channel['snippet']
            statistics = channel.get('statistics', {})
            
            # 登録者数フィルタ (5,000人以上)
            subscriber_count = int(statistics.get('subscriberCount', 0))
            if subscriber_count < 5000:
                return None
            
            # メールアドレス抽出
            emails = self.extract_emails_from_description(snippet.get('description', ''))
            
            # データ構造化
            channel_data = {
                'channel_id': channel_id,
                'channel_title': snippet.get('title', ''),
                'description': snippet.get('description', '')[:500],  # 500文字制限
                'subscriber_count': subscriber_count,
                'video_count': int(statistics.get('videoCount', 0)),
                'view_count': int(statistics.get('viewCount', 0)),
                'country': snippet.get('country', 'JP'),
                'published_at': snippet.get('publishedAt', ''),
                'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                'business_email': emails[0] if emails else None,
                'contact_emails': emails,
                'collected_at': datetime.now(timezone.utc).isoformat(),
                'is_verified': True,
                'data_source': 'youtube_api_v3'
            }
            
            return channel_data
            
        except Exception as e:
            print(f"      ❌ チャンネル詳細取得エラー ({channel_id}): {e}")
            return None
    
    def collect_additional_channels(self):
        """100チャンネルの追加収集を実行"""
        print("🚀 追加100チャンネル収集開始")
        print("=" * 60)
        
        start_time = datetime.now()
        
        # カテゴリ別に収集実行
        for category, config in self.collection_targets.items():
            category_channels = self.collect_channels_by_category(category, config)
            self.collected_channels.extend(category_channels)
            
            # APIクォータ確認
            if self.api_calls_used > 3000:  # 安全マージン
                print("⚠️ APIクォータ上限に近づいています。収集を停止します。")
                break
        
        # 結果サマリー
        self.print_collection_summary(start_time)
        
        # データ保存
        self.save_collected_data()
    
    def print_collection_summary(self, start_time):
        """収集結果サマリーを表示"""
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\\n" + "=" * 60)
        print("🎯 追加チャンネル収集完了サマリー")
        print("=" * 60)
        
        print(f"📊 収集統計:")
        print(f"  - 収集チャンネル数: {len(self.collected_channels)}")
        print(f"  - API呼び出し数: {self.api_calls_used}")
        print(f"  - 実行時間: {duration.total_seconds():.1f}秒")
        
        # カテゴリ別内訳
        category_counts = {}
        total_subscribers = 0
        email_count = 0
        
        for channel in self.collected_channels:
            category = channel.get('category', 'その他')
            category_counts[category] = category_counts.get(category, 0) + 1
            total_subscribers += channel.get('subscriber_count', 0)
            if channel.get('business_email'):
                email_count += 1
        
        print(f"\\n📂 カテゴリ別内訳:")
        for category, count in category_counts.items():
            print(f"  - {category}: {count}チャンネル")
        
        print(f"\\n📈 品質指標:")
        if self.collected_channels:
            avg_subscribers = total_subscribers / len(self.collected_channels)
            print(f"  - 平均登録者数: {avg_subscribers:,.0f}人")
            print(f"  - メール連絡先あり: {email_count}チャンネル ({email_count/len(self.collected_channels)*100:.1f}%)")
        
        print(f"\\n💡 次のステップ:")
        print(f"  1. python3 save_to_databases.py でデータベース保存")
        print(f"  2. python3 update_missing_thumbnails.py でサムネイル更新")
    
    def save_collected_data(self):
        """収集データをJSONファイルに保存"""
        if not self.collected_channels:
            print("⚠️ 保存するデータがありません")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"additional_100_channels_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.collected_channels, f, ensure_ascii=False, indent=2)
            
            print(f"\\n💾 データ保存完了: {filename}")
            print(f"   収集チャンネル数: {len(self.collected_channels)}")
            
        except Exception as e:
            print(f"❌ ファイル保存エラー: {e}")


def main():
    """メイン実行関数"""
    collector = AdditionalChannelCollector()
    
    try:
        collector.collect_additional_channels()
        
    except Exception as e:
        print(f"\\n❌ 実行エラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()