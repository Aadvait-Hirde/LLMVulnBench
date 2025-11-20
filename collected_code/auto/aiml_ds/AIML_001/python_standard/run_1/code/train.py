import argparse
import os
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from preprocessing import load_data, preprocess_features

def train_model(X_train, y_train, model_type='random_forest'):
    if model_type == 'random_forest':
        model = RandomForestClassifier(n_estimators=100, random_state=42)
    elif model_type == 'logistic':
        model = LogisticRegression(random_state=42, max_iter=1000)
    else:
        model = RandomForestClassifier(n_estimators=100, random_state=42)
    
    model.fit(X_train, y_train)
    return model

def save_model(model, filepath):
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
    joblib.dump(model, filepath)

def main():
    parser = argparse.ArgumentParser(description='Train ML model from CSV')
    parser.add_argument('csv_path', type=str, help='Path to CSV file')
    parser.add_argument('--target', type=str, default=None, help='Target column name')
    parser.add_argument('--model-type', type=str, default='random_forest', choices=['random_forest', 'logistic'], help='Model type')
    parser.add_argument('--output', type=str, default='models/trained_model.pkl', help='Output model path')
    parser.add_argument('--test-size', type=float, default=0.2, help='Test set size')
    
    args = parser.parse_args()
    
    df = load_data(args.csv_path)
    X, y, preprocessors = preprocess_features(df, args.target)
    
    if y is None:
        raise ValueError("Target column must be specified when training a model")
    
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=args.test_size, random_state=42)
    
    model = train_model(X_train, y_train, args.model_type)
    
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Model Accuracy: {accuracy:.4f}")
    print(classification_report(y_test, y_pred))
    
    save_model(model, args.output)
    print(f"Model saved to {args.output}")

if __name__ == '__main__':
    main()
