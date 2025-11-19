import streamlit as st
import pandas as pd
from workflow.db import SessionLocal
from workflow.auth import authenticate_user, create_user
from workflow.actions import (
    add_donation,
    get_user_donations,
    get_distribution_history,
    get_all_donations,
    get_stock_overview,
    add_distribution
)

# ---------------------------------------------------------
# INITIAL SETUP
# ---------------------------------------------------------

st.set_page_config(page_title="Food Donation App", layout="wide")

def get_db():
    return SessionLocal()

# ---------------------------------------------------------
# AUTH PAGES
# ---------------------------------------------------------

def login_page():
    st.subheader("Login")

    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login", key="login_button"):
        db = get_db()
        user = authenticate_user(db, email, password)

        if user:
            st.session_state.email = user.email
            st.session_state.role = user.role
            st.session_state.user_id = user.user_id
            st.success(f"Logged in as {user.role.capitalize()}")
            st.rerun()
        else:
            st.error("Invalid email or password.")


def signup_page():
    st.subheader("Create Account")

    email = st.text_input("Email", key="signup_email")
    username = st.text_input("Username", key="signup_username")
    password = st.text_input("Password", type="password", key="signup_password")

    role = st.selectbox(
        "Select Your Role",
        ["user", "admin", "org"],
        key="signup_role"
    )

    if st.button("Sign Up", key="signup_button"):
        db = get_db()
        try:
            create_user(
                db,
                email=email,
                username=username,
                password=password,
                role=role,
            )
            st.success("🎉 Account created successfully!")
            st.info("➡️ Please go to the **Login** tab and sign in.")
        except Exception as e:
            st.error(str(e))


def auth_gateway():
    st.title("🍱 Food Donation & Distribution App")

    tab_login, tab_signup = st.tabs(["Login", "New User"])
    with tab_login:
        login_page()
    with tab_signup:
        signup_page()

# ---------------------------------------------------------
# USER PAGES
# ---------------------------------------------------------

def page_user_donate():
    st.header("Donate Food")

    item = st.text_input("Food Item", key="donate_item")
    qty = st.number_input("Quantity", min_value=1, key="donate_qty")

    if st.button("Submit Donation", key="donate_button"):
        db = get_db()
        payload = [{"item": item, "qty": qty}]
        add_donation(db, st.session_state.user_id, payload)
        st.success("Donation recorded successfully!")


def page_user_my_donations():
    st.header("My Donations")

    db = get_db()
    donations = get_user_donations(db, st.session_state.user_id)

    if not donations:
        st.info("You have not made any donations yet.")
        return

    rows = []
    for d in donations:
        for item in d.quantity:
            rows.append({
                "Donation ID": d.donation_id,
                "Item": item["item"],
                "Quantity": item["qty"]
            })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)


def page_user_distribution():
    st.header("Distribution History")

    db = get_db()
    records = get_distribution_history(db)

    if not records:
        st.info("No distribution records available.")
        return

    rows = []
    for d in records:
        for item in d.quantity:
            rows.append({
                "Distribution ID": d.distribution_id,
                "Address": d.address,
                "State": d.state,
                "Item": item["item"],
                "Quantity": item["qty"]
            })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)


def page_user_where_donated():
    st.header("Where Did My Donations Go?")

    db = get_db()
    dist = get_distribution_history(db)
    donations = get_user_donations(db, st.session_state.user_id)

    user_items = []
    for d in donations:
        for item in d.quantity:
            user_items.append(item["item"].lower())

    rows = []
    for dis in dist:
        for item in dis.quantity:
            if item["item"].lower() in user_items:
                rows.append({
                    "Distribution ID": dis.distribution_id,
                    "Address": dis.address,
                    "State": dis.state,
                    "Item Distributed": item["item"],
                    "Quantity": item["qty"]
                })

    if not rows:
        st.info("Your donated items have not been distributed yet.")
        return

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)

# ---------------------------------------------------------
# ADMIN PAGES
# ---------------------------------------------------------

def page_admin_manage():
    st.header("Manage All Donations")

    db = get_db()
    donations = get_all_donations(db)

    if not donations:
        st.info("No donation entries found.")
        return

    rows = []
    for d in donations:
        for item in d.quantity:
            rows.append({
                "Donation ID": d.donation_id,
                "User ID": d.user_id,
                "Item": item["item"],
                "Quantity": item["qty"]
            })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)


def page_admin_stock():
    st.header("Total Food Stock Overview")

    db = get_db()
    stock = get_stock_overview(db)

    if not stock:
        st.info("No donations yet.")
        return

    df = pd.DataFrame([
        {"Item": k, "Total Quantity": v} for k, v in stock.items()
    ])

    st.subheader("📦 Combined Stock")
    st.dataframe(df, use_container_width=True)


def page_admin_record_distribution():
    st.header("Record Distribution")

    address = st.text_input("Address", key="dist_address")
    state = st.text_input("State", key="dist_state")

    item = st.text_input("Food Item", key="dist_item")
    qty = st.number_input("Quantity", min_value=1, key="dist_qty")

    if "dist_items" not in st.session_state:
        st.session_state.dist_items = []

    if st.button("Add Item", key="dist_add_item"):
        st.session_state.dist_items.append({"item": item, "qty": qty})
        st.success("Item added.")

    if st.session_state.dist_items:
        st.write("📦 Items to Distribute:")
        df = pd.DataFrame(st.session_state.dist_items)
        st.dataframe(df, use_container_width=True)

    if st.button("Submit Distribution", key="dist_submit"):
        if not st.session_state.dist_items:
            st.error("Add at least one item.")
            return

        db = get_db()
        add_distribution(
            db,
            user_id=st.session_state.user_id,
            address=address,
            state=state,
            quantity=st.session_state.dist_items
        )

        st.success("Distribution recorded successfully!")
        st.session_state.dist_items = []

# ---------------------------------------------------------
# MAIN APP (RBAC LOGIC)
# ---------------------------------------------------------

def main():
    if "email" not in st.session_state:
        st.session_state.email = None
        st.session_state.role = None
        st.session_state.user_id = None

    if st.session_state.email is None:
        auth_gateway()
        return

    st.sidebar.success(f"Logged in as {st.session_state.email} ({st.session_state.role})")

    if st.sidebar.button("Logout", key="logout_btn"):
        st.session_state.email = None
        st.session_state.role = None
        st.session_state.user_id = None
        st.rerun()

    # USER
    if st.session_state.role == "user":
        menu = st.sidebar.radio(
            "Menu",
            ["Donate", "My Donations",  "Where Did My Food Go?"],
            key="user_menu"
        )
        if menu == "Donate":
            page_user_donate()
        elif menu == "My Donations":
            page_user_my_donations()
        # elif menu == "Distribution History":
        #     page_user_distribution()
        elif menu == "Where Did My Food Go?":
            page_user_where_donated()

    # ADMIN
    elif st.session_state.role == "admin":
        menu = st.sidebar.radio(
            "Admin Menu",
            ["Manage Donations", "Stock Overview", "Record Distribution"],
            key="admin_menu"
        )
        if menu == "Manage Donations":
            page_admin_manage()
        elif menu == "Stock Overview":
            page_admin_stock()
        elif menu == "Record Distribution":
            page_admin_record_distribution()

    # ORG
    elif st.session_state.role == "org":
        st.header("ORG Dashboard (Coming Soon)")
        st.info("Org-level functionality will be added.")

if __name__ == "__main__":
    main()
