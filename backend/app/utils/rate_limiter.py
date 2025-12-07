from slowapi import Limiter
from slowapi.util import get_remote_address
from app.config import settings


def get_rate_limit_key(request):
    """
    Get rate limit key based on authentication status

    Authenticated users get higher limits, anonymous users get lower limits
    """
    # Check if user is authenticated (has valid Authorization header)
    auth_header = request.headers.get("Authorization")

    if auth_header and auth_header.startswith("Bearer "):
        # Authenticated user - use token as key for per-user limiting
        token = auth_header.split(" ")[1]
        return f"authenticated:{token[:20]}"  # Use first 20 chars of token
    else:
        # Anonymous user - use IP address
        return f"anonymous:{get_remote_address(request)}"


# Initialize limiter
limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=[]  # We'll set limits per route
)


def get_rate_limit_string(request) -> str:
    """
    Get rate limit string based on authentication

    Returns:
        Rate limit string (e.g., "100/minute")
    """
    auth_header = request.headers.get("Authorization")

    if auth_header and auth_header.startswith("Bearer "):
        return f"{settings.RATE_LIMIT_AUTHENTICATED}/minute"
    else:
        return f"{settings.RATE_LIMIT_ANONYMOUS}/minute"
