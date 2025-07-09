import os
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.metrics import precision_recall_curve, average_precision_score, roc_curve
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import signal
import warnings
import multiprocessing
warnings.filterwarnings('ignore')

# Get the number of CPU cores (leaving one free)
N_JOBS = max(1, multiprocessing.cpu_count() - 1)
print(f"Using {N_JOBS} CPU cores for parallel processing")

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), 'data')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')  # Directory for balanced datasets
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), 'models')
FIGURES_DIR = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), 'figures')

# Create directories if they don't exist
for directory in [MODELS_DIR, FIGURES_DIR]:
    os.makedirs(directory, exist_ok=True)

def load_balanced_data(method='combined'):
    """
    Load the balanced dataset from a CSV file.
    
    Parameters:
    -----------
    method : str
        The balancing method used ('combined' in this case).
    
    Returns:
    --------
    X : array-like
        Feature matrix.
    y : array-like
        Labels array.
    """
    # Use the specific balanced dataset (already processed externally)
    data_path = os.path.join(PROCESSED_DIR, 'balanced_dataset_combined_20250223_081210.csv')
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Balanced dataset not found at: {data_path}")
    
    # Load the data
    df = pd.read_csv(data_path)
    
    # Separate features and labels
    X = df.drop(columns=['label'])
    y = df['label']
    
    print(f"Loaded balanced dataset from {data_path}")
    print(f"Dataset shape: {X.shape}")
    unique, counts = np.unique(y, return_counts=True)
    for u, c in zip(unique, counts):
        print(f"Class {u}: {c} samples ({(c/len(y))*100:.2f}%)")
    
    return X.values, y.values

def train_and_evaluate(balancing_method='combined'):
    """
    Train and evaluate models using the balanced dataset.
    """
    print("Loading balanced data...")
    try:
        features, labels = load_balanced_data(balancing_method)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return None
    
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(
        features, 
        labels, 
        test_size=0.3,  # Increased test size
        random_state=42, 
        stratify=labels
    )
    print(f"Training set shape: {X_train.shape}")
    print(f"Test set shape: {X_test.shape}")
    
    # Save test set for threshold optimization
    joblib.dump(X_test, os.path.join(MODELS_DIR, 'X_test.joblib'))
    joblib.dump(y_test, os.path.join(MODELS_DIR, 'y_test.joblib'))
    
    # Create model pipelines with preprocessing only
    rf_pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', RandomForestClassifier(
            random_state=42,
            n_jobs=N_JOBS  # Parallel processing for RandomForest
        ))
    ])
    
    gb_pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', GradientBoostingClassifier(
            random_state=42,
            validation_fraction=0.2,
            n_iter_no_change=5,
            tol=1e-4,
            verbose=0
        ))
    ])
    
    # Parameter grids (reduced for faster training)
    rf_param_grid = {
        'classifier__n_estimators': [100],
        'classifier__max_depth': [10],
        'classifier__min_samples_split': [5],
        'classifier__min_samples_leaf': [2],
        'classifier__max_features': ['sqrt'],
        'classifier__class_weight': ['balanced']
    }

    gb_param_grid = {
        'classifier__n_estimators': [100],
        'classifier__learning_rate': [0.1],
        'classifier__max_depth': [3],
        'classifier__min_samples_split': [5],
        'classifier__min_samples_leaf': [2],
        'classifier__subsample': [0.8]
    }

    # Train models with cross-validation
    models = {}
    
    # Train and evaluate RandomForest
    print("\nTraining RandomForest...")
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)  # Using 3 folds
    rf_grid = GridSearchCV(
        rf_pipeline, 
        rf_param_grid, 
        scoring='roc_auc',
        cv=cv,
        verbose=2,
        n_jobs=N_JOBS,
        refit=True
    )
    rf_grid.fit(X_train, y_train)
    
    print("\nBest parameters for RandomForest:")
    print(rf_grid.best_params_)
    rf_best = rf_grid.best_estimator_
    
    models['RandomForest'] = evaluate_model(rf_best, X_test, y_test, 'RandomForest')
    
    # Train and evaluate GradientBoosting
    print("\nTraining GradientBoosting...")
    gb_grid = GridSearchCV(
        gb_pipeline, 
        gb_param_grid, 
        scoring='roc_auc',
        cv=cv,
        verbose=2,
        n_jobs=N_JOBS,
        refit=True
    )
    gb_grid.fit(X_train, y_train)
    
    print("\nBest parameters for GradientBoosting:")
    print(gb_grid.best_params_)
    gb_best = gb_grid.best_estimator_
    
    models['GradientBoosting'] = evaluate_model(gb_best, X_test, y_test, 'GradientBoosting')
    
    # Save models
    for name, model_info in models.items():
        model_path = os.path.join(MODELS_DIR, f"{name.lower().replace(' ', '_')}_{balancing_method}_model.joblib")
        joblib.dump(model_info['model'], model_path)
        print(f"Saved {name} model to {model_path}")
    
    # Create and save visualizations
    plot_model_performance(models, y_test, balancing_method)
    
    # Determine best model based on PR-AUC
    best_model = max(models.items(), key=lambda x: x[1]['pr_auc'])[0]
    print(f"\nBest performing model: {best_model}")
    
    return models[best_model]['model']

def plot_model_performance(models, y_test, balancing_method):
    """Generate and save performance visualization plots."""
    plt.figure(figsize=(15, 12))
    
    # ROC curves
    plt.subplot(2, 2, 1)
    for name, model_info in models.items():
        fpr, tpr, _ = roc_curve(y_test, model_info['y_proba'])
        plt.plot(fpr, tpr, label=f"{name} (AUC = {model_info['roc_auc']:.3f})")
    plt.plot([0, 1], [0, 1], 'k--')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title(f'ROC Curves (Balanced Dataset)')
    plt.legend()
    
    # Precision-Recall curves
    plt.subplot(2, 2, 2)
    for name, model_info in models.items():
        precision, recall, _ = precision_recall_curve(y_test, model_info['y_proba'])
        plt.plot(recall, precision, label=f"{name} (PR-AUC = {model_info['pr_auc']:.3f})")
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title(f'Precision-Recall Curves (Balanced Dataset)')
    plt.legend()
    
    # Confusion matrices
    for i, (name, model_info) in enumerate(models.items()):
        plt.subplot(2, 2, 3+i)
        cm = confusion_matrix(y_test, model_info['y_pred'])
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False)
        plt.xlabel('Predicted Label')
        plt.ylabel('True Label')
        plt.title(f'Confusion Matrix - {name}')
    
    plt.tight_layout()
    save_path = os.path.join(FIGURES_DIR, f'model_performance_balanced.png')
    plt.savefig(save_path)
    print(f"Saved performance visualizations to {save_path}")

def find_optimal_threshold(model, X_test, y_test):
    """
    Find the optimal threshold for the given model based on the test set.
    
    Parameters:
    -----------
    model : estimator object
        The trained model.
    X_test : array-like
        Test feature matrix.
    y_test : array-like
        Test labels.
    
    Returns:
    --------
    optimal_threshold : float
        The optimal threshold value.
    """
    y_proba = model.predict_proba(X_test)[:, 1]
    precision, recall, thresholds = precision_recall_curve(y_test, y_proba)
    f1_scores = 2 * (precision * recall) / (precision + recall)
    optimal_threshold = thresholds[np.argmax(f1_scores)]
    print(f"Optimal threshold: {optimal_threshold:.3f}")
    return optimal_threshold

def evaluate_model(model, X_test, y_test, name):
    """Perform detailed evaluation of a model."""
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    
    print(f"\n{name} Results:")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, digits=4))
    
    # Plot prediction probabilities distribution
    plt.figure(figsize=(10, 4))
    plt.hist(y_proba[y_test == 0], bins=50, alpha=0.5, label='Normal')
    plt.hist(y_proba[y_test == 1], bins=50, alpha=0.5, label='Anomaly')
    plt.xlabel('Prediction Probability')
    plt.ylabel('Count')
    plt.title(f'{name} - Prediction Probabilities Distribution')
    plt.legend()
    plt.savefig(os.path.join(FIGURES_DIR, f'{name.lower()}_prob_dist.png'))
    plt.close()
    
    return {
        'model': model,
        'y_pred': y_pred,
        'y_proba': y_proba,
        'roc_auc': roc_auc_score(y_test, y_proba),
        'pr_auc': average_precision_score(y_test, y_proba)
    }

if __name__ == "__main__":
    print("\nTraining models with balanced dataset...")
    # Use the 'combined' balanced dataset as defined in load_balanced_data()
    best_model = train_and_evaluate('combined')
    if best_model is not None:
        X_test = joblib.load(os.path.join(MODELS_DIR, 'X_test.joblib'))
        y_test = joblib.load(os.path.join(MODELS_DIR, 'y_test.joblib'))
        print("\nFinding optimal threshold for anomaly detection...")
        find_optimal_threshold(best_model, X_test, y_test)
