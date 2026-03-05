from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from routes.reseller import router as reseller_router
from routes.admin import router as admin_router

security = HTTPBearer()

app = FastAPI(
    title="Coupon Marketplace API",
    components={"securitySchemes": {"BearerAuth": {"type": "http", "scheme": "bearer"}}}
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reseller_router)
app.include_router(admin_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}