from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import joblib
import numpy as np
import os
import logging
from functools import wraps
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(32).hex())
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per hour"],
    storage_uri="memory://"
)

MODEL_PATH = os.environ.get('MODEL_PATH', 'model.pkl')
model = None

def load_model():
    global model
    if model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
        model = joblib.load(MODEL_PATH)
    return model

def validate_json(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        try:
            data = request.get_json()
            if data is None:
                return jsonify({'error': 'Invalid JSON'}), 400
        except Exception:
            return jsonify({'error': 'Invalid JSON format'}), 400
        return f(*args, **kwargs)
    return decorated_function

def validate_feature_vector(features):
    if not isinstance(features, list):
        return False, "Features must be a list"
    if len(features) == 0:
        return False, "Features cannot be empty"
    if not all(isinstance(x, (int, float)) for x in features):
        return False, "All features must be numeric"
    if len(features) > 10000:
        return False, "Feature vector too large"
    return True, None

@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Type'] = 'application/json'
    return response

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({'error': 'Rate limit exceeded'}), 429

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

@app.route('/predict', methods=['POST'])
@limiter.limit("10 per minute")
@validate_json
def predict():
    try:
        data = request.get_json()
        
        if 'features' not in data:
            return jsonify({'error': 'Missing required field: features'}), 400
        
        features = data['features']
        is_valid, error_msg = validate_feature_vector(features)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        model_instance = load_model()
        feature_array = np.array(features, dtype=np.float64).reshape(1, -1)
        
        prediction = model_instance.predict(feature_array)
        
        if hasattr(prediction, 'tolist'):
            prediction_result = prediction.tolist()
        else:
            prediction_result = float(prediction[0]) if len(prediction) == 1 else prediction.tolist()
        
        logger.info(f"Prediction successful for {len(features)} features")
        
        return jsonify({
            'prediction': prediction_result,
            'status': 'success'
        }), 200
        
    except FileNotFoundError as e:
        logger.error(f"Model loading error: {str(e)}")
        return jsonify({'error': 'Model unavailable'}), 503
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        return jsonify({'error': 'Prediction failed'}), 500

@app.route('/health', methods=['GET'])
def health():
    try:
        load_model()
        return jsonify({'status': 'healthy'}), 200
    except Exception:
        return jsonify({'status': 'unhealthy'}), 503

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
