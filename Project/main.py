from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.churn import router as churn_router
from routers.customers import router as customer_router
from routers.features import router as features_router
from routers.high_risk import router as high_risk_router
from routers.prediction import router as prediction_router

app = FastAPI(
    title="Customer Retention API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "Customer Retention API is running!"
    }


app.include_router(high_risk_router)
app.include_router(customer_router)
app.include_router(churn_router)
app.include_router(features_router)
app.include_router(prediction_router)