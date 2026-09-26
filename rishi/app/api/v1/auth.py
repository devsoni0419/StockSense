from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.config import settings
from app.models.user import User
from app.schemas.user import (
    UserCreate, UserLogin, UserResponse, UserUpdate,
    TokenResponse, ForgotPasswordRequest, VerifyOTPRequest, ResetPasswordRequest
)
from app.schemas.common import ApiResponse
from app.utils.security import hash_password, verify_password, create_access_token
from app.services.otp_service import create_otp, verify_otp, mark_otp_as_used

router = APIRouter(prefix="/auth", tags=["Authentication & Profile"])


@router.post("/signup", response_model=ApiResponse[UserResponse], status_code=status.HTTP_201_CREATED)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account."""
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    user = User(
        name=user_in.name,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        role=user_in.role.value if hasattr(user_in.role, "value") else str(user_in.role),
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return ApiResponse(
        success=True,
        message="User account created successfully.",
        data=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=ApiResponse[TokenResponse])
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate with email and password to receive a JWT access token."""
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated."
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": user.email, "role": user.role, "user_id": user.id},
        expires_delta=access_token_expires
    )

    return ApiResponse(
        success=True,
        message="Login successful.",
        data=TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )
    )


@router.post("/forgot-password", response_model=ApiResponse[dict])
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Request OTP-based password reset.
    Generates a 6-digit OTP code with expiration.
    """
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        # Prevent email enumeration while maintaining security
        return ApiResponse(
            success=True,
            message="If an account with this email exists, an OTP has been dispatched.",
            data={"email": req.email}
        )

    otp_code = create_otp(db, req.email)
    
    # Return code in response for easier local testing/development
    data_response = {"email": req.email, "expires_in_minutes": settings.OTP_EXPIRE_MINUTES}
    if settings.DEBUG:
        data_response["dev_otp"] = otp_code

    return ApiResponse(
        success=True,
        message="OTP for password reset generated successfully.",
        data=data_response
    )


@router.post("/verify-otp", response_model=ApiResponse[dict])
def verify_reset_otp(req: VerifyOTPRequest, db: Session = Depends(get_db)):
    """Verify validity of OTP code before resetting password."""
    is_valid = verify_otp(db, req.email, req.otp)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP code."
        )

    return ApiResponse(
        success=True,
        message="OTP verified successfully. You may now reset your password.",
        data={"email": req.email, "verified": True}
    )


@router.post("/reset-password", response_model=ApiResponse[dict])
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using verified OTP code."""
    is_valid = verify_otp(db, req.email, req.otp)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP code."
        )

    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found."
        )

    user.hashed_password = hash_password(req.new_password)
    mark_otp_as_used(db, req.email, req.otp)
    db.commit()

    return ApiResponse(
        success=True,
        message="Password has been reset successfully. You can now login with your new password.",
        data={"email": req.email}
    )


@router.get("/me", response_model=ApiResponse[UserResponse])
def get_my_profile(current_user: User = Depends(get_current_user)):
    """Retrieve current logged in user's profile."""
    return ApiResponse(
        success=True,
        message="User profile retrieved.",
        data=UserResponse.model_validate(current_user)
    )


@router.put("/me", response_model=ApiResponse[UserResponse])
def update_my_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current logged in user's profile details or password."""
    if user_update.name:
        current_user.name = user_update.name
    if user_update.password:
        current_user.hashed_password = hash_password(user_update.password)
    if user_update.role and current_user.role == "admin":
        current_user.role = user_update.role.value if hasattr(user_update.role, "value") else str(user_update.role)
    
    db.commit()
    db.refresh(current_user)
    return ApiResponse(
        success=True,
        message="Profile updated successfully.",
        data=UserResponse.model_validate(current_user)
    )


@router.post("/logout", response_model=ApiResponse[dict])
def logout(current_user: User = Depends(get_current_user)):
    """Logout current user."""
    return ApiResponse(
        success=True,
        message="Logged out successfully.",
        data={"email": current_user.email}
    )
