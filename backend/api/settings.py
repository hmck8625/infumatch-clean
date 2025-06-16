"""
ユーザー設定管理API

企業ユーザーの設定情報を管理するエンドポイント
"""

from typing import Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from core.database import get_firestore_client
from services.database_service import DatabaseService
from api.auth import get_current_user

router = APIRouter(prefix="/api/settings", tags=["settings"])

# Pydanticモデル
class CompanyInfo(BaseModel):
    companyName: str = ""
    industry: str = ""
    employeeCount: str = ""
    website: str = ""
    description: str = ""
    contactPerson: Optional[str] = ""
    contactEmail: Optional[str] = ""

class ProductInfo(BaseModel):
    id: str
    name: str
    category: str = ""
    targetAudience: str = ""
    priceRange: str = ""
    description: str = ""

class NegotiationSettings(BaseModel):
    preferredTone: str = "professional"
    responseTimeExpectation: str = "24時間以内"
    budgetFlexibility: str = "medium"
    decisionMakers: list[str] = Field(default_factory=list)
    communicationPreferences: list[str] = Field(default_factory=lambda: ["email"])
    specialInstructions: Optional[str] = ""
    keyPriorities: Optional[list[str]] = Field(default_factory=list)
    avoidTopics: Optional[list[str]] = Field(default_factory=list)

class MatchingSettings(BaseModel):
    priorityCategories: list[str] = Field(default_factory=list)
    minSubscribers: int = 1000
    maxSubscribers: int = 1000000
    minEngagementRate: float = 2.0
    excludeCategories: list[str] = Field(default_factory=list)
    geographicFocus: list[str] = Field(default_factory=lambda: ["日本"])
    priorityKeywords: Optional[list[str]] = Field(default_factory=list)
    excludeKeywords: Optional[list[str]] = Field(default_factory=list)

class UserSettings(BaseModel):
    userId: str
    companyInfo: CompanyInfo
    products: list[ProductInfo] = Field(default_factory=list)
    negotiationSettings: NegotiationSettings
    matchingSettings: MatchingSettings
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class UserSettingsUpdate(BaseModel):
    companyInfo: Optional[CompanyInfo] = None
    products: Optional[list[ProductInfo]] = None
    negotiationSettings: Optional[NegotiationSettings] = None
    matchingSettings: Optional[MatchingSettings] = None

@router.get("", response_model=UserSettings)
async def get_user_settings(current_user: dict = Depends(get_current_user)):
    """
    現在のユーザーの設定を取得
    """
    try:
        user_email = current_user.get("email")
        if not user_email:
            raise HTTPException(status_code=401, detail="User email not found")
        
        db = get_firestore_client()
        doc_ref = db.collection("user_settings").document(user_email)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            return UserSettings(**data)
        else:
            # デフォルト設定を返す
            now = datetime.now(timezone.utc).isoformat()
            default_settings = UserSettings(
                userId=user_email,
                companyInfo=CompanyInfo(),
                negotiationSettings=NegotiationSettings(),
                matchingSettings=MatchingSettings(),
                createdAt=now,
                updatedAt=now
            )
            return default_settings
            
    except Exception as e:
        print(f"Error getting user settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("", response_model=UserSettings)
async def update_user_settings(
    settings: UserSettingsUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    ユーザーの設定を更新
    """
    try:
        user_email = current_user.get("email")
        if not user_email:
            raise HTTPException(status_code=401, detail="User email not found")
        
        db = get_firestore_client()
        doc_ref = db.collection("user_settings").document(user_email)
        
        # 既存の設定を取得
        doc = doc_ref.get()
        if doc.exists:
            existing_data = doc.to_dict()
        else:
            # 新規作成の場合
            now = datetime.now(timezone.utc).isoformat()
            existing_data = {
                "userId": user_email,
                "createdAt": now
            }
        
        # 更新データを準備
        update_data = existing_data.copy()
        
        # 各フィールドを更新
        if settings.companyInfo is not None:
            update_data["companyInfo"] = settings.companyInfo.dict()
        if settings.products is not None:
            update_data["products"] = [p.dict() for p in settings.products]
        if settings.negotiationSettings is not None:
            update_data["negotiationSettings"] = settings.negotiationSettings.dict()
        if settings.matchingSettings is not None:
            update_data["matchingSettings"] = settings.matchingSettings.dict()
        
        # 更新日時を設定
        update_data["updatedAt"] = datetime.now(timezone.utc).isoformat()
        
        # Firestoreに保存
        doc_ref.set(update_data)
        
        # 保存したデータを返す
        return UserSettings(**update_data)
        
    except Exception as e:
        print(f"Error updating user settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("")
async def delete_user_settings(current_user: dict = Depends(get_current_user)):
    """
    ユーザーの設定を削除
    """
    try:
        user_email = current_user.get("email")
        if not user_email:
            raise HTTPException(status_code=401, detail="User email not found")
        
        db = get_firestore_client()
        doc_ref = db.collection("user_settings").document(user_email)
        doc_ref.delete()
        
        return {"success": True, "message": "Settings deleted successfully"}
        
    except Exception as e:
        print(f"Error deleting user settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/section/{section}")
async def update_settings_section(
    section: str,
    data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """
    設定の特定セクションを更新
    """
    try:
        user_email = current_user.get("email")
        if not user_email:
            raise HTTPException(status_code=401, detail="User email not found")
        
        valid_sections = ["companyInfo", "products", "negotiationSettings", "matchingSettings"]
        if section not in valid_sections:
            raise HTTPException(status_code=400, detail=f"Invalid section: {section}")
        
        db = get_firestore_client()
        doc_ref = db.collection("user_settings").document(user_email)
        
        # 既存の設定を取得
        doc = doc_ref.get()
        if doc.exists:
            existing_data = doc.to_dict()
        else:
            now = datetime.now(timezone.utc).isoformat()
            existing_data = {
                "userId": user_email,
                "createdAt": now,
                "companyInfo": {},
                "products": [],
                "negotiationSettings": {},
                "matchingSettings": {}
            }
        
        # セクションを更新
        existing_data[section] = data
        existing_data["updatedAt"] = datetime.now(timezone.utc).isoformat()
        
        # 保存
        doc_ref.set(existing_data)
        
        return {
            "success": True,
            "message": f"{section} updated successfully",
            "data": existing_data
        }
        
    except Exception as e:
        print(f"Error updating settings section: {e}")
        raise HTTPException(status_code=500, detail=str(e))