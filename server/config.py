# Configuration values
from datetime import timedelta

SECRET_KEY = "essecreto"  # change for production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

DATABASE_URL = "sqlite:///./data.db"  # sqlite file in project root
MEASUREMENTS_PAGE_SIZE = 200
