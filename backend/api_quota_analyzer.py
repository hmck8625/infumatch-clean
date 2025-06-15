#!/usr/bin/env python3
"""
YouTube Data API クォータ分析スクリプト

@description API使用量を分析し、残りの取得可能チャンネル数を計算
@author InfuMatch Development Team
@version 1.0.0
"""

import json
from datetime import datetime, timedelta

class YouTubeAPIQuotaAnalyzer:
    """YouTube API クォータ分析クラス"""
    
    def __init__(self):
        # YouTube Data API v3 のクォータ制限
        self.daily_quota_limit = 10000  # 1日あたりのクォータ上限
        
        # 各API操作のクォータコスト
        self.quota_costs = {
            'search': 100,          # search().list() 1回あたり
            'channels': 1,          # channels().list() 1回あたり
            'videos': 1,            # videos().list() 1回あたり
            'playlists': 1,         # playlists().list() 1回あたり
            'playlistItems': 1      # playlistItems().list() 1回あたり
        }
    
    def calculate_collection_cost(self, search_queries, max_results_per_query, channels_per_search):
        """データ収集にかかるクォータコストを計算"""
        print("🧮 YouTube Data API クォータコスト計算")
        print("=" * 60)
        
        # 検索フェーズのコスト
        search_cost = len(search_queries) * self.quota_costs['search']
        
        # 予想チャンネル数
        expected_channels = len(search_queries) * channels_per_search
        
        # チャンネル詳細取得のコスト（50チャンネルずつバッチ処理）
        channels_batches = (expected_channels + 49) // 50  # 切り上げ
        channels_cost = channels_batches * self.quota_costs['channels']
        
        total_cost = search_cost + channels_cost
        
        print(f"📊 コスト内訳:")
        print(f"  - 検索クエリ数: {len(search_queries)}")
        print(f"  - 検索フェーズコスト: {search_cost} クォータ")
        print(f"  - 予想チャンネル数: {expected_channels}")
        print(f"  - チャンネル詳細バッチ数: {channels_batches}")
        print(f"  - チャンネル詳細コスト: {channels_cost} クォータ")
        print(f"  - 合計コスト: {total_cost} クォータ")
        
        return total_cost, expected_channels
    
    def analyze_past_usage(self):
        """過去の使用量を分析"""
        print("\n📈 過去のAPI使用量分析")
        print("=" * 60)
        
        # ゲーム系収集（4チャンネル）
        gaming_queries = [
            "ゲーム実況", "実況プレイ", "ゲーム配信", 
            "マインクラフト 実況", "フォートナイト 実況"
        ]
        gaming_cost, gaming_channels = self.calculate_collection_cost(
            gaming_queries, 5, 1
        )
        
        print(f"\n🎮 ゲーム系収集:")
        print(f"  - 実際取得: 4チャンネル")
        print(f"  - 推定コスト: {gaming_cost} クォータ")
        
        # 多カテゴリ収集（20チャンネル）
        multi_category_queries = [
            "料理", "レシピ", "グルメ", "お菓子作り", "料理チャンネル",
            "メイク", "コスメ", "美容", "スキンケア", "ヘアアレンジ",
            "日常", "ライフスタイル", "暮らし", "ルーティン", "生活",
            "勉強", "学習", "教育", "解説", "講座",
            "歌ってみた", "演奏", "音楽", "カバー", "弾いてみた",
            "バラエティ", "エンタメ", "面白", "コメディ", "企画"
        ]
        multi_cost, multi_channels = self.calculate_collection_cost(
            multi_category_queries, 4, 1
        )
        
        print(f"\n🎭 多カテゴリ収集:")
        print(f"  - 実際取得: 20チャンネル")
        print(f"  - 推定コスト: {multi_cost} クォータ")
        
        total_used = gaming_cost + multi_cost
        remaining_quota = self.daily_quota_limit - total_used
        
        print(f"\n📊 本日の使用量サマリー:")
        print(f"  - 使用済みクォータ: {total_used} / {self.daily_quota_limit}")
        print(f"  - 残りクォータ: {remaining_quota}")
        print(f"  - 使用率: {total_used/self.daily_quota_limit*100:.1f}%")
        
        return total_used, remaining_quota
    
    def calculate_additional_capacity(self, remaining_quota):
        """追加で取得可能なチャンネル数を計算"""
        print(f"\n🚀 追加取得可能チャンネル数計算")
        print("=" * 60)
        
        # 効率的な収集パターンを想定
        scenarios = [
            {
                "name": "効率重視（大量検索）",
                "search_queries": 20,
                "channels_per_search": 3,
                "description": "多くの検索クエリで幅広く収集"
            },
            {
                "name": "バランス型",
                "search_queries": 10,
                "channels_per_search": 5,
                "description": "検索とチャンネル取得のバランス"
            },
            {
                "name": "精密収集",
                "search_queries": 5,
                "channels_per_search": 8,
                "description": "少ない検索で高品質チャンネルを厳選"
            }
        ]
        
        for scenario in scenarios:
            cost, channels = self.calculate_collection_cost(
                ["dummy"] * scenario["search_queries"],
                5,
                scenario["channels_per_search"]
            )
            
            # 残りクォータで何回実行できるか
            possible_rounds = remaining_quota // cost
            total_additional_channels = possible_rounds * channels
            
            print(f"\n📋 {scenario['name']}:")
            print(f"   説明: {scenario['description']}")
            print(f"   1回のコスト: {cost} クォータ")
            print(f"   1回の取得数: {channels} チャンネル")
            print(f"   実行可能回数: {possible_rounds} 回")
            print(f"   追加取得可能: {total_additional_channels} チャンネル")
        
        return scenarios
    
    def recommend_collection_strategy(self, remaining_quota):
        """推奨収集戦略を提案"""
        print(f"\n💡 推奨収集戦略")
        print("=" * 60)
        
        if remaining_quota >= 8000:
            print("🟢 大容量収集可能")
            print("   - 推奨: 複数カテゴリの大規模収集")
            print("   - 目標: 100+ チャンネル")
            print("   - 戦略: 効率重視 + バランス型の組み合わせ")
            
        elif remaining_quota >= 3000:
            print("🟡 中規模収集可能")
            print("   - 推奨: 特定カテゴリの深掘り収集")
            print("   - 目標: 30-50 チャンネル")
            print("   - 戦略: バランス型で確実に収集")
            
        elif remaining_quota >= 1000:
            print("🟠 小規模収集可能")
            print("   - 推奨: 高品質チャンネルの精密収集")
            print("   - 目標: 10-20 チャンネル")
            print("   - 戦略: 精密収集で質重視")
            
        else:
            print("🔴 残りクォータ少")
            print("   - 推奨: 明日まで待機")
            print("   - 目標: クォータリセットを待つ")
            print("   - 戦略: データ整理と分析に専念")
        
        print(f"\n📅 クォータリセット時刻: 毎日 午前0時（太平洋標準時）")
        print(f"📅 日本時間では: 毎日 午後5時（夏時間）/ 午後6時（標準時間）")
    
    def estimate_future_collections(self):
        """将来の収集計画を提案"""
        print(f"\n🔮 将来の収集計画提案")
        print("=" * 60)
        
        future_categories = [
            "旅行・アウトドア",
            "ペット・動物",
            "テクノロジー・ガジェット",
            "ビジネス・自己啓発",
            "アニメ・漫画",
            "スポーツ・フィットネス",
            "ファッション",
            "DIY・ハンドメイド"
        ]
        
        print("📋 収集候補カテゴリ:")
        for i, category in enumerate(future_categories, 1):
            print(f"  {i}. {category}")
        
        print(f"\n📊 長期収集目標:")
        print(f"  - 目標総チャンネル数: 200-500")
        print(f"  - 推定必要日数: 10-20日")
        print(f"  - 1日あたり目標: 20-30チャンネル")
        print(f"  - 連絡先取得目標: 20-50件（10%成功率想定）")

def main():
    """メイン実行関数"""
    analyzer = YouTubeAPIQuotaAnalyzer()
    
    print("📊 YouTube Data API クォータ分析レポート")
    print("=" * 80)
    print(f"⏰ 分析実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 過去の使用量分析
    total_used, remaining_quota = analyzer.analyze_past_usage()
    
    # 追加収集可能数計算
    analyzer.calculate_additional_capacity(remaining_quota)
    
    # 推奨戦略
    analyzer.recommend_collection_strategy(remaining_quota)
    
    # 将来計画
    analyzer.estimate_future_collections()
    
    print(f"\n🎯 結論:")
    if remaining_quota >= 1000:
        max_additional = remaining_quota // 150  # 保守的な見積もり
        print(f"✅ 本日中にさらに約 {max_additional} チャンネルの追加収集が可能")
    else:
        print(f"⏸️ 本日のクォータはほぼ使い切り、明日のリセットを待機推奨")
    
    print(f"\n📈 現在のデータベース状況:")
    print(f"  - 登録済み: 24チャンネル")
    print(f"  - 連絡可能: 3チャンネル")
    print(f"  - カテゴリ: 3種類")

if __name__ == "__main__":
    main()