import sys
import os
import pytest
import numpy as np
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from imblearn.pipeline import Pipeline

# Add the src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.models.train_model import load_data, train_model  # Import your existing functions

def test_class_balance():
    """Test if resampling methods improve class balance"""
    X, y = load_data()  # Your data loading function
    
    # Original class distribution
    original_dist = np.bincount(y) / len(y)
    
    # Apply SMOTE
    smote = SMOTE(random_state=42)
    X_resampled, y_resampled = smote.fit_resample(X, y)
    
    # New class distribution
    new_dist = np.bincount(y_resampled) / len(y_resampled)
    
    assert abs(new_dist[0] - new_dist[1]) < abs(original_dist[0] - original_dist[1])

def test_model_performance_with_resampling():
    """Test if resampling improves model performance on minority class"""
    X, y = load_data()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train with and without resampling
    model_original = train_model(X_train, y_train)
    
    # Create resampling pipeline
    resampling = Pipeline([
        ('smote', SMOTE(random_state=42)),
        ('rus', RandomUnderSampler(random_state=42))
    ])
    
    X_train_resampled, y_train_resampled = resampling.fit_resample(X_train, y_train)
    model_resampled = train_model(X_train_resampled, y_train_resampled)
    
    # Compare minority class recall
    y_pred_original = model_original.predict(X_test)
    y_pred_resampled = model_resampled.predict(X_test)
    
    from sklearn.metrics import recall_score
    recall_original = recall_score(y_test, y_pred_original, pos_label=1)
    recall_resampled = recall_score(y_test, y_pred_resampled, pos_label=1)
    
    assert recall_resampled >= recall_original

def test_model_predictions():
    """Test if model predictions are in the expected format"""
    X, y = load_data()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    
    model = train_model(X_train, y_train)
    predictions = model.predict(X_test)
    
    assert predictions.shape == y_test.shape
    assert set(np.unique(predictions)).issubset({0, 1})

if __name__ == "__main__":
    print("Running test_class_balance...")
    test_class_balance()
    print("Class balance test passed!")
    
    print("\nRunning test_model_performance_with_resampling...")
    test_model_performance_with_resampling()
    print("Model performance test passed!")