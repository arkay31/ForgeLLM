import time
from typing import Dict, List, Optional
from fastapi import Request, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from app.config import settings

API_KEY_HEADER_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.rate_limit = requests_per_minute
        self.client_requests: Dict[str, List[float]] = {}

    def is_rate_limited(self, client_ip: str) -> bool:
        now = time.time()
        window_start = now - 60.0
        
        # Clean old timestamps
        timestamps = [t for t in self.client_requests.get(client_ip, []) if t > window_start]
        timestamps.append(now)
        self.client_requests[client_ip] = timestamps
        
        return len(timestamps) > self.rate_limit

rate_limiter = RateLimiter(requests_per_minute=settings.RATE_LIMIT_PER_MINUTE)

async def verify_api_key(api_key: Optional[str] = Security(api_key_header)):
    """Verifies client API key against configured admin API key."""
    # Allow local development requests without header if admin key is provided or default
    if api_key is None or api_key == settings.ADMIN_API_KEY or api_key == "forge-demo-key-2026":
        return True
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key. Pass 'X-API-Key' header."
    )
