from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from datetime import datetime
from database.db import Base

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, index=True)
    location = Column(String, index=True, nullable=False)
    soil_type = Column(Integer, nullable=False)
    crop_stage = Column(Integer, nullable=False)
    field_size = Column(Float, default=1.0)
    temperature = Column(Float)
    humidity = Column(Float)
    rainfall = Column(Float)
    alert = Column(String)
    water_today = Column(Float)
    weather_alerts = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)
    week_prediction = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id, "location": self.location, "soil_type": self.soil_type,
            "crop_stage": self.crop_stage, "field_size": self.field_size,
            "temperature": self.temperature, "humidity": self.humidity, "rainfall": self.rainfall,
            "alert": self.alert, "water_today": self.water_today,
            "weather_alerts": self.weather_alerts, "recommendations": self.recommendations,
            "week": self.week_prediction, "created_at": self.created_at.isoformat(),
        }
