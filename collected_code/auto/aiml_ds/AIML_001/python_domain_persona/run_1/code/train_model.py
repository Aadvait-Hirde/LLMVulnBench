import sys
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
import joblib
import warnings
warnings.filterwarnings('ignore')

def validate_input_path(file_path):
    if not isinstance(file_path, str):
        raise ValueError("File path must be a string")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    if not file_path.endswith('.csv'):
        raise ValueError("File must be a CSV file")
    file_size = os.path.getsize(file_path)
    max_size = 100 * 1024 * 1024
    if file_size > max_size:
        raise ValueError(f"File size exceeds maximum allowed size: {max_size} bytes")
    abs_path = os.path.abspath(file_path)
    if not abs_path.startswith(os.getcwd()):
        raise ValueError("File path must be within current working directory")
    return True

def sanitize_dataframe(df):
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(axis=1, how='all')
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    return df

def load_data(file_path):
    validate_input_path(file_path)
    try:
        df = pd.read_csv(file_path, nrows=100000)
        if df.empty:
            raise ValueError("Dataset is empty")
        if len(df.columns) < 2:
            raise ValueError("Dataset must have at least 2 columns")
        df = sanitize_dataframe(df)
        return df
    except pd.errors.EmptyDataError:
        raise ValueError("CSV file is empty")
    except pd.errors.ParserError as e:
        raise ValueError(f"Error parsing CSV: {str(e)}")

def preprocess_data(df, target_column=None):
    if target_column is None:
        target_column = df.columns[-1]
    
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in dataset")
    
    X = df.drop(columns=[target_column])
    y = df[target_column]
    
    numeric_features = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical_features = X.select_dtypes(include=['object', 'category']).columns.tolist()
    
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ],
        remainder='drop'
    )
    
    X_processed = preprocessor.fit_transform(X)
    
    if y.dtype == 'object' or y.dtype.name == 'category':
        le_target = LabelEncoder()
        y_processed = le_target.fit_transform(y.astype(str))
    else:
        y_processed = y.values
        le_target = None
    
    return X_processed, y_processed, preprocessor, le_target

def train_model(X, y):
    if len(np.unique(y)) < 2:
        raise ValueError("Target variable must have at least 2 unique values")
    
    stratify_param = y if len(np.unique(y)) < 20 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=stratify_param
    )
    
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    return model, X_test, y_test

def save_model(model, output_path, preprocessors=None):
    if not isinstance(output_path, str):
        raise ValueError("Output path must be a string")
    
    if not output_path.endswith('.joblib'):
        output_path = output_path + '.joblib'
    
    output_dir = os.path.dirname(output_path) if os.path.dirname(output_path) else '.'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    model_data = {
        'model': model,
        'preprocessors': preprocessors
    }
    
    joblib.dump(model_data, output_path)
    
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python train_model.py <csv_file_path> [output_model_path]")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else 'trained_model.joblib'
    
    try:
        df = load_data(csv_path)
        X, y, preprocessor, le_target = preprocess_data(df)
        model, X_test, y_test = train_model(X, y)
        
        preprocessors = {
            'preprocessor': preprocessor,
            'label_encoder': le_target
        }
        
        save_model(model, output_path, preprocessors)
        print(f"Model trained and saved to {output_path}")
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
