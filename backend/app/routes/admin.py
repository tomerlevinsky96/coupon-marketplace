from fastapi import APIRouter, Depends, HTTPException
from middleware.auth import require_admin
from services.product_service import product_service
from repositories.auth_repository import auth_repository
from models.schemas import (
    CouponCreate, CouponUpdate,
    AdminLoginRequest
)
import secrets

router = APIRouter(prefix="/api/admin", tags=["Admin API"])

# ── Auth ─────────────────────────────────────────

@router.post("/auth/login")
def admin_login(body: AdminLoginRequest):
    """Admin login - returns JWT token"""
    result = auth_repository.admin_login(body.username, body.password)
    if not result:
        raise HTTPException(status_code=401, detail={
            "error_code": "UNAUTHORIZED",
            "message": "Invalid credentials"
        })
    return result

# ── Products ─────────────────────────────────────

@router.get("/products")
def get_all_products(admin=Depends(require_admin)):
    """Get all products with full data"""
    return product_service.get_all_admin()

# ── Public Customer Endpoints (no auth needed) ────
@router.get("/public/products")
def get_public_products():
    """Public endpoint for customers - no auth required"""
    return product_service.get_available_products()




@router.get("/products/{product_id}")
def get_product(product_id: str, admin=Depends(require_admin)):
    """Get single product with full data"""
    product = product_service.get_by_id_admin(product_id)
    if not product:
        raise HTTPException(status_code=404, detail={
            "error_code": "PRODUCT_NOT_FOUND",
            "message": "Product not found"
        })
    return product

@router.post("/products", status_code=201)
def create_coupon(body: CouponCreate, admin=Depends(require_admin)):
    """Create a new coupon"""
    return product_service.create_coupon(body.dict())

@router.patch("/products/{product_id}")
def update_coupon(
    product_id: str,
    body: CouponUpdate,
    admin=Depends(require_admin)
):
    """Update a coupon"""
    result = product_service.update_coupon(
        product_id,
        body.dict(exclude_none=True)
    )
    if not result:
        raise HTTPException(status_code=404, detail={
            "error_code": "PRODUCT_NOT_FOUND",
            "message": "Product not found"
        })
    return result

@router.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: str, admin=Depends(require_admin)):
    """Delete a product"""
    deleted = product_service.delete_product(product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail={
            "error_code": "PRODUCT_NOT_FOUND",
            "message": "Product not found"
        })

# ── Direct Purchase (customers) ───────────────────











@router.post("/products/{product_id}/purchase")
def direct_purchase(product_id: str):
    """Customer purchases directly at minimum sell price"""
    result = product_service.direct_purchase(product_id)

    if "error" in result:
        error_map = {
            "PRODUCT_NOT_FOUND": 404,
            "PRODUCT_ALREADY_SOLD": 409
        }
        raise HTTPException(
            status_code=error_map.get(result["error"], 400),
            detail={
                "error_code": result["error"],
                "message": result["error"].replace("_", " ").title()
            }
        )
    return result

# ── Reseller Token Management ─────────────────────

@router.get("/reseller-tokens")
def list_tokens(admin=Depends(require_admin)):
    """List all reseller tokens"""
    return auth_repository.list_reseller_tokens()

@router.post("/reseller-tokens", status_code=201)
def create_token(body: dict, admin=Depends(require_admin)):
    """Create a new reseller token"""
    name = body.get("name")
    if not name:
        raise HTTPException(status_code=400, detail={
            "error_code": "VALIDATION_ERROR",
            "message": "name is required"
        })
    raw_token = secrets.token_hex(32)
    token = auth_repository.create_reseller_token(name, raw_token)
    return {
        **dict(token),
        "token": raw_token,
        "note": "Store this token securely. It will not be shown again."
    }

