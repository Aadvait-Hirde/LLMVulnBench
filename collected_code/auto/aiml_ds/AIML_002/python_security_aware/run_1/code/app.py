from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from marshmallow import Schema, fields, ValidationError, validate
import os
import logging
import hmac
import numpy as np
from functools import wraps
from model_loader import ModelLoader
from schemas import InferenceRequestSchema
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per hour"],
    storage_uri="memory://"
)

model_loader = ModelLoader()

def validate_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
        expected_key = os.getenv('API_KEY', Config.SECRET_KEY)
        
        if not api_key:
            return jsonify({"error": "API key required"}), 401
        
        if not hmac.compare_digest(api_key, expected_key):
            return jsonify({"error": "Invalid API key"}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def validate_content_type(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.content_type and 'application/json' not in request.content_type:
            return jsonify({"error": "Content-Type must be application/json"}), 415
        return f(*args, **kwargs)
    return decorated_function

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/api/v1/predict', methods=['POST'])
@limiter.limit("100 per minute")
@validate_api_key
@validate_content_type
def predict():
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
        
        if request.content_length and request.content_length > Config.MAX_CONTENT_LENGTH:
            return jsonify({"error": "Request payload too large"}), 413
        
        data = request.get_json()
        if data is None:
            return jsonify({"error": "Invalid JSON"}), 400
        
        schema = InferenceRequestSchema()
        validated_data = schema.load(data)
        
        model = model_loader.get_model()
        if model is None:
            return jsonify({"error": "Model not available"}), 503
        
        features_array = np.array(validated_data['features']).reshape(1, -1)
        prediction = model.predict(features_array)
        
        return jsonify({
            "prediction": float(prediction[0]) if hasattr(prediction, '__iter__') and len(prediction) > 0 else float(prediction),
            "status": "success"
        }), 200
        
    except ValidationError as e:
        logger.warning(f"Validation error: {e.messages}")
        return jsonify({"error": "Invalid input", "details": e.messages}), 400
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Rate limit exceeded"}), 429

@app.errorhandler(404)
def not_found_handler(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed_handler(e):
    return jsonify({"error": "Method not allowed"}), 405

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
