import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.config import settings
from app.models.user import PasswordResetOTP
from app.utils.security import generate_otp

logger = logging.getLogger(__name__)


def create_otp(db: Session, email: str) -> str:
    """Generate and record a 6-digit OTP for password reset."""
    code = generate_otp(6)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
    
    # Invalidate any previous unused OTPs for this email
    db.query(PasswordResetOTP).filter(
        PasswordResetOTP.email == email,
        PasswordResetOTP.is_used == False
    ).update({"is_used": True})
    
    otp_record = PasswordResetOTP(
        email=email,
        otp_code=code,
        expires_at=expires_at,
        is_used=False
    )
    db.add(otp_record)
    db.commit()
    db.refresh(otp_record)
    
    # In development/demo, log the OTP clearly so the user or tester can use it immediately!
    logger.info(f"===> [OTP-RESET] OTP code for {email} is: {code} (Valid for {settings.OTP_EXPIRE_MINUTES} minutes)")
    print(f"\n[StockSense OTP] Password reset code for {email}: {code} (Expires in {settings.OTP_EXPIRE_MINUTES}m)\n")
    return code


def verify_otp(db: Session, email: str, otp_code: str) -> bool:
    """Verify if the OTP is valid, unused, and not expired."""
    now = datetime.now(timezone.utc)
    record = db.query(PasswordResetOTP).filter(
        PasswordResetOTP.email == email,
        PasswordResetOTP.otp_code == otp_code,
        PasswordResetOTP.is_used == False,
        PasswordResetOTP.expires_at >= now
    ).first()
    return record is not None


def mark_otp_as_used(db: Session, email: str, otp_code: str) -> bool:
    """Mark the OTP as consumed after successful password reset."""
    now = datetime.now(timezone.utc)
    record = db.query(PasswordResetOTP).filter(
        PasswordResetOTP.email == email,
        PasswordResetOTP.otp_code == otp_code,
        PasswordResetOTP.is_used == False,
        PasswordResetOTP.expires_at >= now
    ).first()
    if record:
        record.is_used = True
        db.commit()
        return True
    return False
