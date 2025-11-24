# crud.py
from sqlalchemy.orm import Session
from workflow.model import FoodDonation, Distribution


# 1) User → Add Donation
def add_donation(db: Session, user_id: int, quantity: list):
    donation = FoodDonation(user_id=user_id, quantity=quantity)
    db.add(donation)
    db.commit()
    db.refresh(donation)
    return donation


# 2) User → Get Past Donations
def get_user_donations(db: Session, user_id: int):
    return (
        db.query(FoodDonation)
        .filter(FoodDonation.user_id == user_id)
        .order_by(FoodDonation.donation_id.desc())
        .all()
    )


# 3) User → Watch Distribution History
def get_distribution_history(db: Session):
    return (
        db.query(Distribution)
        .order_by(Distribution.distribution_id.desc())
        .all()
    )


# 4) Admin → Manage All Donations
def get_all_donations(db: Session):
    return (
        db.query(FoodDonation)
        .order_by(FoodDonation.donation_id.desc())
        .all()
    )


# 5) Admin → Stock Overview (Aggregate Quantity)
def get_stock_overview(db: Session):
    """
    Returns a dict: { "rice": 20, "dal": 15, ... }
    Aggregates all donation quantity JSON arrays.
    """
    donations = db.query(FoodDonation).all()
    stock = {}

    for d in donations:
        for item in d.quantity:  # each item = { "item": "rice", "qty": 5 }
            name = item["item"]
            qty = item["qty"]
            stock[name] = stock.get(name, 0) + qty

    return stock

def add_distribution(db, user_id: int, address: str, state: str, quantity: list):
    # Step 1: Get current stock
    current_stock = get_stock_overview(db)

    # Step 2: Validate
    for item in quantity:
        name = item["item"].lower()
        qty = item["qty"]

        if name not in current_stock:
            raise Exception(f"Item '{name}' is not in stock.")
        if current_stock[name] < qty:
            raise Exception(
                f"Not enough '{name}' in stock. Available: {current_stock[name]}, Requested: {qty}"
            )

    # Step 3: If everything ok → record distribution
    new_dis = Distribution(
        user_id=user_id,
        address=address,
        state=state,
        quantity=quantity,
    )

    db.add(new_dis)
    db.commit()
    db.refresh(new_dis)

    return new_dis
