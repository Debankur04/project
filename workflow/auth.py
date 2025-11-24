# auth.py
import time
import bcrypt
from sqlalchemy.orm import Session
from workflow.model import User, OTPStore
from workflow.email_utils import generate_otp, send_otp_email

# Allowed roles
ALLOWED_ROLES = {"user", "admin", "org"}

# Only these emails can become admin
ADMIN_ALLOWED_EMAILS = {
    "abc.org@gmail.com",
    'debankurdutta04@gmail.com',
}


# ------------------------------------------------------
# PASSWORD UTILS
# ------------------------------------------------------
def hash_password(password: str) -> str:
    """Generate a bcrypt hash of the given password."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


# ------------------------------------------------------
# USER ACCOUNT OPERATIONS
# ------------------------------------------------------
def create_user(db: Session, email: str, username: str, password: str, role: str = "user"):
    """
    Create a new user with safe role enforcement.
    - Only whitelisted emails can become admin.
    - Duplicate emails are rejected.
    """

    email = email.strip().lower()
    username = username.strip()
    role = role.lower()

    # Validate role
    if role not in ALLOWED_ROLES:
        raise ValueError(f"Invalid role: {role}. Allowed roles: {ALLOWED_ROLES}")

    # Restrict admin registration
    if role == "admin" and email not in ADMIN_ALLOWED_EMAILS:
        raise ValueError("Only approved admin emails can register as admin.")

    # Check if email already exists
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise ValueError("A user with this email already exists.")

    # Hash password and create user
    hashed = hash_password(password)
    new_user = User(email=email, username=username, password=hashed, role=role)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def authenticate_user(db: Session, email: str, password: str):
    """
    Basic email + password authentication.
    Used BEFORE OTP verification.
    """
    email = email.strip().lower()
    user = db.query(User).filter(User.email == email).first()

    if not user:
        return None
    if not verify_password(password, user.password):
        return None

    return user


def get_user_by_email(db: Session, email: str):
    email = email.strip().lower()
    return db.query(User).filter(User.email == email).first()


def set_user_role(db: Session, user_id: int, new_role: str):
    """
    Safely update user roles.
    - Prevent unauthorized admin assignment.
    """

    new_role = new_role.lower()

    if new_role not in ALLOWED_ROLES:
        raise ValueError(f"Invalid role: {new_role}. Allowed: {ALLOWED_ROLES}")

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise ValueError("User not found.")

    # Prevent forced admin via backend
    if new_role == "admin" and user.email not in ADMIN_ALLOWED_EMAILS:
        raise ValueError("This user is not allowed to become admin.")

    user.role = new_role
    db.commit()
    db.refresh(user)
    return user


# ------------------------------------------------------
# OTP LOGIC
# ------------------------------------------------------
def create_and_send_otp(email: str, db: Session):
    """
    Create a 6-digit OTP, store it with 5 min expiry,
    delete previous OTPs, and send email.
    """
    email = email.strip().lower()

    otp = generate_otp()
    expires_at = int(time.time()) + 300  # valid for 5 minutes

    # Remove old OTPs for this email
    db.query(OTPStore).filter(OTPStore.email == email).delete()

    # Save new OTP
    otp_record = OTPStore(email=email, otp=otp, expires_at=expires_at)
    db.add(otp_record)
    db.commit()

    # Send via email provider
    send_otp_email(email, otp)
    return True


def verify_otp(email: str, otp: str, db: Session):
    """
    Verify that OTP matches and is not expired.
    Auto-deletes OTP on success.
    """
    email = email.strip().lower()
    otp = otp.strip()

    record = db.query(OTPStore).filter(OTPStore.email == email).first()

    if not record:
        return False

    if record.otp != otp:
        return False

    if time.time() > record.expires_at:
        return False  # expired

    # OTP valid → delete it
    db.delete(record)
    db.commit()
    return True
