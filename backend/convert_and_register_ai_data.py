#!/usr/bin/env python3
"""
AI分析データのFirestore登録用フォーマット変換＆登録

@description ai_enhanced_youtubers.jsonをFirestore形式に変換してデータベースに登録
@author InfuMatch Development Team
@version 2.0.0
"""

import json
import os
from datetime import datetime, timezone
from google.cloud import firestore

def initialize_firestore():
    """Firestore クライアントを初期化"""
    try:
        project_id = "hackathon-462905"
        db = firestore.Client(project=project_id)
        print(f"✅ Firestore クライアント初期化完了 (プロジェクト: {project_id})")
        return db
    except Exception as e:
        print(f"❌ Firestore クライアント初期化エラー: {e}")
        return None

def load_ai_enhanced_data():
    """AI分析統合データを読み込み"""
    try:
        with open('ai_enhanced_youtubers.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ {len(data)} 件のAI分析データを読み込みました")
        return data
    except FileNotFoundError:
        print("❌ ai_enhanced_youtubers.json が見つかりません")
        return []
    except Exception as e:
        print(f"❌ データ読み込みエラー: {e}")
        return []

def convert_to_firestore_format(ai_channel_data):
    """AI分析データをFirestore形式に変換"""
    try:
        # AI分析データから必要な情報を抽出
        ai_analysis = ai_channel_data.get('ai_analysis', {})
        
        # ブランド安全性スコアを取得
        brand_safety = ai_analysis.get('brand_safety', {})
        brand_safety_score = brand_safety.get('overall_safety_score', 0.8)
        
        # カテゴリ情報を取得
        category_tags = ai_analysis.get('category_tags', {})
        primary_category = category_tags.get('primary_category', '未分類')
        
        # 商品マッチング情報を取得
        product_matching = ai_analysis.get('product_matching', {})
        recommended_products = product_matching.get('recommended_products', [])
        
        # Firestore用フォーマット（既存のスキーマに合わせる）
        firestore_doc = {
            'channel_id': ai_channel_data['channel_id'],
            'channel_title': ai_channel_data['channel_title'],
            'description': ai_channel_data['description'],
            'subscriber_count': ai_channel_data['subscriber_count'],
            'video_count': ai_channel_data['video_count'],
            'view_count': ai_channel_data['view_count'],
            'category': primary_category,
            'country': ai_channel_data.get('country', 'JP'),
            'language': 'ja',
            'contact_info': {
                'emails': ai_channel_data.get('emails', []),
                'primary_email': ai_channel_data.get('emails', [None])[0] if ai_channel_data.get('emails') else None
            },
            'engagement_metrics': {
                'engagement_rate': ai_channel_data.get('engagement_estimate', 0) / 100,
                'avg_views_per_video': ai_channel_data['view_count'] / ai_channel_data['video_count'] if ai_channel_data['video_count'] > 0 else 0,
                'has_contact': ai_channel_data.get('has_contact', False)
            },
            'ai_analysis': {
                'engagement_rate': ai_channel_data.get('engagement_estimate', 0) / 100,
                'content_quality_score': 0.8,
                'brand_safety_score': brand_safety_score,
                'growth_potential': 0.7,
                'full_analysis': ai_analysis,  # 完全なAI分析データを保存
                'advanced': {
                    'enhanced_at': datetime.now(timezone.utc).isoformat(),
                    'category': primary_category,
                    'sub_categories': category_tags.get('sub_categories', []),
                    'content_themes': category_tags.get('content_themes', []),
                    'safety_score': brand_safety_score,
                    'confidence': ai_analysis.get('analysis_confidence', 0.5),
                    'target_age': category_tags.get('target_age_group', '不明'),
                    'top_product': recommended_products[0].get('category', '未定') if recommended_products else '未定',
                    'match_score': recommended_products[0].get('match_score', 0.5) if recommended_products else 0.5
                }
            },
            'status': 'active',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'last_analyzed': ai_channel_data.get('collected_at', datetime.now(timezone.utc).isoformat()),
            'fetched_at': ai_channel_data.get('collected_at', datetime.now(timezone.utc).isoformat()),
            'data_source': 'youtube_api',
            'collection_method': 'ai_enhanced_search'
        }
        
        return firestore_doc
        
    except Exception as e:
        print(f"❌ データ変換エラー ({ai_channel_data.get('channel_title', 'Unknown')}): {e}")
        return None

def register_to_firestore(db, channels_data):
    """Firestoreにデータを登録"""
    if not db:
        print("❌ Firestoreクライアントが無効です")
        return False
        
    success_count = 0
    error_count = 0
    
    print(f"\n🔥 Firestoreに {len(channels_data)} チャンネルを登録中...")
    
    for i, channel_data in enumerate(channels_data, 1):
        try:
            # Firestore形式に変換
            firestore_doc = convert_to_firestore_format(channel_data)
            if not firestore_doc:
                error_count += 1
                continue
                
            # 既存のドキュメントをチェック
            doc_ref = db.collection('influencers').document(firestore_doc['channel_id'])
            existing_doc = doc_ref.get()
            
            if existing_doc.exists:
                print(f"⚠️  {i:2d}. {firestore_doc['channel_title']} (既存データをスキップ)")
                continue
                
            # Firestoreに登録
            doc_ref.set(firestore_doc)
            
            print(f"✅ {i:2d}. {firestore_doc['channel_title']} (登録者: {firestore_doc['subscriber_count']:,})")
            success_count += 1
            
        except Exception as e:
            print(f"❌ {i:2d}. 登録失敗 ({channel_data.get('channel_title', 'Unknown')}): {e}")
            error_count += 1
            continue
    
    print(f"\n📊 Firestore登録結果:")
    print(f"  成功: {success_count} 件")
    print(f"  失敗: {error_count} 件")
    
    return success_count > 0

def main():
    """メイン実行関数"""
    print("🤖 AI分析統合YouTuberデータ - Firestore登録")
    print("=" * 60)
    
    # AI分析データを読み込み
    channels_data = load_ai_enhanced_data()
    if not channels_data:
        print("❌ 登録するデータがありません")
        return
    
    print(f"📊 登録対象: {len(channels_data)} チャンネル")
    
    # カテゴリ別統計
    categories = {}
    for channel in channels_data:
        ai_analysis = channel.get('ai_analysis', {})
        category = ai_analysis.get('category_tags', {}).get('primary_category', '未分類')
        categories[category] = categories.get(category, 0) + 1
    
    print("📋 カテゴリ分布:")
    for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {category}: {count} チャンネル")
    
    # Firestore初期化
    db = initialize_firestore()
    if not db:
        print("❌ Firestore初期化に失敗しました")
        return
    
    # Firestoreに登録
    if register_to_firestore(db, channels_data):
        print("✅ Firestore登録完了")
    else:
        print("❌ Firestore登録に失敗しました")
    
    print("\n🎉 データベース登録処理完了！")

if __name__ == "__main__":
    main()