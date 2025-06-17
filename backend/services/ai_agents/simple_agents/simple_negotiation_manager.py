"""
シンプル交渉マネージャー - 4エージェント統合

@description 4つのシンプルエージェントを統合する軽量マネージャー
@author InfuMatch Development Team
@version 3.0.0
"""

import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime

from .thread_analysis_agent import ThreadAnalysisAgent
from .reply_strategy_agent import ReplyStrategyAgent
from .content_evaluation_agent import ContentEvaluationAgent
from .pattern_generation_agent import PatternGenerationAgent

logger = logging.getLogger(__name__)


class SimpleNegotiationManager:
    """
    シンプル交渉マネージャー
    
    4つのエージェントを順次実行:
    1. ThreadAnalysisAgent - スレッド分析
    2. ReplyStrategyAgent - 戦略立案
    3. ContentEvaluationAgent - 内容評価
    4. PatternGenerationAgent - 3パターン生成
    """
    
    def __init__(self):
        """マネージャーの初期化"""
        try:
            # 4つのエージェントを初期化
            self.thread_agent = ThreadAnalysisAgent()
            self.strategy_agent = ReplyStrategyAgent()
            self.evaluation_agent = ContentEvaluationAgent()
            self.pattern_agent = PatternGenerationAgent()
            
            self.manager_id = "simple_negotiation_manager"
            self.processing_stages = [
                "スレッド分析",
                "戦略立案", 
                "内容評価",
                "パターン生成"
            ]
            
            logger.info("🎯 SimpleNegotiationManager 初期化完了")
            
        except Exception as e:
            logger.error(f"❌ SimpleNegotiationManager 初期化エラー: {str(e)}")
            raise
    
    async def process_negotiation(
        self,
        thread_messages: List[Dict[str, Any]],
        company_settings: Dict[str, Any],
        custom_instructions: str = "",
        callback_func=None
    ) -> Dict[str, Any]:
        """
        4段階の交渉処理を実行
        
        Args:
            thread_messages: スレッドメッセージリスト
            company_settings: 企業設定情報
            custom_instructions: カスタム指示
            callback_func: 進捗コールバック関数
            
        Returns:
            Dict: 処理結果
        """
        try:
            logger.info("🎯 4段階交渉処理開始")
            start_time = datetime.now()
            
            results = {
                "manager_id": self.manager_id,
                "processing_start": start_time.isoformat(),
                "stages": {},
                "final_patterns": {},
                "success": True
            }
            
            # Stage 1: スレッド分析
            if callback_func:
                await callback_func("スレッド分析", "開始", "メッセージ履歴を分析中")
            
            logger.info("📊 Stage 1: スレッド分析開始")
            logger.info("📥 ThreadAnalysisAgent INPUT:")
            logger.info(f"  - thread_messages: {len(thread_messages)}件のメッセージ")
            logger.info(f"  - company_settings: {len(company_settings)}項目の設定")
            
            thread_analysis = await self.thread_agent.analyze_thread(
                thread_messages, company_settings
            )
            
            logger.info("📤 ThreadAnalysisAgent OUTPUT:")
            logger.info(f"  - negotiation_stage: {thread_analysis.get('negotiation_stage', '不明')}")
            logger.info(f"  - sentiment_tone: {thread_analysis.get('sentiment_analysis', {}).get('tone', '不明')}")
            logger.info(f"  - key_topics: {thread_analysis.get('key_topics', [])}")
            logger.info(f"  - urgency_level: {thread_analysis.get('urgency_level', '不明')}")
            logger.info(f"  - confidence: {thread_analysis.get('analysis_confidence', 0.0)}")
            
            results["stages"]["thread_analysis"] = {
                "status": "completed",
                "result": thread_analysis,
                "timestamp": datetime.now().isoformat()
            }
            
            if callback_func:
                await callback_func("スレッド分析", "完了", f"交渉段階: {thread_analysis.get('negotiation_stage', '不明')}")
            
            # Stage 2: 戦略立案
            if callback_func:
                await callback_func("戦略立案", "開始", "返信戦略を考案中")
            
            logger.info("🧠 Stage 2: 戦略立案開始")
            logger.info("📥 ReplyStrategyAgent INPUT:")
            logger.info(f"  - thread_analysis: 交渉段階={thread_analysis.get('negotiation_stage', '不明')}")
            logger.info(f"  - company_settings: {len(company_settings)}項目")
            logger.info(f"  - custom_instructions: '{custom_instructions}'" if custom_instructions else "  - custom_instructions: 未設定")
            
            strategy_plan = await self.strategy_agent.plan_reply_strategy(
                thread_analysis, company_settings, custom_instructions
            )
            
            logger.info("📤 ReplyStrategyAgent OUTPUT:")
            logger.info(f"  - primary_approach: {strategy_plan.get('primary_approach', '不明')}")
            logger.info(f"  - key_messages: {strategy_plan.get('key_messages', [])}")
            logger.info(f"  - language_setting: {strategy_plan.get('language_setting', '不明')}")
            logger.info(f"  - tone_setting: {strategy_plan.get('tone_setting', '不明')}")
            logger.info(f"  - strategy_confidence: {strategy_plan.get('strategy_confidence', 0.0)}")
            
            results["stages"]["strategy_planning"] = {
                "status": "completed",
                "result": strategy_plan,
                "timestamp": datetime.now().isoformat()
            }
            
            if callback_func:
                await callback_func("戦略立案", "完了", f"アプローチ: {strategy_plan.get('primary_approach', '不明')}")
            
            # Stage 3: 内容評価（基本評価として簡易実行）
            if callback_func:
                await callback_func("内容評価", "開始", "戦略内容を評価中")
            
            logger.info("🔍 Stage 3: 内容評価開始")
            # 戦略プランを基に簡易評価を実行
            strategy_summary = f"戦略: {strategy_plan.get('primary_approach', '')} メッセージ: {', '.join(strategy_plan.get('key_messages', []))}"
            logger.info("📥 ContentEvaluationAgent INPUT:")
            logger.info(f"  - proposed_content: '{strategy_summary}'")
            logger.info(f"  - evaluation_method: quick_approval_check")
            
            evaluation_result = await self.evaluation_agent.quick_approval_check(strategy_summary)
            
            logger.info("📤 ContentEvaluationAgent OUTPUT:")
            logger.info(f"  - quick_score: {evaluation_result.get('quick_score', 0.0)}")
            logger.info(f"  - approval_recommendation: {evaluation_result.get('approval_recommendation', '不明')}")
            logger.info(f"  - risk_flags: {evaluation_result.get('risk_flags', [])}")
            logger.info(f"  - content_length: {evaluation_result.get('content_length', 0)}")
            logger.info(f"  - confidence_level: {evaluation_result.get('confidence_level', 0.0)}")
            
            results["stages"]["content_evaluation"] = {
                "status": "completed",
                "result": evaluation_result,
                "timestamp": datetime.now().isoformat()
            }
            
            if callback_func:
                await callback_func("内容評価", "完了", f"評価: {evaluation_result.get('approval_recommendation', '不明')}")
            
            # Stage 4: 3パターン生成
            if callback_func:
                await callback_func("パターン生成", "開始", "3つの返信パターンを生成中")
            
            logger.info("🎨 Stage 4: パターン生成開始")
            logger.info("📥 PatternGenerationAgent INPUT:")
            logger.info(f"  - thread_analysis: 交渉段階={thread_analysis.get('negotiation_stage', '不明')}")
            logger.info(f"  - strategy_plan: アプローチ={strategy_plan.get('primary_approach', '不明')}")
            logger.info(f"  - evaluation_result: 承認={evaluation_result.get('approval_recommendation', '不明')}")
            logger.info(f"  - company_settings: {len(company_settings)}項目")
            logger.info(f"  - custom_instructions: '{custom_instructions}'" if custom_instructions else "  - custom_instructions: 未設定")
            
            patterns_result = await self.pattern_agent.generate_three_patterns(
                thread_analysis, strategy_plan, evaluation_result, 
                company_settings, custom_instructions
            )
            
            logger.info("📤 PatternGenerationAgent OUTPUT:")
            if "pattern_collaborative" in patterns_result:
                logger.info(f"  - collaborative: '{patterns_result['pattern_collaborative'].get('content', '生成エラー')[:100]}...'")
            if "pattern_balanced" in patterns_result:
                logger.info(f"  - balanced: '{patterns_result['pattern_balanced'].get('content', '生成エラー')[:100]}...'")
            if "pattern_assertive" in patterns_result:
                logger.info(f"  - assertive: '{patterns_result['pattern_assertive'].get('content', '生成エラー')[:100]}...'")
            if "generation_metadata" in patterns_result:
                metadata = patterns_result["generation_metadata"]
                logger.info(f"  - confidence_level: {metadata.get('confidence_level', 0.0)}")
                logger.info(f"  - language_setting: {metadata.get('language_setting', '不明')}")
            
            results["stages"]["pattern_generation"] = {
                "status": "completed",
                "result": patterns_result,
                "timestamp": datetime.now().isoformat()
            }
            results["final_patterns"] = patterns_result
            
            if callback_func:
                await callback_func("パターン生成", "完了", "3つの返信パターン生成完了")
            
            # 処理完了
            end_time = datetime.now()
            processing_duration = (end_time - start_time).total_seconds()
            
            results.update({
                "processing_end": end_time.isoformat(),
                "processing_duration_seconds": processing_duration,
                "total_stages": len(self.processing_stages),
                "completed_stages": 4,
                "success": True
            })
            
            logger.info(f"✅ 4段階交渉処理完了 ({processing_duration:.2f}秒)")
            logger.info("📋 最終処理結果サマリー:")
            logger.info(f"   ⏱️ 総処理時間: {processing_duration:.2f}秒")
            logger.info(f"   🎯 完了段階数: {results['completed_stages']}/{results['total_stages']}")
            logger.info(f"   📊 成功フラグ: {results['success']}")
            if results.get('final_patterns'):
                pattern_count = len([k for k in results['final_patterns'].keys() if k.startswith('pattern_')])
                logger.info(f"   🎨 生成パターン数: {pattern_count}パターン")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ 4段階交渉処理エラー: {str(e)}")
            
            if callback_func:
                await callback_func("エラー", "失敗", f"処理エラー: {str(e)}")
            
            return {
                "manager_id": self.manager_id,
                "success": False,
                "error": str(e),
                "processing_start": start_time.isoformat() if 'start_time' in locals() else datetime.now().isoformat(),
                "stages": results.get("stages", {}) if 'results' in locals() else {},
                "final_patterns": {}
            }
    
    async def get_quick_response(
        self,
        latest_message: str,
        company_settings: Dict[str, Any],
        custom_instructions: str = ""
    ) -> Dict[str, Any]:
        """
        簡易返信生成（単一メッセージ用）
        
        Args:
            latest_message: 最新メッセージ
            company_settings: 企業設定情報
            custom_instructions: カスタム指示
            
        Returns:
            Dict: 簡易返信結果
        """
        try:
            logger.info("⚡ 簡易返信生成開始")
            
            # 単一メッセージをスレッド形式に変換
            thread_messages = [
                {
                    "sender": "influencer",
                    "content": latest_message,
                    "timestamp": datetime.now().isoformat()
                }
            ]
            
            # 戦略立案のみ実行（簡易版）
            strategy_plan = await self.strategy_agent.plan_reply_strategy(
                {"negotiation_stage": "関心表明", "key_topics": ["返信要求"]},
                company_settings,
                custom_instructions
            )
            
            # バランス型パターンのみ生成
            single_pattern = await self.pattern_agent.generate_single_pattern(
                "balanced",
                "ご連絡ありがとうございます。",
                strategy_plan,
                company_settings
            )
            
            return {
                "success": True,
                "response_type": "quick_response",
                "content": single_pattern.get("content", ""),
                "approach": "balanced",
                "strategy_summary": strategy_plan.get("primary_approach", "balanced"),
                "custom_instructions_applied": bool(custom_instructions),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 簡易返信生成エラー: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response_type": "quick_response_error",
                "content": "返信生成エラーが発生しました。",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_manager_status(self) -> Dict[str, Any]:
        """マネージャーステータスを取得"""
        try:
            agents_status = {}
            
            # 各エージェントの能力情報を取得
            for agent_name, agent in [
                ("thread_analysis", self.thread_agent),
                ("reply_strategy", self.strategy_agent), 
                ("content_evaluation", self.evaluation_agent),
                ("pattern_generation", self.pattern_agent)
            ]:
                try:
                    agents_status[agent_name] = agent.get_capabilities()
                    agents_status[agent_name]["status"] = "active"
                except Exception as e:
                    agents_status[agent_name] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            return {
                "manager_id": self.manager_id,
                "manager_type": "simple_negotiation_manager",
                "total_agents": 4,
                "processing_stages": self.processing_stages,
                "agents": agents_status,
                "system_health": "healthy",
                "capabilities": [
                    "thread_analysis",
                    "strategy_planning",
                    "content_evaluation", 
                    "multi_pattern_generation",
                    "custom_instructions_support",
                    "company_settings_integration"
                ],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ マネージャーステータス取得エラー: {str(e)}")
            return {
                "manager_id": self.manager_id,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_supported_features(self) -> Dict[str, Any]:
        """サポート機能一覧を取得"""
        return {
            "negotiation_processing": {
                "stages": 4,
                "description": "4段階の交渉処理"
            },
            "pattern_generation": {
                "patterns": ["collaborative", "balanced", "assertive"],
                "description": "3つの異なるアプローチでの返信生成"
            },
            "customization": {
                "custom_instructions": True,
                "company_settings": True,
                "language_support": ["Japanese", "English", "Chinese"]
            },
            "evaluation": {
                "content_quality": True,
                "risk_assessment": True,
                "approval_recommendations": True
            },
            "performance": {
                "async_processing": True,
                "progress_callbacks": True,
                "error_handling": True
            }
        }