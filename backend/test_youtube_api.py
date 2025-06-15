#!/usr/bin/env python3
"""
YouTube API統合テストスクリプト

実装した新機能をテストします
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# パスを追加
sys.path.append(os.path.dirname(__file__))

async def test_category_analyzer():
    """カテゴリ分析のテスト"""
    print("🧪 Testing CategoryAnalyzer...")
    
    try:
        from services.ai_analyzers import CategoryAnalyzer
        
        analyzer = CategoryAnalyzer()
        
        # テストデータ
        test_channel = {
            'channel_name': 'ビューティーガール',
            'description': 'メイクアップチュートリアルとスキンケアレビューを投稿しています。お仕事のご依頼は beauty@example.com まで！',
            'video_count': 150,
            'subscriber_count': 50000
        }
        
        # 分析実行（Gemini APIが利用可能な場合）
        result = await analyzer.analyze_channel_category(test_channel)
        
        print("✅ Category Analysis Result:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return True
        
    except Exception as e:
        print(f"❌ CategoryAnalyzer test failed: {e}")
        return False

async def test_email_extractor():
    """メール抽出のテスト"""
    print("\n🧪 Testing AdvancedEmailExtractor...")
    
    try:
        from services.ai_analyzers import AdvancedEmailExtractor
        
        extractor = AdvancedEmailExtractor()
        
        # テストデータ
        test_channel = {
            'description': '''
            美容系YouTuberです！
            メイクアップチュートリアルを毎週アップしています。
            
            お仕事のご依頼・コラボレーションについては
            business@beautychannel.com まで
            
            プライベートな質問は personal@gmail.com へお願いします
            '''
        }
        
        # メール抽出実行
        result = await extractor.extract_business_emails(test_channel)
        
        print("✅ Email Extraction Result:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return True
        
    except Exception as e:
        print(f"❌ AdvancedEmailExtractor test failed: {e}")
        return False

async def test_batch_processor():
    """バッチプロセッサーのテスト"""
    print("\n🧪 Testing YouTubeBatchProcessor...")
    
    try:
        from services.batch_processor import YouTubeBatchProcessor
        
        processor = YouTubeBatchProcessor()
        
        # 検索クエリ生成のテスト
        beauty_queries = processor._generate_search_queries('beauty')
        print(f"✅ Beauty search queries: {beauty_queries}")
        
        gaming_queries = processor._generate_search_queries('gaming')
        print(f"✅ Gaming search queries: {gaming_queries}")
        
        # トレンド分析のテスト（サンプルデータ）
        test_channels = [
            {
                'channel_id': 'UC123',
                'subscriber_count': 50000,
                'engagement_rate': 4.5,
                'topic_categories': ['Beauty', 'Lifestyle'],
                'emails': ['business@example.com']
            },
            {
                'channel_id': 'UC456', 
                'subscriber_count': 25000,
                'engagement_rate': 6.2,
                'topic_categories': ['Gaming', 'Entertainment'],
                'emails': []
            }
        ]
        
        trend_analysis = processor._analyze_trends(test_channels)
        print("✅ Trend Analysis Result:")
        print(json.dumps(trend_analysis, indent=2, ensure_ascii=False))
        
        return True
        
    except Exception as e:
        print(f"❌ YouTubeBatchProcessor test failed: {e}")
        return False

async def test_integrated_analyzer():
    """統合AI分析のテスト"""
    print("\n🧪 Testing IntegratedAIAnalyzer...")
    
    try:
        from services.ai_analyzers import IntegratedAIAnalyzer
        
        analyzer = IntegratedAIAnalyzer()
        
        # テストデータ
        test_channel = {
            'channel_id': 'UC_TEST_123',
            'channel_name': 'コスメレビューch',
            'description': '''
            コスメレビューとメイクチュートリアルをお届けします！
            新作コスメの使用感や、季節に合わせたメイク方法を紹介。
            
            ビジネスのお問い合わせ：
            collaboration@cosmetuber.jp
            
            チャンネル登録お願いします♪
            ''',
            'subscriber_count': 75000,
            'video_count': 200,
            'view_count': 8500000,
            'engagement_rate': 4.8
        }
        
        # 包括的分析実行
        result = await analyzer.comprehensive_analysis(test_channel)
        
        print("✅ Comprehensive Analysis Result:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return True
        
    except Exception as e:
        print(f"❌ IntegratedAIAnalyzer test failed: {e}")
        return False

def test_environment():
    """環境設定のテスト"""
    print("🧪 Testing Environment Setup...")
    
    # 環境変数の確認
    required_vars = ['YOUTUBE_API_KEY', 'GEMINI_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {missing_vars}")
        print("   Set these in .env.local file")
        return False
    
    print("✅ Environment variables configured")
    return True

async def main():
    """メインテスト実行"""
    print("=" * 60)
    print("🚀 YouTube API Integration Test Suite")
    print("=" * 60)
    
    # 環境テスト
    env_ok = test_environment()
    
    if not env_ok:
        print("\n❌ Environment setup failed. Please configure API keys.")
        return
    
    # 各コンポーネントのテスト
    tests = [
        test_batch_processor(),     # APIキー不要のテスト
        test_category_analyzer(),   # Gemini API使用
        test_email_extractor(),     # Gemini API使用
        test_integrated_analyzer()  # 全機能統合
    ]
    
    results = await asyncio.gather(*tests, return_exceptions=True)
    
    # 結果集計
    passed = sum(1 for r in results if r is True)
    total = len(results)
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! YouTube API integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Check API keys and network connection.")
    
    print("=" * 60)

if __name__ == "__main__":
    # 非同期テスト実行
    asyncio.run(main())