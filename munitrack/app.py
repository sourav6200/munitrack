import streamlit as st
from utils.database import init_db
from utils.auth import login_page
from pages import citizen, admin, worker

st.set_page_config(
    page_title="MuniTrack — Municipality Issue Manager",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject global CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0a1628 !important;
    border-right: 1px solid #1e3a5f;
}
section[data-testid="stSidebar"] .stRadio label {
    color: #94a3b8 !important;
    font-size: 14px;
}

/* Hide default streamlit menu */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Status badges */
.badge-pending  { background:#fef3c7; color:#92400e; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
.badge-assigned { background:#dbeafe; color:#1e40af; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
.badge-resolved { background:#dcfce7; color:#166534; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
.badge-rejected { background:#fee2e2; color:#991b1b; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }

/* Priority */
.priority-high   { background:#fee2e2; color:#991b1b; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:700; }
.priority-medium { background:#fef3c7; color:#92400e; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:700; }
.priority-low    { background:#dcfce7; color:#166534; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:700; }

/* Cards */
.issue-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 16px 18px;
    margin-bottom: 10px;
    transition: border-color 0.15s;
}
.stat-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 16px 20px;
    text-align: center;
}
.stat-number { font-size: 32px; font-weight: 700; margin: 0; }
.stat-label  { font-size: 12px; color: #94a3b8; margin: 0; }

/* GPS display */
.gps-box {
    background: #0d2137;
    border: 1px solid #1e3a5f;
    border-radius: 8px;
    padding: 10px 16px;
    font-family: monospace;
    color: #22c55e;
    font-size: 13px;
    display: inline-block;
    margin: 8px 0;
}

/* Timeline */
.timeline-item {
    border-left: 2px solid #334155;
    padding: 0 0 16px 16px;
    margin-left: 8px;
    position: relative;
    font-size: 13px;
    color: #94a3b8;
}
.timeline-item::before {
    content: '';
    width: 10px; height: 10px;
    border-radius: 50%;
    background: #3b82f6;
    position: absolute;
    left: -6px; top: 2px;
}

.divider { border: none; border-top: 1px solid #334155; margin: 16px 0; }

/* Buttons */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 500 !important;
}
</style>
""", unsafe_allow_html=True)

# Init DB on first run
init_db()

# Auth check
if "user" not in st.session_state:
    login_page()
    st.stop()

user = st.session_state["user"]

# ── Sidebar ──────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style='padding:12px 0 20px;'>
        <div style='font-size:22px;font-weight:700;color:#f1f5f9;'>🏛️ MuniTrack</div>
        <div style='font-size:12px;color:#64748b;margin-top:2px;'>Municipality Issue Manager</div>
    </div>
    <div style='background:#273449;border-radius:10px;padding:12px 14px;margin-bottom:20px;border:1px solid #334155;'>
        <div style='font-size:13px;font-weight:600;color:#f1f5f9;'>{user["name"]}</div>
        <div style='font-size:11px;color:#94a3b8;'>{user["email"]}</div>
        <div style='margin-top:6px;'>
            <span style='background:{"#1d4ed8" if user["role"]=="citizen" else "#7e22ce" if user["role"]=="admin" else "#15803d"};
                         color:{"#93c5fd" if user["role"]=="citizen" else "#d8b4fe" if user["role"]=="admin" else "#86efac"};
                         padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;text-transform:uppercase;'>
                {user["role"]}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if user["role"] == "citizen":
        page = st.radio("Navigation", ["🏠 Dashboard", "📋 My Reports", "📍 Report Issue"], label_visibility="collapsed")
    elif user["role"] == "admin":
        page = st.radio("Navigation", ["🏠 Dashboard", "📋 All Issues", "👷 Workers", "📊 Analytics"], label_visibility="collapsed")
    else:
        page = st.radio("Navigation", ["🏠 Dashboard", "🔧 My Tasks"], label_visibility="collapsed")

    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
    if st.button("🚪 Sign Out", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ── Route to pages ────────────────────────────────────────
if user["role"] == "citizen":
    if "Dashboard" in page:
        citizen.dashboard()
    elif "My Reports" in page:
        citizen.my_reports()
    elif "Report Issue" in page:
        citizen.report_issue()

elif user["role"] == "admin":
    if "Dashboard" in page:
        admin.dashboard()
    elif "All Issues" in page:
        admin.all_issues()
    elif "Workers" in page:
        admin.workers_page()
    elif "Analytics" in page:
        admin.analytics()

elif user["role"] == "worker":
    if "Dashboard" in page:
        worker.dashboard()
    elif "My Tasks" in page:
        worker.my_tasks()
