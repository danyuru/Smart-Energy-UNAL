from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

# Incoming payload from ESP32
class MeasurementPayload(BaseModel):
    device_id: Optional[str] = "esp32_pzem"   # default
    voltage: float
    current: float
    power: float
    energy: float
    timestamp: Optional[datetime] = None


class MeasurementOut(BaseModel):
    id: int
    device_id: str
    voltage: float
    current: float
    power: float
    energy: float
    timestamp: datetime

    class Config:
        orm_mode = True

# Device view
class DeviceOut(BaseModel):
    id: int
    device_id: str
    name: Optional[str]

    class Config:
        orm_mode = True

# User schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Summary
class SummaryOut(BaseModel):
    device_id: str
    latest_power: float
    latest_energy_wh: float
    daily_energy_wh: float
    daily_cost_cop: float
