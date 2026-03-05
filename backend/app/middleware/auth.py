from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from repositories.auth_repository import auth_repository
from jose import jwt, JWTError
import os

bearer_scheme = HTTPBearer()

def require_reseller(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    reseller = auth_repository.verify_reseller_token(token)
    if not reseller:
        raise HTTPException(status_code=401, detail={
            "error_code": "UNAUTHORIZED",
            "message": "Invalid or inactive reseller token"
        })
    return reseller

def require_admin(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            os.getenv("JWT_SECRET", "secret"),
            algorithms=["HS256"]
        )
        if payload.get("role") != "admin":
            raise HTTPException(status_code=401, detail={
                "error_code": "UNAUTHORIZED",
                "message": "Not an admin"
            })
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail={
            "error_code": "UNAUTHORIZED",
            "message": "Invalid or expired token"
        })