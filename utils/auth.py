import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials

def get_gspread_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/spreadsheets"
    ]

    # ✅ Use secrets directly — no need for json.loads
    creds_dict = st.secrets["google_creds"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
    client = gspread.authorize(creds)
    return client


# --- USER CREDENTIALS ---
CREDENTIALS = {
    "main": {"admin": "mainpass"},
    "trade_sheet": {"trader": "traderpass"},
    "daily_transaction": {"dailyuser": "dailypass"},
    "bank_statements": {"bankuser": "bankerpass1"},
    "database": {"dbadmin": "dbpass1"},
    "finance": {"financeuser": "financepass"},  # Finance credentials
    "hr": {"hruser": "hrpass"}  # HR credentials
}

# --- OPTIONAL APP-WIDE LOGIN ---
def app_login():
    st.session_state.setdefault("app_authenticated", True)
    return True

# --- PAGE-SPECIFIC AUTH ---
def check_access(section_key: str):
    if "auth" not in st.session_state:
        st.session_state.auth = {}

    if st.session_state.auth.get(section_key, {}).get("authenticated"):
        return True

    st.subheader("🔐 Login Required")
    username = st.text_input("Username", key=f"{section_key}_username")
    password = st.text_input("Password", type="password", key=f"{section_key}_password")

    if st.button("Login", key=f"{section_key}_login"):
        valid_users = CREDENTIALS.get(section_key, {})
        if username in valid_users and password == valid_users[username]:
            st.session_state.auth[section_key] = {
                "authenticated": True,
                "username": username,
            }
            st.success(f"Welcome, {username}!")
            st.rerun()
        else:
            st.error("Invalid credentials")
            return False

    st.stop()

# --- LOGOUT ---
def logout(section_key: str):
    if st.session_state.get("auth", {}).get(section_key, {}).get("authenticated"):
        if st.button("🚪 Logout"):
            st.session_state.auth[section_key] = {"authenticated": False}
            st.success("Logged out successfully")
            st.rerun()
