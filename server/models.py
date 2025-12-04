from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    measurements = relationship("Measurement", back_populates="device", cascade="all, delete-orphan")

class Measurement(Base):
    __tablename__ = "measurements"
    id = Column(Integer, primary_key=True, index=True)
    device_id_fk = Column(Integer, ForeignKey("devices.id"), nullable=False)
    voltage = Column(Float, nullable=False)
    current = Column(Float, nullable=False)
    power = Column(Float, nullable=False)
    energy = Column(Float, nullable=False)  # Wh or chosen unit
    timestamp = Column(DateTime, nullable=False)

    device = relationship("Device", back_populates="measurements")

class DailyAggregate(Base):
    __tablename__ = "daily_aggregates"
    id = Column(Integer, primary_key=True, index=True)
    device_id_fk = Column(Integer, ForeignKey("devices.id"), nullable=False)
    date = Column(DateTime, nullable=False)  # store date at midnight UTC
    total_energy_wh = Column(Float, default=0.0)
    total_cost_cop = Column(Float, default=0.0)
