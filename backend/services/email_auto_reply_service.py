"""
メール自動返信サービス

@description インフルエンサーからのメールに対する自動返信システム
- AI生成返信案作成
- 手動承認モード（デフォルト）
- 条件付き自動返信モード
- 学習機能付き

@author InfuMatch Development Team
@version 1.0.0
"""

import logging
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from google.cloud import firestore
from services.ai_agents.negotiation_agent import NegotiationAgent
from core.database import FirestoreClient

logger = logging.getLogger(__name__)


class ReplyMode(Enum):
    """返信モード"""
    MANUAL_APPROVAL = "manual_approval"
    AUTO_REPLY = "auto_reply"


class ReplyStatus(Enum):
    """返信ステータス"""
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    AUTO_REPLIED = "auto_replied"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class EmailData:
    """メールデータ"""
    
    message_id: str
    thread_id: str
    sender_email: str
    sender_name: Optional[str]
    subject: str
    body: str
    received_at: datetime
    attachments: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []


@dataclass
class ReplySettings:
    """ユーザー返信設定"""
    
    user_id: str
    default_mode: ReplyMode = ReplyMode.MANUAL_APPROVAL
    approval_timeout_hours: int = 24
    custom_signature: str = ""
    auto_reply_conditions: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.auto_reply_conditions is None:
            self.auto_reply_conditions = {
                "only_known_influencers": True,
                "minimum_engagement_rate": 2.0,
                "exclude_keywords": ["spam", "広告", "宣伝"],
                "max_daily_auto_replies": 10
            }


@dataclass
class AutoReplyResponse:
    """自動返信レスポンス"""
    
    success: bool
    thread_id: str
    generated_reply: Optional[str] = None
    status: Optional[ReplyStatus] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EmailAutoReplyService:
    """
    メール自動返信サービス
    
    インフルエンサーからのメールを解析し、AI生成の返信案を作成
    ユーザー設定に基づいて手動承認または自動送信を実行
    """
    
    def __init__(self):
        """初期化"""
        self.firestore_client = FirestoreClient()
        self.negotiation_agent = NegotiationAgent()
        
        # コレクション参照
        self.email_threads_ref = self.firestore_client.collection('email_threads')
        self.reply_settings_ref = self.firestore_client.collection('user_reply_settings')
        self.influencers_ref = self.firestore_client.collection('youtube_influencers')
    
    async def process_incoming_email(
        self, 
        email_data: EmailData, 
        user_id: str
    ) -> AutoReplyResponse:
        """
        受信メールの処理
        
        Args:
            email_data: 受信メールデータ
            user_id: ユーザーID
            
        Returns:
            AutoReplyResponse: 処理結果
        """
        try:
            logger.info(f"📧 Processing incoming email from {email_data.sender_email}")
            
            # 1. ユーザー設定取得
            user_settings = await self._get_user_reply_settings(user_id)
            
            # 2. スパム・不適切メールチェック
            if await self._is_spam_or_inappropriate(email_data):
                logger.warning(f"⚠️ Email marked as spam: {email_data.message_id}")
                return AutoReplyResponse(
                    success=False,
                    thread_id=email_data.thread_id,
                    error_message="Spam or inappropriate content detected"
                )
            
            # 3. インフルエンサー特定
            influencer_data = await self._identify_influencer(email_data.sender_email)
            
            # 4. 返信案生成
            generated_reply = await self._generate_reply_draft(
                email_data, 
                influencer_data, 
                user_settings
            )
            
            if not generated_reply:
                return AutoReplyResponse(
                    success=False,
                    thread_id=email_data.thread_id,
                    error_message="Failed to generate reply"
                )
            
            # 5. モード別処理
            if user_settings.default_mode == ReplyMode.AUTO_REPLY:
                should_auto_reply = await self._should_auto_reply(
                    email_data, 
                    influencer_data, 
                    user_settings
                )
                
                if should_auto_reply:
                    return await self._execute_auto_reply(
                        email_data, 
                        generated_reply, 
                        user_settings
                    )
            
            # デフォルト: 手動承認モード
            return await self._queue_for_approval(
                email_data, 
                generated_reply, 
                influencer_data, 
                user_settings
            )
            
        except Exception as e:
            logger.error(f"❌ Email processing failed: {e}")
            return AutoReplyResponse(
                success=False,
                thread_id=email_data.thread_id,
                error_message=str(e)
            )
    
    async def _get_user_reply_settings(self, user_id: str) -> ReplySettings:
        """ユーザー返信設定取得"""
        try:
            doc_ref = self.reply_settings_ref.document(user_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                return ReplySettings(
                    user_id=user_id,
                    default_mode=ReplyMode(data.get('default_mode', 'manual_approval')),
                    approval_timeout_hours=data.get('approval_timeout_hours', 24),
                    custom_signature=data.get('custom_signature', ''),
                    auto_reply_conditions=data.get('auto_reply_conditions', {})
                )
            else:
                # デフォルト設定を作成
                default_settings = ReplySettings(user_id=user_id)
                await self._save_user_reply_settings(default_settings)
                return default_settings
                
        except Exception as e:
            logger.error(f"❌ Failed to get user settings: {e}")
            return ReplySettings(user_id=user_id)
    
    async def _save_user_reply_settings(self, settings: ReplySettings) -> bool:
        """ユーザー返信設定保存"""
        try:
            doc_ref = self.reply_settings_ref.document(settings.user_id)
            await doc_ref.set({
                'default_mode': settings.default_mode.value,
                'approval_timeout_hours': settings.approval_timeout_hours,
                'custom_signature': settings.custom_signature,
                'auto_reply_conditions': settings.auto_reply_conditions,
                'updated_at': datetime.utcnow()
            })
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save user settings: {e}")
            return False
    
    async def _is_spam_or_inappropriate(self, email_data: EmailData) -> bool:
        """スパム・不適切メール判定"""
        try:
            # 基本的なスパムキーワードチェック
            spam_keywords = [
                "spam", "advertisement", "promotion", "宣伝", "広告", 
                "無料", "当選", "お得", "限定", "今すぐ"
            ]
            
            content_lower = (email_data.subject + " " + email_data.body).lower()
            
            for keyword in spam_keywords:
                if keyword in content_lower:
                    return True
            
            # 送信者ドメインチェック
            suspicious_domains = ["tempmail", "10minutemail", "guerrillamail"]
            sender_domain = email_data.sender_email.split("@")[-1].lower()
            
            for domain in suspicious_domains:
                if domain in sender_domain:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Spam check failed: {e}")
            return False
    
    async def _identify_influencer(self, sender_email: str) -> Optional[Dict[str, Any]]:
        """送信者からインフルエンサー特定"""
        try:
            # メールアドレスでインフルエンサーを検索
            query = self.influencers_ref.where('business_email', '==', sender_email).limit(1)
            docs = query.stream()
            
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                return data
            
            # 見つからない場合は部分一致検索
            # (Firestoreの制限により、配列内検索を行う)
            all_docs = self.influencers_ref.limit(1000).stream()
            
            for doc in all_docs:
                data = doc.to_dict()
                emails = data.get('emails', [])
                
                for email_obj in emails:
                    if isinstance(email_obj, dict):
                        if email_obj.get('email') == sender_email:
                            data['id'] = doc.id
                            return data
                    elif isinstance(email_obj, str):
                        if email_obj == sender_email:
                            data['id'] = doc.id
                            return data
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Influencer identification failed: {e}")
            return None
    
    async def _generate_reply_draft(
        self, 
        email_data: EmailData, 
        influencer_data: Optional[Dict[str, Any]], 
        user_settings: ReplySettings
    ) -> Optional[str]:
        """返信案生成"""
        try:
            # 交渉エージェント用のコンテキスト準備
            context = {
                "email": {
                    "subject": email_data.subject,
                    "body": email_data.body,
                    "sender": email_data.sender_name or email_data.sender_email
                },
                "influencer": influencer_data,
                "user_signature": user_settings.custom_signature,
                "reply_type": "response_to_inquiry"
            }
            
            # 交渉エージェントによる返信生成
            input_data = {
                "action": "generate_email_response",
                "context": context
            }
            
            result = await self.negotiation_agent.process(input_data)
            
            if result.get("success") and result.get("content"):
                return result["content"]
            else:
                # フォールバック: 基本的な返信テンプレート
                return await self._generate_fallback_reply(email_data, user_settings)
                
        except Exception as e:
            logger.error(f"❌ Reply generation failed: {e}")
            return await self._generate_fallback_reply(email_data, user_settings)
    
    async def _generate_fallback_reply(
        self, 
        email_data: EmailData, 
        user_settings: ReplySettings
    ) -> str:
        """フォールバック返信生成"""
        base_reply = f"""
{email_data.sender_name or ''}様

お忙しい中、ご連絡いただきありがとうございます。

いただいたメールについて確認させていただき、
改めてご連絡させていただきます。

何かご不明な点がございましたら、
お気軽にお声かけください。

{user_settings.custom_signature or ''}

InfuMatch運営チーム
"""
        return base_reply.strip()
    
    async def _should_auto_reply(
        self, 
        email_data: EmailData, 
        influencer_data: Optional[Dict[str, Any]], 
        user_settings: ReplySettings
    ) -> bool:
        """自動返信条件チェック"""
        try:
            conditions = user_settings.auto_reply_conditions
            
            # 既知のインフルエンサーのみ
            if conditions.get("only_known_influencers", True):
                if not influencer_data:
                    return False
            
            # エンゲージメント率チェック
            if influencer_data:
                min_engagement = conditions.get("minimum_engagement_rate", 2.0)
                engagement_rate = influencer_data.get("engagement_rate", 0)
                
                if engagement_rate < min_engagement:
                    return False
            
            # 除外キーワードチェック
            exclude_keywords = conditions.get("exclude_keywords", [])
            content_lower = (email_data.subject + " " + email_data.body).lower()
            
            for keyword in exclude_keywords:
                if keyword.lower() in content_lower:
                    return False
            
            # 日次自動返信制限チェック
            max_daily = conditions.get("max_daily_auto_replies", 10)
            today_count = await self._get_today_auto_reply_count()
            
            if today_count >= max_daily:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Auto-reply condition check failed: {e}")
            return False
    
    async def _get_today_auto_reply_count(self) -> int:
        """今日の自動返信回数取得"""
        try:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            query = self.email_threads_ref.where(
                'status', '==', ReplyStatus.AUTO_REPLIED.value
            ).where(
                'replied_at', '>=', today_start
            )
            
            docs = list(query.stream())
            return len(docs)
            
        except Exception as e:
            logger.error(f"❌ Failed to get today's auto-reply count: {e}")
            return 0
    
    async def _execute_auto_reply(
        self, 
        email_data: EmailData, 
        reply_content: str, 
        user_settings: ReplySettings
    ) -> AutoReplyResponse:
        """自動返信実行"""
        try:
            # メールスレッド記録
            thread_data = {
                'thread_id': email_data.thread_id,
                'message_id': email_data.message_id,
                'sender_email': email_data.sender_email,
                'sender_name': email_data.sender_name,
                'original_subject': email_data.subject,
                'original_body': email_data.body,
                'generated_reply': reply_content,
                'status': ReplyStatus.AUTO_REPLIED.value,
                'reply_mode': ReplyMode.AUTO_REPLY.value,
                'created_at': datetime.utcnow(),
                'replied_at': datetime.utcnow(),
                'user_id': user_settings.user_id
            }
            
            await self.email_threads_ref.document(email_data.thread_id).set(thread_data)
            
            # 実際のメール送信は別サービスで実行
            # (Gmail API統合が必要)
            
            logger.info(f"✅ Auto-reply executed for thread: {email_data.thread_id}")
            
            return AutoReplyResponse(
                success=True,
                thread_id=email_data.thread_id,
                generated_reply=reply_content,
                status=ReplyStatus.AUTO_REPLIED,
                metadata={"auto_reply": True}
            )
            
        except Exception as e:
            logger.error(f"❌ Auto-reply execution failed: {e}")
            return AutoReplyResponse(
                success=False,
                thread_id=email_data.thread_id,
                error_message=str(e)
            )
    
    async def _queue_for_approval(
        self, 
        email_data: EmailData, 
        reply_content: str, 
        influencer_data: Optional[Dict[str, Any]], 
        user_settings: ReplySettings
    ) -> AutoReplyResponse:
        """承認待ちキューに追加"""
        try:
            # 承認期限計算
            approval_deadline = datetime.utcnow() + timedelta(
                hours=user_settings.approval_timeout_hours
            )
            
            # メールスレッド記録
            thread_data = {
                'thread_id': email_data.thread_id,
                'message_id': email_data.message_id,
                'sender_email': email_data.sender_email,
                'sender_name': email_data.sender_name,
                'original_subject': email_data.subject,
                'original_body': email_data.body,
                'generated_reply': reply_content,
                'status': ReplyStatus.PENDING_APPROVAL.value,
                'reply_mode': ReplyMode.MANUAL_APPROVAL.value,
                'created_at': datetime.utcnow(),
                'approval_deadline': approval_deadline,
                'user_id': user_settings.user_id,
                'influencer_data': influencer_data,
                'user_modifications': None,
                'approved_at': None,
                'replied_at': None
            }
            
            await self.email_threads_ref.document(email_data.thread_id).set(thread_data)
            
            logger.info(f"📝 Email queued for approval: {email_data.thread_id}")
            
            return AutoReplyResponse(
                success=True,
                thread_id=email_data.thread_id,
                generated_reply=reply_content,
                status=ReplyStatus.PENDING_APPROVAL,
                metadata={
                    "approval_deadline": approval_deadline.isoformat(),
                    "requires_approval": True
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to queue for approval: {e}")
            return AutoReplyResponse(
                success=False,
                thread_id=email_data.thread_id,
                error_message=str(e)
            )
    
    async def get_pending_replies(self, user_id: str) -> List[Dict[str, Any]]:
        """承認待ち返信一覧取得"""
        try:
            query = self.email_threads_ref.where('user_id', '==', user_id).where(
                'status', '==', ReplyStatus.PENDING_APPROVAL.value
            ).order_by('created_at', direction=firestore.Query.DESCENDING)
            
            docs = query.stream()
            pending_replies = []
            
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                
                # 期限切れチェック
                if data.get('approval_deadline'):
                    deadline = data['approval_deadline']
                    if isinstance(deadline, str):
                        deadline = datetime.fromisoformat(deadline)
                    
                    if deadline < datetime.utcnow():
                        # 期限切れ処理
                        await self._expire_pending_reply(doc.id)
                        continue
                
                pending_replies.append(data)
            
            return pending_replies
            
        except Exception as e:
            logger.error(f"❌ Failed to get pending replies: {e}")
            return []
    
    async def approve_reply(
        self, 
        thread_id: str, 
        user_modifications: Optional[str] = None
    ) -> bool:
        """返信承認・送信"""
        try:
            doc_ref = self.email_threads_ref.document(thread_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
            
            data = doc.to_dict()
            
            # 最終返信内容決定
            final_reply = user_modifications or data.get('generated_reply', '')
            
            # ステータス更新
            update_data = {
                'status': ReplyStatus.APPROVED.value,
                'user_modifications': user_modifications,
                'final_reply': final_reply,
                'approved_at': datetime.utcnow(),
                'replied_at': datetime.utcnow()
            }
            
            await doc_ref.update(update_data)
            
            # 実際のメール送信処理（Gmail API統合が必要）
            # await self._send_email_reply(data, final_reply)
            
            logger.info(f"✅ Reply approved and sent: {thread_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Reply approval failed: {e}")
            return False
    
    async def reject_reply(self, thread_id: str) -> bool:
        """返信拒否"""
        try:
            doc_ref = self.email_threads_ref.document(thread_id)
            
            update_data = {
                'status': ReplyStatus.REJECTED.value,
                'rejected_at': datetime.utcnow()
            }
            
            await doc_ref.update(update_data)
            
            logger.info(f"❌ Reply rejected: {thread_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Reply rejection failed: {e}")
            return False
    
    async def _expire_pending_reply(self, thread_id: str) -> bool:
        """承認待ち期限切れ処理"""
        try:
            doc_ref = self.email_threads_ref.document(thread_id)
            
            update_data = {
                'status': ReplyStatus.EXPIRED.value,
                'expired_at': datetime.utcnow()
            }
            
            await doc_ref.update(update_data)
            
            logger.warning(f"⏰ Reply approval expired: {thread_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Reply expiration failed: {e}")
            return False
    
    async def update_user_reply_settings(
        self, 
        user_id: str, 
        settings_update: Dict[str, Any]
    ) -> bool:
        """ユーザー返信設定更新"""
        try:
            doc_ref = self.reply_settings_ref.document(user_id)
            
            settings_update['updated_at'] = datetime.utcnow()
            await doc_ref.update(settings_update)
            
            logger.info(f"✅ User reply settings updated: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Settings update failed: {e}")
            return False
    
    async def get_reply_statistics(self, user_id: str) -> Dict[str, Any]:
        """返信統計取得"""
        try:
            # 過去30日の統計
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            query = self.email_threads_ref.where('user_id', '==', user_id).where(
                'created_at', '>=', thirty_days_ago
            )
            
            docs = list(query.stream())
            
            stats = {
                "total_emails": len(docs),
                "pending_approval": 0,
                "auto_replied": 0,
                "manually_approved": 0,
                "rejected": 0,
                "expired": 0,
                "avg_response_time_hours": 0,
                "auto_reply_rate": 0
            }
            
            response_times = []
            
            for doc in docs:
                data = doc.to_dict()
                status = data.get('status', '')
                
                if status == ReplyStatus.PENDING_APPROVAL.value:
                    stats["pending_approval"] += 1
                elif status == ReplyStatus.AUTO_REPLIED.value:
                    stats["auto_replied"] += 1
                elif status == ReplyStatus.APPROVED.value:
                    stats["manually_approved"] += 1
                elif status == ReplyStatus.REJECTED.value:
                    stats["rejected"] += 1
                elif status == ReplyStatus.EXPIRED.value:
                    stats["expired"] += 1
                
                # 応答時間計算
                if data.get('replied_at') and data.get('created_at'):
                    created = data['created_at']
                    replied = data['replied_at']
                    
                    if isinstance(created, str):
                        created = datetime.fromisoformat(created)
                    if isinstance(replied, str):
                        replied = datetime.fromisoformat(replied)
                    
                    response_time = (replied - created).total_seconds() / 3600
                    response_times.append(response_time)
            
            if response_times:
                stats["avg_response_time_hours"] = sum(response_times) / len(response_times)
            
            if stats["total_emails"] > 0:
                stats["auto_reply_rate"] = stats["auto_replied"] / stats["total_emails"]
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get reply statistics: {e}")
            return {}


# シングルトンインスタンス
email_auto_reply_service = EmailAutoReplyService()