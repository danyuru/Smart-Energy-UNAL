from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, WebSocket
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from typing import List, Optional
from sqlalchemy import func
import asyncio


from . import database, models, schemas, crud, auth, websocket_manager, config

# Initialize DB
database.init_db()

app = FastAPI(title="Smart Energy - Commercial API", version="1.0.0")
ws_manager = websocket_manager.WebSocketManager()

# CORS: allow all for prototype (adjust in production)
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency: DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----- Auth endpoints -----
@app.post("/api/register", response_model=dict)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = crud.get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = auth.get_password_hash(user_in.password)
    user = crud.create_user(db, user_in.email, hashed)
    return {"email": user.email, "id": user.id}

@app.post("/api/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect credentials")
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# ----- Measurement ingestion (ESP32) -----
@app.post("/api/measurements", status_code=201)
async def receive_measurement(payload: schemas.MeasurementPayload, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Validate timestamp
    if payload.timestamp is None:
        timestamp = datetime.utcnow()
    else:
        timestamp = payload.timestamp

    # find or create device
    device_id = payload.device_id or "esp32_pzem"

    device = crud.get_device_by_device_id(db, device_id)
    if not device:
        device = crud.create_device(db, device_id)


    # store measurement (energy unit: Wh recommended)
    m = crud.create_measurement(db, device, payload.voltage, payload.current, payload.power, payload.energy, timestamp)

    # Broadcast to websocket clients (do not await here)
    message = {"type": "measurement", "data": {
        "id": m.id,
        "device_id": device.device_id,
        "voltage": m.voltage,
        "current": m.current,
        "power": m.power,
        "energy": m.energy,
        "timestamp": m.timestamp.isoformat()
    }}
    # schedule async broadcast
    asyncio.create_task(ws_manager.broadcast(message))

    # optionally schedule background aggregation or notification
    # background_tasks.add_task(do_aggregate_or_notify, device.device_id)

    return {"status": "ok", "measurement_id": m.id}

# ----- Measurements query ----- 
@app.get("/api/measurements", response_model=List[schemas.MeasurementOut])
def get_measurements(device_id: Optional[str] = None, start: Optional[datetime] = None, end: Optional[datetime] = None, skip: int = 0, limit: int = config.MEASUREMENTS_PAGE_SIZE, db: Session = Depends(get_db)):
    rows = crud.query_measurements(db, device_id=device_id, start=start, end=end, skip=skip, limit=limit)
    # map rows -> schema with device_id string
    out = []
    for r in rows:
        out.append(schemas.MeasurementOut(
            id=r.id,
            device_id=r.device.device_id,
            voltage=r.voltage,
            current=r.current,
            power=r.power,
            energy=r.energy,
            timestamp=r.timestamp
        ))
    return out

# ----- Devices endpoints -----
@app.get("/api/devices", response_model=List[schemas.DeviceOut])
def list_devices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    devs = crud.list_devices(db, skip=skip, limit=limit)
    return devs

@app.get("/api/devices/{device_id}/summary", response_model=schemas.SummaryOut)
def device_summary(device_id: str, db: Session = Depends(get_db)):
    dev = crud.get_device_by_device_id(db, device_id)
    if not dev:
        raise HTTPException(status_code=404, detail="Device not found")
    # latest measurement
    latest = db.query(models.Measurement).filter(models.Measurement.device_id_fk == dev.id).order_by(models.Measurement.timestamp.desc()).first()
    latest_power = latest.power if latest else 0.0
    latest_energy = latest.energy if latest else 0.0
    # daily aggregate (simple sum)
    today = date.today()
    total_today = db.query(models.Measurement).filter(
        models.Measurement.device_id_fk == dev.id,
        models.Measurement.timestamp >= datetime(today.year, today.month, today.day),
        models.Measurement.timestamp <= datetime(today.year, today.month, today.day, 23,59,59)
    ).with_entities(func.sum(models.Measurement.energy)).scalar() or 0.0

    # For cost calculation you can apply tariffs here (not implemented)
    return schemas.SummaryOut(
        device_id=device_id,
        latest_power=latest_power,
        latest_energy_wh=latest_energy,
        daily_energy_wh=float(total_today),
        daily_cost_cop=0.0
    )

# ----- Websocket real-time -----
@app.websocket("/ws/realtime")
async def ws_realtime(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        while True:
            await ws.receive_text()  # keep connection alive
    except:
        ws_manager.disconnect(ws)

# ----- Protected example route -----
@app.get("/api/profile")
def profile(current_user = Depends(auth.get_current_user)):
    return {"email": current_user.email, "id": current_user.id}
