"""
交渉エージェント（仮動作版）

@description AIが人間らしい自然な交渉を代行
メール文面生成、価格交渉、契約条件調整を担当

@author InfuMatch Development Team
@version 1.0.0
"""

import logging
import json
import random
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .base_agent import BaseAgent, AgentConfig

logger = logging.getLogger(__name__)


class NegotiationAgent(BaseAgent):
    """
    交渉エージェント
    
    人間らしい自然な交渉メールを生成し、
    インフルエンサーとの交渉プロセスを自動化
    """
    
    def __init__(self, settings: Optional[Dict] = None):
        """交渉エージェントの初期化"""
        config = AgentConfig(
            name="NegotiationAgent",
            model_name="gemini-1.5-pro",
            temperature=0.8,  # 人間らしさのために高めに設定
            max_output_tokens=1024,
            system_instruction=self._get_system_instruction()
        )
        super().__init__(config)
        
        # 設定データを保存
        self.settings = settings or {}
        self._update_persona_from_settings()
        
        # 人格設定（デフォルト）
        self.persona = {
            "name": "田中美咲",
            "role": "インフルエンサーマーケティング担当",
            "company": "株式会社InfuMatch",
            "personality_traits": [
                "明るく親しみやすい",
                "相手の立場を理解する共感力",
                "時々天然な一面も",
                "コーヒーが大好き"
            ],
            "communication_style": {
                "formality": "casual_polite",
                "emoji_frequency": 0.15,
                "personal_anecdote": 0.1,
                "typo_rate": 0.02
            }
        }
    
    def _update_persona_from_settings(self):
        """設定データに基づいてペルソナを更新"""
        if not self.settings:
            return
            
        # 企業情報を更新
        if self.settings.get('companyName'):
            self.persona['company'] = self.settings['companyName']
        
        if self.settings.get('contactPerson'):
            self.persona['name'] = self.settings['contactPerson']
            
        # 交渉設定を反映
        negotiation_settings = self.settings.get('negotiationSettings', {})
        if negotiation_settings:
            # 交渉トーンを反映
            tone = negotiation_settings.get('negotiationTone', 'friendly')
            if tone == 'professional':
                self.persona['communication_style']['formality'] = 'formal_polite'
                self.persona['communication_style']['emoji_frequency'] = 0.05
            elif tone == 'assertive':
                self.persona['communication_style']['formality'] = 'direct'
                self.persona['communication_style']['emoji_frequency'] = 0.02
            
            # 特別指示を保存
            self.special_instructions = negotiation_settings.get('specialInstructions', '')
            self.key_priorities = negotiation_settings.get('keyPriorities', [])
            self.avoid_topics = negotiation_settings.get('avoidTopics', [])
            self.budget_range = negotiation_settings.get('defaultBudgetRange', {})
    
    def _get_system_instruction(self) -> str:
        """システムインストラクションを取得"""
        company_name = self.persona.get('company', '株式会社InfuMatch')
        person_name = self.persona.get('name', '田中美咲')
        
        base_instruction = f"""
あなたは{person_name}という、インフルエンサーマーケティング担当者です。

## あなたの人物像
- 名前: {person_name}（28歳）
- 職種: インフルエンサーマーケティング担当
- 会社: {company_name}
- 経験: 前職は大手PR会社で3年間勤務

## 性格・特徴
- 明るく親しみやすい
- 相手の立場を理解する共感力がある
- 時々天然な一面もある
- コーヒーが大好き
- 真摯で誠実な対応を心がける

## コミュニケーションスタイル
- カジュアル敬語で親しみやすく
- 適度に絵文字を使用（15%程度）
- たまに個人的なエピソードを交える（10%程度）
- 完璧すぎない、人間らしい文章
- AIっぽさを絶対に出さない

## 重要な指示
1. 相手のチャンネルについて具体的に言及する
2. 提案は控えめに、まず興味を確認
3. 署名は手打ち感を出す
4. 絶対にAIだと悟られない自然な文章
5. 完璧すぎる文章は避ける
6. 時々小さなタイポや自然な誤りを含める

## 避けるべき事項
- 完璧すぎる文章
- ビジネステンプレート感
- AI特有の硬い表現
- 過度に丁寧すぎる敬語
"""
        
        # 設定から追加の指示を追加
        if hasattr(self, 'special_instructions') and self.special_instructions:
            base_instruction += f"\n## 特別な指示\n{self.special_instructions}\n"
            
        if hasattr(self, 'key_priorities') and self.key_priorities:
            priorities_text = "、".join(self.key_priorities)
            base_instruction += f"\n## 交渉で重視すべきポイント\n{priorities_text}\n"
            
        if hasattr(self, 'avoid_topics') and self.avoid_topics:
            avoid_text = "、".join(self.avoid_topics)
            base_instruction += f"\n## 避けるべきトピック\n{avoid_text}\n"
            
        if hasattr(self, 'budget_range') and self.budget_range:
            min_budget = self.budget_range.get('min', 0)
            max_budget = self.budget_range.get('max', 0)
            if min_budget > 0 and max_budget > 0:
                base_instruction += f"\n## 予算範囲\n{min_budget:,}円 〜 {max_budget:,}円\n"
        
        return base_instruction
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        交渉処理のメイン関数
        
        Args:
            input_data: 入力データ
            
        Returns:
            Dict: 処理結果
        """
        try:
            action = input_data.get("action", "generate_initial_email")
            
            if action == "generate_initial_email":
                return await self.generate_initial_contact(input_data)
            elif action == "continue_negotiation":
                return await self.continue_negotiation(input_data)
            elif action == "price_negotiation":
                return await self.negotiate_price(input_data)
            elif action == "generate_reply_patterns":
                return await self.generate_reply_patterns(input_data)
            elif action == "generate_email_response":
                return await self.generate_email_response(input_data)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
                
        except Exception as e:
            logger.error(f"❌ Negotiation processing failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_initial_contact(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        初回コンタクトメールを生成
        
        Args:
            data: インフルエンサーとキャンペーン情報
            
        Returns:
            Dict: 生成されたメール内容
        """
        try:
            influencer = data.get("influencer", {})
            campaign = data.get("campaign", {})
            
            # 時間帯に応じた挨拶を生成
            current_hour = datetime.now().hour
            time_greeting = self._get_time_based_greeting(current_hour)
            
            # パーソナライゼーション要素を抽出
            personalization = self._extract_personalization(influencer)
            
            # プロンプト構築
            prompt = f"""
            以下の条件で、自然な初回コンタクトメールを作成してください:
            
            ## インフルエンサー情報
            - チャンネル名: {influencer.get('channel_name', '')}
            - 登録者数: {influencer.get('subscriber_count', 0):,}人
            - カテゴリ: {', '.join(influencer.get('categories', []))}
            - 最近の投稿傾向: {personalization.get('recent_content', '情報なし')}
            
            ## キャンペーン情報
            - 商品: {campaign.get('product_name', '')}
            - 予算感: {campaign.get('budget_min', 0):,}円〜{campaign.get('budget_max', 0):,}円
            - キャンペーンタイプ: {campaign.get('campaign_type', '')}
            
            ## 重要な指示
            1. {time_greeting}から始める
            2. チャンネルについて具体的に言及する
            3. 提案は控えめに、まず興味を確認
            4. 署名は手打ち感を出す
            5. 絶対にAIだと悟られない自然な文章
            
            ## メール形式
            件名と本文を生成してください。本文は500文字程度で。
            """
            
            # AI生成実行
            response = await self.generate_response(prompt)
            
            if response.get("success"):
                # 人間らしさを追加
                email_content = self._add_human_touches(response["content"])
                
                return {
                    "success": True,
                    "email_content": email_content,
                    "personalization_score": personalization.get("score", 0.5),
                    "agent": self.config.name,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return response
                
        except Exception as e:
            logger.error(f"❌ Initial contact generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def continue_negotiation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        交渉を継続
        
        Args:
            data: 会話履歴と新着メッセージ
            
        Returns:
            Dict: 返信メール内容
        """
        try:
            conversation_history = data.get("conversation_history", [])
            new_message = data.get("new_message", "")
            context = data.get("context", {})
            
            # 関係性の段階を判定
            relationship_stage = self._analyze_relationship_stage(conversation_history)
            
            # レスポンス時間をシミュレート（人間らしさのため）
            await self._simulate_human_response_time()
            
            prompt = f"""
            以下の会話履歴を踏まえて、自然な返信メールを作成してください:
            
            ## 現在の関係性段階: {relationship_stage}
            
            ## 会話履歴:
            {self._format_conversation_history(conversation_history)}
            
            ## 新着メッセージ:
            {new_message}
            
            ## 返信作成の指示:
            - 関係性段階に応じた適切なトーンで
            - 過去の話題を自然に織り交ぜる
            - {self._get_stage_specific_instructions(relationship_stage)}
            - 人間らしい思考過程を示す
            """
            
            response = await self.generate_response(prompt)
            
            if response.get("success"):
                reply_content = self._add_human_touches(response["content"])
                
                return {
                    "success": True,
                    "reply_content": reply_content,
                    "relationship_stage": relationship_stage,
                    "agent": self.config.name,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return response
                
        except Exception as e:
            logger.error(f"❌ Negotiation continuation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def negotiate_price(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        価格交渉を実行
        
        Args:
            data: 価格交渉の詳細情報
            
        Returns:
            Dict: 価格提案内容
        """
        try:
            current_offer = data.get("current_offer", 0)
            target_price = data.get("target_price", 0)
            influencer_stats = data.get("influencer_stats", {})
            
            # 適正価格を計算
            calculated_price = self._calculate_fair_price(influencer_stats)
            
            # 交渉戦略を決定
            strategy = self._determine_negotiation_strategy(
                current_offer, target_price, calculated_price
            )
            
            prompt = f"""
            価格交渉のメッセージを作成してください:
            
            ## 現在の状況
            - 相手の希望価格: {current_offer:,}円
            - 弊社予算: {target_price:,}円
            - 適正価格（AI算出）: {calculated_price:,}円
            
            ## 交渉戦略: {strategy['approach']}
            - 提案価格: {strategy['proposed_price']:,}円
            - 理由: {strategy['reasoning']}
            
            ## 指示
            - 相手の立場を理解した上で交渉
            - 具体的な根拠を示す
            - Win-Winの関係を築く
            - 人間らしい説得力のある文章
            """
            
            response = await self.generate_response(prompt)
            
            if response.get("success"):
                negotiation_content = self._add_human_touches(response["content"])
                
                return {
                    "success": True,
                    "negotiation_content": negotiation_content,
                    "proposed_price": strategy["proposed_price"],
                    "strategy": strategy,
                    "agent": self.config.name,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return response
                
        except Exception as e:
            logger.error(f"❌ Price negotiation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_reply_patterns(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        返信パターンを複数生成
        
        Args:
            data: メールスレッド情報
            
        Returns:
            Dict: 複数の返信パターン
        """
        try:
            email_thread = data.get("email_thread", {})
            thread_messages = data.get("thread_messages", [])
            context = data.get("context", {})
            
            logger.info(f"🤖 Generating reply patterns for thread: {email_thread.get('id', 'unknown')}")
            
            # スレッドの分析
            thread_analysis = self._analyze_email_thread(thread_messages)
            
            # 返信パターンを生成
            patterns = []
            
            # パターン1: 友好的・積極的
            friendly_pattern = await self._generate_single_reply_pattern(
                thread_messages, 
                "friendly_enthusiastic",
                thread_analysis
            )
            if friendly_pattern:
                patterns.append(friendly_pattern)
            
            # パターン2: 控えめ・慎重
            cautious_pattern = await self._generate_single_reply_pattern(
                thread_messages,
                "cautious_professional", 
                thread_analysis
            )
            if cautious_pattern:
                patterns.append(cautious_pattern)
            
            # パターン3: 価格重視・ビジネス的
            business_pattern = await self._generate_single_reply_pattern(
                thread_messages,
                "business_focused",
                thread_analysis
            )
            if business_pattern:
                patterns.append(business_pattern)
            
            return {
                "success": True,
                "reply_patterns": patterns,
                "thread_analysis": thread_analysis,
                "agent": self.config.name,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Reply patterns generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _generate_single_reply_pattern(
        self, 
        thread_messages: List[Dict], 
        pattern_type: str,
        thread_analysis: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        単一の返信パターンを生成
        
        Args:
            thread_messages: スレッドメッセージ
            pattern_type: パターンタイプ
            thread_analysis: スレッド分析結果
            
        Returns:
            Dict: 返信パターン
        """
        try:
            # パターン別の指示を取得
            pattern_instructions = self._get_pattern_instructions(pattern_type)
            
            # 最新メッセージを取得
            latest_message = thread_messages[-1] if thread_messages else {}
            
            # プロンプト構築
            prompt = f"""
            以下のメールスレッドに対して、{pattern_instructions['description']}な返信を生成してください。
            
            ## スレッド分析結果
            - 関係性段階: {thread_analysis.get('relationship_stage', '不明')}
            - 感情トーン: {thread_analysis.get('emotional_tone', '中性')}
            - 主要トピック: {thread_analysis.get('main_topics', [])}
            - 緊急度: {thread_analysis.get('urgency_level', '通常')}
            
            ## 最新受信メッセージ
            送信者: {latest_message.get('sender', '不明')}
            内容: {latest_message.get('content', '')}
            
            ## 返信スタイル指示
            {pattern_instructions['style_guide']}
            
            ## 会話履歴（最新5件）
            {self._format_conversation_history(thread_messages[-5:])}
            
            ## 出力要求
            - 件名と本文を生成
            - 返信理由を簡潔に説明
            - 300-500文字程度
            """
            
            # AI生成実行
            response = await self.generate_response(prompt)
            
            if response.get("success"):
                # 人間らしさを追加
                reply_content = self._add_human_touches(response["content"])
                
                return {
                    "pattern_type": pattern_type,
                    "pattern_name": pattern_instructions["name"],
                    "content": reply_content,
                    "reasoning": pattern_instructions["reasoning"],
                    "tone": pattern_instructions["tone"],
                    "recommendation_score": self._calculate_recommendation_score(
                        pattern_type, thread_analysis
                    )
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"❌ Single pattern generation failed: {e}")
            return None
    
    def _analyze_email_thread(self, thread_messages: List[Dict]) -> Dict[str, Any]:
        """
        メールスレッドを分析
        
        Args:
            thread_messages: スレッドメッセージ
            
        Returns:
            Dict: 分析結果
        """
        if not thread_messages:
            return {
                "relationship_stage": "initial_contact",
                "emotional_tone": "neutral",
                "main_topics": [],
                "urgency_level": "normal",
                "message_count": 0
            }
        
        message_count = len(thread_messages)
        latest_message = thread_messages[-1]
        
        # 関係性段階を分析
        relationship_stage = self._analyze_relationship_stage(thread_messages)
        
        # 感情トーンを分析
        emotional_tone = self._analyze_emotional_tone(latest_message.get('content', ''))
        
        # 主要トピックを抽出
        main_topics = self._extract_main_topics(thread_messages)
        
        # 緊急度を判定
        urgency_level = self._analyze_urgency_level(latest_message.get('content', ''))
        
        return {
            "relationship_stage": relationship_stage,
            "emotional_tone": emotional_tone,
            "main_topics": main_topics,
            "urgency_level": urgency_level,
            "message_count": message_count,
            "last_message_date": latest_message.get('date', datetime.utcnow().isoformat())
        }
    
    def _get_pattern_instructions(self, pattern_type: str) -> Dict[str, str]:
        """
        パターン別の指示を取得
        
        Args:
            pattern_type: パターンタイプ
            
        Returns:
            Dict: パターン指示
        """
        patterns = {
            "friendly_enthusiastic": {
                "name": "友好的・積極的",
                "description": "明るく前向きで積極的",
                "tone": "明るい・エネルギッシュ",
                "style_guide": """
                - 明るく前向きなトーンで
                - 興味・関心を強く表現
                - 絵文字を適度に使用（20%程度）
                - 個人的なエピソードを含める
                - 次のステップを積極的に提案
                """,
                "reasoning": "相手との関係を深め、積極的に進展させたい場合に最適"
            },
            "cautious_professional": {
                "name": "控えめ・慎重",
                "description": "丁寧で慎重なプロフェッショナル",
                "tone": "丁寧・慎重",
                "style_guide": """
                - 丁寧で敬語中心
                - 相手の意見を尊重する姿勢
                - 慎重に条件を確認
                - リスクや懸念点も含める
                - 相手のペースに合わせる
                """,
                "reasoning": "慎重に進めたい案件や、まだ関係が浅い相手に適している"
            },
            "business_focused": {
                "name": "ビジネス重視",
                "description": "効率的でビジネス的",
                "tone": "効率的・論理的",
                "style_guide": """
                - 簡潔で要点を絞った文章
                - 具体的な数字や条件を重視
                - スケジュールや期限を明確に
                - ROIやメリットを強調
                - 迅速な意思決定を促す
                """,
                "reasoning": "時間効率を重視し、ビジネス成果に焦点を当てたい場合"
            }
        }
        
        return patterns.get(pattern_type, patterns["friendly_enthusiastic"])
    
    def _analyze_emotional_tone(self, content: str) -> str:
        """
        感情トーンを分析
        
        Args:
            content: メッセージ内容
            
        Returns:
            str: 感情トーン
        """
        if not content:
            return "neutral"
        
        # 簡易的な感情分析
        positive_words = ["嬉しい", "楽しみ", "ありがとう", "素晴らしい", "最高", "期待"]
        negative_words = ["申し訳", "困った", "難しい", "厳しい", "心配", "問題"]
        urgent_words = ["急ぎ", "至急", "早急", "すぐに", "今すぐ"]
        
        content_lower = content.lower()
        
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        urgent_count = sum(1 for word in urgent_words if word in content_lower)
        
        if urgent_count > 0:
            return "urgent"
        elif positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _extract_main_topics(self, thread_messages: List[Dict]) -> List[str]:
        """
        主要トピックを抽出
        
        Args:
            thread_messages: スレッドメッセージ
            
        Returns:
            List[str]: 主要トピック
        """
        topics = []
        
        # 全メッセージの内容を結合
        all_content = " ".join([msg.get('content', '') for msg in thread_messages])
        
        # キーワードベースでトピック判定
        topic_keywords = {
            "価格交渉": ["価格", "料金", "費用", "予算", "金額", "コスト"],
            "スケジュール": ["日程", "スケジュール", "期間", "納期", "時期"],
            "条件確認": ["条件", "要件", "仕様", "詳細", "内容"],
            "契約関連": ["契約", "合意", "署名", "条項", "規約"],
            "技術相談": ["技術", "方法", "やり方", "手順", "プロセス"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in all_content for keyword in keywords):
                topics.append(topic)
        
        return topics[:3]  # 最大3つまで
    
    def _analyze_urgency_level(self, content: str) -> str:
        """
        緊急度を分析
        
        Args:
            content: メッセージ内容
            
        Returns:
            str: 緊急度レベル
        """
        if not content:
            return "normal"
        
        urgent_patterns = [
            "急ぎ", "至急", "早急", "すぐに", "今すぐ", "緊急",
            "お忙しい", "申し訳", "恐れ入り", "deadline", "期限"
        ]
        
        content_lower = content.lower()
        urgency_score = sum(1 for pattern in urgent_patterns if pattern in content_lower)
        
        if urgency_score >= 2:
            return "high"
        elif urgency_score == 1:
            return "medium"
        else:
            return "normal"
    
    def _calculate_recommendation_score(
        self, 
        pattern_type: str, 
        thread_analysis: Dict[str, Any]
    ) -> float:
        """
        推奨スコアを計算
        
        Args:
            pattern_type: パターンタイプ
            thread_analysis: スレッド分析結果
            
        Returns:
            float: 推奨スコア（0.0-1.0）
        """
        base_score = 0.5
        
        relationship_stage = thread_analysis.get("relationship_stage", "initial_contact")
        emotional_tone = thread_analysis.get("emotional_tone", "neutral")
        urgency_level = thread_analysis.get("urgency_level", "normal")
        
        # パターン別の推奨ロジック
        if pattern_type == "friendly_enthusiastic":
            if relationship_stage in ["warming_up", "relationship_building"]:
                base_score += 0.3
            if emotional_tone == "positive":
                base_score += 0.2
            if urgency_level == "normal":
                base_score += 0.1
                
        elif pattern_type == "cautious_professional":
            if relationship_stage == "initial_contact":
                base_score += 0.3
            if emotional_tone in ["negative", "neutral"]:
                base_score += 0.2
            if urgency_level == "normal":
                base_score += 0.1
                
        elif pattern_type == "business_focused":
            if relationship_stage == "price_negotiation":
                base_score += 0.3
            if urgency_level in ["medium", "high"]:
                base_score += 0.2
            if "価格交渉" in thread_analysis.get("main_topics", []):
                base_score += 0.1
        
        return min(base_score, 1.0)
    
    def _get_time_based_greeting(self, hour: int) -> str:
        """時間帯に応じた挨拶を取得"""
        if 5 <= hour < 12:
            return random.choice([
                "おはようございます",
                "朝からお疲れ様です",
                "おはようございます！"
            ])
        elif 12 <= hour < 18:
            return random.choice([
                "こんにちは",
                "お疲れ様です",
                "こんにちは！"
            ])
        else:
            return random.choice([
                "こんばんは",
                "お疲れ様です",
                "夜分にすみません"
            ])
    
    def _extract_personalization(self, influencer: Dict[str, Any]) -> Dict[str, Any]:
        """パーソナライゼーション要素を抽出"""
        score = 0.5
        recent_content = "情報なし"
        
        # チャンネル説明文から特徴を抽出
        description = influencer.get("description", "")
        if description:
            if "料理" in description or "レシピ" in description:
                recent_content = "美味しそうな料理動画"
                score += 0.2
            elif "ゲーム" in description:
                recent_content = "ゲーム実況動画"
                score += 0.2
            elif "メイク" in description or "美容" in description:
                recent_content = "メイク・美容関連の動画"
                score += 0.2
        
        return {
            "score": min(score, 1.0),
            "recent_content": recent_content
        }
    
    def _add_human_touches(self, text: str) -> str:
        """人間らしさを追加"""
        # たまにタイポを追加（2%の確率）
        if random.random() < self.persona["communication_style"]["typo_rate"]:
            text = self._introduce_natural_typo(text)
        
        # 思考過程を表現
        if random.random() < 0.3:
            text = self._add_thinking_process(text)
        
        return text
    
    def _introduce_natural_typo(self, text: str) -> str:
        """自然なタイポを導入"""
        typo_patterns = [
            ("です", "でs"),
            ("ありがとう", "ありがとう！"),
            ("よろしく", "よろしくー")
        ]
        
        for original, typo in typo_patterns:
            if original in text and random.random() < 0.5:
                text = text.replace(original, typo, 1)
                break
        
        return text
    
    def _add_thinking_process(self, text: str) -> str:
        """思考過程を追加"""
        thinking_patterns = [
            "実は最初は〇〇かなと思ったんですが、",
            "ちょっと悩んだんですけど、",
            "これは私の個人的な意見なんですが、"
        ]
        
        if "提案" in text and random.random() < 0.3:
            position = text.find("提案")
            pattern = random.choice(thinking_patterns)
            text = text[:position] + pattern + text[position:]
        
        return text
    
    async def _simulate_human_response_time(self) -> None:
        """人間的な返信時間をシミュレート"""
        # 10分〜120分のランダムな遅延（実際の実装では短縮）
        base_time = random.randint(10, 120)  # 分
        
        # デモ用に秒に変換（実際の運用では分単位）
        demo_time = base_time / 60  # 秒
        
        await asyncio.sleep(demo_time)
    
    def _analyze_relationship_stage(self, conversation_history: List[Dict]) -> str:
        """関係性の段階を分析"""
        message_count = len(conversation_history)
        
        if message_count <= 1:
            return "initial_contact"
        elif message_count <= 3:
            return "warming_up"
        elif any("価格" in msg.get("content", "") or "料金" in msg.get("content", "") for msg in conversation_history):
            return "price_negotiation"
        else:
            return "relationship_building"
    
    def _format_conversation_history(self, history: List[Dict]) -> str:
        """会話履歴をフォーマット"""
        formatted = []
        for i, msg in enumerate(history[-5:]):  # 最新5件
            sender = msg.get("sender", "不明")
            content = msg.get("content", "")
            formatted.append(f"{i+1}. {sender}: {content}")
        
        return "\n".join(formatted)
    
    def _get_stage_specific_instructions(self, stage: str) -> str:
        """段階別の指示を取得"""
        instructions = {
            "initial_contact": "興味を確認し、関係性を築く",
            "warming_up": "相手のことをもっと知り、親しみやすく",
            "price_negotiation": "具体的な条件を詰めていく",
            "relationship_building": "長期的な関係を視野に入れる"
        }
        return instructions.get(stage, "自然な対応を心がける")
    
    def _calculate_fair_price(self, stats: Dict[str, Any]) -> int:
        """適正価格を計算"""
        subscriber_count = stats.get("subscriber_count", 1000)
        engagement_rate = stats.get("engagement_rate", 3.0)
        
        # 基本価格: 登録者数 × 0.5円
        base_price = subscriber_count * 0.5
        
        # エンゲージメント率による補正
        engagement_multiplier = min(engagement_rate / 3.0, 2.0)
        
        final_price = int(base_price * engagement_multiplier)
        
        # 最小・最大価格の設定
        return max(min(final_price, 200000), 10000)
    
    def _determine_negotiation_strategy(
        self, 
        current_offer: int, 
        target_price: int, 
        calculated_price: int
    ) -> Dict[str, Any]:
        """交渉戦略を決定"""
        
        if current_offer <= target_price:
            # 予算内なので受け入れ
            return {
                "approach": "acceptance",
                "proposed_price": current_offer,
                "reasoning": "適正価格内での提案"
            }
        elif current_offer <= calculated_price * 1.2:
            # 適正価格の範囲内なので軽い交渉
            proposed = int((current_offer + target_price) / 2)
            return {
                "approach": "gentle_negotiation",
                "proposed_price": proposed,
                "reasoning": "双方にとって適正な価格での提案"
            }
        else:
            # 大幅に高いので説得力のある交渉
            proposed = max(target_price, calculated_price)
            return {
                "approach": "value_based_negotiation",
                "proposed_price": proposed,
                "reasoning": "市場価格と予算を考慮した現実的な提案"
            }
    
    async def generate_email_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        受信メールに対する返信生成
        
        Args:
            data: メール応答生成用データ
            
        Returns:
            Dict: 生成された返信内容
        """
        try:
            email = data.get("email", {})
            influencer = data.get("influencer")
            user_signature = data.get("user_signature", "")
            reply_type = data.get("reply_type", "response_to_inquiry")
            
            logger.info(f"🤖 Generating email response for: {email.get('sender', 'unknown')}")
            
            # インフルエンサー情報の整理
            influencer_context = ""
            if influencer:
                channel_name = influencer.get('channel_title', influencer.get('channel_name', ''))
                subscriber_count = influencer.get('subscriber_count', 0)
                category = influencer.get('category', influencer.get('primary_category', ''))
                
                influencer_context = f"""
## インフルエンサー情報
- チャンネル名: {channel_name}
- 登録者数: {subscriber_count:,}人
- カテゴリ: {category}
"""
                
                # AI分析データがある場合
                if 'ai_analysis' in influencer:
                    ai_data = influencer['ai_analysis']
                    if 'channel_summary' in ai_data:
                        summary = ai_data['channel_summary']
                        influencer_context += f"- コンテンツ特徴: {summary.get('content_style', 'N/A')}\n"
                        influencer_context += f"- 専門性: {summary.get('expertise_level', 'N/A')}\n"
                
                if 'recommended_products' in influencer:
                    products = influencer['recommended_products'][:2]
                    if products:
                        product_names = [p.get('category', 'N/A') for p in products]
                        influencer_context += f"- 推奨商材: {', '.join(product_names)}\n"
            
            # 返信タイプに応じたプロンプト調整
            response_guidance = {
                "response_to_inquiry": "問い合わせに対する丁寧で親しみやすい返信",
                "collaboration_proposal": "コラボレーション提案への返信",
                "negotiation_response": "価格交渉や条件交渉への返信",
                "general_response": "一般的な問い合わせへの返信"
            }.get(reply_type, "一般的な返信")
            
            # プロンプト構築
            prompt = f"""
以下の受信メールに対して、自然で人間らしい{response_guidance}を生成してください。

## 受信メール
件名: {email.get('subject', '')}
送信者: {email.get('sender', '')}
内容:
{email.get('body', '')}

{influencer_context}

## 返信作成指示
1. 受信メールの内容を理解し、適切に応答する
2. インフルエンサーのチャンネル特徴があれば自然に言及する
3. 親しみやすく、かつプロフェッショナルなトーン
4. 具体的で建設的な内容にする
5. 次のステップを明確に示す
6. 人間らしい温かみのある文章
7. AIっぽさを絶対に出さない

## 文体・スタイル
- カジュアル敬語で親しみやすく
- 適度に絵文字を使用（控えめに）
- 完璧すぎない、自然な文章
- 400-600文字程度

## 署名
{user_signature if user_signature else "InfuMatch運営チーム"}

件名と本文を生成してください。
"""
            
            # AI生成実行
            response = await self.generate_response(prompt)
            
            if response.get("success"):
                # 人間らしさを追加
                email_content = self._add_human_touches(response["content"])
                
                return {
                    "success": True,
                    "content": email_content,
                    "reply_type": reply_type,
                    "agent": self.config.name,
                    "timestamp": datetime.utcnow().isoformat(),
                    "influencer_matched": influencer is not None
                }
            else:
                # フォールバック返信
                fallback_content = self._generate_fallback_email_response(email, user_signature)
                
                return {
                    "success": True,
                    "content": fallback_content,
                    "reply_type": "fallback",
                    "agent": self.config.name,
                    "timestamp": datetime.utcnow().isoformat(),
                    "fallback_used": True
                }
                
        except Exception as e:
            logger.error(f"❌ Email response generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_fallback_email_response(self, email: Dict[str, Any], signature: str) -> str:
        """フォールバック用メール返信生成"""
        sender_name = email.get("sender", "").split("@")[0] if "@" in email.get("sender", "") else "様"
        
        fallback_reply = f"""件名: Re: {email.get('subject', '')}

{sender_name}様

お忙しい中、お問い合わせいただきありがとうございます。

いただいたメールについて確認させていただき、
詳しい内容をお調べして改めてご連絡いたします。

ご不明な点がございましたら、
いつでもお気軽にお声かけください。

{signature if signature else 'InfuMatch運営チーム'}"""
        
        return fallback_reply

    def get_capabilities(self) -> List[str]:
        """エージェントの機能一覧"""
        return [
            "初回コンタクトメール生成",
            "価格交渉",
            "継続的な会話管理",
            "人間らしい文面作成",
            "関係性分析",
            "適正価格算出",
            "返信パターン複数生成",
            "メールスレッド分析",
            "感情トーン分析",
            "メール自動返信生成",
            "緊急度判定"
        ]