# Water My Field — Smart Irrigation Advisor

A 3-tier web application that tells farmers, in plain language, whether their
field needs watering today — built with a Flask + ML backend, a PostgreSQL
database, and a farmer-first frontend designed for low-literacy, low-bandwidth,
multilingual use.

**Live app:** https://smart-irrigation-pi6v.onrender.com

---

## What this project actually demonstrates

This started as a basic single-file Flask script and was rebuilt into a
complete, deployed, end-to-end system:

- **3-tier architecture** — presentation (Flask + Jinja2), business logic
  (service layer), and data (SQLAlchemy + PostgreSQL), properly separated
- **Machine learning** — an SVM classifier predicting irrigation need, with a
  full EDA + model comparison notebook (`eda/`) benchmarking 6 different
  algorithms on a real Kaggle dataset, not just one hardcoded choice
- **Real deployment** — live on Render with a managed PostgreSQL database,
  gunicorn production server, environment-based secrets
- **Accessibility-first UI** — English/Hindi toggle, text-to-speech result
  readout, large tap targets, plain-language copy instead of technical jargon
- **Installable as an app** — PWA support (manifest + service worker), plus a
  native Android wrapper built with Flet (`mobile-app/`)

## Architecture

```
Website (Jinja2 templates)  →  Middle Tier (Flask routes + services)  →  Database (PostgreSQL via SQLAlchemy)
                                          ↓
                                 ML model (scikit-learn, joblib)
```

| Layer | Files | Responsibility |
|---|---|---|
| Website | `templates/`, `static/` | Farmer-facing form, result page, history |
| Middle Tier | `routes/predict_routes.py` | HTTP handling only |
| | `services/weather_service.py` | OpenWeatherMap API integration |
| | `services/irrigation_service.py` | ML inference + irrigation business logic |
| | `services/report_service.py` | Excel report generation |
| Database | `database/models.py`, `database/db.py` | SQLAlchemy models, session management |
| ML / Data Science | `eda/` | Real-dataset EDA, 6-model comparison, trained model export |

## Features

- Predicts today's irrigation need from live weather + soil + crop stage
- 7-day irrigation forecast
- Prediction history log (persisted in PostgreSQL)
- Downloadable Excel report per prediction
- English / Hindi UI toggle
- Text-to-speech result readout (for low-literacy accessibility)
- Installable as a home-screen app (PWA) or native Android app

## Tech Stack

**Backend:** Flask, SQLAlchemy, Gunicorn, PostgreSQL
**ML:** scikit-learn, joblib, pandas, numpy
**Frontend:** Jinja2, vanilla JS, custom SVG icon system
**Data Science:** Jupyter, matplotlib, seaborn
**Deployment:** Render (web service + managed Postgres)
**Mobile:** Flet (Python-to-APK WebView wrapper)

---

## Setup — run locally

```bash
git clone https://github.com/Shubhveer/smart-irrigation.git
cd smart-irrigation

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt

cp .env.example .env
# edit .env — add your OpenWeatherMap API key (https://openweathermap.org/api)

python app.py
```
Visit `http://127.0.0.1:5000`.

## Deployment (Render)

- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app`
- **Environment variables:** `OPENWEATHER_API_KEY`, `FLASK_SECRET_KEY`, `FLASK_DEBUG=false`, `DATABASE_URL` (from a Render PostgreSQL instance)

See `.env.example` for the full list of required variables.

## The ML side

### Irrigation model (no synthetic data)
`train_model.py` now trains **only on a real dataset**: the
[Smart Agriculture Dataset](https://www.kaggle.com/datasets/chaitanyagopidesi/smart-agriculture-dataset)
saved as `eda/data/smart_agriculture_dataset.csv` (see `eda/data/README.md`).
It compares Logistic Regression / Random Forest / Gradient Boosting with 5-fold CV,
reports held-out test metrics, and saves `models/irrigation_real.joblib`.
The synthetic generator and the stand-in CSV were removed.

> **Status:** the live app still loads the older `irrigation_model.pkl`, which was trained
> on synthetic rules. Switching `services/irrigation_service.py` to the real-data model needs
> a mapping from the form's soil/stage options to the dataset's categories
> (printed at the end of training). See `eda/README.md` Section 17.

### Crop disease detection (PlantVillage)
A trained model is included in `models/` (MobileNetV3-Large, ImageNet-pretrained, 38 classes, 17 MB, CPU inference).
- `ml/train_cpu_transfer.py`: **recommended**. No GPU and no 2 GB download: fetches a 20,923-image stratified subset
  from GitHub, extracts features once, trains the classifier head and exports ONE ONNX file. About 7 minutes on one CPU core.
- `ml/train_disease_model.py`: full fine-tuning for machines with a GPU.
- `eda/plantvillage/plantvillage_eda.ipynb`: executed EDA, plus `plantvillage_splits.csv`.
- `services/disease_service.py`: onnxruntime inference; used by `/image-check` and `POST /api/disease-detect`.
  Blank/non-photo images are rejected and low-confidence predictions return "retake the photo".

**Measured results** (random 10% held-out split of the 20,923 images; see `models/disease_model_info.json`):
accuracy 97.6%, macro-F1 0.976. These numbers are optimistic: PlantVillage photos are lab-style, several photos of the same leaf can
land in different splits, and background colour alone predicts the class far above chance (see the EDA). Expect lower accuracy on
real field photos. The model can only choose among its 38 classes (14 crops), so it cannot recognise other crops or pests, and
every result carries a "confirm with an expert" note.

## Languages (English, Hindi, Marathi)
The whole website is translated on the server: pages, results, disease names and advice, error messages, the Excel report and
the mobile-API text. Switch language with the buttons in the top bar. Details, how to edit translations and how to add a
language: `docs/TRANSLATIONS.md`. Check completeness with `python -m unittest tests.test_i18n -v`.

## Project structure

```
smart-irrigation/
├── app.py                      # App factory / entrypoint
├── database/
│   ├── db.py
│   └── models.py
├── services/
│   ├── weather_service.py
│   ├── irrigation_service.py
│   └── report_service.py
├── routes/
│   └── predict_routes.py
├── templates/
│   ├── base.html, index.html, result.html, history.html, _icons.html
├── static/
│   ├── style.css, app.js, manifest.json, service-worker.js, icons/
├── eda/
│   ├── smart_irrigation_eda.ipynb
│   ├── data/smart_agriculture_dataset.csv
│   ├── model/                  # models exported from the notebook
│   ├── requirements-eda.txt
│   └── README.md
├── irrigation_model.pkl        # currently deployed model (synthetic-trained, to be replaced)
├── train_model.py              # trains the irrigation model on the real CSV
├── translations/               # hi.json, mr.json (Hindi / Marathi text)
├── tests/test_i18n.py          # checks that nothing is left in English
├── ml/train_cpu_transfer.py    # disease model training, CPU-friendly (recommended)
├── ml/train_disease_model.py   # disease model training, GPU fine-tuning
├── models/                     # trained disease_model.onnx + labels + metrics
├── requirements.txt
├── Procfile
├── .env.example
└── .gitignore
```

## Known limitations / next steps

- Deployed irrigation model is still synthetic-trained; swapping in the notebook's
  real-data model requires either adding a soil-moisture input to the form or
  retraining without it (see `eda/README.md` Section 17 for both options)
- SQLite is used as a local dev fallback; production uses PostgreSQL via
  `DATABASE_URL`
- No user accounts yet — prediction history is global, not per-farmer
- Android APK build via Flet; iOS not pursued (Android-first audience)
