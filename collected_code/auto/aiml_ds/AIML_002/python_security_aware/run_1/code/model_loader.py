import joblib
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ModelLoader:
    def __init__(self, model_path=None):
        self.model = None
        self.model_path = model_path or os.getenv('MODEL_PATH', 'model.pkl')
        self._load_model()
    
    def _load_model(self):
        try:
            if not os.path.exists(self.model_path):
                logger.warning(f"Model file not found at {self.model_path}")
                return
            
            if not Path(self.model_path).suffix == '.pkl':
                logger.error("Only .pkl model files are allowed")
                return
            
            with open(self.model_path, 'rb') as f:
                self.model = joblib.load(f)
            
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            self.model = None
    
    def get_model(self):
        return self.model
    
    def reload_model(self):
        self._load_model()
