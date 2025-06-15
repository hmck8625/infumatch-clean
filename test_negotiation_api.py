#!/usr/bin/env python3
"""
交渉エージェントAPIのテストスクリプト
"""

import sys
import os
import asyncio
import json

# backend ディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_negotiation_agent():
    """交渉エージェントの直接テスト"""
    try:
        from services.ai_agents.negotiation_agent import NegotiationAgent
        
        print("🤖 交渉エージェントをテスト中...")
        
        # エージェント初期化
        agent = NegotiationAgent()
        print("✅ エージェント初期化完了")
        
        # テストデータ
        test_data = {
            "action": "generate_reply_patterns",
            "email_thread": {
                "id": "test_thread_123",
                "subject": "コラボレーションについて",
                "participants": ["田中美咲", "テスト料理YouTuber"]
            },
            "thread_messages": [
                {
                    "sender": "テスト料理YouTuber",
                    "content": "お疲れ様です。ご提案いただいた件、とても興味があります。料金についてもう少し詳しく教えていただけますか？",
                    "date": "2024-06-14T10:00:00Z",
                    "isFromUser": False
                }
            ],
            "context": {
                "platform": "gmail",
                "thread_length": 1
            }
        }
        
        # 処理実行
        print("🔄 返信パターン生成中...")
        result = await agent.process(test_data)
        
        # 結果表示
        if result.get("success"):
            print("✅ 返信パターン生成成功！")
            print(f"📊 生成されたパターン数: {len(result.get('reply_patterns', []))}")
            
            for i, pattern in enumerate(result.get('reply_patterns', []), 1):
                print(f"\n--- パターン {i}: {pattern.get('pattern_name', 'Unknown')} ---")
                print(f"タイプ: {pattern.get('pattern_type', 'Unknown')}")
                print(f"トーン: {pattern.get('tone', 'Unknown')}")
                print(f"推奨度: {pattern.get('recommendation_score', 0.0):.2f}")
                print(f"内容: {pattern.get('content', 'No content')[:100]}...")
            
            # スレッド分析結果
            thread_analysis = result.get('thread_analysis', {})
            print(f"\n📈 スレッド分析結果:")
            print(f"関係性段階: {thread_analysis.get('relationship_stage', 'Unknown')}")
            print(f"感情トーン: {thread_analysis.get('emotional_tone', 'Unknown')}")
            print(f"緊急度: {thread_analysis.get('urgency_level', 'Unknown')}")
            print(f"主要トピック: {thread_analysis.get('main_topics', [])}")
            
        else:
            print(f"❌ 処理エラー: {result.get('error', 'Unknown error')}")
            
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        print("必要なモジュールがインストールされていません")
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
        import traceback
        traceback.print_exc()

async def test_api_endpoints():
    """APIエンドポイントの直接テスト"""
    try:
        from fastapi.testclient import TestClient
        
        # backend ディレクトリをパスに追加してmainモジュールをインポート
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
        from main import app
        
        client = TestClient(app)
        
        print("\n🌐 APIエンドポイントテスト")
        
        # ヘルスチェック
        response = client.get("/health")
        print(f"Health check: {response.status_code} - {response.json()}")
        
        # negotiation status
        response = client.get("/api/v1/negotiation/status")
        print(f"Negotiation status: {response.status_code} - {response.json()}")
        
        # reply-patterns エンドポイント
        test_payload = {
            "email_thread": {
                "id": "test_thread_123",
                "subject": "コラボレーションについて",
                "participants": ["田中美咲", "テスト料理YouTuber"]
            },
            "thread_messages": [
                {
                    "sender": "テスト料理YouTuber",
                    "content": "お疲れ様です。ご提案いただいた件、とても興味があります。",
                    "date": "2024-06-14T10:00:00Z",
                    "isFromUser": False
                }
            ],
            "context": {
                "platform": "gmail",
                "thread_length": 1
            }
        }
        
        response = client.post("/api/v1/negotiation/reply-patterns", json=test_payload)
        print(f"Reply patterns: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('success')}")
            if result.get('metadata'):
                patterns = result['metadata'].get('reply_patterns', [])
                print(f"Generated {len(patterns)} patterns")
        else:
            print(f"Error response: {response.text}")
            
    except ImportError as e:
        print(f"❌ FastAPI テストクライアント利用不可: {e}")
    except Exception as e:
        print(f"❌ APIテストエラー: {e}")
        import traceback
        traceback.print_exc()

def main():
    """メイン実行関数"""
    print("🧪 交渉エージェントAPI統合テスト開始")
    
    # 直接エージェントテスト
    asyncio.run(test_negotiation_agent())
    
    # APIエンドポイントテスト
    asyncio.run(test_api_endpoints())
    
    print("\n✅ テスト完了")

if __name__ == "__main__":
    main()