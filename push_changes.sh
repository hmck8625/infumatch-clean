#!/bin/bash

# 完全自動交渉システムの変更をコミット・プッシュ

echo "📦 変更をステージング..."
git add -A

echo "💾 コミット作成..."
git commit -m "feat: 完全自動交渉システム実装完了 (Phase 1-3)

Phase 1: 基本的な自動交渉
- Gmail API連携によるスレッド返信機能
- 4段階交渉処理システム
- カスタム指示対応

Phase 2: インテリジェント自動交渉  
- 動的戦略調整機能
- Gmail自動監視システム
- スレッド状態管理
- マルチラウンド交渉対応

Phase 3: AI学習と完全自動化
- 交渉パターンストレージ
- 戦略最適化エンジン（強化学習）
- 予測分析モジュール
- 完全自動化オーケストレーター（4モード対応）

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

echo "🚀 リモートにプッシュ..."
git push origin main

echo "✅ 完了!"