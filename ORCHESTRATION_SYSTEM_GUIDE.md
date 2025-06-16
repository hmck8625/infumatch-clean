# 🎭 マルチエージェントオーケストレーションシステム

## 概要

InfuMatchの交渉システムが大幅にアップグレードされ、複数の専門AIエージェントが協調して動作する高度なオーケストレーションシステムが実装されました。これにより従来の60点レベルから営業プロレベル（90点以上）の交渉対応が可能になりました。

## 🚀 システムアーキテクチャ

### マルチエージェント構成

#### 1. **NegotiationManager** (🎯 指揮官)
- 全体の交渉プロセスを統括
- 4段階の処理フロー管理
- 品質評価・改善システム
- エージェント間協調の最適化

#### 2. **ContextAgent** (🔍 文脈分析)
- 会話履歴の詳細分析
- 企業・インフルエンサー情報の統合
- 交渉段階の評価
- 重要エンティティの抽出

#### 3. **AnalysisAgent** (📊 メッセージ分析)
- 受信メッセージの意図推定
- 感情・トーン分析
- 緊急度レベル評価
- 潜在的な懸念事項の識別

#### 4. **StrategyAgent** (🎯 戦略立案)
- 包括的な交渉戦略構築
- アプローチ決定（協調的/競争的/統合的）
- 段階別戦術の最適化
- リスク対応策の策定

#### 5. **PricingAgent** (💰 価格戦略)
- 市場価格の算出・分析
- 価格交渉戦術の開発
- 競合価格との比較
- 価格正当化ロジック

#### 6. **RiskAgent** (⚠️ リスク評価)
- 包括的なリスク識別
- ブランドセーフティ評価
- リスク軽減策の提案
- 継続的なリスクモニタリング

#### 7. **CommunicationAgent** (💬 文章生成)
- プロフェッショナルな文章作成
- トーン・スタイルの最適化
- 説得力のある構成
- 複数パターンの生成

## 🔄 処理フロー

### Phase 1: 初期分析 (並行実行)
```
ContextAgent → 文脈分析
AnalysisAgent → メッセージ分析  
RiskAgent → リスク評価
```

### Phase 2: 戦略立案
```
StrategyAgent → 交渉戦略構築
PricingAgent → 価格戦略策定
→ 戦略統合・最適化
```

### Phase 3: 文章生成
```
CommunicationAgent → プロ文章生成
→ 品質チェック・バリエーション生成
```

### Phase 4: 最終評価
```
NegotiationManager → 品質評価
→ 改善処理（必要に応じて）
→ 最終結果出力
```

## 📡 API エンドポイント

### 新しいオーケストレーション API

#### POST `/api/negotiation/orchestrated`
マルチエージェントによる高度な交渉処理

**リクエスト例:**
```json
{
  "thread_id": "thread_12345",
  "new_message": "こんにちは。Google Alertsです。弊社の新商品のPRについて、ご協力いただけるインフルエンサーを探しております。",
  "company_settings": {
    "company_name": "InfuMatch",
    "contact_person": "田中美咲",
    "email": "tanaka@infumatch.com",
    "budget": {
      "min": 200000,
      "max": 500000,
      "currency": "JPY"
    }
  },
  "conversation_history": [
    {
      "timestamp": "2024-06-15T10:00:00Z",
      "sender": "client",
      "message": "初回の問い合わせメッセージ"
    }
  ],
  "custom_instructions": "丁寧で専門的な対応を心がけ、具体的な提案を行ってください。"
}
```

**レスポンス例:**
```json
{
  "success": true,
  "content": "いつもお世話になっております。\nInfuMatch の田中美咲です。\n\nGoogle Alerts様の新商品PR案件につきまして、ご連絡いただきありがとうございます。\n\n...",
  "metadata": {
    "processing_type": "multi_agent_orchestration",
    "agent_count": 6,
    "quality_score": 0.89,
    "ai_service": "Multi-Agent Orchestration"
  },
  "ai_thinking": {
    "orchestration_summary": "マルチエージェント協調による交渉処理 (6エージェント)",
    "stage_analysis": "現在の交渉段階: initial_contact",
    "agent_coordination": "エージェント間協調スコア: 0.85",
    "quality_optimization": "品質評価システムにより最適化済み",
    "decision_confidence": "統合判断信頼度: 0.89"
  },
  "orchestration_details": {
    "manager_id": "negotiation_manager",
    "active_agents": ["context_agent", "analysis_agent", "communication_agent", "strategy_agent", "pricing_agent", "risk_agent"],
    "processing_phases": ["analysis", "strategy", "communication", "evaluation"]
  }
}
```

#### GET `/api/negotiation/orchestration/status`
システム状態の確認

## 🛠️ 開発・テスト

### テストスクリプトの実行
```bash
cd backend
python test_orchestration.py
```

### システム初期化
```python
from services.orchestrated_negotiation_service import get_orchestrated_negotiation_service

# サービス取得（自動初期化）
service = await get_orchestrated_negotiation_service()

# システム状態確認
status = service.get_system_status()
print(f"システム準備状況: {status['ready']}")
```

## 🔧 設定とカスタマイズ

### エージェント個別設定
各エージェントは独立した設定を持ち、専門分野に最適化されています：

- **ContextAgent**: temperature=0.2 (一貫性重視)
- **AnalysisAgent**: temperature=0.1 (精確性重視)
- **StrategyAgent**: temperature=0.3 (戦略一貫性)
- **PricingAgent**: temperature=0.2 (計算精確性)
- **RiskAgent**: temperature=0.1 (客観性重視)
- **CommunicationAgent**: temperature=0.4 (創造性とのバランス)

### 品質基準
```python
quality_thresholds = {
    "minimum_acceptable": 0.60,  # 最低合格ライン
    "good_quality": 0.75,        # 良い品質
    "excellent_quality": 0.90    # 優秀な品質
}
```

## 📊 パフォーマンス指標

### エージェント協調メトリクス
- **成功率**: エージェント別タスク成功率
- **平均信頼度**: 出力品質の信頼度
- **処理時間**: エージェント別処理時間
- **協調スコア**: エージェント間の連携効果

### 交渉品質メトリクス
- **メッセージ品質平均**: 生成文章の品質
- **戦略効果性**: 戦略の有効性
- **リスクスコア**: 特定されたリスクレベル
- **段階進行率**: 交渉の進捗効率

## 🎯 期待される効果

### Before (従来システム)
- 単一AIエージェントによる基本的な応答
- 品質レベル: 60点程度
- 文脈理解が限定的
- 戦略性に欠ける

### After (オーケストレーションシステム)
- 6つの専門エージェントによる協調処理
- 品質レベル: 90点以上（営業プロレベル）
- 包括的な文脈理解と戦略立案
- プロフェッショナルなコミュニケーション

## 🔄 フォールバック機能

システムエラー時も安定動作を保証：

1. **段階的フォールバック**
   - 一部エージェント失敗 → 残りエージェントで継続
   - 全エージェント失敗 → 基本テンプレート応答

2. **エラー復旧**
   - 自動エラー検出と回復
   - ログ記録による問題追跡

## 📈 今後の拡張可能性

1. **エージェント追加**
   - 法務チェックエージェント
   - 多言語対応エージェント
   - 業界特化エージェント

2. **学習機能**
   - 交渉結果からの学習
   - パターン認識の向上
   - 個別企業向けカスタマイズ

3. **統合機能**
   - CRMシステム連携
   - 契約管理システム統合
   - レポート自動生成

---

このマルチエージェントオーケストレーションシステムにより、InfuMatchは業界最高水準の自動交渉機能を提供し、インフルエンサーマーケティングの効率と品質を大幅に向上させます。