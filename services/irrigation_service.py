import os, logging, joblib, pandas as pd
logger=logging.getLogger(__name__)
MODEL_PATH=os.path.join(os.path.dirname(os.path.dirname(__file__)),"irrigation_model.pkl")
_model=None
def load_model():
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH): raise RuntimeError("Real-data irrigation model is not installed. Run train_model.py with the downloaded Smart Agriculture Dataset.")
        _model=joblib.load(MODEL_PATH)
    return _model
def predict_irrigation(crop,soil,stage,moi,temp,humidity):
    model=load_model()
    features=pd.DataFrame([{"crop ID":crop,"soil_type":soil,"Seedling Stage":stage,"MOI":moi,"temp":temp,"humidity":humidity}])
    return int(model.predict(features)[0])
def build_today_result(crop,soil,stage,moi,temp,humidity,field_size):
    irrigation=predict_irrigation(crop,soil,stage,moi,temp,humidity)
    labels={0:"No Irrigation Needed",1:"Irrigation Required",2:"Excess Water Condition"}
    alert=labels.get(irrigation,"Unknown irrigation state")
    water=round(500*field_size,2) if irrigation==1 else 0
    weather_alerts=[]
    if humidity<40: weather_alerts.append("LOW_HUMIDITY")
    if temp>35: weather_alerts.append("HIGH_TEMP")
    recommendations=[]
    if irrigation==1: recommendations+=["IRRIGATE_TIME","CHECK_SOIL"]
    if irrigation==2: recommendations.append("AVOID_IRRIGATION")
    return {"irrigation":irrigation,"alert":alert,"water_today":water,"weather_alerts":weather_alerts,"recommendations":recommendations}
def build_week_prediction(forecast_data,crop,soil,stage,moi,field_size):
    week=[]
    for day in forecast_data:
        irrigation=predict_irrigation(crop,soil,stage,moi,day["temp"],day["humidity"])
        week.append({"day":day["day"],"irrigation":"Irrigation Required" if irrigation==1 else ("Excess Water" if irrigation==2 else "No Irrigation"),"water":round(400*field_size if irrigation==1 else 0,2)})
    return week