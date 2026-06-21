import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import setup_logging
from app.middleware.request_middleware import RequestMiddleware
from app.db.base import Base
from app.db.session import engine
from app.websocket.manager import websocket_manager

# Import all models to ensure they're created
from app.db.models import (
    user, api_key, request_log, decision_log, 
    feature_log, ml_prediction, feedback
)

# Import API routes
from app.api.routes import dashboard
#from app.api.routes.activity import router as activity_router
#from app.api.routes.settings import router as settings_router
#from app.api.routes.usage import router as usage_router


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
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS middleware (for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600, #Cache preflight requests for 1 hour
)

# Include API routes
app.include_router(dashboard.router)
#app.include_router(activity_router)
#app.include_router(usage_router)
#app.include_router(settings_router)

#Add middleware
app.add_middleware(RequestMiddleware)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            # Handle client messages if needed
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)


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

#NORMAL_ENDPOINTS
@app.get("/api/users/me")
async def users_me():
    return {"id": 123, "username": "testuser"}

@app.get("/api/products")
async def products():
    return {"products": [{"id": 1, "name": "Product A"}]}

@app.get("/api/search")
async def search(q: str = ""):
    return {"query": q, "results": []}

#SENSITIVE_ENDPOINTS
@app.get("/admin/dashboard")
async def admin_dashboard():
    return {"status": "admin dashboard"}

@app.get("/api/admin/users")
async def api_admin_users():
    return {"users": []}

@app.get("/api/internal/metrics")
async def internal_metrics():
    return {"cpu": 45, "memory": 1024}

@app.get("/.git/config")
async def git_config():
    return {"file": ".git/config"}

@app.get("/backup/db.sql")
async def backup_db():
    return {"file": "database backup"}

# ============ ADDITIONAL NORMAL ENDPOINTS ============

@app.get("/api/users/me")
async def users_me():
    return {"id": 123, "username": "testuser", "email": "test@example.com"}

@app.get("/api/products")
async def products():
    return {
        "products": [
            {"id": 1, "name": "Product A", "price": 99.99},
            {"id": 2, "name": "Product B", "price": 149.99}
        ]
    }

@app.get("/api/search")
async def search(q: str = "", page: int = 1):
    return {"query": q, "page": page, "results": [], "total": 0}

# ============ SENSITIVE/ADMIN ENDPOINTS ============

@app.get("/admin/dashboard")
async def admin_dashboard():
    return {"status": "admin_dashboard", "stats": {"users": 1234, "requests": 56789}}

@app.get("/api/admin/users")
async def api_admin_users():
    return {
        "users": [
            {"id": 1, "username": "admin", "role": "admin"},
            {"id": 2, "username": "user1", "role": "user"}
        ]
    }

@app.get("/api/internal/metrics")
async def internal_metrics():
    return {
        "cpu_usage": 45.2,
        "memory_usage": 1024,
        "requests_per_second": 150,
        "error_rate": 0.02
    }

@app.get("/.git/config")
async def git_config():
    return {
        "[core]": "repositoryformatversion = 0",
        "[remote 'origin']": "url = https://github.com/example/repo.git"
    }

@app.get("/backup/db.sql")
async def backup_db():
    return {"file": "database_backup.sql", "size": "15MB", "data": "SQL dump here"}

# ============ SCANNER TARGETS ============

@app.get("/.env")
async def env_file():
    return {
        "DB_PASSWORD": "secret123",
        "API_KEY": "sk_test_123456",
        "JWT_SECRET": "super_secret_key"
    }

@app.get("/debug")
async def debug_endpoint():
    return {"debug": True, "info": "Debug mode enabled", "trace": "detailed_info"}

@app.get("/api/private")
async def private_endpoint():
    return {"secret": "sensitive_data", "api_key": "private_key_123"}

@app.get("/api/internal")
async def internal_endpoint():
    return {"internal": True, "data": "internal_system_data"}

@app.get("/graphql")
async def graphql_endpoint():
    return {"message": "GraphQL endpoint", "schema": "query { hello }"}

@app.get("/phpmyadmin")
async def phpmyadmin():
    return {"status": "phpMyAdmin", "version": "4.9.7", "database": "mysql"}

# ============ ADDITIONAL ATTACK TARGETS ============

@app.get("/backup.zip")
async def backup_zip():
    return {"message": "Backup archive", "size": "15MB", "download": "backup.zip"}

@app.get("/database.sql")
async def database_sql():
    return {"file": "database.sql", "content": "CREATE TABLE users..."}

@app.get("/api/v2/users")
async def api_v2_users():
    return {"version": "v2", "users": []}

@app.get("/swagger.json")
async def swagger_json():
    return {"openapi": "3.0.0", "info": {"title": "API", "version": "1.0.0"}}

@app.get("/openapi.json")
async def openapi_json():
    return {"openapi": "3.0.0", "paths": {"/api/data": {"get": {}}}}

@app.get("/actuator/health")
async def actuator_health():
    return {"status": "UP", "components": {"db": {"status": "UP"}}}

@app.get("/actuator/env")
async def actuator_env():
    return {"activeProfiles": ["prod"], "propertySources": []}

@app.get("/metrics")
async def metrics():
    return {"requests": 1000, "errors": 10, "latency": 0.5}

@app.get("/trace")
async def trace():
    return {"traces": [{"id": 1, "duration": 100}]}

@app.get("/dump")
async def dump():
    return {"dump": "system_dump_data"}

@app.get("/.aws/credentials")
async def aws_credentials():
    return {"aws_access_key_id": "AKIAIOSFODNN7EXAMPLE", "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"}

@app.get("/.ssh/id_rsa")
async def ssh_key():
    return {"private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA..."}

@app.get("/password.txt")
async def password_file():
    return {"passwords": ["admin123", "password123", "qwerty"]}

@app.get("/credentials.txt")
async def credentials_file():
    return {"credentials": [{"user": "admin", "pass": "admin123"}]}

# ============ AUTH ENDPOINTS ============

@app.post("/auth")
async def auth(payload: dict):
    username = payload.get("username")
    password = payload.get("password")
    if username == "admin" and password == "admin123":
        return {"token": "fake-jwt-token"}
    return {"error": "Invalid credentials"}

@app.post("/api/auth")
async def api_auth(payload: dict):
    return await auth(payload)

@app.post("/token")
async def token(payload: dict):
    return await auth(payload)

@app.post("/oauth/token")
async def oauth_token(payload: dict):
    return await auth(payload)