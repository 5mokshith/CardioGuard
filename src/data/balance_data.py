import os
import pandas as pd
import numpy as np
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from imblearn.combine import SMOTEENN
from datetime import datetime
from sklearn.preprocessing import LabelEncoder

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), 'data')
RAW_DIR = os.path.join(DATA_DIR, 'extracted')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')

# Ensure processed directory exists
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Load dataset
DATASET_PATH = os.path.join(RAW_DIR, 'mit_st_features.csv')
df = pd.read_csv(DATASET_PATH)

# Print column names for verification
print("Available columns:", df.columns.tolist())

# Handle categorical columns
categorical_columns = ['record', 'lead', 'st_type', 'st_severity']
label_encoders = {}

for col in categorical_columns:
    if col in df.columns:
        label_encoders[col] = LabelEncoder()
        df[col] = label_encoders[col].fit_transform(df[col].astype(str))

# Remove any remaining non-numeric columns
numeric_columns = df.select_dtypes(include=[np.number]).columns
df = df[numeric_columns]

# Separate features and labels
X = df.drop(columns=['label'])
y = df['label']

print(f"\nOriginal dataset shape: {X.shape}")
print(f"Class distribution before balancing:\n{y.value_counts()}")

def balance_and_save(X, y, method, method_name):
    """
    Balances the dataset using the specified method and saves it as a CSV file.
    """
    X_balanced, y_balanced = method.fit_resample(X, y)

    # Combine X and y back into a DataFrame
    balanced_df = pd.DataFrame(X_balanced, columns=X.columns)
    balanced_df['label'] = y_balanced  # Changed from 'target' to 'label'

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"balanced_dataset_{method_name}_{timestamp}.csv"
    save_path = os.path.join(PROCESSED_DIR, filename)

    # Save to CSV
    balanced_df.to_csv(save_path, index=False)

    print(f"Balanced dataset ({method_name}) saved to: {save_path}")
    print(f"Balanced dataset shape: {balanced_df.shape}")
    print(f"Class distribution after balancing:\n{balanced_df['label'].value_counts()}\n")

# Apply balancing techniques
print("\nApplying SMOTE (Oversampling)...")
balance_and_save(X, y, SMOTE(sampling_strategy='auto', random_state=42), 'smote')

print("\nApplying Random Undersampling...")
balance_and_save(X, y, RandomUnderSampler(sampling_strategy='auto', random_state=42), 'undersample')

print("\nApplying Combined (SMOTE + ENN)...")
balance_and_save(X, y, SMOTEENN(random_state=42), 'combined')

print("\nAll balanced datasets have been saved successfully!")
