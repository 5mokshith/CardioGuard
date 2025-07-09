import os
import joblib
import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
import warnings
warnings.filterwarnings('ignore')

# Define the model class that will be used by the ECG server
class ECGAnomalyDetector(BaseEstimator, ClassifierMixin):
    def __init__(self, model_path=None, threshold=0.5):
        """
        Initialize the ECG anomaly detector model
        
        Args:
            model_path: Path to the trained model file (.joblib)
            threshold: Classification threshold for anomaly detection
        """
        self.model_path = model_path
        self.threshold = threshold
        self.model = None
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
    
    def load_model(self, model_path):
        """Load a trained model from disk"""
        try:
            self.model = joblib.load(model_path)
            print(f"Successfully loaded model from {model_path}")
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def predict(self, X):
        """
        Predict class labels for samples in X
        
        Args:
            X: Features (can be a single sample or batch)
        
        Returns:
            Array of predicted class labels (0=normal, 1=anomaly)
        """
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() first.")
            
        # Ensure X is 2D
        if X.ndim == 1:
            X = X.reshape(1, -1)
        
        # Get probability predictions
        probas = self.predict_proba(X)[:, 1]
        
        # Apply threshold
        return (probas >= self.threshold).astype(int)
    
    def predict_proba(self, X):
        """
        Predict class probabilities for samples in X
        
        Args:
            X: Features (can be a single sample or batch)
        
        Returns:
            Array of class probabilities [P(normal), P(anomaly)]
        """
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        # Ensure X is 2D
        if X.ndim == 1:
            X = X.reshape(1, -1)
        
        # Get raw probabilities from the underlying model
        return self.model.predict_proba(X)
    
    def get_confidence(self, X):
        """
        Get confidence score for anomaly detection
        
        Args:
            X: Features (can be a single sample or batch)
        
        Returns:
            Confidence score for anomaly class (higher = more confident it's an anomaly)
        """
        probas = self.predict_proba(X)[:, 1]
        return probas

# Helper function to load the best model
def load_best_model(models_dir='models', model_name='randomforest_model.joblib'):
    """
    Load the best trained model for ECG anomaly detection
    
    Args:
        models_dir: Directory containing model files
        model_name: Name of the model file to load
    
    Returns:
        Loaded ECGAnomalyDetector instance
    """
    model_path = os.path.join(models_dir, model_name)
    
    # Try to load optimal threshold if available
    threshold = 0.5
    threshold_path = os.path.join(models_dir, 'optimal_threshold.txt')
    if os.path.exists(threshold_path):
        try:
            with open(threshold_path, 'r') as f:
                threshold = float(f.read().strip())
        except:
            pass

    # Create and return the model
    detector = ECGAnomalyDetector(model_path=model_path, threshold=threshold)
    return detector

# Example usage
if __name__ == "__main__":
    # Load the model
    models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models')
    detector = load_best_model(models_dir=models_dir)
    
    # Test with random data
    test_data = np.random.randn(5, 14)  # 5 samples with 14 features
    
    # Get predictions
    predictions = detector.predict(test_data)
    confidences = detector.get_confidence(test_data)
    
    # Print results
    print(f"Loaded model with threshold: {detector.threshold}")
    for i, (pred, conf) in enumerate(zip(predictions, confidences)):
        status = "ANOMALY" if pred == 1 else "NORMAL"
        print(f"Sample {i+1}: {status} (confidence: {conf:.4f})")