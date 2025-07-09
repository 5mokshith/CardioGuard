import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE
from joblib import dump
from collections import Counter
import os

# Device Configuration
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# Load actual dataset
data_path = r"C:\Users\moksh\classroom\test_ML_deepalert\test\data\processed\balanced_dataset_combined_20250223_081210.csv"
data = pd.read_csv(data_path)
X = data.iloc[:, :-1].values  # Features
y = data.iloc[:, -1].values   # Labels

# Print initial class distribution
print("Initial class distribution:", Counter(y))

# Splitting data before SMOTE
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Apply SMOTE to training data only
smote = SMOTE(random_state=42)
X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)
print("After SMOTE class distribution:", Counter(y_train_resampled))

# Normalize Features
scaler = StandardScaler()
X_train_resampled = scaler.fit_transform(X_train_resampled)
X_test = scaler.transform(X_test)

# Save the scaler for inference
dump(scaler, 'scaler.joblib')

# Convert to PyTorch tensors
X_train_tensor = torch.FloatTensor(X_train_resampled).to(device)
y_train_tensor = torch.FloatTensor(y_train_resampled).to(device)
X_test_tensor = torch.FloatTensor(X_test).to(device)
y_test_tensor = torch.FloatTensor(y_test).to(device)

# Create DataLoader with correct TensorDataset
train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
train_loader = DataLoader(dataset=train_dataset, batch_size=64, shuffle=True)

# Define Model Architecture
class MLPModel(nn.Module):
    def __init__(self, input_dim):
        super(MLPModel, self).__init__()
        self.fc1 = nn.Linear(input_dim, 64)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.sigmoid(self.fc3(x))
        return x

# Initialize Model
model = MLPModel(input_dim=X_train.shape[1]).to(device)

# Handle class imbalance
pos_weight = torch.tensor([len(y_train)/(2*np.bincount(y_train)[1])]).to(device)
criterion = nn.BCELoss()

# Optimizer
optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-5)

# Modify the training loop section
num_epochs = 30
best_f1 = 0
patience = 5
patience_counter = 0
best_loss = float('inf')

print("Starting training...")
print(f"Training on device: {device}")

for epoch in range(num_epochs):
    model.train()
    total_loss = 0
    
    for features, labels in train_loader:
        labels = labels.view(-1, 1)
        optimizer.zero_grad()
        outputs = model(features)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    
    avg_loss = total_loss / len(train_loader)
    
    # Validation
    model.eval()
    with torch.no_grad():
        outputs = model(X_test_tensor)
        predictions = (outputs > 0.5).float()
        # Move tensors to CPU before converting to numpy
        predictions = predictions.cpu().numpy()
        y_test_numpy = y_test_tensor.cpu().numpy()
        report = classification_report(y_test_numpy, predictions, output_dict=True)
    
    # Access F1 score using string key '1' instead of integer 1
    try:
        current_f1 = report['1']['f1-score']  # Changed from report[1] to report['1']
    except KeyError:
        # Fallback if label is different
        current_f1 = report['pos']['f1-score'] if 'pos' in report else 0.0
        
    print(f"Epoch {epoch+1}/{num_epochs} | Loss: {avg_loss:.4f} | Validation F1: {current_f1:.4f}")
    
    # Save best model and early stopping
    if current_f1 > best_f1:
        best_f1 = current_f1
        # Create models directory if it doesn't exist
        os.makedirs("models", exist_ok=True)
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'loss': avg_loss,
            'f1_score': current_f1,
            'input_dim': X_train.shape[1],
        }, "models/best_model.pth")
        print(f"Saved new best model with F1 score: {current_f1:.4f}")
        patience_counter = 0
    else:
        patience_counter += 1
    
    # Early stopping
    if patience_counter >= patience:
        print(f"Early stopping triggered after {epoch+1} epochs")
        break

print("\nTraining Summary:")
print(f"Best validation F1: {best_f1:.4f}")
print("Model saved at: models/")