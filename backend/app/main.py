import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.logging import setup_logging
from app.middleware.request_middleware import RequestMiddleware
from app.db.base import Base
from app.db.session import engine

from app.db.models import user, api_key, request_log, decision_log


#Setup logging
setup_logging()
logger = logging.getLogger(__name__)

#Lifespan(startup-shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('Starting API Security System...')

    #create DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info('Database initialized')

    yield

    logger.info("Shutting down API Security System...")

#Create app
app = FastAPI(
    title = "AI-Powered API Security System",
    version = "1.0.0",
    lifespan = lifespan
)

#Add middleware
app.add_middleware(RequestMiddleware)

#Test endpoint
@app.get('/api/test')
async def test():
    return {'message':'working'}

#Health Check
@app.get('/health')
async def health():
    return {'status': 'ok'}

# AUTH / LOGIN (attack target)
@app.post("/login")
async def login(payload: dict):
    username = payload.get("username")
    password = payload.get("password")

    # fake auth logic
    if username == "admin" and password == "admin123":
        return {"status": "success", "token": "fake-jwt-token"}

    return {"status": "failed", "message": "Invalid credentials"}


# USER PROFILE
@app.get("/api/profile")
async def profile():
    return {
        "user_id": 123,
        "name": "Test User",
        "role": "user"
    }

# DATA ENDPOINT (scraping target)
@app.get("/api/data")
async def get_data():
    return {
        "data": [i for i in range(10)],
        "message": "sample data"
    }



# ADMIN (sensitive endpoint)
@app.get("/admin")
async def admin():
    return {"status": "admin panel"}

# CONFIG (scanner target)
@app.get("/config")
async def config():
    return {"debug": False, "version": "1.0"}

# PASSWORD RESET (attack surface)
@app.post("/reset-password")
async def reset_password(payload: dict):
    email = payload.get("email")
    return {"status": "reset link sent", "email": email}

# DEBUG / HIDDEN (scanner)
@app.get("/debug")
async def debug():
    return {"debug": "info"}


# PRIVATE API (high risk)
@app.get("/api/private")
async def private():
    return {"secret": "sensitive data"}