import pickle
import os

class ModelLoader:
    def __init__(self, model_path='models/model.pkl'):
        self.model_path = model_path
        self._model = None
    
    def get_model(self):
        if self._model is None:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model file not found: {self.model_path}")
            with open(self.model_path, 'rb') as f:
                self._model = pickle.load(f)
        return self._model
