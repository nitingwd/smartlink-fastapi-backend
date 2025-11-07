from pydantic import BaseModel
from typing import Optional

class URLRequest(BaseModel):
    originalUrl: str
    customSlug: Optional[str] = None

class URLResponse(BaseModel):
    shortUrl: str
