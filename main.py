from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import IntegrityError
import random
import string

app = FastAPI()

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./urls.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Model
class URL(Base):
    __tablename__ = "urls"
    id = Column(Integer, primary_key=True, index=True)
    original = Column(String, nullable=False)
    short = Column(String, unique=True, index=True)

Base.metadata.create_all(bind=engine)

# Schemas
class URLRequest(BaseModel):
    originalUrl: str
    customSlug: str | None = None

class URLResponse(BaseModel):
    shortUrl: str

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Slug generator
def generate_random_slug(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Base URL
BASE_URL = "https://smartlink-fastapi-backend.onrender.com"

# Shorten endpoint
@app.post("/api/shorten", response_model=URLResponse)
def shorten_url(request: URLRequest, db: Session = Depends(get_db)):
    new_url = URL(
        original=request.originalUrl,
        short=request.customSlug or generate_random_slug()
    )
    db.add(new_url)
    try:
        db.commit()
        db.refresh(new_url)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Slug already exists")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    return {"shortUrl": f"{BASE_URL}/{new_url.short}"}

# Redirect endpoint
@app.get("/{short}")
def redirect_to_original(short: str, db: Session = Depends(get_db)):
    url = db.query(URL).filter(URL.short == short).first()
    if url:
        return RedirectResponse(url.original)
    else:
        raise HTTPException(status_code=404, detail="Slug not found")
