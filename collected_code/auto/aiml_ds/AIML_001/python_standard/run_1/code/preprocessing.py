import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer

def load_data(csv_path):
    return pd.read_csv(csv_path)

def preprocess_features(df, target_column=None):
    if target_column and target_column in df.columns:
        X = df.drop(columns=[target_column])
        y = df[target_column]
    else:
        X = df
        y = None
    
    numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = X.select_dtypes(include=['object']).columns.tolist()
    
    scaler = None
    label_encoders = {}
    y_encoder = None
    
    if numeric_cols:
        numeric_imputer = SimpleImputer(strategy='mean')
        X[numeric_cols] = numeric_imputer.fit_transform(X[numeric_cols])
        scaler = StandardScaler()
        X[numeric_cols] = scaler.fit_transform(X[numeric_cols])
    
    if categorical_cols:
        categorical_imputer = SimpleImputer(strategy='most_frequent')
        X[categorical_cols] = categorical_imputer.fit_transform(X[categorical_cols])
        for col in categorical_cols:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            label_encoders[col] = le
    
    if y is not None:
        if y.dtype == 'object':
            y_encoder = LabelEncoder()
            y = y_encoder.fit_transform(y)
    
    preprocessors = {
        'scaler': scaler,
        'label_encoders': label_encoders,
        'y_encoder': y_encoder
    }
    
    return X, y, preprocessors
