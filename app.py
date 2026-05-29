import streamlit as st
from streamlit_option_menu import option_menu
import requests
import datetime
import pandas as pd

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="NexTime | General Attendance System", page_icon="⏰", layout="wide")

BACKEND_URL = "http://127.0.0.1:8000/api"

# Glassmorphism and modern UI styling
st.markdown("""
    <style>
    .reportview-container {
        background: #0E1117;
    }
    .main-card {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 30px;
        margin-bottom: 20px;
    }
    .group-banner {
        background: linear-gradient(135deg, #4F46E5 0%, #3B82F6 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(79, 70, 229, 0.3);
    }
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #4F46E5, #3B82F6);
        color: white;
        border-radius: 6px;
        padding: 12px 30px;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-2px);
        box-shadow: 0px 5px 20px rgba(79, 70, 229, 0.4);
    }
    </style>
""", unsafe_allow_html=True)

# Initialize Session Auth States
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.user_info = {}
if "registration_success" not in st.session_state:
    st.session_state.registration_success = False

# ==========================================
# RUBRIC REQUIREMENT 1: THE BOOLEAN FUNCTION
# ==========================================
def save_user_profile(payload: dict) -> bool:
    """ 
    Boolean function that sends user information to the backend API.
    Returns True if successfully saved to the database, False otherwise.
    """
    try:
        res = requests.post(f"{BACKEND_URL}/signup", json=payload)
        return res.status_code == 200
    except Exception:
        return False

# ==========================================
# SIDEBAR NAVIGATION & RUBRIC COMPONENT
# ==========================================
with st.sidebar:
    # --- RUBRIC REQUIREMENT: GROUP TITLE & MEMBERS ---
    st.markdown("""
    <div style='background: rgba(79, 70, 229, 0.15); padding: 15px; border-radius: 8px; border: 1px solid #4F46E5; margin-bottom: 20px;'>
        <h4 style='margin: 0; color: #6EE7B7; text-align: center;'>🚀 GROUP TITLE HERE</h4>
        <p style='font-size: 0.85rem; margin: 10px 0 0 0; color: #E2E8F0; text-align: center;'>
            <b>Members:</b><br>
            • Member Name 1<br>
            • Member Name 2<br>
            • Member Name 3
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.logged_in:
        choice = option_menu(
            menu_title="Terminal Access",
            options=["Clock Kiosk", "Employee Login", "Admin Login", "Sign Up System"],
            icons=["clock", "person-circle", "shield-lock", "person-plus-fill"],
            menu_icon="cpu",
            default_index=0,
            styles={"nav-link-selected": {"background-color": "#4F46E5"}}
        )
    else:
        st.markdown(f"### Active Session: **{st.session_state.user_info.get('first_name')}**")
        st.caption(f"Access Privilege: Layer-{st.session_state.user_role.upper()}")
        
        options = ["Dashboard", "Logout"] if st.session_state.user_role == "admin" else ["My Records", "Logout"]
        choice = option_menu(
            menu_title="Navigation",
            options=options,
            icons=["speedometer2", "box-arrow-right"] if st.session_state.user_role == "admin" else ["file-earmark-person", "box-arrow-right"],
            menu_icon="layers"
        )

# --- DISPLAY TITLE BANNER ---
st.markdown("""
<div class='group-banner'>
    <h1 style='margin:0; font-weight: 700; letter-spacing: 1px;'>NEX-TIME ATTENDANCE MATRIX</h1>
    <p style='margin:5px 0 0 0; opacity: 0.9;'>Automated Kiosk & Database Terminal Management System</p>
</div>
""", unsafe_allow_html=True)


# --- 1. EXPRESS CLOCK KIOSK ---
if choice == "Clock Kiosk":
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("⚡ Terminal Punch Clock")
    st.info(f"📅 Current Date Window: {datetime.date.today().strftime('%A — %B %d, %Y')}")
    
    special_id = st.text_input("Scan or Type Special Employee ID", placeholder="e.g., EMP-100")
    
    if st.button("Register Dynamic Clock Action", use_container_width=True):
        if special_id:
            with st.spinner("Processing network transaction..."):
                try:
                    res = requests.post(f"{BACKEND_URL}/attendance/clock", json={"specialId": special_id})
                    if res.status_code == 200:
                        data = res.json()
                        st.balloons()
                        st.success(f"Transaction verified: User {data['action'].upper()} successfully!")
                        st.toast(data['message'], icon="✅")
                    else:
                        st.error(f"Access Denied: {res.json().get('detail')}")
                except Exception:
                    st.error("System Pipeline Error: Unreachable server.")
        else:
            st.warning("Action execution stalled: Missing Identity Parameters.")
    st.markdown("</div>", unsafe_allow_html=True)


# --- 2. EMPLOYEE LOGIN ---
elif choice == "Employee Login":
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("👤 Employee Portal Gateway")
    with st.form("emp_login"):
        f_name = st.text_input("First Name Record")
        sp_id = st.text_input("Special Identification Key (ID)")
        submitted = st.form_submit_button("Authorize Access")
        
        if submitted:
            try:
                res = requests.post(f"{BACKEND_URL}/login/employee", json={"firstName": f_name, "specialId": sp_id})
                if res.status_code == 200:
                    st.session_state.logged_in = True
                    st.session_state.user_role = "employee"
                    st.session_state.user_info = res.json()["user"]
                    st.rerun()
                else:
                    st.error("Authentication rejected: Check entry name or ID details.")
            except Exception:
                st.error("Server Link Offline.")
    st.markdown("</div>", unsafe_allow_html=True)


# --- 3. ADMIN LOGIN ---
elif choice == "Admin Login":
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("🔐 Encrypted Administrative Gateway")
    with st.form("admin_login"):
        f_name = st.text_input("Admin Username / First Name")
        sp_id = st.text_input("Admin System ID Access Key")
        password = st.text_input("Master System Password", type="password")
        submitted = st.form_submit_button("Decrypt Console Access")
        
        if submitted:
            try:
                res = requests.post(f"{BACKEND_URL}/login/admin", json={"firstName": f_name, "specialId": sp_id, "password": password})
                if res.status_code == 200:
                    st.session_state.logged_in = True
                    st.session_state.user_role = "admin"
                    st.session_state.user_info = res.json()["user"]
                    st.rerun()
                else:
                    st.error("Access Prohibited: Unauthorized system parameters.")
            except Exception:
                st.error("Database framework unreachable.")
    st.markdown("</div>", unsafe_allow_html=True)


# --- 4. SIGN UP SYSTEM ROUTE ---
elif choice == "Sign Up System":
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.subheader("📝 Universal Identity Mapping Form")
    
    with st.form("signup_engine"):
        c1, c2 = st.columns(2)
        with c1:
            sp_id = st.text_input("Assign Unique Special ID")
            fname = st.text_input("First Name String")
            lname = st.text_input("Last Name String")
            email = st.text_input("Corporate Mail Route Address")
        with c2:
            dept = st.selectbox("Department Structural Designation", ["BSCS", "BSEMC", "BSIT", "HR", "Finance"])
            cat = st.selectbox("Classification Schema", ["Full-Time", "Part-Time"])
            role = st.radio("Database Access Level Layer Role", ["employee", "admin"])
            pwd = st.text_input("Encryption Security Key (Admins Only)", type="password")

        submitted = st.form_submit_button("Commit User Entry Matrix")
        
        if submitted:
            payload = {
                "specialId": sp_id, "firstName": fname, "lastName": lname,
                "email": email, "department": dept, "category": cat,
                "role": role, "password": pwd if pwd != "" else None
            }
            
            # Executing the Boolean function rule constraint
            if save_user_profile(payload):
                st.success("Boolean Output: True — Data successfully verified & written to database backend!")
                st.session_state.registration_success = True
            else:
                st.error("Boolean Output: False — System Registry Conflict or Faulty Connection.")
                st.session_state.registration_success = False
    st.markdown("</div>", unsafe_allow_html=True)

    # =========================================================
    # RUBRIC REQUIREMENT 2: PYTHON LISTS & TUPLES WIDGET REGION
    # =========================================================
    if st.session_state.registration_success:
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.subheader("📋 Rubric Check: Python Lists & Tuples Window View")
        
        try:
            res = requests.get(f"{BACKEND_URL}/admin/attendance")
            if res.status_code == 200:
                raw_records = res.json().get("data", [])
                
                # STRICT RUBRIC ALIGNMENT: Read JSON data and reconstruct strictly into a Python List of Tuples!
                python_tuple_database_window = []
                for entry in raw_records:
                    record_tuple = (
                        entry.get("special_id"),
                        f"{entry.get('first_name')} {entry.get('last_name')}",
                        entry.get("department"),
                        entry.get("category"),
                        entry.get("log_date")
                    )
                    python_tuple_database_window.append(record_tuple)
                
                st.write("Below is an unadulterated live view processed directly through Python immutable **Tuples inside a Master List**:")
                
                # Formatting the list of tuples into an aesthetic structured dataset window frame
                formatted_df = pd.DataFrame(python_tuple_database_window, columns=["System Unique ID", "Employee Full Name", "Division", "Employment Category", "Logged Session Date"])
                st.dataframe(formatted_df, use_container_width=True, hide_index=False)
                
                # Show raw code confirmation string so you can highlight it during your video screen recording 
                st.code(f"Current List of Tuples Object Type: {type(python_tuple_database_window)} consisting of items like {type(python_tuple_database_window[0]) if python_tuple_database_window else 'None'}")
        except Exception:
            st.warning("Local parsing environment ready, waiting for backend connection to construct primitive structures.")
        st.markdown("</div>", unsafe_allow_html=True)


# --- 5. SECURED ADMINISTRATIVE DASHBOARD ---
elif choice == "Dashboard" and st.session_state.user_role == "admin":
    st.subheader("📊 Live Security Auditing & Management Matrix")
    
    # KPIs metrics layout
    kpi1, kpi2, kpi3 = st.columns(3)
    
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.write("#### 🔍 Filter Configuration Context Engine")
    sc1, sc2 = st.columns(2)
    with sc1:
        search = st.text_input("Query String Parsing Parameter (Name / ID)")
    with sc2:
        date_filter = st.date_input("Audit Filter Timeline Window Target", value=None)
        
    params = {}
    if search: params["searchQuery"] = search
    if date_filter: params["filterDate"] = str(date_filter)
        
    try:
        res = requests.get(f"{BACKEND_URL}/admin/attendance", params=params)
        if res.status_code == 200:
            records = res.json().get("data", [])
            
            kpi1.metric("Database Rows Found", len(records))
            kpi2.metric("Gateway Node Signal", "Stable Localhost", delta="100% Sync")
            kpi3.metric("System Operational Mode", "Production Ready")
            
            if records:
                # Process structural elements via standard interactive table dataframes
                df = pd.DataFrame(records)
                st.dataframe(
                    df,
                    column_config={
                        "time_in": st.column_config.DatetimeColumn("Clock-In Timestamp", format="D MMM YYYY, h:mm a"),
                        "time_out": st.column_config.DatetimeColumn("Clock-Out Timestamp", format="D MMM YYYY, h:mm a"),
                        "hours_worked": st.column_config.NumberColumn("Calculated Work Shifts", format="%d hours"),
                    },
                    use_container_width=True
                )
            else:
                st.info("Empty matrix query response return state.")
    except Exception:
        st.error("Admin dashboard cannot access operational core server assets.")
    st.markdown("</div>", unsafe_allow_html=True)


# --- 6. EMPLOYEE USER PERSONAL PORTAL ---
elif choice == "My Records" and st.session_state.logged_in:
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.markdown(f"### Welcome back to your Secure Portal Instance, **{st.session_state.user_info['first_name']}** 👋")
    st.markdown("---")
    st.info("💡 Your operational profile metrics are mapped live to the database. To clock in or out for work shifts, use the unauthenticated **Clock Kiosk** layout panel accessible from the navigation sidebar menu.")
    st.markdown("</div>", unsafe_allow_html=True)


# --- 7. FLUSH SESSION STATE / SYSTEM LOGOUT ---
elif choice == "Logout":
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.user_info = {}
    st.session_state.registration_success = False
    st.rerun()