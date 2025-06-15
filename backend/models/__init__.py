"""
データモデル定義

@description Pydantic モデルを使用したデータ構造の定義
型安全性とバリデーションを提供

@author InfuMatch Development Team
@version 1.0.0
"""

from .influencer import InfluencerModel, InfluencerCreate, InfluencerUpdate
from .company import CompanyModel, CompanyCreate, CompanyUpdate
from .campaign import CampaignModel, CampaignCreate, CampaignUpdate
from .negotiation import NegotiationModel, NegotiationCreate, NegotiationUpdate
from .message import MessageModel, MessageCreate, MessageUpdate
from .common import BaseModel, TimestampMixin, StatusMixin

__all__ = [
    # Base models
    "BaseModel",
    "TimestampMixin", 
    "StatusMixin",
    
    # Influencer models
    "InfluencerModel",
    "InfluencerCreate",
    "InfluencerUpdate",
    
    # Company models
    "CompanyModel",
    "CompanyCreate", 
    "CompanyUpdate",
    
    # Campaign models
    "CampaignModel",
    "CampaignCreate",
    "CampaignUpdate",
    
    # Negotiation models
    "NegotiationModel",
    "NegotiationCreate",
    "NegotiationUpdate",
    
    # Message models
    "MessageModel",
    "MessageCreate",
    "MessageUpdate",
]