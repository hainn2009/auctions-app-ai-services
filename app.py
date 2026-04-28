from pathlib import Path

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from reporting import AuctionReport, AuctionReportRequest, build_auction_report, sample_auctions

app = FastAPI(title="Auction AI Services", version="1.1.0")


def _load_model():
    model_path = Path(__file__).resolve().parent / "model" / "model.pkl"
    if not model_path.exists():
        return None
    return joblib.load(model_path)


model = _load_model()


class PredictionInput(BaseModel):
    start_price: float
    bid_count: int
    avg_bid_interval: float
    item_popularity: float


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "service": "auction-ai-services",
    }


@app.post("/predict")
def predict_bid(data: PredictionInput):
    if model is None:
        raise HTTPException(status_code=503, detail="Model is not loaded")

    X = np.array([[data.start_price, data.bid_count, data.avg_bid_interval, data.item_popularity]])
    y_pred = model.predict(X)
    return {"suggested_bid": round(float(y_pred[0]), 2)}


@app.post("/analytics/summary", response_model=AuctionReport)
def analytics_summary(payload: AuctionReportRequest):
    return build_auction_report(payload.auctions, payload.top_n)


@app.get("/analytics/sample", response_model=AuctionReport)
def analytics_sample():
    return build_auction_report(sample_auctions(), top_n=5)
