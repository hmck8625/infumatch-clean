#!/usr/bin/env python3
"""
簡単なYouTube API統合テスト
"""

import asyncio
import json
import sys
import os

# パスを追加
sys.path.append(os.path.dirname(__file__))

def test_gemini_connection():
    """Gemini API接続テスト"""
    print("🧪 Testing Gemini Connection...")
    
    try:
        import google.generativeai as genai
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("❌ GEMINI_API_KEY not found")
            return False
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 簡単なテスト
        response = model.generate_content("Hello! Please respond with 'API connection successful'")
        
        if response.text:
            print(f"✅ Gemini API Response: {response.text.strip()}")
            return True
        else:
            print("❌ No response from Gemini API")
            return False
            
    except Exception as e:
        print(f"❌ Gemini API test failed: {e}")
        return False

async def test_category_analyzer():
    """カテゴリ分析器のテスト"""
    print("\n🧪 Testing Category Analyzer...")
    
    try:
        from services.ai_analyzers import CategoryAnalyzer
        
        analyzer = CategoryAnalyzer()
        
        # テストデータ
        test_channel = {
            'channel_name': 'Tech Review Channel',
            'description': 'Latest gadget reviews and technology tutorials',
            'video_count': 100,
            'subscriber_count': 50000
        }
        
        # カテゴリ分析実行
        result = await analyzer.analyze_channel_category(test_channel)
        
        print("✅ Category Analysis Result:")
        print(f"   Main Category: {result.get('main_category', 'Unknown')}")
        print(f"   Confidence: {result.get('confidence', 0)}")
        print(f"   Sub Categories: {result.get('sub_categories', [])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Category Analyzer test failed: {e}")
        return False

async def test_email_extractor():
    """メール抽出器のテスト"""
    print("\n🧪 Testing Email Extractor...")
    
    try:
        from services.ai_analyzers import AdvancedEmailExtractor
        
        extractor = AdvancedEmailExtractor()
        
        # テストデータ
        test_channel = {
            'description': '''
            Welcome to our tech channel!
            For business inquiries, please contact: business@techchannel.com
            Personal messages: personal@gmail.com (not for business)
            Subscribe for more content!
            '''
        }
        
        # メール抽出実行
        result = await extractor.extract_business_emails(test_channel)
        
        print("✅ Email Extraction Result:")
        if result:
            for email_info in result:
                print(f"   Email: {email_info.get('email')}")
                print(f"   Confidence: {email_info.get('confidence')}")
                print(f"   Purpose: {email_info.get('purpose')}")
        else:
            print("   No business emails found")
        
        return True
        
    except Exception as e:
        print(f"❌ Email Extractor test failed: {e}")
        return False

def test_batch_processor_basic():
    """バッチプロセッサーの基本機能テスト"""
    print("\n🧪 Testing Batch Processor Basic Functions...")
    
    try:
        from services.batch_processor import YouTubeBatchProcessor
        
        processor = YouTubeBatchProcessor()
        
        # 検索クエリ生成テスト
        beauty_queries = processor._generate_search_queries('beauty')
        tech_queries = processor._generate_search_queries('tech')
        
        print("✅ Search Query Generation:")
        print(f"   Beauty queries: {beauty_queries}")
        print(f"   Tech queries: {tech_queries}")
        
        # トレンド分析テスト
        test_data = [
            {
                'channel_id': 'UC123',
                'subscriber_count': 50000,
                'engagement_rate': 4.5,
                'topic_categories': ['Beauty'],
                'emails': ['business@example.com']
            },
            {
                'channel_id': 'UC456',
                'subscriber_count': 25000,
                'engagement_rate': 6.2,
                'topic_categories': ['Gaming'],
                'emails': []
            }
        ]
        
        analysis = processor._analyze_trends(test_data)
        
        print("✅ Trend Analysis:")
        print(f"   Average subscribers: {analysis.get('average_subscriber_count', 0):,.0f}")
        print(f"   Average engagement: {analysis.get('average_engagement_rate', 0):.1f}%")
        print(f"   Contactable rate: {analysis.get('contactable_rate', 0)}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Batch Processor test failed: {e}")
        return False

async def main():
    """メインテスト実行"""
    print("=" * 50)
    print("🚀 YouTube API Simple Test Suite")
    print("=" * 50)
    
    # テスト実行
    tests = [
        ("Gemini Connection", test_gemini_connection()),
        ("Batch Processor Basic", test_batch_processor_basic()),
        ("Category Analyzer", test_category_analyzer()),
        ("Email Extractor", test_email_extractor())
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutine(test_func):
                result = await test_func
            else:
                result = test_func
            
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check configuration.")
    
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())