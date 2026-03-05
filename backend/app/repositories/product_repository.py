from config.database import get_connection

class ProductRepository:

    def get_all_available(self):
        """Get all unsold products - for resellers/customers"""
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT
                    p.id,
                    p.name,
                    p.description,
                    p.image_url,
                    c.minimum_sell_price AS price
                FROM products p
                JOIN coupons c ON c.product_id = p.id
                WHERE c.is_sold = FALSE
                ORDER BY p.created_at DESC
            """)
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    def get_all_admin(self):
        """Get all products with full data - for admin"""
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT
                    p.id,
                    p.name,
                    p.description,
                    p.image_url,
                    p.created_at,
                    p.updated_at,
                    c.cost_price,
                    c.margin_percentage,
                    c.minimum_sell_price,
                    c.is_sold,
                    c.value_type,
                    c.coupon_value
                FROM products p
                JOIN coupons c ON c.product_id = p.id
                ORDER BY p.created_at DESC
            """)
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    def get_by_id_full(self, product_id: str):
        """Get single product with full data"""
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT
                    p.id,
                    p.name,
                    p.description,
                    p.image_url,
                    p.created_at,
                    p.updated_at,
                    c.cost_price,
                    c.margin_percentage,
                    c.minimum_sell_price,
                    c.is_sold,
                    c.value_type,
                    c.coupon_value
                FROM products p
                JOIN coupons c ON c.product_id = p.id
                WHERE p.id = %s
            """, (product_id,))
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()

    def create_coupon(self, data: dict):
        """Create a new coupon product"""
        conn = get_connection()
        cur = conn.cursor()
        try:
            # Insert base product
            cur.execute("""
                INSERT INTO products (name, description, type, image_url)
                VALUES (%s, %s, 'COUPON', %s)
                RETURNING id
            """, (data["name"], data.get("description"), data["image_url"]))

            product_id = cur.fetchone()["id"]

            # Insert coupon details
            cur.execute("""
                INSERT INTO coupons
                    (product_id, cost_price, margin_percentage, value_type, coupon_value)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                product_id,
                data["cost_price"],
                data["margin_percentage"],
                data["value_type"],
                data["coupon_value"]
            ))

            conn.commit()
            return self.get_by_id_full(product_id)
        except:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    def update_coupon(self, product_id: str, data: dict):
        """Update a coupon - only fields that were provided"""
        conn = get_connection()
        cur = conn.cursor()
        try:
            # Update products table fields
            product_fields = {k: v for k, v in data.items()
                            if k in ["name", "description", "image_url"] and v is not None}

            if product_fields:
                sets = ", ".join([f"{k} = %s" for k in product_fields])
                values = list(product_fields.values()) + [product_id]
                cur.execute(f"UPDATE products SET {sets} WHERE id = %s", values)

            # Update coupons table fields
            coupon_fields = {k: v for k, v in data.items()
                           if k in ["cost_price", "margin_percentage", "value_type", "coupon_value"]
                           and v is not None}

            if coupon_fields:
                sets = ", ".join([f"{k} = %s" for k in coupon_fields])
                values = list(coupon_fields.values()) + [product_id]
                cur.execute(f"UPDATE coupons SET {sets} WHERE product_id = %s", values)

            conn.commit()
            return self.get_by_id_full(product_id)
        except:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    def delete(self, product_id: str):
     """Delete a product - also removes purchase log entries"""
     conn = get_connection()
     cur = conn.cursor()
     try:
        # Delete purchase log entries first
        cur.execute(
            "DELETE FROM purchase_log WHERE product_id = %s",
            (product_id,)
        )
        # Then delete the product
        cur.execute(
            "DELETE FROM products WHERE id = %s",
            (product_id,)
        )
        deleted = cur.rowcount > 0
        conn.commit()
        return deleted
     except:
        conn.rollback()
        raise
     finally:
        cur.close()
        conn.close()

    def purchase_atomic(self, product_id: str, final_price: float, channel: str):
        """
        Atomically purchase a product.
        Uses FOR UPDATE to lock the row and prevent race conditions.
        """
        conn = get_connection()
        cur = conn.cursor()
        try:
            # Lock the row so no other request can buy it at the same time
            cur.execute("""
                SELECT
                    p.id,
                    c.minimum_sell_price,
                    c.is_sold,
                    c.value_type,
                    c.coupon_value
                FROM products p
                JOIN coupons c ON c.product_id = p.id
                WHERE p.id = %s
                FOR UPDATE
            """, (product_id,))

            product = cur.fetchone()

            if not product:
                return {"error": "PRODUCT_NOT_FOUND"}

            if product["is_sold"]:
                return {"error": "PRODUCT_ALREADY_SOLD"}

            if final_price is not None and final_price < float(product["minimum_sell_price"]):
                return {"error": "RESELLER_PRICE_TOO_LOW"}

            # Mark as sold
            cur.execute("""
                UPDATE coupons SET is_sold = TRUE WHERE product_id = %s
            """, (product_id,))

            # Write to audit log
            cur.execute("""
                INSERT INTO purchase_log (product_id, channel, final_price)
                VALUES (%s, %s, %s)
            """, (product_id, channel, final_price or float(product["minimum_sell_price"])))

            conn.commit()

            return {
                "success": True,
                "value_type": product["value_type"],
                "coupon_value": product["coupon_value"],
                "minimum_sell_price": float(product["minimum_sell_price"])
            }
        except:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

product_repository = ProductRepository()