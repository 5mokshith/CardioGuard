import numpy as np
from pathlib import Path
from datetime import datetime
from src.data.save_data import save_balanced_dataset

def save_balanced_dataset(X, y, feature_names=None, balance_type='combined', output_dir='data/processed'):
    """
    Save the balanced dataset with consistent key names
    
    Args:
        X: Feature matrix
        y: Target labels
        feature_names: List of feature names (optional)
        balance_type: Type of balancing used ('smote', 'undersample', or 'combined')
        output_dir: Directory to save the data
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = output_dir / f'balanced_dataset_{balance_type}_{timestamp}.npz'
    
    save_dict = {
        'X_test': X,
        'y_test': y
    }
    
    if feature_names is not None:
        save_dict['feature_names'] = feature_names
    
    np.savez(output_path, **save_dict)
    print(f"Saved balanced dataset to: {output_path}")
    return output_path

# When saving your balanced datasets:
save_balanced_dataset(X, y, feature_names, balance_type='smote')