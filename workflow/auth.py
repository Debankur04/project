# auth.py
import bcrypt
from sqlalchemy.orm import Session
from workflow.model import User

# Allowed roles (you can extend)
ALLOWED_ROLES = {"user", "admin", "org"}

# ---------------- PASSWORD UTILS ---------------- #

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


# ---------------- USER OPERATIONS ---------------- #

def create_user(db: Session, email: str, username: str, password: str, role: str = "user"):
    """
    Create a new user. Role defaults to 'user'. If role is invalid, ValueError is raised.
    """
    role = role.lower()
    if role not in ALLOWED_ROLES:
        raise ValueError(f"Invalid role: {role}. Allowed: {ALLOWED_ROLES}")

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise ValueError("User with this email already exists.")

    hashed = hash_password(password)
    new_user = User(email=email, username=username, password=hashed, role=role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def authenticate_user(db: Session, email: str, password: str):
    """
    Returns User instance if authentication succeeds, else None.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def set_user_role(db: Session, user_id: int, new_role: str):
    new_role = new_role.lower()
    if new_role not in ALLOWED_ROLES:
        raise ValueError(f"Invalid role: {new_role}. Allowed: {ALLOWED_ROLES}")
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise ValueError("User not found.")
    user.role = new_role
    db.commit()
    db.refresh(user)
    return user
