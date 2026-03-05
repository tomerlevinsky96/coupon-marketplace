from fastapi import APIRouter, Depends
from middleware.auth import require_reseller
from services.product_service import product_service
from models.schemas import ResellerPurchaseRequest

router = APIRouter(prefix="/api/v1", tags=["Reseller API"])

@router.get("/products")
def get_products(reseller=Depends(require_reseller)):
    """Get all available (unsold) products"""
    return product_service.get_available_products()

@router.get("/products/{product_id}")
def get_product(product_id: str, reseller=Depends(require_reseller)):
    """Get a single product by ID"""
    products = product_service.get_available_products()
    product = next((p for p in products if str(p["id"]) == product_id), None)

    if not product:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail={
            "error_code": "PRODUCT_NOT_FOUND",
            "message": f"Product {product_id} not found"
        })

    return product

@router.post("/products/{product_id}/purchase")
def purchase_product(
    product_id: str,
    body: ResellerPurchaseRequest,
    reseller=Depends(require_reseller)
):
    """Purchase a product as a reseller"""
    result = product_service.reseller_purchase(product_id, body.reseller_price)

    if "error" in result:
        from fastapi import HTTPException
        error_map = {
            "PRODUCT_NOT_FOUND": 404,
            "PRODUCT_ALREADY_SOLD": 409,
            "RESELLER_PRICE_TOO_LOW": 400
        }
        status_code = error_map.get(result["error"], 400)
        raise HTTPException(status_code=status_code, detail={
            "error_code": result["error"],
            "message": {
                "PRODUCT_NOT_FOUND": "Product not found",
                "PRODUCT_ALREADY_SOLD": "This product has already been sold",
                "RESELLER_PRICE_TOO_LOW": "reseller_price is below minimum sell price"
            }.get(result["error"])
        })

    return result