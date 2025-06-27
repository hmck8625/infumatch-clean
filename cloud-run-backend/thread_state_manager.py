"""
スレッド状態管理システム
自動交渉の進行状況とコンテキストを管理
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging

class NegotiationStage(Enum):
    """交渉段階の定義"""
    INITIAL_CONTACT = "initial_contact"
    INTEREST_CONFIRMATION = "interest_confirmation"
    CONDITION_NEGOTIATION = "condition_negotiation"
    FINAL_AGREEMENT = "final_agreement"
    COMPLETED = "completed"
    FAILED = "failed"

class ThreadStatus(Enum):
    """スレッドステータスの定義"""
    ACTIVE = "active"
    WAITING_RESPONSE = "waiting_response"
    PENDING_APPROVAL = "pending_approval"
    AUTO_NEGOTIATING = "auto_negotiating"
    ESCALATED = "escalated"
    COMPLETED = "completed"
    EXPIRED = "expired"

class ThreadStateManager:
    """スレッド状態管理マネージャー"""
    
    def __init__(self, db_client=None):
        self.db = db_client  # Firestoreクライアント（オプション）
        self.collection_name = "negotiation_threads"
        self.cache = {}  # メモリキャッシュ
        
    async def get_thread_state(self, thread_id: str) -> Dict:
        """スレッドの現在の状態を取得"""
        
        # キャッシュから取得を試みる
        if thread_id in self.cache:
            return self.cache[thread_id]
        
        # DBから取得（実装されている場合）
        if self.db:
            try:
                doc = self.db.collection(self.collection_name).document(thread_id).get()
                if doc.exists:
                    state = doc.to_dict()
                    self.cache[thread_id] = state
                    return state
            except Exception as e:
                logging.error(f"スレッド状態の取得エラー: {e}")
        
        # 新規スレッドの場合はデフォルト状態を作成
        return self._create_default_state(thread_id)
    
    async def update_thread_state(
        self, 
        thread_id: str, 
        updates: Dict,
        new_round: bool = False
    ) -> Dict:
        """スレッド状態を更新"""
        
        # 現在の状態を取得
        current_state = await self.get_thread_state(thread_id)
        
        # 新しいラウンドの場合
        if new_round:
            current_state["round_number"] += 1
            current_state["round_history"].append({
                "round": current_state["round_number"],
                "timestamp": datetime.now().isoformat(),
                "updates": updates
            })
        
        # 状態を更新
        for key, value in updates.items():
            if key in current_state:
                current_state[key] = value
        
        # 最終更新日時を更新
        current_state["last_updated"] = datetime.now().isoformat()
        
        # 進行状況を計算
        current_state["progress"] = self._calculate_progress(current_state)
        
        # キャッシュとDBを更新
        self.cache[thread_id] = current_state
        
        if self.db:
            try:
                self.db.collection(self.collection_name).document(thread_id).set(
                    current_state, merge=True
                )
            except Exception as e:
                logging.error(f"スレッド状態の保存エラー: {e}")
        
        return current_state
    
    async def record_negotiation_event(
        self, 
        thread_id: str,
        event_type: str,
        event_data: Dict
    ) -> None:
        """交渉イベントを記録"""
        
        state = await self.get_thread_state(thread_id)
        
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": event_data
        }
        
        state["event_history"].append(event)
        
        # 特定のイベントに基づいて状態を更新
        if event_type == "message_sent":
            state["last_message_sent"] = datetime.now().isoformat()
            state["status"] = ThreadStatus.WAITING_RESPONSE.value
        elif event_type == "response_received":
            state["last_response_received"] = datetime.now().isoformat()
            state["response_time_hours"] = self._calculate_response_time(state)
        elif event_type == "escalation_triggered":
            state["status"] = ThreadStatus.ESCALATED.value
            state["escalation_reason"] = event_data.get("reason", "unknown")
        
        await self.update_thread_state(thread_id, state)
    
    async def advance_negotiation_stage(
        self, 
        thread_id: str,
        new_stage: NegotiationStage
    ) -> Dict:
        """交渉段階を進める"""
        
        state = await self.get_thread_state(thread_id)
        
        # 段階の妥当性をチェック
        current_stage = NegotiationStage(state["negotiation_stage"])
        if not self._is_valid_stage_transition(current_stage, new_stage):
            raise ValueError(f"無効な段階遷移: {current_stage.value} -> {new_stage.value}")
        
        # 段階を更新
        updates = {
            "negotiation_stage": new_stage.value,
            "stage_history": state.get("stage_history", []) + [{
                "stage": new_stage.value,
                "entered_at": datetime.now().isoformat()
            }]
        }
        
        # 完了・失敗の場合はステータスも更新
        if new_stage == NegotiationStage.COMPLETED:
            updates["status"] = ThreadStatus.COMPLETED.value
            updates["completed_at"] = datetime.now().isoformat()
        elif new_stage == NegotiationStage.FAILED:
            updates["status"] = ThreadStatus.COMPLETED.value
            updates["failed_at"] = datetime.now().isoformat()
        
        return await self.update_thread_state(thread_id, updates)
    
    async def check_timeout_status(self, thread_id: str) -> Tuple[bool, Optional[str]]:
        """タイムアウト状態をチェック"""
        
        state = await self.get_thread_state(thread_id)
        
        # 最後のメッセージ送信時刻を確認
        if state.get("last_message_sent"):
            last_sent = datetime.fromisoformat(state["last_message_sent"])
            timeout_hours = state.get("response_timeout_hours", 48)
            
            if datetime.now() - last_sent > timedelta(hours=timeout_hours):
                return True, f"{timeout_hours}時間以上応答がありません"
        
        # 全体のタイムアウトをチェック
        created_at = datetime.fromisoformat(state["created_at"])
        max_duration_days = state.get("max_negotiation_days", 7)
        
        if datetime.now() - created_at > timedelta(days=max_duration_days):
            return True, f"交渉開始から{max_duration_days}日以上経過"
        
        return False, None
    
    async def get_active_threads(
        self, 
        user_id: Optional[str] = None,
        status_filter: Optional[List[ThreadStatus]] = None
    ) -> List[Dict]:
        """アクティブなスレッド一覧を取得"""
        
        threads = []
        
        if self.db:
            try:
                query = self.db.collection(self.collection_name)
                
                if user_id:
                    query = query.where("user_id", "==", user_id)
                
                if status_filter:
                    status_values = [s.value for s in status_filter]
                    query = query.where("status", "in", status_values)
                
                docs = query.stream()
                
                for doc in docs:
                    thread_data = doc.to_dict()
                    thread_data["thread_id"] = doc.id
                    threads.append(thread_data)
                    
            except Exception as e:
                logging.error(f"アクティブスレッドの取得エラー: {e}")
        else:
            # キャッシュから取得
            for thread_id, state in self.cache.items():
                if status_filter is None or ThreadStatus(state["status"]) in status_filter:
                    if user_id is None or state.get("user_id") == user_id:
                        threads.append({**state, "thread_id": thread_id})
        
        # 最終更新日時でソート
        threads.sort(key=lambda x: x.get("last_updated", ""), reverse=True)
        
        return threads
    
    async def analyze_negotiation_patterns(self, thread_id: str) -> Dict:
        """交渉パターンを分析"""
        
        state = await self.get_thread_state(thread_id)
        
        analysis = {
            "total_rounds": state.get("round_number", 0),
            "total_duration_hours": 0,
            "average_response_time_hours": 0,
            "escalation_count": 0,
            "sentiment_trend": [],
            "key_decision_points": [],
            "success_indicators": [],
            "risk_factors": []
        }
        
        # イベント履歴から分析
        events = state.get("event_history", [])
        response_times = []
        
        for event in events:
            if event["type"] == "response_received":
                if "response_time_hours" in event["data"]:
                    response_times.append(event["data"]["response_time_hours"])
            elif event["type"] == "escalation_triggered":
                analysis["escalation_count"] += 1
            elif event["type"] == "sentiment_analyzed":
                analysis["sentiment_trend"].append({
                    "timestamp": event["timestamp"],
                    "sentiment": event["data"].get("sentiment", 0)
                })
        
        # 平均応答時間を計算
        if response_times:
            analysis["average_response_time_hours"] = sum(response_times) / len(response_times)
        
        # 交渉期間を計算
        if state.get("created_at"):
            created = datetime.fromisoformat(state["created_at"])
            analysis["total_duration_hours"] = (datetime.now() - created).total_seconds() / 3600
        
        # 成功指標とリスク要因を特定
        if state.get("negotiation_stage") == NegotiationStage.FINAL_AGREEMENT.value:
            analysis["success_indicators"].append("最終合意段階に到達")
        
        if analysis["escalation_count"] > 2:
            analysis["risk_factors"].append("エスカレーション頻度が高い")
        
        if analysis["average_response_time_hours"] > 48:
            analysis["risk_factors"].append("応答時間が長い")
        
        return analysis
    
    def _create_default_state(self, thread_id: str) -> Dict:
        """デフォルトのスレッド状態を作成"""
        
        return {
            "thread_id": thread_id,
            "status": ThreadStatus.ACTIVE.value,
            "negotiation_stage": NegotiationStage.INITIAL_CONTACT.value,
            "round_number": 1,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "last_message_sent": None,
            "last_response_received": None,
            "response_timeout_hours": 48,
            "max_negotiation_days": 7,
            "round_history": [],
            "event_history": [],
            "stage_history": [{
                "stage": NegotiationStage.INITIAL_CONTACT.value,
                "entered_at": datetime.now().isoformat()
            }],
            "escalation_count": 0,
            "escalation_reason": None,
            "auto_negotiation_enabled": True,
            "progress": 0,
            "context_data": {},
            "metrics": {
                "messages_sent": 0,
                "messages_received": 0,
                "auto_responses": 0,
                "manual_interventions": 0
            }
        }
    
    def _calculate_progress(self, state: Dict) -> float:
        """交渉の進捗を計算（0-100%）"""
        
        stage_weights = {
            NegotiationStage.INITIAL_CONTACT.value: 0.2,
            NegotiationStage.INTEREST_CONFIRMATION.value: 0.4,
            NegotiationStage.CONDITION_NEGOTIATION.value: 0.7,
            NegotiationStage.FINAL_AGREEMENT.value: 0.9,
            NegotiationStage.COMPLETED.value: 1.0,
            NegotiationStage.FAILED.value: 1.0
        }
        
        current_stage = state.get("negotiation_stage", NegotiationStage.INITIAL_CONTACT.value)
        base_progress = stage_weights.get(current_stage, 0) * 100
        
        # ラウンド数による微調整
        round_bonus = min(state.get("round_number", 1) * 2, 10)
        
        return min(base_progress + round_bonus, 100)
    
    def _calculate_response_time(self, state: Dict) -> float:
        """応答時間を計算（時間単位）"""
        
        if state.get("last_message_sent") and state.get("last_response_received"):
            sent = datetime.fromisoformat(state["last_message_sent"])
            received = datetime.fromisoformat(state["last_response_received"])
            
            if received > sent:
                return (received - sent).total_seconds() / 3600
        
        return 0
    
    def _is_valid_stage_transition(
        self, 
        current: NegotiationStage, 
        new: NegotiationStage
    ) -> bool:
        """段階遷移の妥当性をチェック"""
        
        # 既に完了・失敗している場合は遷移不可
        if current in [NegotiationStage.COMPLETED, NegotiationStage.FAILED]:
            return False
        
        # 失敗はどの段階からでも可能
        if new == NegotiationStage.FAILED:
            return True
        
        # 通常の進行順序
        stage_order = [
            NegotiationStage.INITIAL_CONTACT,
            NegotiationStage.INTEREST_CONFIRMATION,
            NegotiationStage.CONDITION_NEGOTIATION,
            NegotiationStage.FINAL_AGREEMENT,
            NegotiationStage.COMPLETED
        ]
        
        try:
            current_idx = stage_order.index(current)
            new_idx = stage_order.index(new)
            
            # 前進のみ許可（1段階ずつ）
            return new_idx == current_idx + 1
        except ValueError:
            return False