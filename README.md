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

## The ML side — from synthetic to real data

The originally shipped model was trained on synthetic, rule-based data (see
`train_model.py`) to get the pipeline working end-to-end first. The `eda/`
folder documents the next step: sourcing a real public dataset, exploring it
properly, and comparing models honestly before picking one — see
[`eda/README.md`](eda/README.md) for the full writeup, or open
[`eda/smart_irrigation_eda.ipynb`](eda/smart_irrigation_eda.ipynb) directly.

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
├── irrigation_model.pkl        # currently deployed model (synthetic-trained)
├── train_model.py              # trains the synthetic fallback model
├── requirements.txt
├── Procfile
├── .env.example
└── .gitignore
```

## Known limitations / next steps

- Deployed model is still synthetic-trained; swapping in the notebook's
  real-data model requires either adding a soil-moisture input to the form or
  retraining without it (see `eda/README.md` Section 17 for both options)
- SQLite is used as a local dev fallback; production uses PostgreSQL via
  `DATABASE_URL`
- No user accounts yet — prediction history is global, not per-farmer
- Android APK build via Flet; iOS not pursued (Android-first audience)
