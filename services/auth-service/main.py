"""
Auth Service - Handles authentication and user management
Runs independently on port 8001
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import jwt
import asyncpg
import uuid
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import os

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "sensor-backend-secret-key-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgresql%409891@localhost:5434/sensordb")

# Database connection with circuit breaker
class ResilientDatabase:
    def __init__(self):
        self.pool = None
        self.is_healthy = True
        self.failure_count = 0
        self.max_failures = 3
    
    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(DB_URL, min_size=2, max_size=10)
            self.is_healthy = True
            self.failure_count = 0
            print("✅ Auth Service DB connected")
        except Exception as e:
            self.is_healthy = False
            print(f"❌ Auth Service DB connection failed: {e}")
    
    async def fetch_one(self, query, *args):
        if not self.is_healthy:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow(query, *args)
                self.failure_count = 0  # Reset on success
                return dict(result) if result else None
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.max_failures:
                self.is_healthy = False
                print(f"⚠️ Circuit breaker opened after {self.max_failures} failures")
            raise HTTPException(status_code=503, detail="Database error")
    
    async def execute(self, query, *args):
        if not self.is_healthy:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(query, *args)
                self.failure_count = 0
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.max_failures:
                self.is_healthy = False
            raise HTTPException(status_code=503, detail="Database error")

db = ResilientDatabase()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    yield
    if db.pool:
        await db.pool.close()

app = FastAPI(title="Auth Service", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str
    email: str

# JWT Functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Endpoints
@app.get("/health")
async def health():
    return {
        "service": "auth-service",
        "status": "healthy" if db.is_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/register", response_model=User)
async def register(user_data: UserCreate):
    try:
        user_id = str(uuid.uuid4())
        await db.execute(
            "INSERT INTO users (id, username, email, hashed_password) VALUES ($1, $2, $3, $4)",
            user_id, user_data.username, user_data.email, user_data.password
        )
        return User(username=user_data.username, email=user_data.email)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.fetch_one(
        "SELECT username, hashed_password FROM users WHERE username = $1",
        form_data.username
    )
    
    if not user or user['hashed_password'] != form_data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user['username']})
    return Token(access_token=access_token, token_type="bearer")

@app.get("/verify")
async def verify(token: str = Depends(oauth2_scheme)):
    username = await verify_token(token)
    user = await db.fetch_one(
        "SELECT username, email FROM users WHERE username = $1",
        username
    )
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
