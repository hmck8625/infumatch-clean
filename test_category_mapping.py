#!/usr/bin/env python3
"""
カテゴリマッピングシステムのテストスクリプト
美容系検索で0件ヒットの問題をデバッグ
"""
import asyncio
import os
from cloud_run_backend.gemini_matching_agent import GeminiMatchingAgent

async def test_category_mapping():
    """カテゴリマッピング機能をテスト"""
    
    # Gemini API キーを環境変数から取得
    gemini_api_key = os.environ.get('GEMINI_API_KEY')
    if not gemini_api_key:
        print("❌ GEMINI_API_KEY environment variable not found")
        return
    
    # エージェントを初期化
    agent = GeminiMatchingAgent(gemini_api_key)
    
    print("🔍 カテゴリマッピングテスト開始")
    print("=" * 50)
    
    # 1. 実際のカテゴリ一覧を取得
    print("📂 利用可能なカテゴリを取得中...")
    available_categories = await agent._get_available_categories()
    print(f"✅ 取得完了: {len(available_categories)}個のカテゴリ")
    print(f"📋 カテゴリ一覧: {available_categories}")
    print()
    
    # 2. テストケース
    test_cases = [
        "美容系",
        "ゲーム実況系", 
        "ビジネス系",
        "料理・グルメ",
        "テクノロジー",
        "ファッション",
        "メイク",
        "コスメ"
    ]
    
    print("🎯 マッピングテスト実行")
    print("-" * 30)
    
    for test_case in test_cases:
        print(f"🔍 テスト: '{test_case}'")
        try:
            mapped_categories = await agent._map_categories_with_gemini(
                test_case, available_categories
            )
            print(f"✅ 結果: {mapped_categories}")
            
            if mapped_categories:
                print(f"   → Firestore検索で使用: {mapped_categories}")
            else:
                print("   ❌ マッピング失敗（全カテゴリ対象になる）")
                
        except Exception as e:
            print(f"   ❌ エラー: {e}")
        
        print()
    
    # 3. 実際のマッチングフローをテスト
    print("🚀 実際のマッチングフローテスト")
    print("-" * 30)
    
    request_data = {
        "company_profile": {
            "name": "テスト化粧品会社",
            "industry": "美容・化粧品",
            "description": "高品質な化粧品を提供",
            "brand_values": ["品質", "信頼性"],
            "target_demographics": ["20-30代女性"],
            "communication_style": "親しみやすい"
        },
        "product_portfolio": {
            "products": [
                {
                    "name": "リップスティック",
                    "category": "化粧品",
                    "description": "長時間持続するリップ",
                    "target_audience": "女性",
                    "price_range": "2000-3000円",
                    "unique_selling_points": ["長持ち", "発色"]
                }
            ]
        },
        "campaign_objectives": {
            "primary_goals": ["ブランド認知度向上"],
            "success_metrics": ["エンゲージメント率"],
            "budget_range": {"min": 100000, "max": 300000},
            "timeline": "3ヶ月"
        },
        "influencer_preferences": {
            "custom_preference": "美容系",
            "subscriber_range": {"min": 10000}
        }
    }
    
    print("📊 美容系インフルエンサー候補を検索中...")
    candidates = await agent._fetch_influencer_candidates(request_data)
    print(f"✅ 検索結果: {len(candidates)}名の候補")
    
    if candidates:
        print("📋 候補例:")
        for i, candidate in enumerate(candidates[:3], 1):
            print(f"  {i}. {candidate.get('channel_name', 'N/A')} - {candidate.get('category', 'N/A')}")
    else:
        print("❌ 候補が見つかりませんでした")
    
    print("\n🏁 テスト完了")

if __name__ == "__main__":
    asyncio.run(test_category_mapping())