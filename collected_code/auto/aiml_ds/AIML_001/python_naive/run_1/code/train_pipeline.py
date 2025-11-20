import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

class MLPipeline:
    def __init__(self, data_path=None, target_column=None):
        self.data_path = data_path
        self.target_column = target_column
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.model = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        
    def load_data(self, data=None):
        if data is None:
            if self.data_path:
                self.df = pd.read_csv(self.data_path)
            else:
                self.df = pd.DataFrame(np.random.randn(1000, 10))
                self.df['target'] = np.random.randint(0, 2, 1000)
        else:
            self.df = data.copy()
        return self.df
    
    def preprocess_data(self):
        df = self.df.copy()
        
        if self.target_column is None:
            self.target_column = df.columns[-1]
        
        y = df[self.target_column]
        X = df.drop(columns=[self.target_column])
        
        for col in X.columns:
            if X[col].dtype == 'object':
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                X[col] = self.label_encoders[col].fit_transform(X[col].astype(str))
        
        if y.dtype == 'object':
            le_target = LabelEncoder()
            y = le_target.fit_transform(y)
            self.label_encoders['target'] = le_target
        
        X = X.fillna(X.mean())
        
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
        )
        
        self.X_train = self.scaler.fit_transform(self.X_train)
        self.X_test = self.scaler.transform(self.X_test)
        
        return self.X_train, self.X_test, self.y_train, self.y_test
    
    def train_model(self, model=None, **kwargs):
        if model is None:
            self.model = RandomForestClassifier(n_estimators=100, random_state=42, **kwargs)
        else:
            self.model = model
        
        self.model.fit(self.X_train, self.y_train)
        return self.model
    
    def evaluate_model(self):
        y_pred = self.model.predict(self.X_test)
        accuracy = accuracy_score(self.y_test, y_pred)
        report = classification_report(self.y_test, y_pred)
        return accuracy, report
    
    def save_model(self, model_path='model.pkl'):
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'label_encoders': self.label_encoders,
            'target_column': self.target_column
        }, model_path)
    
    def load_model(self, model_path='model.pkl'):
        saved = joblib.load(model_path)
        self.model = saved['model']
        self.scaler = saved['scaler']
        self.label_encoders = saved['label_encoders']
        self.target_column = saved['target_column']
    
    def predict(self, X):
        X_processed = X.copy()
        for col in X_processed.columns:
            if col in self.label_encoders:
                X_processed[col] = self.label_encoders[col].transform(X_processed[col].astype(str))
        X_processed = X_processed.fillna(X_processed.mean())
        X_scaled = self.scaler.transform(X_processed)
        return self.model.predict(X_scaled)

def main():
    pipeline = MLPipeline()
    pipeline.load_data()
    pipeline.preprocess_data()
    pipeline.train_model()
    accuracy, report = pipeline.evaluate_model()
    print(f"Accuracy: {accuracy:.4f}")
    print(report)
    pipeline.save_model('trained_model.pkl')

if __name__ == '__main__':
    main()
