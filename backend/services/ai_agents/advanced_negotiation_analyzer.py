"""
高度な交渉分析エージェント

@description 交渉の状況を詳細に分析し、戦略的な返信を生成
@author InfuMatch Development Team
@version 2.0.0
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class NegotiationStage(Enum):
    """交渉段階の詳細定義"""
    INITIAL_CONTACT = "initial_contact"  # 初回接触
    INTEREST_DISCOVERY = "interest_discovery"  # 興味・関心の探索
    REQUIREMENT_GATHERING = "requirement_gathering"  # 要件・ニーズの確認
    PROPOSAL_PRESENTATION = "proposal_presentation"  # 提案・条件提示
    NEGOTIATION_ACTIVE = "negotiation_active"  # 積極的な条件交渉
    FINAL_ADJUSTMENT = "final_adjustment"  # 最終調整
    CONTRACT_PREPARATION = "contract_preparation"  # 契約準備
    POST_DEAL_FOLLOW = "post_deal_follow"  # 契約後フォロー
    STALLED = "stalled"  # 停滞・保留中
    LOST = "lost"  # 失注


@dataclass
class NegotiationContext:
    """交渉コンテキスト"""
    company_goals: Dict[str, Any]
    influencer_profile: Dict[str, Any]
    negotiation_history: List[Dict[str, Any]]
    current_stage: NegotiationStage
    sentiment_trend: List[float]
    key_concerns: List[str]
    opportunities: List[str]
    risks: List[str]


@dataclass
class NegotiationStrategy:
    """交渉戦略"""
    approach: str
    key_messages: List[str]
    tone: str
    urgency_level: str
    next_steps: List[str]
    avoid_topics: List[str]
    success_probability: float


class AdvancedNegotiationAnalyzer:
    """高度な交渉分析器"""
    
    def __init__(self):
        self.stage_transition_rules = self._init_stage_transitions()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.goal_analyzer = GoalAlignmentAnalyzer()
        
    def analyze_negotiation_state(
        self, 
        thread_messages: List[Dict[str, Any]], 
        company_settings: Dict[str, Any]
    ) -> NegotiationContext:
        """
        交渉状態を詳細に分析
        
        Args:
            thread_messages: メールスレッドのメッセージリスト
            company_settings: 企業設定情報
            
        Returns:
            NegotiationContext: 詳細な交渉コンテキスト
        """
        # 現在の交渉段階を特定
        current_stage = self._identify_current_stage(thread_messages)
        
        # 感情推移を分析
        sentiment_trend = self._analyze_sentiment_trend(thread_messages)
        
        # インフルエンサープロファイルを抽出
        influencer_profile = self._extract_influencer_profile(thread_messages)
        
        # 主要な懸念事項を特定
        key_concerns = self._identify_concerns(thread_messages)
        
        # 機会とリスクを評価
        opportunities = self._identify_opportunities(thread_messages, company_settings)
        risks = self._identify_risks(thread_messages, sentiment_trend)
        
        # 企業ゴールを整理
        company_goals = self._structure_company_goals(company_settings)
        
        return NegotiationContext(
            company_goals=company_goals,
            influencer_profile=influencer_profile,
            negotiation_history=thread_messages,
            current_stage=current_stage,
            sentiment_trend=sentiment_trend,
            key_concerns=key_concerns,
            opportunities=opportunities,
            risks=risks
        )
    
    def generate_negotiation_strategy(
        self, 
        context: NegotiationContext
    ) -> NegotiationStrategy:
        """
        交渉戦略を生成
        
        Args:
            context: 交渉コンテキスト
            
        Returns:
            NegotiationStrategy: 詳細な交渉戦略
        """
        # 現在の段階に基づいた基本戦略
        base_strategy = self._get_stage_strategy(context.current_stage)
        
        # ゴール達成度を評価
        goal_alignment = self.goal_analyzer.analyze_alignment(
            context.company_goals, 
            context.influencer_profile
        )
        
        # 感情状態に基づいた調整
        sentiment_adjustment = self._adjust_for_sentiment(
            base_strategy, 
            context.sentiment_trend
        )
        
        # リスクと機会を考慮した最適化
        optimized_strategy = self._optimize_strategy(
            sentiment_adjustment,
            context.opportunities,
            context.risks
        )
        
        return optimized_strategy
    
    def _identify_current_stage(self, messages: List[Dict[str, Any]]) -> NegotiationStage:
        """現在の交渉段階を特定"""
        if not messages:
            return NegotiationStage.INITIAL_CONTACT
            
        # メッセージ数とキーワードに基づいて段階を判定
        message_count = len(messages)
        latest_messages = messages[-3:] if len(messages) >= 3 else messages
        
        # キーワードベースの段階判定
        stage_keywords = {
            NegotiationStage.INITIAL_CONTACT: ["初めまして", "ご連絡", "興味"],
            NegotiationStage.INTEREST_DISCOVERY: ["詳しく", "教えて", "どんな"],
            NegotiationStage.REQUIREMENT_GATHERING: ["条件", "要件", "希望"],
            NegotiationStage.PROPOSAL_PRESENTATION: ["提案", "プラン", "内容"],
            NegotiationStage.NEGOTIATION_ACTIVE: ["価格", "料金", "調整"],
            NegotiationStage.FINAL_ADJUSTMENT: ["最終", "確認", "契約"],
            NegotiationStage.CONTRACT_PREPARATION: ["契約書", "署名", "手続き"],
            NegotiationStage.STALLED: ["検討中", "保留", "後日"],
            NegotiationStage.LOST: ["見送り", "中止", "他社"]
        }
        
        # 最新メッセージから段階を推定
        for stage, keywords in stage_keywords.items():
            for msg in latest_messages:
                content = msg.get("content", "").lower()
                if any(keyword in content for keyword in keywords):
                    return stage
        
        # メッセージ数に基づくフォールバック
        if message_count <= 2:
            return NegotiationStage.INITIAL_CONTACT
        elif message_count <= 5:
            return NegotiationStage.INTEREST_DISCOVERY
        elif message_count <= 8:
            return NegotiationStage.REQUIREMENT_GATHERING
        else:
            return NegotiationStage.NEGOTIATION_ACTIVE
    
    def _analyze_sentiment_trend(self, messages: List[Dict[str, Any]]) -> List[float]:
        """感情推移を分析（-1.0〜1.0のスコア）"""
        trend = []
        for msg in messages:
            content = msg.get("content", "")
            score = self.sentiment_analyzer.analyze(content)
            trend.append(score)
        return trend
    
    def _extract_influencer_profile(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """インフルエンサープロファイルを抽出"""
        profile = {
            "communication_style": "unknown",
            "response_speed": "normal",
            "price_sensitivity": "medium",
            "professionalism": "medium",
            "interests": [],
            "concerns": [],
            "preferred_terms": []
        }
        
        # メッセージから特徴を抽出
        for msg in messages:
            content = msg.get("content", "").lower()
            
            # コミュニケーションスタイル判定
            if "!" in content or "😊" in content:
                profile["communication_style"] = "friendly"
            elif "お世話になっております" in content:
                profile["communication_style"] = "formal"
                
            # 価格感度判定
            if "高い" in content or "予算" in content:
                profile["price_sensitivity"] = "high"
            elif "費用" not in content and "価格" not in content:
                profile["price_sensitivity"] = "low"
        
        return profile
    
    def _identify_concerns(self, messages: List[Dict[str, Any]]) -> List[str]:
        """主要な懸念事項を特定"""
        concerns = []
        concern_keywords = {
            "価格": ["高い", "予算", "費用", "料金"],
            "スケジュール": ["期間", "日程", "いつ", "期限"],
            "内容": ["詳細", "具体的", "どのような"],
            "リスク": ["心配", "懸念", "不安", "大丈夫"]
        }
        
        for msg in messages[-5:]:  # 最新5件をチェック
            content = msg.get("content", "").lower()
            for concern, keywords in concern_keywords.items():
                if any(keyword in content for keyword in keywords):
                    if concern not in concerns:
                        concerns.append(concern)
        
        return concerns
    
    def _identify_opportunities(
        self, 
        messages: List[Dict[str, Any]], 
        company_settings: Dict[str, Any]
    ) -> List[str]:
        """機会を特定"""
        opportunities = []
        
        # ポジティブシグナルをチェック
        positive_signals = {
            "高い関心": ["興味深い", "面白い", "ぜひ"],
            "予算余裕": ["問題ない", "大丈夫", "可能"],
            "即決可能": ["すぐに", "早く", "今週中"],
            "長期関係": ["継続", "定期", "長期"]
        }
        
        for msg in messages:
            content = msg.get("content", "").lower()
            for opportunity, signals in positive_signals.items():
                if any(signal in content for signal in signals):
                    if opportunity not in opportunities:
                        opportunities.append(opportunity)
        
        return opportunities
    
    def _identify_risks(
        self, 
        messages: List[Dict[str, Any]], 
        sentiment_trend: List[float]
    ) -> List[str]:
        """リスクを特定"""
        risks = []
        
        # ネガティブシグナルをチェック
        negative_signals = {
            "競合検討": ["他社", "比較", "検討中"],
            "予算不足": ["高すぎ", "予算オーバー", "厳しい"],
            "関心低下": ["うーん", "微妙", "考えさせて"],
            "時間切れ": ["急いで", "期限", "間に合わない"]
        }
        
        # 感情推移の悪化をチェック
        if len(sentiment_trend) >= 3:
            recent_trend = sentiment_trend[-3:]
            if all(recent_trend[i] < recent_trend[i-1] for i in range(1, len(recent_trend))):
                risks.append("感情悪化傾向")
        
        for msg in messages[-5:]:
            content = msg.get("content", "").lower()
            for risk, signals in negative_signals.items():
                if any(signal in content for signal in signals):
                    if risk not in risks:
                        risks.append(risk)
        
        return risks
    
    def _structure_company_goals(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """企業ゴールを構造化"""
        negotiation_settings = settings.get("negotiationSettings", {})
        
        return {
            "budget_range": negotiation_settings.get("defaultBudgetRange", {}),
            "timeline": negotiation_settings.get("responseTimeExpectation", "24時間以内"),
            "priorities": negotiation_settings.get("keyPriorities", []),
            "avoid_topics": negotiation_settings.get("avoidTopics", []),
            "preferred_tone": negotiation_settings.get("preferredTone", "professional"),
            "decision_makers": negotiation_settings.get("decisionMakers", []),
            "success_metrics": [
                "予算内での契約",
                "品質の高いコンテンツ",
                "長期的な関係構築"
            ]
        }
    
    def _init_stage_transitions(self) -> Dict[NegotiationStage, List[NegotiationStage]]:
        """段階遷移ルールを初期化"""
        return {
            NegotiationStage.INITIAL_CONTACT: [
                NegotiationStage.INTEREST_DISCOVERY,
                NegotiationStage.STALLED,
                NegotiationStage.LOST
            ],
            NegotiationStage.INTEREST_DISCOVERY: [
                NegotiationStage.REQUIREMENT_GATHERING,
                NegotiationStage.STALLED,
                NegotiationStage.LOST
            ],
            NegotiationStage.REQUIREMENT_GATHERING: [
                NegotiationStage.PROPOSAL_PRESENTATION,
                NegotiationStage.STALLED
            ],
            NegotiationStage.PROPOSAL_PRESENTATION: [
                NegotiationStage.NEGOTIATION_ACTIVE,
                NegotiationStage.FINAL_ADJUSTMENT,
                NegotiationStage.STALLED,
                NegotiationStage.LOST
            ],
            NegotiationStage.NEGOTIATION_ACTIVE: [
                NegotiationStage.FINAL_ADJUSTMENT,
                NegotiationStage.PROPOSAL_PRESENTATION,
                NegotiationStage.STALLED,
                NegotiationStage.LOST
            ],
            NegotiationStage.FINAL_ADJUSTMENT: [
                NegotiationStage.CONTRACT_PREPARATION,
                NegotiationStage.NEGOTIATION_ACTIVE,
                NegotiationStage.STALLED
            ],
            NegotiationStage.CONTRACT_PREPARATION: [
                NegotiationStage.POST_DEAL_FOLLOW
            ],
            NegotiationStage.STALLED: [
                NegotiationStage.NEGOTIATION_ACTIVE,
                NegotiationStage.LOST
            ]
        }
    
    def _get_stage_strategy(self, stage: NegotiationStage) -> Dict[str, Any]:
        """段階別の基本戦略を取得"""
        strategies = {
            NegotiationStage.INITIAL_CONTACT: {
                "approach": "relationship_building",
                "tone": "friendly_professional",
                "key_messages": ["興味を持っていただきありがとうございます"],
                "next_steps": ["詳細な情報提供", "質問への回答"],
                "urgency_level": "low"
            },
            NegotiationStage.INTEREST_DISCOVERY: {
                "approach": "consultative_selling",
                "tone": "curious_engaged",
                "key_messages": ["ニーズを理解させていただきたい"],
                "next_steps": ["要件ヒアリング", "事例紹介"],
                "urgency_level": "medium"
            },
            NegotiationStage.NEGOTIATION_ACTIVE: {
                "approach": "value_negotiation",
                "tone": "confident_flexible",
                "key_messages": ["Win-Winの関係を築きたい"],
                "next_steps": ["条件調整", "代替案提示"],
                "urgency_level": "high"
            }
        }
        
        return strategies.get(stage, strategies[NegotiationStage.INITIAL_CONTACT])
    
    def _adjust_for_sentiment(
        self, 
        strategy: Dict[str, Any], 
        sentiment_trend: List[float]
    ) -> Dict[str, Any]:
        """感情状態に基づいて戦略を調整"""
        if not sentiment_trend:
            return strategy
            
        latest_sentiment = sentiment_trend[-1] if sentiment_trend else 0.0
        
        # ネガティブな感情への対応
        if latest_sentiment < -0.3:
            strategy["tone"] = "empathetic_understanding"
            strategy["key_messages"].insert(0, "ご懸念は十分理解しております")
            strategy["urgency_level"] = "low"
        # ポジティブな感情を活かす
        elif latest_sentiment > 0.3:
            strategy["urgency_level"] = "high"
            strategy["key_messages"].append("前向きにご検討いただけて嬉しいです")
        
        return strategy
    
    def _optimize_strategy(
        self,
        strategy: Dict[str, Any],
        opportunities: List[str],
        risks: List[str]
    ) -> NegotiationStrategy:
        """機会とリスクを考慮して戦略を最適化"""
        # 成功確率を計算
        success_probability = 0.5
        success_probability += len(opportunities) * 0.1
        success_probability -= len(risks) * 0.15
        success_probability = max(0.1, min(0.9, success_probability))
        
        # 避けるべきトピックを追加
        avoid_topics = []
        if "予算不足" in risks:
            avoid_topics.append("追加費用")
        if "競合検討" in risks:
            avoid_topics.append("他社比較")
        
        return NegotiationStrategy(
            approach=strategy.get("approach", "balanced"),
            key_messages=strategy.get("key_messages", []),
            tone=strategy.get("tone", "professional"),
            urgency_level=strategy.get("urgency_level", "medium"),
            next_steps=strategy.get("next_steps", []),
            avoid_topics=avoid_topics,
            success_probability=success_probability
        )


class SentimentAnalyzer:
    """感情分析器"""
    
    def analyze(self, text: str) -> float:
        """テキストの感情を分析（-1.0〜1.0）"""
        if not text:
            return 0.0
            
        # ポジティブ/ネガティブワードによる簡易分析
        positive_words = {
            "嬉しい": 0.8, "楽しみ": 0.7, "ありがとう": 0.6,
            "素晴らしい": 0.9, "良い": 0.5, "期待": 0.6,
            "興味": 0.5, "前向き": 0.7, "賛成": 0.8
        }
        
        negative_words = {
            "心配": -0.5, "不安": -0.6, "難しい": -0.4,
            "厳しい": -0.7, "無理": -0.8, "高い": -0.3,
            "問題": -0.5, "懸念": -0.6, "微妙": -0.4
        }
        
        score = 0.0
        word_count = 0
        
        for word, weight in positive_words.items():
            if word in text:
                score += weight
                word_count += 1
                
        for word, weight in negative_words.items():
            if word in text:
                score += weight
                word_count += 1
        
        if word_count > 0:
            return score / word_count
        else:
            return 0.0


class GoalAlignmentAnalyzer:
    """ゴール達成度分析器"""
    
    def analyze_alignment(
        self, 
        company_goals: Dict[str, Any], 
        influencer_profile: Dict[str, Any]
    ) -> float:
        """企業ゴールとインフルエンサーの適合度を分析（0.0〜1.0）"""
        alignment_score = 0.5
        
        # 予算適合度
        if influencer_profile.get("price_sensitivity") == "low":
            alignment_score += 0.2
        elif influencer_profile.get("price_sensitivity") == "high":
            alignment_score -= 0.2
            
        # コミュニケーションスタイル適合度
        preferred_tone = company_goals.get("preferred_tone", "professional")
        if preferred_tone == "professional" and influencer_profile.get("professionalism") == "high":
            alignment_score += 0.1
        elif preferred_tone == "friendly" and influencer_profile.get("communication_style") == "friendly":
            alignment_score += 0.1
            
        # レスポンス速度適合度
        if influencer_profile.get("response_speed") == "fast":
            alignment_score += 0.1
            
        return max(0.0, min(1.0, alignment_score))