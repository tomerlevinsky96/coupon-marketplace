import os
from dotenv import load_dotenv
from pathlib import Path
from database import get_connection
from passlib.context import CryptContext

env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

pwd_context = CryptContext(schemes=["bcrypt"])

conn = get_connection()
cur = conn.cursor()

admin_username = os.getenv("ADMIN_USERNAME", "admin")
admin_password = os.getenv("ADMIN_PASSWORD")

cur.execute(
    "UPDATE admin_users SET password_hash = %s WHERE username = %s",
    (pwd_context.hash(admin_password), admin_username)
)
conn.commit()
print(f"Password reset successfully ")
cur.close()
conn.close()