from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.openapi.docs import get_swagger_ui_html
from database import SessionLocal, init_db
from models import URL
from schemas import URLRequest, URLResponse
from utils import get_unique_short_url

app = FastAPI(
    title="SmartLink API",
    description="FastAPI-based URL shortener",
    version="1.0.0"
)

init_db()

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Swagger UI (optional)
@app.get("/docs", include_in_schema=False)
def custom_swagger_ui():
    return get_swagger_ui_html(openapi_url="/openapi.json", title="SmartLink Docs")

# Shorten URL endpoint
@app.post("/api/shorten", response_model=URLResponse)
def shorten_url(request: URLRequest):
    db = SessionLocal()
    try:
        short = request.customSlug or get_unique_short_url(db, URL)
        exists = db.query(URL).filter(URL.short_url == short).first()
        if exists:
            raise HTTPException(status_code=400, detail="Slug already taken")
        new_url = URL(original_url=request.originalUrl, short_url=short)
        db.add(new_url)
        db.commit()
        db.refresh(new_url)
        return {"shortUrl": f"https://smartlink-backend.onrender.com/{new_url.short_url}"}
    finally:
        db.close()

# Redirect to original URL
@app.get("/{short}")
def redirect_to_original(short: str):
    db = SessionLocal()
    try:
        url_entry = db.query(URL).filter(URL.short_url == short).first()
        if url_entry:
            url_entry.clicks += 1
            db.commit()
            return RedirectResponse(url=url_entry.original_url)
        raise HTTPException(status_code=404, detail="Short URL not found")
    finally:
        db.close()
