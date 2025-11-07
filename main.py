from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
import string, random

# ✅ FastAPI app
app = FastAPI()

# ✅ Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./urls.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ✅ DB model
class URL(Base):
    __tablename__ = "urls"
    id = Column(Integer, primary_key=True, index=True)
    original = Column(String, nullable=False)
    short = Column(String, unique=True, index=True)
    clicks = Column(Integer, default=0)

Base.metadata.create_all(bind=engine)

# ✅ Pydantic schemas
class URLRequest(BaseModel):
    originalUrl: str
    customSlug: Optional[str] = None

class URLResponse(BaseModel):
    shortUrl: str

# ✅ Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Slug generator
def generate_random_slug(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# ✅ Base URL for deployment
BASE_URL = "https://smartlink-fastapi-backend.onrender.com"

# ✅ POST /api/shorten
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
    return {"shortUrl": f"{BASE_URL}/{new_url.short}"}

# ✅ GET /{short}
@app.get("/{short}")
def redirect_to_original(short: str, db: Session = Depends(get_db)):
    url_entry = db.query(URL).filter(URL.short == short).first()
    if url_entry:
        url_entry.clicks += 1
        db.commit()
        return RedirectResponse(url=url_entry.original)
    raise HTTPException(status_code=404, detail="Short URL not found")
