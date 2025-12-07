from fastapi import APIRouter, Depends, HTTPException, status
from app.models.user import UserCreate, UserLogin, User, Token
from app.utils.auth import get_password_hash, verify_password, create_access_token
from datetime import timedelta
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# In-memory user storage for demonstration
# In production, use PostgreSQL with SQLAlchemy
users_db = {}


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user"""

    # Check if user already exists
    if user_data.email in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password
    password_hash = get_password_hash(user_data.password)

    # Create user
    from uuid import uuid4
    from datetime import datetime

    user = User(
        id=uuid4(),
        email=user_data.email,
        role=user_data.role,
        created_at=datetime.utcnow(),
        is_active=True
    )

    # Store user (with password hash)
    users_db[user_data.email] = {
        "user": user,
        "password_hash": password_hash
    }

    return user


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """Login and receive access token"""

    # Get user from database
    user_record = users_db.get(credentials.email)

    if not user_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(credentials.password, user_record["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = user_record["user"]

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role
        },
        expires_delta=access_token_expires
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: dict = Depends(get_current_user)):
    """Refresh access token"""

    from app.utils.auth import get_current_user

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": current_user.user_id,
            "email": current_user.email,
            "role": current_user.role
        },
        expires_delta=access_token_expires
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""

    from app.utils.auth import get_current_user

    # Find user in database
    user_record = next(
        (record for record in users_db.values() if str(record["user"].id) == current_user.user_id),
        None
    )

    if not user_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user_record["user"]
