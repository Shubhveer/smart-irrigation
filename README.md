# Farm Saathi — Smart Irrigation & Farmer Assistance Platform

A practical agricultural decision-support platform that helps farmers understand **when irrigation may be required** using weather conditions, soil information and crop growth stage.

The project combines a **Flask web application, Machine Learning, weather API integration, PostgreSQL, data analysis and mobile/PWA support** into an end-to-end agricultural technology system.

## Live Application

**Web App:**  
https://smart-irrigation-pi6v.onrender.com

**GitHub Repository:**  
https://github.com/Shubhveer/smart-irrigation

---

# Project Overview

Farmers often need to make irrigation decisions using incomplete or difficult-to-understand information.

Farm Saathi provides a simple interface where agricultural inputs can be combined with current weather information and a Machine Learning model to provide an understandable irrigation recommendation.

The project was initially developed as a basic Flask irrigation application and was progressively structured into separate presentation, business-logic and data layers.

---

# Key Features

## Smart Irrigation

Uses agricultural inputs and weather information to determine whether irrigation is indicated.

The current system considers factors such as:

- Temperature
- Humidity
- Rainfall
- Soil information
- Crop growth stage

---

## Live Weather Integration

The application integrates weather information through the OpenWeather API.

Weather data is used for:

- Current conditions
- Irrigation decisions
- Forecast-based planning
- 7-day irrigation analysis

---

## 7-Day Irrigation Forecast

The system provides a forecast-oriented view of irrigation requirements rather than limiting the user to a single day's recommendation.

This helps farmers plan upcoming irrigation activities.

---

## Prediction History

Previous irrigation predictions can be stored and viewed through the application's history functionality.

The production deployment uses PostgreSQL, while local development can fall back to SQLite.

---

## Excel Reports

The application can generate downloadable Excel reports containing prediction-related information.

This makes the results easier to keep as farm records.

---

## Multilingual Interface

The application is designed for accessibility and supports multilingual interaction.

The project includes language support for:

- English
- Hindi
- Marathi

The language system is designed so that farmer-facing information can be presented in a more accessible local language.

---

## Accessibility

The interface focuses on simple farmer-facing communication rather than technical ML terminology.

The project also includes text-to-speech functionality for reading result information aloud.

---

## Plant & Crop Assistance

The expanded Farm Saathi platform includes additional agricultural assistance areas such as:

- Crop health observation
- Soil guidance
- Fertilizer guidance
- Pest observation
- Plant/soil photo screening
- Government agriculture information

Photo-based screening is intended as a preliminary observation aid and should not be treated as a confirmed disease diagnosis or laboratory soil analysis.

---

# System Architecture

```text
                    FARM SAATHI
                         |
                         v
              +----------------------+
              |   Farmer Interface   |
              | Flask + Jinja2 + JS  |
              +----------+-----------+
                         |
                         v
              +----------------------+
              |    Flask Routes      |
              |   Request Handling   |
              +----------+-----------+
                         |
                         v
              +----------------------+
              |    Service Layer     |
              |                      |
              | Weather Service      |
              | Irrigation Service   |
              | Report Service       |
              +----------+-----------+
                         |
              +----------+-----------+
              |                      |
              v                      v
      +---------------+       +---------------+
      | Machine       |       | Weather API   |
      | Learning      |       | OpenWeather   |
      | Model         |       +---------------+
      +-------+-------+
              |
              v
      +---------------+
      | PostgreSQL /  |
      | SQLite        |
      +---------------+
```

The repository separates presentation, business logic and data responsibilities rather than keeping the entire application inside one Flask file.

---

# Machine Learning

The irrigation component uses a Machine Learning classification pipeline.

The repository contains:

```text
irrigation_model.pkl
train_model.py
eda/
```

The `eda/` directory contains the exploratory analysis and model-comparison work.

The project compares multiple Machine Learning algorithms using a real agricultural dataset during the data-science workflow.

## Important Model Note

The currently deployed `irrigation_model.pkl` is trained using a **synthetic, rule-based dataset**.

This was used to establish the complete application pipeline.

The repository also contains an EDA workflow for working with real agricultural data and comparing different models.

Therefore, the current deployed model should **not be interpreted as a production-grade agricultural model** without further validation on representative field data.

The project documents this limitation rather than presenting unsupported accuracy claims.

---

# Data Science Workflow

```text
Agricultural Dataset
        |
        v
Data Cleaning
        |
        v
Exploratory Data Analysis
        |
        v
Feature Analysis
        |
        v
Model Comparison
        |
        v
Model Training
        |
        v
Model Export
        |
        v
Flask Integration
        |
        v
Farmer-Facing Prediction
```

The EDA notebook is available under:

```text
eda/smart_irrigation_eda.ipynb
```

---

# Technology Stack

## Backend

- Python
- Flask
- SQLAlchemy
- Gunicorn

## Machine Learning

- scikit-learn
- joblib
- pandas
- NumPy

## Data Analysis

- Jupyter Notebook
- Matplotlib
- Seaborn

## Frontend

- HTML
- CSS
- JavaScript
- Jinja2

## Database

- PostgreSQL
- SQLite for local development

## APIs

- OpenWeather API

## Deployment

- Render
- Gunicorn
- Managed PostgreSQL

## Mobile / Installable Application

- Progressive Web App support
- Android-oriented application support

The repository currently includes the corresponding deployment and mobile/PWA components.

---

# Project Structure

```text
smart-irrigation/
│
├── app.py
│
├── database/
│   ├── db.py
│   └── models.py
│
├── services/
│   ├── weather_service.py
│   ├── irrigation_service.py
│   └── report_service.py
│
├── routes/
│   └── predict_routes.py
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── result.html
│   ├── history.html
│   └── _icons.html
│
├── static/
│   ├── style.css
│   ├── app.js
│   ├── manifest.json
│   ├── service-worker.js
│   └── icons/
│
├── eda/
│   ├── smart_irrigation_eda.ipynb
│   ├── data/
│   │   └── smart_agriculture_dataset.csv
│   ├── model/
│   ├── requirements-eda.txt
│   └── README.md
│
├── irrigation_model.pkl
├── train_model.py
├── requirements.txt
├── Procfile
├── .env.example
└── .gitignore
```

This structure corresponds to the current repository organization.

---

# Running the Project Locally

## 1. Clone the Repository

```bash
git clone https://github.com/Shubhveer/smart-irrigation.git
```

```bash
cd smart-irrigation
```

---

## 2. Create a Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Copy:

```text
.env.example
```

to:

```text
.env
```

Then configure the required environment variables.

Example:

```env
OPENWEATHER_API_KEY=your_api_key
FLASK_SECRET_KEY=your_secret_key
FLASK_DEBUG=false
DATABASE_URL=your_database_url
```

Do not commit real API keys, passwords or secret keys to GitHub.

---

# Run the Application

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

---

# Deployment

The application can be deployed as a Flask web service.

Example production start command:

```bash
gunicorn app:app
```

Required production configuration includes environment variables such as:

```text
OPENWEATHER_API_KEY
FLASK_SECRET_KEY
FLASK_DEBUG
DATABASE_URL
```

---

# Current Limitations

This project is an evolving agricultural technology project and has several limitations.

### Machine Learning Validation

The deployed irrigation model is currently based on synthetic training data.

A production agricultural system would require:

- Representative field data
- Region-specific calibration
- More soil variables
- Crop-specific datasets
- Longer-term validation
- Evaluation across different weather and soil conditions

### User Accounts

The current application does not yet provide individual farmer accounts.

Therefore, prediction history is not fully separated by farmer.

### Agricultural Recommendations

The system provides decision-support information and should not replace:

- Agricultural experts
- Laboratory soil testing
- Local agricultural recommendations
- Product labels and regulatory guidance

### Photo Screening

Image-based plant/soil screening is intended for preliminary observation and should not be considered a confirmed diagnosis.

---

# Future Development

Possible future improvements include:

- Farmer-specific user accounts
- Region-specific agricultural models
- Better soil-moisture integration
- Real field-data collection
- Crop-specific irrigation models
- Improved plant disease models
- Offline-first mobile functionality
- SMS/WhatsApp notifications
- More government agriculture services
- Farm record management
- Improved Marathi and Hindi coverage
- IoT sensor integration
- Automated irrigation hardware integration

---

# Project Goal

The long-term goal of Farm Saathi is to develop a practical agricultural platform where farmers can access important farm information through a simple interface instead of needing to understand Machine Learning or complex technical data.

```text
Weather
   +
Soil
   +
Crop
   +
Growth Stage
   +
Machine Learning
   |
   v
Farmer-Friendly Decision Support
```

---

# Author

**Shubhveer**

Computer Science & Artificial Intelligence / Machine Learning Student

GitHub:  
https://github.com/Shubhveer

Project:  
https://github.com/Shubhveer/smart-irrigation

---

# License

This project is developed for educational, experimental and agricultural technology development purposes.

Before using the system for real agricultural decisions, validate recommendations with appropriate local agricultural expertise and field data.
