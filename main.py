from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import Base, engine, get_db
from models import URL
from schemas import URLRequest, URLResponse
import string, random

app = FastAPI()

Base.metadata.create_all(bind=engine)

BASE_URL = "https://smartlink-fastapi-backend.onrender.com"

def generate_random_slug(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

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

@app.get("/{short}")
def redirect_to_original(short: str, db: Session = Depends(get_db)):
    url_entry = db.query(URL).filter(URL.short == short).first()
    if url_entry:
        url_entry.clicks += 1
        db.commit()
        return RedirectResponse(url=url_entry.original)
    raise HTTPException(status_code=404, detail="Short URL not found")
