#!/usr/bin/env python3
"""
user_settingsコレクションのセットアップスクリプト

このスクリプトは以下を実行します：
1. Firestoreにuser_settingsコレクションを作成
2. サンプルデータを挿入
3. 接続テスト
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from google.cloud import firestore
from google.oauth2 import service_account
from core.config import get_settings

def setup_user_settings_collection():
    """user_settingsコレクションをセットアップ"""
    
    print("🔧 user_settingsコレクションのセットアップを開始します...")
    
    try:
        # 設定を取得
        settings = get_settings()
        
        # Firestoreクライアントを初期化
        if settings.GOOGLE_APPLICATION_CREDENTIALS:
            credentials = service_account.Credentials.from_service_account_file(
                settings.GOOGLE_APPLICATION_CREDENTIALS
            )
            db = firestore.Client(
                project=settings.GOOGLE_CLOUD_PROJECT_ID,
                credentials=credentials
            )
            print(f"✅ Firestoreクライアントを初期化しました (プロジェクト: {settings.GOOGLE_CLOUD_PROJECT_ID})")
        else:
            # デフォルト認証を使用
            db = firestore.Client(project=settings.GOOGLE_CLOUD_PROJECT_ID)
            print(f"✅ デフォルト認証でFirestoreクライアントを初期化しました")
        
        # user_settingsコレクションの参照を取得
        collection_ref = db.collection('user_settings')
        
        # テストデータを作成
        test_email = "test@example.com"
        test_data = {
            "userId": test_email,
            "companyInfo": {
                "companyName": "テスト株式会社",
                "industry": "IT・ソフトウェア",
                "employeeCount": "10-50",
                "website": "https://example.com",
                "description": "テスト用の企業です",
                "contactPerson": "山田太郎",
                "contactEmail": "contact@example.com"
            },
            "products": [
                {
                    "id": "1",
                    "name": "サンプル商品A",
                    "category": "ソフトウェア",
                    "targetAudience": "中小企業",
                    "priceRange": "月額1万円〜5万円",
                    "description": "業務効率化ツール"
                }
            ],
            "negotiationSettings": {
                "preferredTone": "professional",
                "responseTimeExpectation": "24時間以内",
                "budgetFlexibility": "medium",
                "decisionMakers": ["マーケティング部長", "経営陣"],
                "communicationPreferences": ["email", "slack"],
                "specialInstructions": "丁寧な対応を心がけてください",
                "keyPriorities": ["費用対効果", "実績"],
                "avoidTopics": ["競合他社の話題"]
            },
            "matchingSettings": {
                "priorityCategories": ["テクノロジー", "ビジネス", "教育"],
                "minSubscribers": 10000,
                "maxSubscribers": 500000,
                "minEngagementRate": 2.5,
                "excludeCategories": ["ゲーム", "エンタメ"],
                "geographicFocus": ["日本", "関東"],
                "priorityKeywords": ["IT", "DX", "業務効率化"],
                "excludeKeywords": ["ギャンブル", "アダルト"]
            },
            "createdAt": datetime.utcnow().isoformat(),
            "updatedAt": datetime.utcnow().isoformat()
        }
        
        # ドキュメントを作成または更新
        doc_ref = collection_ref.document(test_email)
        doc_ref.set(test_data)
        print(f"✅ テストドキュメントを作成しました: {test_email}")
        
        # 作成したドキュメントを読み取って確認
        doc = doc_ref.get()
        if doc.exists:
            print("✅ ドキュメントの作成を確認しました")
            print(f"📄 保存されたデータ: {doc.to_dict()}")
        else:
            print("❌ ドキュメントの作成に失敗しました")
            return False
        
        # コレクション内のドキュメント数を確認
        docs = collection_ref.limit(10).get()
        doc_count = len(list(docs))
        print(f"\n📊 user_settingsコレクションの統計:")
        print(f"  - ドキュメント数: {doc_count}")
        
        print("\n✅ user_settingsコレクションのセットアップが完了しました！")
        print("\n💡 次のステップ:")
        print("1. Firebase Console (https://console.firebase.google.com/) で確認")
        print("2. フロントエンドから設定を保存してテスト")
        
        return True
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_user_settings_operations():
    """user_settings操作のテスト"""
    print("\n🧪 user_settings操作のテストを開始します...")
    
    try:
        settings = get_settings()
        
        # Firestoreクライアントを初期化
        if settings.GOOGLE_APPLICATION_CREDENTIALS:
            credentials = service_account.Credentials.from_service_account_file(
                settings.GOOGLE_APPLICATION_CREDENTIALS
            )
            db = firestore.Client(
                project=settings.GOOGLE_CLOUD_PROJECT_ID,
                credentials=credentials
            )
        else:
            db = firestore.Client(project=settings.GOOGLE_CLOUD_PROJECT_ID)
        
        collection_ref = db.collection('user_settings')
        
        # 1. 新規ドキュメントの作成
        test_email2 = "test2@example.com"
        test_data2 = {
            "userId": test_email2,
            "companyInfo": {
                "companyName": "サンプル企業",
                "industry": "製造業",
                "employeeCount": "100-500",
                "website": "",
                "description": ""
            },
            "products": [],
            "negotiationSettings": {
                "preferredTone": "friendly",
                "responseTimeExpectation": "48時間以内",
                "budgetFlexibility": "high",
                "decisionMakers": [],
                "communicationPreferences": ["email"],
                "specialInstructions": "",
                "keyPriorities": [],
                "avoidTopics": []
            },
            "matchingSettings": {
                "priorityCategories": [],
                "minSubscribers": 1000,
                "maxSubscribers": 100000,
                "minEngagementRate": 1.0,
                "excludeCategories": [],
                "geographicFocus": ["日本"],
                "priorityKeywords": [],
                "excludeKeywords": []
            },
            "createdAt": datetime.utcnow().isoformat(),
            "updatedAt": datetime.utcnow().isoformat()
        }
        
        doc_ref2 = collection_ref.document(test_email2)
        doc_ref2.set(test_data2)
        print(f"✅ 2つ目のテストドキュメントを作成しました: {test_email2}")
        
        # 2. ドキュメントの更新テスト
        update_data = {
            "companyInfo.companyName": "更新されたサンプル企業",
            "updatedAt": datetime.utcnow().isoformat()
        }
        doc_ref2.update(update_data)
        print("✅ ドキュメントの更新に成功しました")
        
        # 3. コレクション全体の取得テスト
        all_docs = collection_ref.get()
        print(f"\n📋 user_settingsコレクションの全ドキュメント:")
        for doc in all_docs:
            print(f"  - {doc.id}: {doc.to_dict().get('companyInfo', {}).get('companyName', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ テスト中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== user_settingsコレクション セットアップツール ===\n")
    
    # セットアップを実行
    if setup_user_settings_collection():
        # セットアップ成功時はテストも実行
        test_user_settings_operations()
    else:
        print("\n❌ セットアップに失敗しました")
        sys.exit(1)