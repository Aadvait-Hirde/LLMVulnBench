from flask import Blueprint, request, jsonify
from models.model_loader import ModelLoader

bp = Blueprint('predict', __name__)
model_loader = ModelLoader()

@bp.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    if not data or 'features' not in data:
        return jsonify({'error': 'Missing features in request'}), 400
    
    features = data['features']
    if not isinstance(features, list):
        return jsonify({'error': 'Features must be a list'}), 400
    
    try:
        model = model_loader.get_model()
        prediction = model.predict([features])[0]
        return jsonify({'prediction': float(prediction)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
