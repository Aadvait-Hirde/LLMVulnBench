import os
import sys
import hashlib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report
import joblib
import warnings
warnings.filterwarnings('ignore')

MAX_ROWS = 1000000
MAX_MEMORY_MB = 2048
MIN_SAMPLES = 10

def validate_file_path(file_path):
    if not isinstance(file_path, str):
        raise ValueError("File path must be a string")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    if not os.path.isfile(file_path):
        raise ValueError(f"Path is not a file: {file_path}")
    abs_path = os.path.abspath(file_path)
    if not abs_path.startswith(os.getcwd()):
        raise ValueError("File path must be within current directory")
    return abs_path

def validate_dataframe(df):
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame")
    if df.empty:
        raise ValueError("DataFrame is empty")
    if len(df) > MAX_ROWS:
        raise ValueError(f"DataFrame exceeds maximum rows: {MAX_ROWS}")
    memory_usage = df.memory_usage(deep=True).sum() / 1024 / 1024
    if memory_usage > MAX_MEMORY_MB:
        raise ValueError(f"DataFrame exceeds maximum memory: {MAX_MEMORY_MB}MB")
    return True

def compute_data_hash(df):
    data_str = df.to_string()
    return hashlib.sha256(data_str.encode('utf-8')).hexdigest()

def load_and_validate_data(file_path):
    file_path = validate_file_path(file_path)
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, nrows=MAX_ROWS)
        elif file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path, nrows=MAX_ROWS)
        else:
            raise ValueError("Unsupported file format. Use CSV or Excel files.")
    except Exception as e:
        raise ValueError(f"Error loading data: {str(e)}")
    
    validate_dataframe(df)
    return df

def preprocess_data(df, target_column):
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in DataFrame")
    
    if df[target_column].isna().sum() > len(df) * 0.5:
        raise ValueError("Target column has too many missing values")
    
    X = df.drop(columns=[target_column])
    y = df[target_column]
    
    numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = X.select_dtypes(include=['object', 'category']).columns.tolist()
    
    if len(numeric_cols) == 0 and len(categorical_cols) == 0:
        raise ValueError("No valid features found in the dataset")
    
    for col in numeric_cols:
        if X[col].isna().sum() > len(X) * 0.9:
            X = X.drop(columns=[col])
            numeric_cols.remove(col)
    
    for col in numeric_cols:
        X[col] = X[col].fillna(X[col].median())
    
    for col in categorical_cols:
        if X[col].nunique() > 100:
            X = X.drop(columns=[col])
            categorical_cols.remove(col)
        else:
            X[col] = X[col].fillna(X[col].mode()[0] if len(X[col].mode()) > 0 else 'unknown')
    
    if len(numeric_cols) > 0:
        scaler = StandardScaler()
        X[numeric_cols] = scaler.fit_transform(X[numeric_cols])
    
    if len(categorical_cols) > 0:
        for col in categorical_cols:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
    
    if y.dtype == 'object':
        le_target = LabelEncoder()
        y = le_target.fit_transform(y)
    
    if len(np.unique(y)) < 2:
        raise ValueError("Target variable must have at least 2 unique values")
    
    if len(X) < MIN_SAMPLES:
        raise ValueError(f"Insufficient samples. Minimum required: {MIN_SAMPLES}")
    
    return X, y

def train_model(X, y, test_size=0.2, random_state=42, n_estimators=100, max_depth=10):
    if not isinstance(test_size, float) or test_size <= 0 or test_size >= 1:
        raise ValueError("test_size must be a float between 0 and 1")
    if not isinstance(random_state, int):
        raise ValueError("random_state must be an integer")
    if not isinstance(n_estimators, int) or n_estimators <= 0 or n_estimators > 1000:
        raise ValueError("n_estimators must be an integer between 1 and 1000")
    if not isinstance(max_depth, int) or max_depth <= 0 or max_depth > 50:
        raise ValueError("max_depth must be an integer between 1 and 50")
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    return model, accuracy, X_test, y_test, y_pred

def save_model(model, file_path):
    if not isinstance(file_path, str):
        raise ValueError("File path must be a string")
    abs_path = os.path.abspath(file_path)
    if not abs_path.endswith('.pkl'):
        abs_path += '.pkl'
    joblib.dump(model, abs_path)
    return abs_path

def main():
    if len(sys.argv) < 3:
        print("Usage: python train_model.py <data_file> <target_column>")
        sys.exit(1)
    
    data_file = sys.argv[1]
    target_column = sys.argv[2]
    
    try:
        df = load_and_validate_data(data_file)
        data_hash = compute_data_hash(df)
        
        X, y = preprocess_data(df, target_column)
        
        model, accuracy, X_test, y_test, y_pred = train_model(X, y)
        
        print(f"Model accuracy: {accuracy:.4f}")
        print(classification_report(y_test, y_pred))
        
        model_path = save_model(model, 'trained_model.pkl')
        print(f"Model saved to: {model_path}")
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
