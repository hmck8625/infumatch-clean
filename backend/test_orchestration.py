#!/usr/bin/env python3
"""
マルチエージェントオーケストレーションシステムのテストスクリプト

@description 実装したマルチエージェントシステムの動作確認
@author InfuMatch Development Team
@version 2.0.0
"""

import asyncio
import json
import logging
from datetime import datetime

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_orchestration_system():
    """マルチエージェントオーケストレーションシステムのテスト"""
    
    print("🎭 マルチエージェントオーケストレーションシステム テスト開始")
    print("=" * 80)
    
    try:
        # システムのインポート
        from services.orchestrated_negotiation_service import OrchestratedNegotiationService
        
        print("✅ モジュールインポート成功")
        
        # サービスの初期化
        print("\n🚀 サービス初期化中...")
        service = OrchestratedNegotiationService()
        initialization_success = await service.initialize()
        
        if initialization_success:
            print("✅ マルチエージェントシステム初期化成功")
        else:
            print("⚠️ マルチエージェントシステム初期化部分的成功")
        
        # システム状態の確認
        print("\n📊 システム状態確認...")
        status = service.get_system_status()
        print(f"システム状態: {status['status']}")
        print(f"準備完了: {status['ready']}")
        
        if 'orchestration_system' in status:
            orchestration_status = status['orchestration_system']
            total_agents = orchestration_status['system_health']['total_agents']
            print(f"登録エージェント数: {total_agents}")
            
            if 'orchestration_details' in orchestration_status:
                registered_agents = orchestration_status['orchestration_details']['registered_agents']
                print("📋 登録エージェント:")
                for agent_id, agent_info in registered_agents.items():
                    print(f"  - {agent_id}: {agent_info.get('specialization', 'Unknown')}")
        
        # テストメッセージによる交渉処理
        print("\n💬 テストメッセージ処理中...")
        
        test_message = """
こんにちは。Google Alertsです。

弊社の新商品「AI Search Pro」のPRについて、
ご協力いただけるインフルエンサーを探しております。

以下のような条件で検討いただけますでしょうか：
- YouTube投稿1本
- 商品レビュー形式
- 予算：30万円程度
- 実施時期：来月中

ご検討のほど、よろしくお願いいたします。
"""
        
        company_settings = {
            "company_name": "InfuMatch",
            "contact_person": "田中美咲",
            "email": "tanaka@infumatch.com",
            "budget": {
                "min": 200000,
                "max": 500000,
                "currency": "JPY"
            }
        }
        
        conversation_history = [
            {
                "timestamp": "2024-06-15T10:00:00Z",
                "sender": "client",
                "message": "初回の問い合わせメッセージ"
            }
        ]
        
        custom_instructions = """
以下の点を重視してください：
- 丁寧で専門的な対応
- 具体的な提案内容の提示
- 価格の妥当性をアピール
- 長期的な関係構築を意識
"""
        
        print("🎯 マルチエージェント処理実行中...")
        result = await service.process_negotiation_message(
            thread_id="test_thread_001",
            new_message=test_message,
            company_settings=company_settings,
            conversation_history=conversation_history,
            custom_instructions=custom_instructions
        )
        
        print("\n📄 処理結果:")
        print(f"成功: {result['success']}")
        print(f"処理タイプ: {result['metadata'].get('processing_type', 'unknown')}")
        
        if result['success']:
            print("\n📝 生成された返信:")
            print("-" * 60)
            print(result['content'])
            print("-" * 60)
            
            # AI思考過程の表示
            if 'ai_thinking' in result:
                print("\n🧠 AI思考過程:")
                ai_thinking = result['ai_thinking']
                for key, value in ai_thinking.items():
                    print(f"  {key}: {value}")
            
            # オーケストレーション詳細の表示
            if 'orchestration_details' in result:
                print("\n🎭 オーケストレーション詳細:")
                orchestration = result['orchestration_details']
                print(f"  マネージャーID: {orchestration.get('manager_id')}")
                print(f"  アクティブエージェント: {orchestration.get('active_agents', [])}")
                print(f"  処理フェーズ: {orchestration.get('processing_phases', [])}")
        
        else:
            print(f"❌ 処理失敗: {result.get('metadata', {}).get('fallback_reason', 'unknown')}")
        
        # システムのシャットダウン
        print("\n🔄 システムシャットダウン...")
        await service.shutdown()
        print("✅ システムシャットダウン完了")
        
    except ImportError as e:
        print(f"❌ インポートエラー: {str(e)}")
        print("必要なモジュールが見つかりません")
        
    except Exception as e:
        print(f"❌ テスト実行エラー: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("🎭 マルチエージェントオーケストレーションシステム テスト完了")


async def test_individual_agents():
    """個別エージェントのテスト"""
    
    print("\n🔧 個別エージェントテスト開始")
    print("-" * 60)
    
    try:
        from services.ai_agents.orchestration.orchestration_factory import OrchestrationFactory
        
        # 最小限のシステムでテスト
        manager = OrchestrationFactory.create_minimal_system()
        
        status = OrchestrationFactory.get_system_status(manager)
        print(f"最小システム状態: {status['system_status']}")
        print(f"登録エージェント数: {status['system_health']['total_agents']}")
        
        # カスタムシステムでテスト
        custom_manager = OrchestrationFactory.create_custom_system(['analysis', 'communication', 'strategy'])
        
        custom_status = OrchestrationFactory.get_system_status(custom_manager)
        print(f"カスタムシステム状態: {custom_status['system_status']}")
        print(f"カスタムシステム登録エージェント数: {custom_status['system_health']['total_agents']}")
        
        print("✅ 個別エージェントテスト完了")
        
    except Exception as e:
        print(f"❌ 個別エージェントテスト失敗: {str(e)}")


if __name__ == "__main__":
    print("🎭 マルチエージェントオーケストレーションシステム テストスイート")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # メインテストの実行
    asyncio.run(test_orchestration_system())
    
    # 個別エージェントテストの実行
    asyncio.run(test_individual_agents())
    
    print("\n🎉 全テスト完了")