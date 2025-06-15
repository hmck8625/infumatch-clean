"""
メール自動返信API

@description メール自動返信システムのAPIエンドポイント
@author InfuMatch Development Team
@version 1.0.0
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from services.email_auto_reply_service import (
    email_auto_reply_service,
    EmailData,
    ReplySettings,
    ReplyMode,
    ReplyStatus
)

logger = logging.getLogger(__name__)
router = APIRouter()


# リクエスト・レスポンスモデル
class EmailDataRequest(BaseModel):
    """受信メールデータリクエスト"""
    
    message_id: str = Field(..., description="メッセージID")
    thread_id: str = Field(..., description="スレッドID")
    sender_email: str = Field(..., description="送信者メールアドレス")
    sender_name: Optional[str] = Field(None, description="送信者名")
    subject: str = Field(..., description="件名")
    body: str = Field(..., description="本文")
    received_at: str = Field(..., description="受信時刻（ISO形式）")
    attachments: List[Dict[str, Any]] = Field(default=[], description="添付ファイル")


class ReplySettingsRequest(BaseModel):
    """返信設定リクエスト"""
    
    default_mode: str = Field("manual_approval", description="デフォルト返信モード")
    approval_timeout_hours: int = Field(24, description="承認タイムアウト（時間）", ge=1, le=168)
    custom_signature: str = Field("", description="カスタム署名")
    auto_reply_conditions: Dict[str, Any] = Field(default={}, description="自動返信条件")


class ReplyApprovalRequest(BaseModel):
    """返信承認リクエスト"""
    
    user_modifications: Optional[str] = Field(None, description="ユーザー修正内容")


class ProcessEmailResponse(BaseModel):
    """メール処理レスポンス"""
    
    success: bool
    thread_id: str
    status: str
    generated_reply: Optional[str] = None
    requires_approval: bool = False
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PendingReplyResponse(BaseModel):
    """承認待ち返信レスポンス"""
    
    id: str
    thread_id: str
    sender_email: str
    sender_name: Optional[str]
    original_subject: str
    original_body: str
    generated_reply: str
    created_at: str
    approval_deadline: str
    influencer_data: Optional[Dict[str, Any]] = None


@router.post("/api/v1/email/process", response_model=ProcessEmailResponse)
async def process_incoming_email(
    email_request: EmailDataRequest,
    user_id: str = "default_user"  # 本来はJWT認証から取得
):
    """
    受信メール処理API
    
    受信したメールを解析し、AI返信案を生成して
    ユーザー設定に基づいて処理を実行します。
    """
    try:
        logger.info(f"📧 Processing email from: {email_request.sender_email}")
        
        # EmailDataオブジェクト作成
        email_data = EmailData(
            message_id=email_request.message_id,
            thread_id=email_request.thread_id,
            sender_email=email_request.sender_email,
            sender_name=email_request.sender_name,
            subject=email_request.subject,
            body=email_request.body,
            received_at=datetime.fromisoformat(email_request.received_at.replace('Z', '+00:00')),
            attachments=email_request.attachments
        )
        
        # メール処理実行
        result = await email_auto_reply_service.process_incoming_email(email_data, user_id)
        
        if not result.success:
            raise HTTPException(
                status_code=500,
                detail=result.error_message or "メール処理に失敗しました"
            )
        
        return ProcessEmailResponse(
            success=result.success,
            thread_id=result.thread_id,
            status=result.status.value if result.status else "unknown",
            generated_reply=result.generated_reply,
            requires_approval=result.status == ReplyStatus.PENDING_APPROVAL,
            metadata=result.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Email processing API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"メール処理中にエラーが発生しました: {str(e)}"
        )


@router.get("/api/v1/email/pending-replies", response_model=List[PendingReplyResponse])
async def get_pending_replies(
    user_id: str = "default_user"  # 本来はJWT認証から取得
):
    """
    承認待ち返信一覧取得API
    
    ユーザーの承認待ち返信一覧を取得します。
    """
    try:
        pending_replies = await email_auto_reply_service.get_pending_replies(user_id)
        
        response_list = []
        for reply in pending_replies:
            response_list.append(PendingReplyResponse(
                id=reply['id'],
                thread_id=reply['thread_id'],
                sender_email=reply['sender_email'],
                sender_name=reply.get('sender_name'),
                original_subject=reply['original_subject'],
                original_body=reply['original_body'],
                generated_reply=reply['generated_reply'],
                created_at=reply['created_at'].isoformat() if isinstance(reply['created_at'], datetime) else reply['created_at'],
                approval_deadline=reply['approval_deadline'].isoformat() if isinstance(reply['approval_deadline'], datetime) else reply['approval_deadline'],
                influencer_data=reply.get('influencer_data')
            ))
        
        return response_list
        
    except Exception as e:
        logger.error(f"❌ Get pending replies API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"承認待ち返信取得中にエラーが発生しました: {str(e)}"
        )


@router.post("/api/v1/email/approve-reply/{thread_id}")
async def approve_reply(
    thread_id: str,
    approval_request: ReplyApprovalRequest,
    user_id: str = "default_user"  # 本来はJWT認証から取得
):
    """
    返信承認・送信API
    
    承認待ちの返信を承認し、実際にメール送信を実行します。
    """
    try:
        logger.info(f"✅ Approving reply for thread: {thread_id}")
        
        success = await email_auto_reply_service.approve_reply(
            thread_id=thread_id,
            user_modifications=approval_request.user_modifications
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="指定されたスレッドが見つからないか、処理に失敗しました"
            )
        
        return {
            "success": True,
            "message": "返信が承認され、送信されました",
            "thread_id": thread_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Approve reply API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"返信承認中にエラーが発生しました: {str(e)}"
        )


@router.post("/api/v1/email/reject-reply/{thread_id}")
async def reject_reply(
    thread_id: str,
    user_id: str = "default_user"  # 本来はJWT認証から取得
):
    """
    返信拒否API
    
    承認待ちの返信を拒否します。
    """
    try:
        logger.info(f"❌ Rejecting reply for thread: {thread_id}")
        
        success = await email_auto_reply_service.reject_reply(thread_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="指定されたスレッドが見つからないか、処理に失敗しました"
            )
        
        return {
            "success": True,
            "message": "返信が拒否されました",
            "thread_id": thread_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Reject reply API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"返信拒否中にエラーが発生しました: {str(e)}"
        )


@router.get("/api/v1/email/settings", response_model=ReplySettingsRequest)
async def get_reply_settings(
    user_id: str = "default_user"  # 本来はJWT認証から取得
):
    """
    返信設定取得API
    
    ユーザーの現在の返信設定を取得します。
    """
    try:
        settings = await email_auto_reply_service._get_user_reply_settings(user_id)
        
        return ReplySettingsRequest(
            default_mode=settings.default_mode.value,
            approval_timeout_hours=settings.approval_timeout_hours,
            custom_signature=settings.custom_signature,
            auto_reply_conditions=settings.auto_reply_conditions
        )
        
    except Exception as e:
        logger.error(f"❌ Get reply settings API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"返信設定取得中にエラーが発生しました: {str(e)}"
        )


@router.post("/api/v1/email/settings")
async def update_reply_settings(
    settings_request: ReplySettingsRequest,
    user_id: str = "default_user"  # 本来はJWT認証から取得
):
    """
    返信設定更新API
    
    ユーザーの返信設定を更新します。
    """
    try:
        logger.info(f"⚙️ Updating reply settings for user: {user_id}")
        
        # 設定データ準備
        settings_update = {
            "default_mode": settings_request.default_mode,
            "approval_timeout_hours": settings_request.approval_timeout_hours,
            "custom_signature": settings_request.custom_signature,
            "auto_reply_conditions": settings_request.auto_reply_conditions
        }
        
        success = await email_auto_reply_service.update_user_reply_settings(
            user_id=user_id,
            settings_update=settings_update
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="設定の更新に失敗しました"
            )
        
        return {
            "success": True,
            "message": "返信設定が更新されました"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Update reply settings API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"設定更新中にエラーが発生しました: {str(e)}"
        )


@router.get("/api/v1/email/statistics", response_model=Dict[str, Any])
async def get_reply_statistics(
    user_id: str = "default_user"  # 本来はJWT認証から取得
):
    """
    返信統計情報取得API
    
    ユーザーの返信統計情報を取得します。
    """
    try:
        stats = await email_auto_reply_service.get_reply_statistics(user_id)
        
        return {
            "success": True,
            "statistics": stats,
            "period": "過去30日間",
            "user_id": user_id
        }
        
    except Exception as e:
        logger.error(f"❌ Get reply statistics API error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"統計情報取得中にエラーが発生しました: {str(e)}"
        )


@router.get("/api/v1/email/health")
async def get_email_service_health():
    """
    メール自動返信サービスのヘルスチェックAPI
    """
    try:
        # 基本的なヘルスチェック
        health_status = {
            "service": "EmailAutoReplyService",
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "firestore": "connected",
                "negotiation_agent": "available",
                "email_processing": "operational"
            }
        }
        
        # より詳細なチェックを追加する場合
        # health_status = await email_auto_reply_service.health_check()
        
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Email service health check failed: {e}")
        return {
            "service": "EmailAutoReplyService",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# テスト用エンドポイント
@router.post("/api/v1/email/test-reply-generation")
async def test_reply_generation(
    test_email: EmailDataRequest,
    user_id: str = "default_user"
):
    """
    返信生成テストAPI
    
    実際の送信は行わず、返信案の生成のみをテストします。
    """
    try:
        logger.info("🧪 Testing reply generation")
        
        # EmailDataオブジェクト作成
        email_data = EmailData(
            message_id=test_email.message_id,
            thread_id=test_email.thread_id,
            sender_email=test_email.sender_email,
            sender_name=test_email.sender_name,
            subject=test_email.subject,
            body=test_email.body,
            received_at=datetime.fromisoformat(test_email.received_at.replace('Z', '+00:00')),
            attachments=test_email.attachments
        )
        
        # ユーザー設定取得
        user_settings = await email_auto_reply_service._get_user_reply_settings(user_id)
        
        # インフルエンサー特定
        influencer_data = await email_auto_reply_service._identify_influencer(
            email_data.sender_email
        )
        
        # 返信案生成
        generated_reply = await email_auto_reply_service._generate_reply_draft(
            email_data,
            influencer_data,
            user_settings
        )
        
        return {
            "success": True,
            "generated_reply": generated_reply,
            "influencer_identified": influencer_data is not None,
            "influencer_data": influencer_data,
            "test_mode": True
        }
        
    except Exception as e:
        logger.error(f"❌ Test reply generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"テスト実行中にエラーが発生しました: {str(e)}"
        )