from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import numpy as np
import joblib
import os

app = FastAPI()

class PredictionRequest(BaseModel):
    features: List[float]

class PredictionResponse(BaseModel):
    prediction: List[float]
    probabilities: List[float] = None

model = None

def load_model():
    global model
    model_path = os.getenv("MODEL_PATH", "model.pkl")
    if os.path.exists(model_path):
        model = joblib.load(model_path)
    else:
        class DummyModel:
            def predict(self, X):
                return np.array([0.5] * len(X))
            def predict_proba(self, X):
                return np.array([[0.3, 0.7]] * len(X))
        model = DummyModel()

load_model()

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    try:
        features_array = np.array([request.features])
        prediction = model.predict(features_array)
        probabilities = None
        if hasattr(model, 'predict_proba'):
            probabilities = model.predict_proba(features_array)[0].tolist()
        return PredictionResponse(
            prediction=prediction.tolist(),
            probabilities=probabilities
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy"}
