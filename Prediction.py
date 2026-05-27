import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

# CSV laden
df = pd.read_csv("agg_full.csv", parse_dates=["order_date"])

# Sortieren für zeitliche Reihenfolge (wichtig!)
df = df.sort_values(by=["coating_id", "order_date"])

df["next_day_fill_rate"] = df.groupby("coating_id")["total_fill_rate"].shift(-1)

df = df.dropna(subset=["next_day_fill_rate"])

for col in df.columns:
    if df[col].dtype == bool:
        df[col] = df[col].astype(int)
    elif df[col].dtype == object and set(df[col].dropna().unique()) <= {"True", "False"}:
        df[col] = df[col].map({"False": 0, "True": 1})

# Beispiel: alle numerischen Features außer `total_fill_rate` und Ziel
exclude_cols = ["order_date", "coating_id", "next_day_fill_rate", "total_fill_rate"]
feature_cols = [col for col in df.columns if col not in exclude_cols]

X = df[feature_cols]
y = df["next_day_fill_rate"]

# Train/Test-Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

# Modelltraining
model = RandomForestRegressor(n_estimators=3000, random_state=42)
model.fit(X_train, y_train)

# Vorhersage
y_pred = model.predict(X_test)

# Bewertung
mse = mean_squared_error(y_test, y_pred)
print(f"Mean Squared Error: {mse:.2f}")