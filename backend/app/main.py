import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.logging import setup_logging
from app.middleware.request_middleware import RequestMiddleware
from app.db.base import Base
from app.db.session import engine

# 🔥 ADD THIS LINE (THIS FIXES EVERYTHING)
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