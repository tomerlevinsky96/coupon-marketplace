from config.database import get_connection
from jose import jwt
import os
from datetime import datetime, timedelta
import hashlib

def hash_password(password: str) -> str:
    """Hash password using sha256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return hash_password(plain_password[:72]) == hashed_password

class AuthRepository:

    def verify_reseller_token(self, raw_token: str):
        """
        Check if bearer token matches any active reseller token.
        Tokens are stored hashed so we compare against each one.
        """
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, name, token_hash 
                FROM reseller_tokens 
                WHERE is_active = TRUE
            """)
            tokens = cur.fetchall()

            for token in tokens:
                if verify_password(raw_token, token["token_hash"]):
                    return {"id": token["id"], "name": token["name"]}

            return None
        finally:
            cur.close()
            conn.close()

    def admin_login(self, username: str, password: str):
        """Verify admin credentials and return JWT token"""
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, username, password_hash 
                FROM admin_users 
                WHERE username = %s
            """, (username,))

            admin = cur.fetchone()

            if not admin:
                return None

            if not verify_password(password, admin["password_hash"]):
                return None

            # Create JWT token
            token = jwt.encode(
                {
                    "id": str(admin["id"]),
                    "username": admin["username"],
                    "role": "admin",
                    "exp": datetime.utcnow() + timedelta(hours=8)
                },
                os.getenv("JWT_SECRET", "secret"),
                algorithm="HS256"
            )

            return {"token": token, "username": admin["username"]}
        finally:
            cur.close()
            conn.close()

    def create_reseller_token(self, name: str, raw_token: str):
        """Create a new reseller token - stored hashed"""
        conn = get_connection()
        cur = conn.cursor()
        try:
            token_hash = pwd_context.hash(raw_token)
            cur.execute("""
                INSERT INTO reseller_tokens (name, token_hash)
                VALUES (%s, %s)
                RETURNING id, name, created_at
            """, (name, token_hash))
            result = cur.fetchone()
            conn.commit()
            return result
        except:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    def list_reseller_tokens(self):
        """List all reseller tokens - admin only"""
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, name, is_active, created_at 
                FROM reseller_tokens 
                ORDER BY created_at DESC
            """)
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

auth_repository = AuthRepository()