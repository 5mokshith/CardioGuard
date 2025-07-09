import os
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_curve, 
    precision_recall_curve, average_precision_score,
    auc, f1_score
)

class ModelTester:
    def __init__(self, models_dir, data_dir, figures_dir):
        """
        Initialize ModelTester with directory paths
        
        Args:
            models_dir: Directory containing saved models
            data_dir: Directory containing test data
            figures_dir: Directory to save visualization outputs
        """
        self.models_dir = Path(models_dir)
        self.data_dir = Path(data_dir)
        self.figures_dir = Path(figures_dir)
        self.results = {}
        
    def load_test_data(self, balance_type='combined'):
        """
        Load the test dataset
        
        Args:
            balance_type: Type of balanced dataset to use ('smote', 'undersample', or 'combined')
        
        Returns:
            tuple: (X_test, y_test, feature_names)
        """
        try:
            # Find most recent balanced dataset file
            data_files = list(self.data_dir.glob(f'balanced_dataset_{balance_type}_*.npz'))
            if not data_files:
                raise FileNotFoundError(f"No {balance_type} balanced dataset found")
            
            latest_file = max(data_files, key=lambda x: x.stat().st_mtime)
            print(f"Loading test data from: {latest_file}")
            
            # Load the data
            data = np.load(latest_file)
            print(f"Available keys in data file: {data.files}")
            
            # Map different possible key names
            key_mappings = {
                'X_test': ['X_test', 'x_test', 'X', 'x'],
                'y_test': ['y_test', 'y_test', 'y', 'labels']
            }
            
            # Try to find the correct keys
            X_test = None
            y_test = None
            
            for key in key_mappings['X_test']:
                if key in data.files:
                    X_test = data[key]
                    break
                    
            for key in key_mappings['y_test']:
                if key in data.files:
                    y_test = data[key]
                    break
            
            if X_test is None or y_test is None:
                raise KeyError(f"Could not find test data in the NPZ file. Available keys: {data.files}")
            
            # Generate feature names if not present
            feature_names = data.get('feature_names', 
                                   [f'feature_{i}' for i in range(X_test.shape[1])])
            
            print(f"Loaded data shapes - X: {X_test.shape}, y: {y_test.shape}")
            return X_test, y_test, feature_names
            
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            if 'data' in locals():
                print(f"File content structure: {dict(data.items())}")
            raise
    
    def load_models(self, balance_type='combined'):
        """
        Load trained models
        
        Args:
            balance_type: Type of balanced dataset used for training
        """
        models = {}
        model_types = ['randomforest', 'gradientboosting']
        
        for model_type in model_types:
            model_path = self.models_dir / f'{model_type}_{balance_type}_model.joblib'
            if model_path.exists():
                print(f"Loading {model_type} model from: {model_path}")
                models[model_type] = joblib.load(model_path)
            else:
                print(f"Warning: {model_type} model not found at {model_path}")
        
        return models
    
    def evaluate_model(self, model, X_test, y_test, model_name):
        """
        Evaluate a single model and store results
        
        Args:
            model: Trained model object
            X_test: Test features
            y_test: Test labels
            model_name: Name of the model for reporting
        """
        # Get predictions and probabilities
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]
        
        # Calculate metrics
        results = {
            'classification_report': classification_report(y_test, y_pred, output_dict=True),
            'confusion_matrix': confusion_matrix(y_test, y_pred),
            'roc_curve': roc_curve(y_test, y_prob),
            'pr_curve': precision_recall_curve(y_test, y_prob),
            'average_precision': average_precision_score(y_test, y_prob),
            'predictions': y_pred,
            'probabilities': y_prob
        }
        
        self.results[model_name] = results
        return results
    
    def plot_roc_curves(self, save_path=None):
        """Plot ROC curves for all models"""
        plt.figure(figsize=(10, 8))
        
        for model_name, results in self.results.items():
            fpr, tpr, _ = results['roc_curve']
            roc_auc = auc(fpr, tpr)
            
            plt.plot(fpr, tpr, label=f'{model_name} (AUC = {roc_auc:.3f})')
        
        plt.plot([0, 1], [0, 1], 'k--')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('Receiver Operating Characteristic (ROC) Curves')
        plt.legend(loc='lower right')
        
        if save_path:
            plt.savefig(save_path)
            plt.close()
        else:
            plt.show()
    
    def plot_precision_recall_curves(self, save_path=None):
        """Plot Precision-Recall curves for all models"""
        plt.figure(figsize=(10, 8))
        
        for model_name, results in self.results.items():
            precision, recall, _ = results['pr_curve']
            ap_score = results['average_precision']
            
            plt.plot(recall, precision, label=f'{model_name} (AP = {ap_score:.3f})')
        
        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.title('Precision-Recall Curves')
        plt.legend(loc='lower left')
        
        if save_path:
            plt.savefig(save_path)
            plt.close()
        else:
            plt.show()
    
    def plot_confusion_matrices(self, save_path=None):
        """Plot confusion matrices for all models"""
        n_models = len(self.results)
        fig, axes = plt.subplots(1, n_models, figsize=(6*n_models, 5))
        if n_models == 1:
            axes = [axes]
        
        for ax, (model_name, results) in zip(axes, self.results.items()):
            cm = results['confusion_matrix']
            sns.heatmap(cm, annot=True, fmt='d', ax=ax, cmap='Blues')
            ax.set_title(f'{model_name}\nConfusion Matrix')
            ax.set_xlabel('Predicted')
            ax.set_ylabel('Actual')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
            plt.close()
        else:
            plt.show()
    
    def plot_feature_importance(self, feature_names, save_path=None):
        """Plot feature importance for all models that support it"""
        n_features = len(feature_names)
        n_models = len(self.results)
        
        plt.figure(figsize=(12, 6*n_models))
        
        for i, (model_name, model) in enumerate(self.models.items()):
            if hasattr(model, 'feature_importances_'):
                plt.subplot(n_models, 1, i+1)
                importances = model.feature_importances_
                indices = np.argsort(importances)[::-1]
                
                plt.bar(range(n_features), importances[indices])
                plt.title(f'{model_name} Feature Importance')
                plt.xticks(range(n_features), [feature_names[i] for i in indices], rotation=45, ha='right')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
            plt.close()
        else:
            plt.show()
    
    def test_all_models(self, balance_type='combined'):
        """
        Test all models and generate comprehensive evaluation
        
        Args:
            balance_type: Type of balanced dataset to use
        """
        # Create output directories if they don't exist
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        
        # Load test data and models
        X_test, y_test, feature_names = self.load_test_data(balance_type)
        self.models = self.load_models(balance_type)
        
        # Evaluate each model
        for model_name, model in self.models.items():
            print(f"\nEvaluating {model_name}...")
            self.evaluate_model(model, X_test, y_test, model_name)
            
            # Print classification report
            clf_report = self.results[model_name]['classification_report']
            print("\nClassification Report:")
            print(pd.DataFrame(clf_report).transpose())
        
        # Generate and save visualizations
        self.plot_roc_curves(self.figures_dir / f'roc_curves_{balance_type}.png')
        self.plot_precision_recall_curves(self.figures_dir / f'pr_curves_{balance_type}.png')
        self.plot_confusion_matrices(self.figures_dir / f'confusion_matrices_{balance_type}.png')
        self.plot_feature_importance(feature_names, self.figures_dir / f'feature_importance_{balance_type}.png')
        
        # Compare models using correct dictionary key
        f1_scores = {
            model_name: self._get_metric_from_report(
                results['classification_report'],
                metric_key='f1-score',
                avg_type='weighted avg'
            )
            for model_name, results in self.results.items()
        }
        
        best_model = max(f1_scores.items(), key=lambda x: x[1])
        print(f"\nBest performing model: {best_model[0]} (F1-score: {best_model[1]:.3f})")
        
        return self.results

    def _get_metric_from_report(self, clf_report, metric_key='f1-score', avg_type='weighted avg'):
        """
        Helper method to safely extract metrics from classification report
        
        Args:
            clf_report (dict): Classification report dictionary
            metric_key (str): Metric to extract (default: 'f1-score')
            avg_type (str): Average type (default: 'weighted avg')
        
        Returns:
            float: Metric value
        """
        try:
            return clf_report[avg_type][metric_key]
        except KeyError:
            # If key not found, print available keys for debugging
            print(f"\nAvailable keys in classification report:")
            print(f"Top level keys: {list(clf_report.keys())}")
            if avg_type in clf_report:
                print(f"Keys in {avg_type}: {list(clf_report[avg_type].keys())}")
            raise

def main():
    # Set up paths
    current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    project_root = current_dir.parent.parent
    
    models_dir = project_root / 'models'
    data_dir = project_root / 'data' / 'processed'
    figures_dir = project_root / 'figures'
    
    # Initialize tester
    tester = ModelTester(models_dir, data_dir, figures_dir)
    
    # Test models for each balance type
    balance_types = ['smote', 'undersample', 'combined']
    
    for balance_type in balance_types:
        print(f"\nTesting models trained on {balance_type} balanced dataset...")
        tester.test_all_models(balance_type)

if __name__ == "__main__":
    main()