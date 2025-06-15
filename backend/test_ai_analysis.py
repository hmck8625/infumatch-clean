#!/usr/bin/env python3
"""
AI分析機能テスト

@description リアルタイムAI分析機能のテスト実行
簡単なサンプルデータでAI分析を実行

@author InfuMatch Development Team
@version 1.0.0
"""

import asyncio
import json
from services.ai_channel_analyzer import AdvancedChannelAnalyzer

async def test_ai_analysis():
    """AI分析機能のテスト"""
    print("🤖 AI分析機能テスト開始")
    print("=" * 60)
    
    # テスト用サンプルデータ
    sample_channel_data = {
        "channel_id": "UC_test_123",
        "channel_title": "ひとり暮らしのコスメレビュー",
        "description": "20代女性によるプチプラコスメのレビューチャンネルです。メイク初心者向けに、ドラッグストアで買える化粧品をわかりやすく紹介しています。スキンケアやヘアケアの情報も配信中！お仕事依頼はメールでお願いします。contact@example.com",
        "subscriber_count": 45000,
        "video_count": 150,
        "view_count": 2500000,
        "category": "美容・コスメ",
        "engagement_estimate": 3.7
    }
    
    # AI分析器を初期化
    analyzer = AdvancedChannelAnalyzer()
    
    try:
        print("🔄 AI分析実行中...")
        print(f"   チャンネル: {sample_channel_data['channel_title']}")
        print(f"   登録者数: {sample_channel_data['subscriber_count']:,}人")
        print()
        
        # 包括的AI分析実行
        analysis_result = await analyzer.analyze_channel_comprehensive(sample_channel_data)
        
        print("✅ AI分析完了!")
        print("=" * 60)
        
        # 結果表示
        print("📊 AI分析結果:")
        print(f"   分析ID: {analysis_result.get('channel_id')}")
        print(f"   分析時刻: {analysis_result.get('analysis_timestamp')}")
        print(f"   信頼度: {analysis_result.get('analysis_confidence', 0):.2f}")
        print()
        
        # カテゴリタグ分析
        category_tags = analysis_result.get('category_tags', {})
        print("🎯 カテゴリ分析:")
        print(f"   主カテゴリ: {category_tags.get('primary_category', 'N/A')}")
        print(f"   サブカテゴリ: {', '.join(category_tags.get('sub_categories', []))}")
        print(f"   コンテンツテーマ: {', '.join(category_tags.get('content_themes', []))}")
        print(f"   対象年齢層: {category_tags.get('target_age_group', 'N/A')}")
        print()
        
        # チャンネル概要分析
        summary = analysis_result.get('channel_summary', {})
        print("📝 チャンネル概要:")
        print(f"   概要: {summary.get('channel_description', 'N/A')}")
        print(f"   コンテンツスタイル: {summary.get('content_style', 'N/A')}")
        print(f"   更新頻度推定: {summary.get('posting_frequency', 'N/A')}")
        print(f"   専門性: {summary.get('expertise_level', 'N/A')}")
        print(f"   エンタメ性: {summary.get('entertainment_value', 'N/A')}")
        print(f"   教育価値: {summary.get('educational_value', 'N/A')}")
        print()
        
        # 商材マッチング分析
        product_matching = analysis_result.get('product_matching', {})
        print("💼 商材マッチング:")
        recommended_products = product_matching.get('recommended_products', [])
        for i, product in enumerate(recommended_products[:3], 1):
            print(f"   {i}. カテゴリ: {product.get('category', 'N/A')}")
            print(f"      価格帯: {product.get('price_range', 'N/A')}")
            print(f"      マッチ度: {product.get('match_score', 0):.2f}")
            print(f"      理由: {product.get('reasoning', 'N/A')}")
            print()
        
        print(f"   推奨コラボ形式: {', '.join(product_matching.get('collaboration_formats', []))}")
        print(f"   期待効果: {product_matching.get('expected_impact', 'N/A')}")
        print(f"   想定コンバージョン: {product_matching.get('target_conversion', 'N/A')}")
        print()
        
        # オーディエンス分析
        audience = analysis_result.get('audience_profile', {})
        print("👥 オーディエンス分析:")
        print(f"   オーディエンス規模: {audience.get('audience_size', 'N/A')}")
        print(f"   エンゲージメントレベル: {audience.get('engagement_level', 'N/A')}")
        print(f"   リーチポテンシャル: {audience.get('reach_potential', 'N/A')}")
        
        demographics = audience.get('estimated_demographics', {})
        print(f"   推定年齢層: {demographics.get('age', 'N/A')}")
        print(f"   性別分布: {demographics.get('gender', 'N/A')}")
        print(f"   所得層: {demographics.get('income', 'N/A')}")
        print()
        
        # ブランドセーフティ
        brand_safety = analysis_result.get('brand_safety', {})
        print("🛡️ ブランドセーフティ:")
        print(f"   コンテンツ適切性: {brand_safety.get('content_appropriateness', 'N/A')}")
        print(f"   炎上リスク: {brand_safety.get('controversy_risk', 'N/A')}")
        print(f"   ブランドイメージ影響: {brand_safety.get('brand_image_impact', 'N/A')}")
        print(f"   コンプライアンス: {brand_safety.get('compliance_score', 0):.2f}")
        print(f"   総合安全性: {brand_safety.get('overall_safety_score', 0):.2f}")
        print(f"   注意事項: {brand_safety.get('safety_notes', 'N/A')}")
        
        print("=" * 60)
        print("🎉 AI分析テスト完了!")
        
        # 結果をJSONファイルに保存
        with open('ai_analysis_test_result.json', 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        
        print("💾 分析結果を ai_analysis_test_result.json に保存しました")
        
        return analysis_result
        
    except Exception as e:
        print(f"❌ AI分析エラー: {e}")
        return None

async def main():
    """メイン実行関数"""
    await test_ai_analysis()

if __name__ == "__main__":
    asyncio.run(main())