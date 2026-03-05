from pydantic import BaseModel, HttpUrl
from typing import Optional
from enum import Enum
from uuid import UUID
from datetime import datetime

# ── Enums ────────────────────────────────────────

class ProductType(str, Enum):
    COUPON = "COUPON"

class CouponValueType(str, Enum):
    STRING = "STRING"
    IMAGE = "IMAGE"

# ── Coupon Schemas ───────────────────────────────

class CouponCreate(BaseModel):
    """What admin sends when creating a coupon"""
    name: str
    description: Optional[str] = None
    image_url: str
    cost_price: float
    margin_percentage: float
    value_type: CouponValueType
    coupon_value: str

class CouponUpdate(BaseModel):
    """All fields optional for partial updates"""
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    cost_price: Optional[float] = None
    margin_percentage: Optional[float] = None
    value_type: Optional[CouponValueType] = None
    coupon_value: Optional[str] = None

class CouponPublic(BaseModel):
    """What resellers see - no cost/margin"""
    id: UUID
    name: str
    description: Optional[str]
    image_url: str
    price: float

class CouponAdmin(BaseModel):
    """What admin sees - full data"""
    id: UUID
    name: str
    description: Optional[str]
    image_url: str
    cost_price: float
    margin_percentage: float
    minimum_sell_price: float
    is_sold: bool
    value_type: CouponValueType
    coupon_value: str
    created_at: datetime
    updated_at: datetime

# ── Purchase Schemas ─────────────────────────────

class ResellerPurchaseRequest(BaseModel):
    """What reseller sends to buy a coupon"""
    reseller_price: float

class PurchaseResponse(BaseModel):
    """Returned after successful purchase"""
    product_id: UUID
    final_price: float
    value_type: CouponValueType
    value: str

# ── Auth Schemas ─────────────────────────────────

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class AdminLoginResponse(BaseModel):
    token: str
    username: str

# ── Error Schema ─────────────────────────────────

class ErrorResponse(BaseModel):
    error_code: str
    message: str