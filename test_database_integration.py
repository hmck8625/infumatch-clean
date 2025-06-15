#!/usr/bin/env python3
"""
データベース統合テストスクリプト

@description Firestore と BigQuery との連携をテスト
@author InfuMatch Development Team
@version 1.0.0
"""

import sys
import os
import asyncio

# パス設定
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'services'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'core'))

async def test_database_integration():
    """データベース統合テストメイン"""
    try:
        # データベースサービスのインポート
        from backend.services.database_service import database_service
        
        print("🔍 Testing database integration...")
        print("=" * 50)
        
        # 1. ヘルスチェック
        print("1. Database health check...")
        health = await database_service.health_check()
        print(f"   Health status: {health}")
        
        # 2. インフルエンサー取得テスト
        print("\n2. Testing influencer retrieval...")
        influencers = await database_service.get_influencers(limit=5)
        print(f"   Found {len(influencers)} influencers:")
        
        for i, inf in enumerate(influencers[:3], 1):
            print(f"   {i}. {inf['name']}")
            print(f"      - Channel ID: {inf['channelId']}")
            print(f"      - Subscribers: {inf['subscriberCount']:,}")
            print(f"      - Category: {inf['category']}")
            print(f"      - Engagement Rate: {inf['engagementRate']}%")
        
        # 3. カテゴリ別検索テスト
        print("\n3. Testing category search...")
        tech_influencers = await database_service.get_influencers(
            category="テクノロジー", 
            limit=3
        )
        print(f"   Found {len(tech_influencers)} tech influencers")
        
        # 4. キーワード検索テスト
        print("\n4. Testing keyword search...")
        gaming_influencers = await database_service.get_influencers(
            keyword="ゲーム",
            limit=3
        )
        print(f"   Found {len(gaming_influencers)} gaming influencers")
        
        # 5. 特定インフルエンサー取得テスト
        print("\n5. Testing specific influencer retrieval...")
        if influencers:
            first_influencer_id = influencers[0]['id']
            detailed_inf = await database_service.get_influencer_by_id(first_influencer_id)
            if detailed_inf:
                print(f"   Retrieved detailed data for: {detailed_inf['name']}")
                print(f"   Email: {detailed_inf.get('email', 'N/A')}")
            else:
                print(f"   Could not retrieve detailed data for ID: {first_influencer_id}")
        
        print("\n" + "=" * 50)
        print("✅ Database integration test completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import database service: {e}")
        print("   This might be expected if Google Cloud libraries are not installed")
        print("   Testing with mock data should still work")
        return False
        
    except Exception as e:
        print(f"❌ Database integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_database_integration())
    sys.exit(0 if result else 1)