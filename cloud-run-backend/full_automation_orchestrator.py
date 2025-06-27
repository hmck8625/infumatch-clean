"""
完全自動化オーケストレーター
すべてのコンポーネントを統合し、完全自動交渉を実現
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging

# 各モジュールのインポート
from auto_negotiation_manager import AutoNegotiationManager
from gmail_auto_monitor import GmailAutoMonitor
from thread_state_manager import ThreadStateManager, NegotiationStage, ThreadStatus
from negotiation_pattern_storage import NegotiationPatternStorage, NegotiationOutcome
from strategy_optimization_engine import StrategyOptimizationEngine, OptimizationMetric
from predictive_analytics_module import PredictiveAnalyticsModule

class AutomationMode(Enum):
    """自動化モード"""
    MANUAL = "manual"                    # 手動モード
    SEMI_AUTO = "semi_auto"             # 半自動（承認必要）
    FULL_AUTO = "full_auto"             # 完全自動
    LEARNING = "learning"               # 学習モード（観察のみ）

class FullAutomationOrchestrator:
    """完全自動化オーケストレーター"""
    
    def __init__(self, gemini_model, db_client=None):
        self.gemini_model = gemini_model
        self.db = db_client
        
        # 各コンポーネントの初期化
        self.thread_state_manager = ThreadStateManager(db_client)
        self.pattern_storage = NegotiationPatternStorage(db_client)
        self.optimization_engine = StrategyOptimizationEngine(self.pattern_storage, db_client)
        self.predictive_analytics = PredictiveAnalyticsModule(self.pattern_storage, self.optimization_engine)
        self.auto_negotiation_manager = AutoNegotiationManager(gemini_model, db_client)
        
        # Gmail監視（認証マネージャーは後で注入）
        self.gmail_monitor = None
        
        # オーケストレーション設定
        self.orchestration_config = {
            "mode": AutomationMode.SEMI_AUTO,
            "max_concurrent_negotiations": 5,
            "decision_confidence_threshold": 0.8,
            "learning_batch_size": 10,
            "optimization_interval_hours": 24,
            "emergency_stop_enabled": True,
            "human_escalation_rules": {
                "budget_deviation_percentage": 30,
                "negotiation_rounds_limit": 5,
                "risk_score_threshold": 0.8,
                "sentiment_threshold": -0.5
            }
        }
        
        # 実行状態
        self.is_running = False
        self.active_negotiations = {}
        self.performance_metrics = {
            "total_negotiations": 0,
            "successful_closures": 0,
            "failed_negotiations": 0,
            "average_time_to_close": 0,
            "total_deal_value": 0,
            "automation_interventions": 0
        }
    
    async def start_full_automation(
        self,
        user_id: str,
        company_settings: Dict,
        automation_mode: AutomationMode = AutomationMode.SEMI_AUTO
    ) -> Dict:
        """完全自動化を開始"""
        
        if self.is_running:
            return {
                "success": False,
                "message": "既に自動化が実行中です"
            }
        
        self.orchestration_config["mode"] = automation_mode
        self.is_running = True
        
        print(f"🚀 完全自動化システム起動 - モード: {automation_mode.value}")
        
        # 非同期タスクを開始
        asyncio.create_task(self._orchestration_loop(user_id, company_settings))
        
        # 定期的な最適化タスク
        asyncio.create_task(self._optimization_loop())
        
        # パフォーマンス監視タスク
        asyncio.create_task(self._performance_monitoring_loop())
        
        return {
            "success": True,
            "message": f"自動化システムが{automation_mode.value}モードで起動しました",
            "mode": automation_mode.value,
            "config": self.orchestration_config,
            "timestamp": datetime.now().isoformat()
        }
    
    async def stop_automation(self) -> Dict:
        """自動化を停止"""
        
        self.is_running = False
        
        # Gmail監視を停止
        if self.gmail_monitor:
            await self.gmail_monitor.stop_monitoring()
        
        # アクティブな交渉を保存
        for thread_id, negotiation in self.active_negotiations.items():
            await self.thread_state_manager.update_thread_state(
                thread_id,
                {"status": ThreadStatus.PENDING_APPROVAL.value}
            )
        
        return {
            "success": True,
            "message": "自動化システムを停止しました",
            "active_negotiations_saved": len(self.active_negotiations),
            "performance_summary": self.performance_metrics,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _orchestration_loop(
        self,
        user_id: str,
        company_settings: Dict
    ) -> None:
        """メインオーケストレーションループ"""
        
        while self.is_running:
            try:
                # 1. 新着メールチェック（Gmail監視経由）
                if self.gmail_monitor and self.orchestration_config["mode"] != AutomationMode.MANUAL:
                    # Gmail監視は別タスクで実行されるため、ここでは状態確認のみ
                    pass
                
                # 2. アクティブな交渉の処理
                await self._process_active_negotiations(company_settings)
                
                # 3. 学習とパターン更新
                if self.orchestration_config["mode"] == AutomationMode.LEARNING:
                    await self._learning_cycle()
                
                # 4. タイムアウトチェック
                await self._check_timeouts()
                
                # 5. エスカレーションチェック
                await self._check_escalations()
                
                # 待機
                await asyncio.sleep(30)  # 30秒ごとに実行
                
            except Exception as e:
                logging.error(f"オーケストレーションエラー: {e}")
                await asyncio.sleep(60)  # エラー時は長めに待機
    
    async def _process_active_negotiations(
        self,
        company_settings: Dict
    ) -> None:
        """アクティブな交渉を処理"""
        
        # 同時実行数制限
        if len(self.active_negotiations) >= self.orchestration_config["max_concurrent_negotiations"]:
            return
        
        # 処理待ちの交渉を取得
        pending_threads = await self.thread_state_manager.get_active_threads(
            status_filter=[ThreadStatus.ACTIVE, ThreadStatus.WAITING_RESPONSE]
        )
        
        for thread_data in pending_threads[:5]:  # 最大5件処理
            thread_id = thread_data["thread_id"]
            
            if thread_id in self.active_negotiations:
                continue
            
            # 予測分析を実行
            prediction = await self.predictive_analytics.generate_comprehensive_prediction(
                thread_id,
                thread_data,
                []  # 会話履歴は別途取得
            )
            
            # 自動化モードに応じた処理
            if self.orchestration_config["mode"] == AutomationMode.FULL_AUTO:
                await self._execute_full_auto_negotiation(
                    thread_id, thread_data, prediction, company_settings
                )
            elif self.orchestration_config["mode"] == AutomationMode.SEMI_AUTO:
                await self._execute_semi_auto_negotiation(
                    thread_id, thread_data, prediction, company_settings
                )
            
            self.active_negotiations[thread_id] = {
                "started_at": datetime.now(),
                "prediction": prediction,
                "status": "processing"
            }
    
    async def _execute_full_auto_negotiation(
        self,
        thread_id: str,
        thread_data: Dict,
        prediction: Dict,
        company_settings: Dict
    ) -> None:
        """完全自動交渉を実行"""
        
        print(f"🤖 完全自動交渉実行: {thread_id}")
        
        # 戦略最適化
        optimized_strategy = await self.optimization_engine.optimize_strategy(
            thread_data,
            [],  # 履歴パターン
            OptimizationMetric.DEAL_CLOSURE_RATE
        )
        
        # 予測信頼度チェック
        if prediction["overall_confidence"] < self.orchestration_config["decision_confidence_threshold"]:
            print(f"⚠️ 信頼度不足: {prediction['overall_confidence']:.2f}")
            await self._escalate_to_human(thread_id, "低信頼度")
            return
        
        # リスクチェック
        risk_level = prediction["risk_assessment"]["overall_risk_level"]
        if risk_level == "high":
            print(f"⚠️ 高リスク検出: {thread_id}")
            if self.orchestration_config["emergency_stop_enabled"]:
                await self._escalate_to_human(thread_id, "高リスク")
                return
        
        # 自動交渉マネージャーで処理
        result = await self.auto_negotiation_manager.process_auto_negotiation_round(
            thread_id=thread_id,
            new_message="",  # 最新メッセージ
            conversation_history=[],  # 会話履歴
            company_settings=company_settings,
            round_number=thread_data.get("round_number", 1)
        )
        
        if result["success"] and result.get("action") == "auto_send":
            # 自動送信実行
            await self._execute_auto_send(thread_id, result)
            
            # パフォーマンスメトリクス更新
            self.performance_metrics["automation_interventions"] += 1
            
            # パターン記録
            await self._record_negotiation_pattern(thread_id, result, "auto_executed")
    
    async def _execute_semi_auto_negotiation(
        self,
        thread_id: str,
        thread_data: Dict,
        prediction: Dict,
        company_settings: Dict
    ) -> None:
        """半自動交渉を実行（人間の承認付き）"""
        
        print(f"🤝 半自動交渉実行: {thread_id}")
        
        # 推奨アクションを生成
        recommendations = prediction["recommended_actions"]
        
        # 人間の判断が必要な条件をチェック
        escalation_rules = self.orchestration_config["human_escalation_rules"]
        
        needs_human = False
        escalation_reasons = []
        
        # 予算逸脱チェック
        budget_gap = thread_data.get("budget_gap_percentage", 0)
        if budget_gap > escalation_rules["budget_deviation_percentage"]:
            needs_human = True
            escalation_reasons.append("予算逸脱")
        
        # ラウンド数チェック
        if thread_data.get("round_number", 1) > escalation_rules["negotiation_rounds_limit"]:
            needs_human = True
            escalation_reasons.append("交渉長期化")
        
        # リスクスコアチェック
        if prediction.get("risk_score", 0) > escalation_rules["risk_score_threshold"]:
            needs_human = True
            escalation_reasons.append("高リスク")
        
        if needs_human:
            await self._queue_for_human_approval(
                thread_id, recommendations, escalation_reasons
            )
        else:
            # 自動実行可能
            await self._execute_full_auto_negotiation(
                thread_id, thread_data, prediction, company_settings
            )
    
    async def _optimization_loop(self) -> None:
        """定期的な最適化ループ"""
        
        while self.is_running:
            try:
                # 最適化間隔待機
                await asyncio.sleep(
                    self.orchestration_config["optimization_interval_hours"] * 3600
                )
                
                print("🔧 戦略最適化サイクル開始")
                
                # パフォーマンスデータを収集
                performance_data = await self._collect_performance_data()
                
                # 各交渉の結果を学習
                for thread_id, outcome in performance_data.items():
                    if "strategy_used" in outcome:
                        await self.optimization_engine.update_strategy_weights(
                            outcome, outcome["strategy_used"]
                        )
                
                # パターン分析を更新
                analytics = await self.pattern_storage.get_pattern_analytics()
                
                print(f"📊 最適化完了 - 成功率: {analytics['average_success_rate']:.2%}")
                
            except Exception as e:
                logging.error(f"最適化ループエラー: {e}")
    
    async def _performance_monitoring_loop(self) -> None:
        """パフォーマンス監視ループ"""
        
        while self.is_running:
            try:
                await asyncio.sleep(300)  # 5分ごと
                
                # メトリクスを計算
                if self.performance_metrics["total_negotiations"] > 0:
                    success_rate = (
                        self.performance_metrics["successful_closures"] / 
                        self.performance_metrics["total_negotiations"]
                    )
                    
                    print(f"📈 パフォーマンス: 成功率 {success_rate:.2%}, "
                          f"総取引数 {self.performance_metrics['total_negotiations']}")
                
                # 異常検知
                if success_rate < 0.3 and self.performance_metrics["total_negotiations"] > 10:
                    print("⚠️ パフォーマンス低下を検出")
                    # 自動的に慎重モードに切り替え
                    self.orchestration_config["decision_confidence_threshold"] = 0.9
                
            except Exception as e:
                logging.error(f"監視ループエラー: {e}")
    
    async def _learning_cycle(self) -> None:
        """学習サイクル（観察モード）"""
        
        # 人間の交渉を観察して学習
        completed_negotiations = await self._get_recently_completed_negotiations()
        
        for negotiation in completed_negotiations:
            # パターンを抽出
            pattern_data = self._extract_pattern_from_negotiation(negotiation)
            
            # 成功メトリクスを計算
            success_metrics = self._calculate_success_metrics(negotiation)
            
            # パターンストレージに記録
            await self.pattern_storage.record_negotiation_pattern(
                negotiation["thread_id"],
                pattern_data,
                NegotiationOutcome.DEAL_CLOSED if negotiation["success"] else NegotiationOutcome.NEGOTIATION_FAILED,
                success_metrics
            )
        
        print(f"📚 学習完了: {len(completed_negotiations)}件の交渉から学習")
    
    async def _check_timeouts(self) -> None:
        """タイムアウトをチェック"""
        
        for thread_id, negotiation in list(self.active_negotiations.items()):
            started_at = negotiation["started_at"]
            
            # 48時間以上経過
            if datetime.now() - started_at > timedelta(hours=48):
                print(f"⏰ タイムアウト: {thread_id}")
                
                # タイムアウト処理
                await self.thread_state_manager.update_thread_state(
                    thread_id,
                    {"status": ThreadStatus.EXPIRED.value}
                )
                
                del self.active_negotiations[thread_id]
    
    async def _check_escalations(self) -> None:
        """エスカレーション条件をチェック"""
        
        for thread_id in list(self.active_negotiations.keys()):
            thread_state = await self.thread_state_manager.get_thread_state(thread_id)
            
            # エスカレーション済みチェック
            if thread_state.get("status") == ThreadStatus.ESCALATED.value:
                await self._escalate_to_human(thread_id, thread_state.get("escalation_reason"))
                del self.active_negotiations[thread_id]
    
    async def _execute_auto_send(
        self,
        thread_id: str,
        negotiation_result: Dict
    ) -> None:
        """自動送信を実行"""
        
        print(f"📤 自動送信実行: {thread_id}")
        
        # 実際の送信処理（Gmail API経由）
        # TODO: Gmail送信実装
        
        # 送信イベントを記録
        await self.thread_state_manager.record_negotiation_event(
            thread_id,
            "message_sent",
            {
                "auto_sent": True,
                "content": negotiation_result.get("selected_pattern", {}).get("content", ""),
                "confidence": negotiation_result.get("confidence", 0)
            }
        )
    
    async def _escalate_to_human(
        self,
        thread_id: str,
        reason: str
    ) -> None:
        """人間にエスカレート"""
        
        print(f"👤 人間にエスカレート: {thread_id} - 理由: {reason}")
        
        await self.thread_state_manager.update_thread_state(
            thread_id,
            {
                "status": ThreadStatus.ESCALATED.value,
                "escalation_reason": reason,
                "escalated_at": datetime.now().isoformat()
            }
        )
        
        # 通知を送信（実装は省略）
    
    async def _queue_for_human_approval(
        self,
        thread_id: str,
        recommendations: List[Dict],
        reasons: List[str]
    ) -> None:
        """人間の承認待ちキューに追加"""
        
        await self.thread_state_manager.update_thread_state(
            thread_id,
            {
                "status": ThreadStatus.PENDING_APPROVAL.value,
                "approval_reasons": reasons,
                "ai_recommendations": recommendations,
                "queued_at": datetime.now().isoformat()
            }
        )
    
    async def _record_negotiation_pattern(
        self,
        thread_id: str,
        result: Dict,
        execution_type: str
    ) -> None:
        """交渉パターンを記録"""
        
        # パターンデータを構築
        pattern_data = {
            "execution_type": execution_type,
            "conversation_summary": result.get("context_analysis", {}),
            "key_phrases": result.get("key_phrases", []),
            "negotiation_flow": result.get("flow", []),
            "decision_points": result.get("decisions", [])
        }
        
        # 成功メトリクス（仮）
        success_metrics = {
            "deal_value": 0,
            "duration_hours": 24,
            "rounds_count": result.get("round_number", 1),
            "satisfaction_score": result.get("confidence", 0.5)
        }
        
        await self.pattern_storage.record_negotiation_pattern(
            thread_id,
            pattern_data,
            NegotiationOutcome.DEAL_CLOSED,  # 仮
            success_metrics
        )
    
    async def _collect_performance_data(self) -> Dict:
        """パフォーマンスデータを収集"""
        
        # 最近完了した交渉のデータを収集
        return {}  # 実装は省略
    
    async def _get_recently_completed_negotiations(self) -> List[Dict]:
        """最近完了した交渉を取得"""
        
        # 実装は省略
        return []
    
    def _extract_pattern_from_negotiation(self, negotiation: Dict) -> Dict:
        """交渉からパターンを抽出"""
        
        return {
            "conversation_summary": {},
            "key_phrases": [],
            "negotiation_flow": [],
            "decision_points": []
        }
    
    def _calculate_success_metrics(self, negotiation: Dict) -> Dict:
        """成功メトリクスを計算"""
        
        return {
            "deal_value": 0,
            "duration_hours": 24,
            "rounds_count": 1,
            "satisfaction_score": 0.7,
            "budget_efficiency": 0.8
        }
    
    async def get_automation_status(self) -> Dict:
        """自動化の状態を取得"""
        
        return {
            "is_running": self.is_running,
            "mode": self.orchestration_config["mode"].value,
            "active_negotiations": len(self.active_negotiations),
            "performance_metrics": self.performance_metrics,
            "config": self.orchestration_config,
            "last_optimization": datetime.now().isoformat()  # 仮
        }
    
    def set_gmail_monitor(self, gmail_monitor: GmailAutoMonitor) -> None:
        """Gmail監視を設定"""
        
        self.gmail_monitor = gmail_monitor