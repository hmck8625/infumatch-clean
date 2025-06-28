"""
自動交渉エージェントマネージャー
InfuMatchの自動交渉システムの核となるモジュール
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

# スレッド状態管理をインポート
try:
    from thread_state_manager import ThreadStateManager, NegotiationStage, ThreadStatus
    print("✅ ThreadStateManager imported successfully")
except ImportError as e:
    print(f"⚠️ ThreadStateManager import failed: {e}")
    ThreadStateManager = None
    NegotiationStage = None
    ThreadStatus = None

# 既存のSimpleNegotiationManagerを拡張
class AutoNegotiationManager:
    """自動交渉マネージャー - 既存の4段階処理を自動化"""
    
    def __init__(self, gemini_model, db_client=None):
        self.gemini_model = gemini_model
        self.manager_id = "auto_negotiation_manager_v1"
        
        # スレッド状態管理の初期化
        if ThreadStateManager:
            self.thread_state_manager = ThreadStateManager(db_client)
        else:
            self.thread_state_manager = None
            print("⚠️ ThreadStateManager not available")
        
        # 自動交渉設定のデフォルト値
        self.default_settings = {
            "enabled": False,
            "max_rounds": 3,
            "auto_approval_threshold": 75,
            "budget_flexibility_limit": 15,  # 15%まで
            "response_time_limit": 24,  # 24時間
            "working_hours": {"start": 9, "end": 18},
            "max_daily_negotiations": 10,
            "escalation_conditions": [
                "budget_exceeded",
                "negative_sentiment",
                "complex_terms",
                "max_rounds_reached"
            ]
        }
        
    async def process_auto_negotiation_round(
        self, 
        thread_id: str,
        new_message: str,
        conversation_history: List[Dict],
        company_settings: Dict,
        round_number: int = 1
    ) -> Dict:
        """自動交渉ラウンドを実行"""
        
        try:
            print(f"🤖 自動交渉ラウンド {round_number} 開始 - Thread: {thread_id}")
            start_time = datetime.now()
            
            # スレッド状態を取得/更新
            if self.thread_state_manager:
                thread_state = await self.thread_state_manager.get_thread_state(thread_id)
                
                # 新しいラウンドとして記録
                await self.thread_state_manager.record_negotiation_event(
                    thread_id,
                    "round_started",
                    {"round_number": round_number, "message": new_message[:100]}
                )
            else:
                thread_state = {"thread_id": thread_id, "round_number": round_number}
            
            # 1. 自動交渉設定を取得
            auto_settings = self._get_auto_negotiation_settings(company_settings)
            if not auto_settings.get("enabled", False):
                return {
                    "success": False,
                    "error": "自動交渉が無効化されています",
                    "action": "manual_required"
                }
            
            # 2. 交渉コンテキストを分析
            context_analysis = await self._analyze_negotiation_context(
                thread_id, conversation_history, round_number
            )
            
            print(f"📊 交渉コンテキスト分析完了: {context_analysis.get('stage', 'unknown')}")
            
            # 3. エスカレーション条件をチェック
            escalation_result = await self._check_escalation_conditions(
                context_analysis, auto_settings, round_number
            )
            
            if escalation_result["needs_escalation"]:
                print(f"🚨 エスカレーション必要: {escalation_result['reason']}")
                return await self._create_escalation_response(
                    thread_id, escalation_result, context_analysis
                )
            
            # 4. 既存の4段階交渉処理を実行（自動モード）
            negotiation_result = await self._execute_auto_negotiation_stages(
                new_message, conversation_history, company_settings, context_analysis
            )
            
            print(f"🎯 交渉処理完了 - 信頼度: {negotiation_result.get('confidence', 0)}")
            
            # 5. 自動送信判定
            auto_send_decision = await self._evaluate_auto_send(
                negotiation_result, context_analysis, auto_settings
            )
            
            if auto_send_decision["should_auto_send"]:
                print("✅ 自動送信実行")
                return await self._prepare_auto_send_response(
                    thread_id, negotiation_result, context_analysis, round_number
                )
            else:
                print("⏸️ 人間承認待ち")
                return await self._queue_for_approval(
                    thread_id, negotiation_result, auto_send_decision["reason"]
                )
                
        except Exception as e:
            print(f"❌ 自動交渉エラー: {str(e)}")
            return {
                "success": False,
                "error": f"自動交渉処理中にエラーが発生: {str(e)}",
                "action": "manual_required",
                "thread_id": thread_id
            }
    
    async def _analyze_negotiation_context(
        self, 
        thread_id: str, 
        conversation_history: List[Dict], 
        round_number: int
    ) -> Dict:
        """交渉コンテキストを分析"""
        
        # 会話履歴から重要な要素を抽出
        context = {
            "thread_id": thread_id,
            "round_number": round_number,
            "total_messages": len(conversation_history),
            "negotiation_topics": [],
            "mentioned_budget": None,
            "sentiment_trend": [],
            "urgency_indicators": [],
            "decision_points": []
        }
        
        # 最近の会話から予算情報を抽出
        for msg in conversation_history[-3:]:  # 直近3件
            content = msg.get("content", "").lower()
            
            # 予算関連キーワード検索
            budget_keywords = ["円", "万円", "価格", "料金", "費用", "予算", "金額"]
            if any(keyword in content for keyword in budget_keywords):
                context["mentioned_budget"] = self._extract_budget_info(content)
            
            # 急ぎ度指標
            urgency_keywords = ["急ぎ", "至急", "すぐに", "早急", "緊急"]
            if any(keyword in content for keyword in urgency_keywords):
                context["urgency_indicators"].append("high_urgency")
                
        # 動的に交渉段階を判定
        context["stage"] = await self._determine_negotiation_stage(
            conversation_history, round_number, context
        )
            
        return context
    
    async def _check_escalation_conditions(
        self, 
        context_analysis: Dict, 
        auto_settings: Dict, 
        round_number: int
    ) -> Dict:
        """エスカレーション条件をチェック - 強化版安全機構"""
        
        escalation_reasons = []
        
        # 1. 最大ラウンド数チェック
        max_rounds = auto_settings.get("max_rounds", 3)
        if round_number >= max_rounds:
            escalation_reasons.append("max_rounds_reached")
        
        # 2. 予算超過チェック（強化版）
        if context_analysis.get("mentioned_budget"):
            budget_info = context_analysis["mentioned_budget"]
            if budget_info.get("exceeds_limit", False):
                escalation_reasons.append("budget_exceeded")
            
            # 予算柔軟性限界チェック
            if budget_info.get("max_amount"):
                budget_flexibility_limit = auto_settings.get("budget_flexibility_limit", 10)
                company_budget = auto_settings.get("company_budget_max", 1000000)
                if budget_info["max_amount"] > company_budget * (1 + budget_flexibility_limit / 100):
                    escalation_reasons.append("budget_flexibility_exceeded")
        
        # 3. 感情分析チェック（新規追加）
        sentiment_threshold = auto_settings.get("sentiment_threshold", -0.5)
        recent_messages = context_analysis.get("recent_messages", [])
        if recent_messages:
            # ネガティブキーワードチェック
            negative_keywords = ["不満", "困る", "問題", "難しい", "無理", "できない", "高い", "安い", "不可能", "取り消", "キャンセル", "中止"]
            recent_text = " ".join([msg.get("content", "") for msg in recent_messages[-2:]])
            negative_count = sum(1 for keyword in negative_keywords if keyword in recent_text)
            
            if negative_count >= 2:
                escalation_reasons.append("negative_sentiment_detected")
        
        # 4. 緊急停止キーワードチェック（新規追加）
        emergency_keywords = auto_settings.get("emergency_keywords", ["キャンセル", "中止", "終了", "ストップ", "やめる", "取りやめ"])
        conversation_text = " ".join([
            msg.get("content", "") for msg in context_analysis.get("recent_messages", [])
        ])
        
        if any(keyword in conversation_text for keyword in emergency_keywords):
            escalation_reasons.append("emergency_keyword_detected")
        
        # 5. 緊急度チェック  
        if "high_urgency" in context_analysis.get("urgency_indicators", []):
            escalation_reasons.append("urgent_decision_required")
        
        # 6. 複雑な条件チェック（強化版）
        complex_keywords = ["契約", "法的", "保証", "責任", "権利", "義務", "訴訟", "損害", "賠償", "規約", "条項"]
        if any(keyword in conversation_text for keyword in complex_keywords):
            escalation_reasons.append("complex_legal_terms")
        
        # 7. 稼働時間外チェック（新規追加）
        current_time = datetime.now()
        working_hours = auto_settings.get("working_hours", {"start": 9, "end": 18})
        if not (working_hours["start"] <= current_time.hour < working_hours["end"]):
            escalation_reasons.append("outside_working_hours")
        
        # 8. 交渉段階チェック（新規追加）
        stage = context_analysis.get("stage", "initial_contact")
        if stage == "final_agreement":
            # 最終合意段階は必ず人間確認
            escalation_reasons.append("final_agreement_requires_human")
        
        return {
            "needs_escalation": len(escalation_reasons) > 0,
            "reasons": escalation_reasons,
            "primary_reason": escalation_reasons[0] if escalation_reasons else None,
            "escalation_count": len(escalation_reasons),
            "critical": len(escalation_reasons) >= 3  # 3つ以上の理由がある場合は重要
        }
    
    async def _execute_auto_negotiation_stages(
        self, 
        new_message: str, 
        conversation_history: List[Dict], 
        company_settings: Dict,
        context_analysis: Dict
    ) -> Dict:
        """既存の4段階処理を自動交渉モードで実行"""
        
        # SimpleNegotiationManagerの機能を借用（シンプルな統合）
        from main import SimpleNegotiationManager
        
        base_manager = SimpleNegotiationManager(self.gemini_model)
        
        # 自動交渉用のカスタム指示を生成
        auto_instructions = self._generate_auto_instructions(context_analysis)
        
        # 既存の4段階処理を実行
        result = await base_manager.process_negotiation(
            conversation_history=conversation_history,
            new_message=new_message,
            company_settings=company_settings,
            custom_instructions=auto_instructions
        )
        
        # 自動交渉用の追加情報を付与
        if result.get("success"):
            result["auto_mode"] = True
            result["context_analysis"] = context_analysis
            result["auto_instructions"] = auto_instructions
            result["confidence"] = self._calculate_confidence(result, context_analysis)
        
        return result
    
    def _generate_auto_instructions(self, context_analysis: Dict) -> str:
        """交渉コンテキストに基づいて自動指示を生成"""
        
        instructions = []
        
        # 交渉段階に応じた指示
        stage = context_analysis.get("stage", "initial_contact")
        
        if stage == "initial_contact":
            instructions.append("興味を引く魅力的な提案を心がけてください")
        elif stage == "interest_confirmation":
            instructions.append("相手の関心事に焦点を当てて具体的なメリットを提示してください")
        elif stage == "condition_negotiation":
            instructions.append("柔軟性を示しながらも企業の利益を確保してください")
        elif stage == "final_agreement":
            instructions.append("合意に向けて建設的で協力的な姿勢を示してください")
        
        # 急ぎ度に応じた指示
        if "high_urgency" in context_analysis.get("urgency_indicators", []):
            instructions.append("相手の緊急性を理解し、迅速な対応を約束してください")
        
        # 予算に関する指示
        if context_analysis.get("mentioned_budget"):
            instructions.append("予算に関する相談は柔軟に対応する姿勢を示してください")
        
        return "、".join(instructions) if instructions else "プロフェッショナルで協力的な対応を心がけてください"
    
    def _calculate_confidence(self, negotiation_result: Dict, context_analysis: Dict) -> float:
        """自動交渉の信頼度を計算"""
        
        base_confidence = 0.7
        
        # 交渉処理の成功度
        if negotiation_result.get("patterns"):
            base_confidence += 0.1
            
        # 分析の信頼度
        analysis_confidence = negotiation_result.get("analysis", {}).get("analysis_confidence", 0.5)
        base_confidence += (analysis_confidence - 0.5) * 0.2
        
        # 交渉段階による調整
        stage = context_analysis.get("stage", "initial_contact")
        if stage in ["initial_contact", "interest_confirmation"]:
            base_confidence += 0.1  # 初期段階は信頼度高め
        elif stage == "final_agreement":
            base_confidence -= 0.1  # 最終段階は慎重に
            
        return min(max(base_confidence, 0.0), 1.0)
    
    async def _evaluate_auto_send(
        self, 
        negotiation_result: Dict, 
        context_analysis: Dict, 
        auto_settings: Dict
    ) -> Dict:
        """自動送信可否を評価 - 強化版安全チェック"""
        
        # 1. 基本的な信頼度チェック
        confidence = negotiation_result.get("confidence", 0.0)
        threshold = auto_settings.get("auto_approval_threshold", 75) / 100.0
        
        if confidence < threshold:
            return {
                "should_auto_send": False,
                "reason": f"信頼度が閾値を下回りました ({confidence:.1%} < {threshold:.1%})",
                "safety_score": confidence
            }
        
        # 2. リスクフラグチェック
        evaluation = negotiation_result.get("evaluation", {})
        risk_flags = evaluation.get("risk_flags", [])
        
        if risk_flags:
            return {
                "should_auto_send": False,
                "reason": f"リスクフラグが検出されました: {', '.join(risk_flags)}",
                "safety_score": 0.3
            }
        
        # 3. 稼働時間チェック
        current_time = datetime.now()
        working_hours = auto_settings.get("working_hours", {"start": 9, "end": 18})
        
        if not (working_hours["start"] <= current_time.hour < working_hours["end"]):
            return {
                "should_auto_send": False,
                "reason": "稼働時間外のため、人間の確認が必要です",
                "safety_score": 0.5
            }
        
        # 4. 交渉段階による安全性評価（新規追加）
        stage = context_analysis.get("stage", "initial_contact")
        stage_safety = {
            "initial_contact": 0.9,      # 初期接触は比較的安全
            "interest_confirmation": 0.8, # 興味確認も安全
            "condition_negotiation": 0.6, # 条件交渉は慎重に
            "final_agreement": 0.3        # 最終合意は人間確認推奨
        }
        
        stage_safety_score = stage_safety.get(stage, 0.5)
        if stage_safety_score < 0.5:
            return {
                "should_auto_send": False,
                "reason": f"交渉段階「{stage}」では人間の確認が推奨されます",
                "safety_score": stage_safety_score
            }
        
        # 5. 金額チェック（新規追加）
        if context_analysis.get("mentioned_budget"):
            budget_info = context_analysis["mentioned_budget"]
            max_amount = budget_info.get("max_amount", 0)
            
            # 100万円を超える金額が言及された場合は人間確認
            if max_amount > 1000000:
                return {
                    "should_auto_send": False,
                    "reason": f"高額取引（{max_amount:,}円）のため人間の確認が必要です",
                    "safety_score": 0.4
                }
        
        # 6. 返信内容の長さチェック（新規追加）
        selected_pattern = negotiation_result.get("patterns", {}).get("pattern_balanced", {})
        reply_content = selected_pattern.get("content", "")
        
        if len(reply_content) > 1000:  # 1000文字を超える長文
            return {
                "should_auto_send": False,
                "reason": "返信が長文のため、人間の確認が推奨されます",
                "safety_score": 0.7
            }
        
        # 7. 総合安全スコアの計算
        safety_score = min(
            confidence,
            stage_safety_score,
            0.9 if not risk_flags else 0.5,
            0.8 if len(reply_content) < 500 else 0.6
        )
        
        return {
            "should_auto_send": True,
            "reason": "全ての安全条件を満たしています",
            "safety_score": safety_score,
            "checks_passed": {
                "confidence": confidence >= threshold,
                "no_risk_flags": len(risk_flags) == 0,
                "working_hours": True,
                "stage_appropriate": stage_safety_score >= 0.5,
                "amount_safe": context_analysis.get("mentioned_budget") is None or 
                             context_analysis["mentioned_budget"].get("max_amount", 0) <= 1000000,
                "content_length_ok": len(reply_content) <= 1000
            }
        }
    
    async def _prepare_auto_send_response(
        self, 
        thread_id: str, 
        negotiation_result: Dict, 
        context_analysis: Dict, 
        round_number: int
    ) -> Dict:
        """自動送信用のレスポンスを準備"""
        
        # バランス型パターンを選択（最も安全な選択肢）
        patterns = negotiation_result.get("patterns", {})
        selected_pattern = patterns.get("pattern_balanced", {})
        
        if not selected_pattern:
            # フォールバック: 利用可能な最初のパターン
            selected_pattern = next(iter(patterns.values())) if patterns else {}
        
        return {
            "success": True,
            "action": "auto_send",
            "thread_id": thread_id,
            "round_number": round_number,
            "selected_pattern": selected_pattern,
            "confidence": negotiation_result.get("confidence", 0.0),
            "reasoning": "自動交渉エージェントによる送信",
            "context": context_analysis,
            "auto_negotiation": True,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _create_escalation_response(
        self, 
        thread_id: str, 
        escalation_result: Dict, 
        context_analysis: Dict
    ) -> Dict:
        """エスカレーション用のレスポンスを作成"""
        
        return {
            "success": True,
            "action": "escalation_required",
            "thread_id": thread_id,
            "escalation_reason": escalation_result["primary_reason"],
            "escalation_details": escalation_result["reasons"],
            "context": context_analysis,
            "message": f"自動交渉をエスカレートします: {escalation_result['primary_reason']}",
            "requires_human_intervention": True,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _queue_for_approval(
        self, 
        thread_id: str, 
        negotiation_result: Dict, 
        reason: str
    ) -> Dict:
        """承認待ちキューに追加"""
        
        return {
            "success": True,
            "action": "approval_required",
            "thread_id": thread_id,
            "pending_approval": True,
            "approval_reason": reason,
            "negotiation_result": negotiation_result,
            "deadline": (datetime.now() + timedelta(hours=24)).isoformat(),
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_auto_negotiation_settings(self, company_settings: Dict) -> Dict:
        """企業設定から自動交渉設定を取得"""
        
        # 企業設定に自動交渉設定がある場合はそれを使用
        auto_settings = company_settings.get("autoNegotiationSettings", {})
        
        # デフォルト設定とマージ
        merged_settings = self.default_settings.copy()
        merged_settings.update(auto_settings)
        
        return merged_settings
    
    def _extract_budget_info(self, content: str) -> Dict:
        """テキストから予算情報を抽出"""
        
        import re
        
        # 金額パターンを検索
        amount_patterns = [
            r'(\d+)万円',
            r'(\d+)円',
            r'(\d+)k',
            r'(\d+)K'
        ]
        
        extracted_amounts = []
        for pattern in amount_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                try:
                    amount = int(match)
                    if '万円' in pattern:
                        amount *= 10000
                    extracted_amounts.append(amount)
                except ValueError:
                    continue
        
        if extracted_amounts:
            max_amount = max(extracted_amounts)
            return {
                "extracted_amounts": extracted_amounts,
                "max_amount": max_amount,
                "exceeds_limit": max_amount > 1000000  # 100万円超過をチェック
            }
        
        return {"extracted_amounts": [], "max_amount": None, "exceeds_limit": False}

    async def _determine_negotiation_stage(
        self, 
        conversation_history: List[Dict],
        round_number: int,
        context: Dict
    ) -> str:
        """会話内容に基づいて動的に交渉段階を判定"""
        
        # スレッド状態管理から現在のステージを取得
        if self.thread_state_manager and context.get("thread_id"):
            try:
                thread_state = await self.thread_state_manager.get_thread_state(
                    context["thread_id"]
                )
                current_stage = thread_state.get("negotiation_stage")
                if current_stage:
                    return current_stage
            except Exception:
                pass
        
        # 会話内容から段階を推定
        if len(conversation_history) <= 2:
            return "initial_contact"
        
        # 最近のメッセージから段階判定のキーワードを検索
        recent_messages = " ".join([
            msg.get("content", "") for msg in conversation_history[-3:]
        ]).lower()
        
        # 最終合意段階のシグナル
        final_signals = ["契約", "合意", "確定", "決定", "締結", "了承"]
        if any(signal in recent_messages for signal in final_signals):
            return "final_agreement"
        
        # 条件交渉段階のシグナル
        negotiation_signals = ["価格", "条件", "期間", "納期", "支払", "料金"]
        if any(signal in recent_messages for signal in negotiation_signals):
            return "condition_negotiation"
        
        # 興味確認段階のシグナル
        interest_signals = ["興味", "関心", "詳細", "もっと", "教えて"]
        if any(signal in recent_messages for signal in interest_signals):
            return "interest_confirmation"
        
        # デフォルトはラウンド数ベース
        if round_number <= 1:
            return "initial_contact"
        elif round_number <= 2:
            return "interest_confirmation"
        elif round_number <= 4:
            return "condition_negotiation"
        else:
            return "final_agreement"

    # 管理・統計機能
    async def get_auto_negotiation_stats(self, company_id: str, days: int = 7) -> Dict:
        """自動交渉の統計情報を取得"""
        
        # 実装は後のフェーズで詳細化
        return {
            "total_auto_negotiations": 0,
            "success_rate": 0.0,
            "average_rounds": 0.0,
            "escalation_rate": 0.0,
            "common_escalation_reasons": [],
            "period_days": days
        }