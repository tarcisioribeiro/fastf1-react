"""
Train the best performing model (LightGBM) and save it.
"""
import os
import sys
import django

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from ml.feature_engineering import prepare_position_features_enhanced
from ml.trainer import F1PerformanceModel

print("="*80)
print("TRAINING BEST MODEL: LIGHTGBM")
print("="*80)

# Load data
print("\nLoading enhanced features...")
X, y = prepare_position_features_enhanced(year_start=2018)

print(f"Loaded {X.shape[0]} samples with {X.shape[1]} features")

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"Train: {len(X_train)}, Test: {len(X_test)}")

# Train LightGBM model
print("\nTraining LightGBM model...")
model = F1PerformanceModel(model_type='position', algorithm='lightgbm')
metrics = model.train(year_start=2018, incremental=False)

print("\n" + "="*80)
print("TRAINING COMPLETE")
print("="*80)
print(f"\nTest R²: {metrics['test']['r2']:.4f} ({metrics['test']['r2']*100:.2f}%)")
print(f"Test MAE: {metrics['test']['mae']:.3f} positions")
print(f"Test RMSE: {metrics['test']['rmse']:.3f} positions")

# Calculate additional metrics
y_pred_test = model.model.predict(model.scaler.transform(X_test))
test_errors = np.abs(y_test - y_pred_test)

print(f"\nError Distribution:")
print(f"  Errors ≤1 pos: {(test_errors <= 1).sum() / len(test_errors) * 100:.1f}%")
print(f"  Errors ≤2 pos: {(test_errors <= 2).sum() / len(test_errors) * 100:.1f}%")
print(f"  Errors ≤3 pos: {(test_errors <= 3).sum() / len(test_errors) * 100:.1f}%")
print(f"  Median error: {np.median(test_errors):.2f} positions")

print(f"\nModel saved at: {model.model_path}")
print("="*80)
