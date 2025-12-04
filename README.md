# Smart Energy - FastAPI server (Level 2 prototype)

Requirements:
  - Python 3.9+
  - pip install -r requirements.txt

Run:
  cd server
  uvicorn main:app --reload --host 0.0.0.0 --port 8000

Notes:
  - The server uses SQLite by default (data.db)
  - Register a user: POST /api/register
  - Obtain token: POST /api/token (use username=email and password)
  - ESP32 should POST to /api/measurements as JSON (device_id, voltage, current, power, energy, timestamp optional)
  - WebSocket for real-time: ws://<host>:8000/ws/realtime
