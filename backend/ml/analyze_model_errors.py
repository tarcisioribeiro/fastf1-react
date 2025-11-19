"""
Script to analyze current model errors and identify patterns.
This helps us understand where the model is failing and guide improvements.
"""
import os
import sys
import django

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split

from ml.feature_engineering import prepare_position_features_enhanced
from ml.trainer import F1PerformanceModel

def analyze_model_errors():
    """Analyze current position model errors."""
    print("=" * 80)
    print("ANALYZING POSITION MODEL ERRORS")
    print("=" * 80)

    # Load current model
    model = F1PerformanceModel(model_type='position')
    if not model.load_model():
        print("ERROR: Could not load position model")
        return

    print(f"\nModel loaded successfully")
    print(f"Training samples: {model.metadata.get('training_samples', 'unknown')}")
    print(f"Last trained: {model.metadata.get('last_trained', 'unknown')}")

    # Load data
    print("\nLoading training data...")
    X, y = prepare_position_features_enhanced(year_start=2018)

    if X.empty or y.empty:
        print("ERROR: No training data available")
        return

    print(f"Data loaded: {X.shape[0]} samples, {X.shape[1]} features")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Align features
    from ml.feature_engineering import align_features
    X_train = align_features(X_train, model.feature_names)
    X_test = align_features(X_test, model.feature_names)

    # Scale
    X_train_scaled = model.scaler.transform(X_train)
    X_test_scaled = model.scaler.transform(X_test)

    # Predictions
    y_pred_train = model.model.predict(X_train_scaled)
    y_pred_test = model.model.predict(X_test_scaled)

    # Calculate errors
    train_errors = np.abs(y_train - y_pred_train)
    test_errors = np.abs(y_test - y_pred_test)

    print("\n" + "=" * 80)
    print("ERROR ANALYSIS")
    print("=" * 80)

    print(f"\nTrain set:")
    print(f"  Mean Absolute Error: {train_errors.mean():.3f} positions")
    print(f"  Median Absolute Error: {np.median(train_errors):.3f} positions")
    print(f"  Max Error: {train_errors.max():.3f} positions")
    print(f"  Std Error: {train_errors.std():.3f} positions")

    print(f"\nTest set:")
    print(f"  Mean Absolute Error: {test_errors.mean():.3f} positions")
    print(f"  Median Absolute Error: {np.median(test_errors):.3f} positions")
    print(f"  Max Error: {test_errors.max():.3f} positions")
    print(f"  Std Error: {test_errors.std():.3f} positions")

    # Error distribution
    print(f"\nError distribution (Test set):")
    print(f"  Errors <= 1 position: {(test_errors <= 1).sum()} ({(test_errors <= 1).sum() / len(test_errors) * 100:.1f}%)")
    print(f"  Errors <= 2 positions: {(test_errors <= 2).sum()} ({(test_errors <= 2).sum() / len(test_errors) * 100:.1f}%)")
    print(f"  Errors <= 3 positions: {(test_errors <= 3).sum()} ({(test_errors <= 3).sum() / len(test_errors) * 100:.1f}%)")
    print(f"  Errors > 5 positions: {(test_errors > 5).sum()} ({(test_errors > 5).sum() / len(test_errors) * 100:.1f}%)")

    # Analyze by position range
    print(f"\n" + "=" * 80)
    print("ERROR BY POSITION RANGE")
    print("=" * 80)

    # Top 5
    top5_mask = y_test <= 5
    if top5_mask.sum() > 0:
        top5_errors = test_errors[top5_mask]
        print(f"\nTop 5 positions (n={top5_mask.sum()}):")
        print(f"  MAE: {top5_errors.mean():.3f}")
        print(f"  Median: {np.median(top5_errors):.3f}")
        print(f"  Max: {top5_errors.max():.3f}")

    # Midfield (6-15)
    mid_mask = (y_test > 5) & (y_test <= 15)
    if mid_mask.sum() > 0:
        mid_errors = test_errors[mid_mask]
        print(f"\nMidfield (6-15) (n={mid_mask.sum()}):")
        print(f"  MAE: {mid_errors.mean():.3f}")
        print(f"  Median: {np.median(mid_errors):.3f}")
        print(f"  Max: {mid_errors.max():.3f}")

    # Backmarkers (16-20)
    back_mask = y_test > 15
    if back_mask.sum() > 0:
        back_errors = test_errors[back_mask]
        print(f"\nBackmarkers (16-20) (n={back_mask.sum()}):")
        print(f"  MAE: {back_errors.mean():.3f}")
        print(f"  Median: {np.median(back_errors):.3f}")
        print(f"  Max: {back_errors.max():.3f}")

    # Feature importance (for tree-based models)
    if hasattr(model.model, 'feature_importances_'):
        print(f"\n" + "=" * 80)
        print("TOP 20 MOST IMPORTANT FEATURES")
        print("=" * 80)

        importances = model.model.feature_importances_
        feature_importance_df = pd.DataFrame({
            'feature': model.feature_names,
            'importance': importances
        }).sort_values('importance', ascending=False)

        print("\n" + feature_importance_df.head(20).to_string(index=False))

        # Save to file
        feature_importance_df.to_csv('/app/models/feature_importance_position.csv', index=False)
        print(f"\nFull feature importance saved to /app/models/feature_importance_position.csv")

    # Identify worst predictions
    print(f"\n" + "=" * 80)
    print("WORST 10 PREDICTIONS (Test set)")
    print("=" * 80)

    worst_idx = np.argsort(test_errors)[-10:][::-1]

    for i, idx in enumerate(worst_idx, 1):
        actual = y_test.iloc[idx]
        predicted = y_pred_test[idx]
        error = test_errors.iloc[idx]

        print(f"\n{i}. Error: {error:.2f} positions")
        print(f"   Actual: P{int(actual)}, Predicted: P{predicted:.1f}")

        # Get some feature info
        grid_pos = X_test['grid_position'].iloc[idx] if 'grid_position' in X_test.columns else 'N/A'
        quali_pos = X_test['quali_position'].iloc[idx] if 'quali_position' in X_test.columns else 'N/A'

        print(f"   Grid: P{int(grid_pos) if grid_pos != 'N/A' else grid_pos}, Quali: P{int(quali_pos) if quali_pos != 'N/A' else quali_pos}")

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    analyze_model_errors()
