from sqlalchemy.orm import Session
from . import models
from datetime import datetime, date
from sqlalchemy import func


# Users
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, email: str, hashed_password: str):
    user = models.User(email=email, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# Devices
def get_device_by_device_id(db: Session, device_id: str):
    return db.query(models.Device).filter(models.Device.device_id == device_id).first()

def create_device(db: Session, device_id: str, name: str | None = None):
    dev = models.Device(device_id=device_id, name=name)
    db.add(dev)
    db.commit()
    db.refresh(dev)
    return dev

def list_devices(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Device).offset(skip).limit(limit).all()

# Measurements
def create_measurement(db: Session, device: models.Device, voltage: float, current: float, power: float, energy: float, timestamp: datetime):
    m = models.Measurement(device_id_fk=device.id, voltage=voltage, current=current, power=power, energy=energy, timestamp=timestamp)
    db.add(m)
    db.commit()
    db.refresh(m)
    return m

def query_measurements(db: Session, device_id: str | None = None, start: datetime | None = None, end: datetime | None = None, skip: int = 0, limit: int = 200):
    q = db.query(models.Measurement).join(models.Device)
    if device_id:
        q = q.filter(models.Device.device_id == device_id)
    if start:
        q = q.filter(models.Measurement.timestamp >= start)
    if end:
        q = q.filter(models.Measurement.timestamp <= end)
    return q.order_by(models.Measurement.timestamp.desc()).offset(skip).limit(limit).all()

# Aggregates example: sum energy by day
def compute_daily_total(db: Session, device: models.Device, day: date):
    # sum energy in Wh for that date (timestamps assumed UTC)
    start = datetime(day.year, day.month, day.day)
    end = datetime(day.year, day.month, day.day, 23, 59, 59)
    total = db.query(models.Measurement).filter(
        models.Measurement.device_id_fk == device.id,
        models.Measurement.timestamp >= start,
        models.Measurement.timestamp <= end
    ).with_entities(func.sum(models.Measurement.energy)).scalar() or 0.0
    return float(total)
