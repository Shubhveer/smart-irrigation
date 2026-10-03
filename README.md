# Farm Saathi — Smart Irrigation & Farmer Assistance Platform

Farm Saathi is a Flask-based agricultural decision-support platform. The irrigation ML pipeline now uses a public real-world Smart Agriculture Dataset rather than the previous synthetic training generator.

## Real-data ML architecture

Real Smart Agriculture Dataset
→ data validation and cleaning
→ EDA
→ stratified train/test split
→ categorical + numeric preprocessing
→ Random Forest classifier
→ actual test-set evaluation
→ irrigation_model.pkl
→ Flask inference

The public dataset contains crop/soil/growth and environmental variables including crop ID, soil type, seedling stage, moisture index (MOI), temperature, humidity and an irrigation-result label. The dataset defines three result states; the current model keeps all three.

## Dataset setup

Source: Smart Agriculture Dataset — Chaitanya Gopidesi, Kaggle
https://www.kaggle.com/datasets/chaitanyagopidesi/smart-agriculture-dataset

Download the CSV yourself and place it at:
eda/data/raw/smart_agriculture_dataset.csv

The raw dataset is not generated or fabricated by this repository. The old stand-in CSV and synthetic model artifacts were removed.

## EDA + training

Install dependencies:

pip install -r requirements.txt
pip install -r eda/requirements-eda.txt

Run the full EDA and evaluation:

python eda/real_irrigation_pipeline.py --data eda/data/raw/smart_agriculture_dataset.csv

Train/export only:

python train_model.py --data eda/data/raw/smart_agriculture_dataset.csv

The EDA creates plots in eda/reports/. Metrics are printed from the actual held-out test set; the repository does not claim fixed accuracy, precision, recall or F1 values.

## Important model/data distinction

The irrigation model predicts an irrigation state. It does not learn litres of water from the dataset. The current Flask water quantity is still application business logic. A measured irrigation-volume dataset should be added before presenting litre predictions as ML-derived quantities.

## Flask integration

The live prediction form now accepts:
- crop
- soil type
- crop stage
- soil moisture (MOI)
- field size

Temperature and humidity come from the weather service. Rainfall may be used for weather alerts but is not substituted for MOI.

## Other Farm Saathi modules

The repository also contains crop health, soil, fertilizer, pest, farm planning, government-news and image-check modules, plus the Flutter project under flutter_application_1/.

## Development note

The real-data model file is intentionally absent until the public dataset is downloaded and training is run. This prevents the application from silently falling back to the old synthetic model.
