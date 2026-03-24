# ==========================================
# 🌊 Coastal Water Quality ML - FINAL CLEAN MODEL
# ==========================================

import pandas as pd
import numpy as np
import pickle

from collections import Counter
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.utils.class_weight import compute_class_weight

# ==========================================
# 1. LOAD DATA
# ==========================================
df = pd.read_csv("data.csv")
df.columns = df.columns.str.strip()

print("Columns:", df.columns)

# ==========================================
# 2. TARGET VARIABLE
# ==========================================
df['Quality'] = df['CCME_WQI']

# ==========================================
# 3. REMOVE EXTREMELY RARE CLASSES (FIX WARNINGS)
# ==========================================
value_counts = df['Quality'].value_counts()

# Keep only classes with >= 10 samples
valid_classes = value_counts[value_counts >= 10].index
df = df[df['Quality'].isin(valid_classes)]

print("\nFiltered Class Distribution:\n", df['Quality'].value_counts())

# ==========================================
# 4. ENCODE TARGET
# ==========================================
le = LabelEncoder()
y = le.fit_transform(df['Quality'])

# ==========================================
# 5. FEATURE SELECTION (MATCH YOUR DATASET)
# ==========================================
features = [
    'Ammonia (mg/l)',
    'Biochemical Oxygen Demand (mg/l)',
    'Dissolved Oxygen (mg/l)',
    'Orthophosphate (mg/l)',
    'pH (ph units)',
    'Temperature (cel)',
    'Nitrogen (mg/l)',
    'Nitrate (mg/l)'
]

# Keep only available columns
features = [f for f in features if f in df.columns]

X = df[features]

# Handle missing values
X = X.fillna(X.mean())

print("\nUsing Features:", features)

# ==========================================
# 6. TRAIN TEST SPLIT
# ==========================================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# ==========================================
# 7. HANDLE CLASS IMBALANCE
# ==========================================
classes = np.unique(y)
weights = compute_class_weight(class_weight='balanced', classes=classes, y=y)
class_weights = dict(zip(classes, weights))

# ==========================================
# 8. BASE MODELS
# ==========================================
rf = RandomForestClassifier(
    n_estimators=200,
    max_depth=15,
    class_weight=class_weights,
    random_state=42
)

gb = GradientBoostingClassifier(random_state=42)

lr = LogisticRegression(max_iter=1000)

# ==========================================
# 9. STACKING ENSEMBLE
# ==========================================
stack_model = StackingClassifier(
    estimators=[
        ('rf', rf),
        ('gb', gb)
    ],
    final_estimator=lr,
    passthrough=True
)

# ==========================================
# 10. PIPELINE
# ==========================================
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('model', stack_model)
])

# ==========================================
# 11. SAFE CROSS VALIDATION (NO WARNINGS)
# ==========================================
class_counts = Counter(y)
min_class_size = min(class_counts.values())

n_splits = min(3, min_class_size)
if n_splits < 2:
    n_splits = 2

cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

scores = cross_val_score(pipeline, X, y, cv=cv)

print("\nCross Validation Accuracy:", scores.mean())

# ==========================================
# 12. TRAIN FINAL MODEL
# ==========================================
pipeline.fit(X_train, y_train)

y_pred = pipeline.predict(X_test)

print("Test Accuracy:", accuracy_score(y_test, y_pred))

# ==========================================
# 13. SAVE MODEL FILES
# ==========================================
pickle.dump(pipeline, open("model.pkl", "wb"))
pickle.dump(le, open("encoder.pkl", "wb"))
pickle.dump(features, open("features.pkl", "wb"))

print("\n✅ MODEL TRAINED & SAVED SUCCESSFULLY!")