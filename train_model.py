import numpy as np
import joblib
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split

rng = np.random.default_rng(42)
N = 4000
temp = rng.uniform(15, 45, N)
humidity = rng.uniform(15, 95, N)
rainfall = rng.exponential(2.0, N)
soil = rng.integers(0, 3, N)
stage = rng.integers(0, 4, N)

soil_dryness_factor = np.select([soil == 0, soil == 1, soil == 2], [1.3, 1.0, 0.75])
stage_sensitivity = np.select([stage == 0, stage == 1, stage == 2, stage == 3], [1.2, 1.1, 1.0, 0.85])
dryness_score = ((45 - humidity) * 0.4 + (temp - 20) * 0.6 - rainfall * 3.0) * soil_dryness_factor * stage_sensitivity
dryness_score += rng.normal(0, 3, N)
irrigation_needed = (dryness_score > 12).astype(int)

X = np.column_stack([temp, humidity, rainfall, soil, stage])
y = irrigation_needed
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = SVC(kernel="rbf", C=10, gamma="scale")
model.fit(X_train, y_train)
print("Test accuracy:", model.score(X_test, y_test))

joblib.dump(model, "irrigation_model.pkl")
print("Saved irrigation_model.pkl")
