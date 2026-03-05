from repositories.product_repository import product_repository

class ProductService:

    def get_available_products(self):
        """Get all unsold products - public view"""
        products = product_repository.get_all_available()
        return [self._to_public(p) for p in products]

    def get_all_admin(self):
        """Get all products - admin view with full data"""
        return product_repository.get_all_admin()

    def get_by_id_admin(self, product_id: str):
        """Get single product - admin view"""
        return product_repository.get_by_id_full(product_id)

    def create_coupon(self, data: dict):
        """Create a new coupon - admin only"""
        return product_repository.create_coupon(data)

    def update_coupon(self, product_id: str, data: dict):
        """Update coupon - admin only"""
        # Block any attempt to set server-calculated fields
        data.pop("minimum_sell_price", None)
        data.pop("is_sold", None)

        existing = product_repository.get_by_id_full(product_id)
        if not existing:
            return None

        return product_repository.update_coupon(product_id, data)

    def delete_product(self, product_id: str):
        """Delete product - admin only"""
        existing = product_repository.get_by_id_full(product_id)
        if not existing:
            return False
        return product_repository.delete(product_id)

    def reseller_purchase(self, product_id: str, reseller_price: float):
        """Purchase via reseller channel"""
        result = product_repository.purchase_atomic(
            product_id, reseller_price, "RESELLER"
        )

        if "error" in result:
            return result

        return {
            "success": True,
            "product_id": product_id,
            "final_price": reseller_price,
            "value_type": result["value_type"],
            "value": result["coupon_value"]
        }

    def direct_purchase(self, product_id: str):
        """Purchase via direct customer channel"""
        result = product_repository.purchase_atomic(
            product_id, None, "DIRECT"
        )

        if "error" in result:
            return result

        return {
            "success": True,
            "product_id": product_id,
            "final_price": result["minimum_sell_price"],
            "value_type": result["value_type"],
            "value": result["coupon_value"]
        }

    def _to_public(self, product):
        """Strip sensitive fields for public API"""
        return {
            "id": product["id"],
            "name": product["name"],
            "description": product["description"],
            "image_url": product["image_url"],
            "price": float(product["price"])
        }

product_service = ProductService()