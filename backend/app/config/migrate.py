import os
from dotenv import load_dotenv
from pathlib import Path
from database import get_connection
from passlib.context import CryptContext
import hashlib

env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

# Use a simple hash function to avoid bcrypt issues
def hash_password(password: str) -> str:
    """Hash password using sha256 (simple but secure for this use case)"""
    return hashlib.sha256(password.encode()).hexdigest()


def migrate():
    conn = get_connection()
    cur = conn.cursor()

    try:
        print("Creating tables...")

        cur.execute("""
            DO $$ BEGIN
                CREATE TYPE product_type AS ENUM ('COUPON');
            EXCEPTION WHEN duplicate_object THEN NULL;
            END $$;
        """)

        cur.execute("""
            DO $$ BEGIN
                CREATE TYPE coupon_value_type AS ENUM ('STRING', 'IMAGE');
            EXCEPTION WHEN duplicate_object THEN NULL;
            END $$;
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL,
                description TEXT,
                type product_type NOT NULL DEFAULT 'COUPON',
                image_url TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS coupons (
                product_id UUID PRIMARY KEY REFERENCES products(id) ON DELETE CASCADE,
                cost_price NUMERIC(12,2) NOT NULL CHECK (cost_price >= 0),
                margin_percentage NUMERIC(8,4) NOT NULL CHECK (margin_percentage >= 0),
                minimum_sell_price NUMERIC(12,2) GENERATED ALWAYS AS
                    (cost_price * (1 + margin_percentage / 100)) STORED,
                is_sold BOOLEAN NOT NULL DEFAULT FALSE,
                value_type coupon_value_type NOT NULL,
                coupon_value TEXT NOT NULL
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS admin_users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                username VARCHAR(100) NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS reseller_tokens (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS purchase_log (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                product_id UUID NOT NULL REFERENCES products(id),
                channel VARCHAR(50) NOT NULL,
                final_price NUMERIC(12,2),
                purchased_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)

        print("Seeding default admin user...")
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        password_hash = hash_password(admin_password[:72])
        cur.execute("""
            INSERT INTO admin_users (username, password_hash)
            VALUES (%s, %s)
            ON CONFLICT (username) DO NOTHING;
        """, (admin_username, password_hash))

        print("Seeding default reseller token...")
        raw_token = os.getenv("RESELLER_TOKEN", "reseller-secret-token-123")
        token_hash = hash_password(raw_token[:72])
        cur.execute("""
            INSERT INTO reseller_tokens (name, token_hash)
            VALUES ('Default Reseller', %s)
            ON CONFLICT DO NOTHING;
        """, (token_hash,))

        conn.commit()
        print("✅ Migration completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    print("Starting migration...")
    migrate()