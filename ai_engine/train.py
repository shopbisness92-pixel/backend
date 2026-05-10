import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor
import joblib

# -----------------------------
# 1️⃣ Load dataset
# -----------------------------
data = pd.read_csv("dataset/ethical_compliance_dataset.csv")

# -----------------------------
# 2️⃣ Preprocessing & Feature Engineering
# -----------------------------
# Drop non-numeric or complex columns
cols_to_drop = [
    "project_name",
    "description",
    "scan_date",
    "previous_scores",
    "recommendations",
    "ethical_flags"
]

X = data.drop(cols_to_drop + ["score"], axis=1)
y = data["score"]

# -----------------------------
# 2️⃣1 Encode categorical columns
# -----------------------------
encoders = {}
for col in ["compliance_framework", "scan_type"]:
    le = LabelEncoder()
    X[col] = le.fit_transform(X[col])
    encoders[col] = le

# -----------------------------
# 2️⃣2 Ensure binary compliance flags exist
# -----------------------------
flag_cols = ["hipaa_flag", "pii_flag", "soc2_flag"]
for col in flag_cols:
    if col not in X.columns:
        X[col] = 0  # default to 0 if missing

# -----------------------------
# 2️⃣3 Optional: Create combined feature
# -----------------------------
# Example: total_issues + compliance_flags
X["total_issues"] = X["critical"] + X["high"] + X["medium"] + X["low"]
X["compliance_score"] = X["hipaa_flag"] + X["pii_flag"] + X["soc2_flag"]

# -----------------------------
# 3️⃣ Train/Test Split
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# -----------------------------
# 4️⃣ Model Training
# -----------------------------
model = RandomForestRegressor(
    n_estimators=200,  # increased trees for stability
    max_depth=15,      # deeper to capture more patterns
    random_state=42,
    n_jobs=-1          # use all CPU cores
)

model.fit(X_train, y_train)

# -----------------------------
# 5️⃣ Save model and encoders
# -----------------------------
joblib.dump(model, "model_escc.pkl")
joblib.dump(encoders, "encoders.pkl")

# -----------------------------
# 6️⃣ Quick Evaluation
# -----------------------------
accuracy = model.score(X_test, y_test)
print(f"📊 Model Accuracy (R^2 Score): {accuracy:.4f}")
print("✅ ESCC AI Model Trained Successfully with HIPAA/PII/SOC2 Flags and saved to model_escc.pkl")
