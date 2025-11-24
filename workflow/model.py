# models.py
from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from workflow.db import Base
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)   # hashed password
    role = Column(String, nullable=False, default="user")  # "user", "admin", (optional "org")

    donations = relationship("FoodDonation", back_populates="user", cascade="all, delete-orphan")
    distributions = relationship("Distribution", back_populates="user", cascade="all, delete-orphan")


class FoodDonation(Base):
    __tablename__ = "food_donations"

    donation_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    quantity = Column(JSON, nullable=False)   # list of food items, e.g. [{"item":"rice","qty":2}, ...]

    user = relationship("User", back_populates="donations")


class Distribution(Base):
    __tablename__ = "distribution"

    distribution_id = Column(Integer, primary_key=True, index=True)
    address = Column(String, nullable=False)
    state = Column(String, nullable=False)
    quantity = Column(JSON, nullable=False)     # list of items/quantities
    user_id = Column(Integer, ForeignKey("users.user_id"))  # admin or org who recorded it

    user = relationship("User", back_populates="distributions")

class OTPStore(Base):
    __tablename__ = "otp_store"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False)
    otp = Column(String, nullable=False)
    expires_at = Column(Integer, nullable=False)  # unix timestamp