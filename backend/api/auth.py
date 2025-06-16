"""
簡易認証モジュール

本番環境では適切な認証システムに置き換える必要があります
"""

from fastapi import HTTPException, Header
from typing import Optional, Dict

async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, str]:
    """
    現在のユーザー情報を取得（簡易版）
    
    本番環境では以下を実装:
    - JWTトークンの検証
    - Google OAuth認証
    - セッション管理
    """
    
    # 開発環境用の簡易実装
    # Authorizationヘッダーからメールアドレスを取得
    if authorization and authorization.startswith("Bearer "):
        # Bearer token形式: "Bearer user@example.com"
        email = authorization.replace("Bearer ", "").strip()
        if "@" in email:
            return {"email": email}
    
    # デフォルトユーザー（開発用）
    return {"email": "test@example.com"}