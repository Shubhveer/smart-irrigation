# Real Dataset Setup

Dataset: Smart Agriculture Dataset — Chaitanya Gopidesi (Kaggle)
Source: https://www.kaggle.com/datasets/chaitanyagopidesi/smart-agriculture-dataset

The dataset contains 16,411 records and fields including crop ID, soil type, seedling stage, moisture index (MOI), temperature, humidity and irrigation result. A recent peer-reviewed smart-irrigation study documents the same public dataset and its three target states: 0 = no irrigation, 1 = irrigation required, 2 = excess water condition.

Download the CSV from Kaggle and place it at eda/data/raw/smart_agriculture_dataset.csv.

Run: python eda/real_irrigation_pipeline.py --data eda/data/raw/smart_agriculture_dataset.csv

Do not commit the raw dataset until redistribution terms are confirmed. The previous checked-in CSV was a stand-in and is no longer used.