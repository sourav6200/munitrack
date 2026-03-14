import streamlit as st
import sqlite3
import re
from utils.database import DB_PATH, hash_pw, register_user

DEPARTMENTS = ["Roads", "Water", "Electricity", "Sanitation", "Parks", "Buildings", "Drainage"]


# ── helpers ──────────────────────────────────────────────────────────────────

def authenticate(email, password):
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email.strip().lower(), hash_pw(password))
        ).fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception:
        return None


def _valid_email(email):
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email.strip()))


def _valid_phone(phone):
    digits = re.sub(r"\D", "", phone)
    return 7 <= len(digits) <= 15


# ── shared page header ────────────────────────────────────────────────────────

def _page_header():
    st.markdown("""
    <style>
    .auth-logo   { font-size:44px; text-align:center; margin-bottom:6px; }
    .auth-title  { font-size:28px; font-weight:700; text-align:center; color:#f1f5f9; margin:0; }
    .auth-sub    { font-size:13px; text-align:center; color:#64748b; margin:4px 0 28px; }
    .strength-wrap { height:4px; background:#334155; border-radius:4px; margin:6px 0 2px; overflow:hidden; }
    .strength-bar  { height:100%; border-radius:4px; transition:width .3s, background .3s; }
    .strength-text { font-size:11px; }
    div[data-testid="stTabs"] button {
        font-size:15px !important;
        font-weight:600 !important;
        padding:10px 28px !important;
    }
    </style>
    <div style="max-width:500px;margin:0 auto;padding-top:40px;">
        <div class="auth-logo">🏛️</div>
        <p class="auth-title">MuniTrack</p>
        <p class="auth-sub">Municipality Issue Management System</p>
    </div>
    """, unsafe_allow_html=True)


# ── Login tab ─────────────────────────────────────────────────────────────────

def _login_tab():
    _, col, _ = st.columns([1, 5, 1])
    with col:
        email    = st.text_input("Email address", placeholder="you@example.com", key="li_email")
        password = st.text_input("Password", type="password", placeholder="••••••", key="li_pass")

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        if st.button("Sign In", use_container_width=True, type="primary", key="li_submit"):
            if not email or not password:
                st.error("Please enter your email and password.")
            else:
                user = authenticate(email, password)
                if user:
                    st.session_state["user"] = user
                    st.session_state.pop("auth_tab", None)
                    st.rerun()
                else:
                    st.error("Incorrect email or password.")

        st.markdown("---")
        st.markdown("<p style='font-size:13px;color:#64748b;margin-bottom:6px;'>Quick demo login (password: <code>123</code>)</p>", unsafe_allow_html=True)
        demo_accounts = [
            ("Citizen",              "citizen@muni.gov"),
            ("Admin",                "admin@muni.gov"),
            ("Worker - Roads",       "worker1@muni.gov"),
            ("Worker - Water",       "worker2@muni.gov"),
            ("Worker - Sanitation",  "worker3@muni.gov"),
        ]
        dcols = st.columns(2)
        for i, (label, mail) in enumerate(demo_accounts):
            with dcols[i % 2]:
                if st.button(label, key=f"demo_{i}", use_container_width=True):
                    user = authenticate(mail, "123")
                    if user:
                        st.session_state["user"] = user
                        st.rerun()

        st.markdown(
            "<p style='text-align:center;font-size:13px;color:#64748b;margin-top:16px;'>"
            "New to MuniTrack? Switch to the <b>Register</b> tab above.</p>",
            unsafe_allow_html=True
        )


# ── Register tab ──────────────────────────────────────────────────────────────

def _register_tab():
    _, col, _ = st.columns([1, 5, 1])
    with col:

        # Role selector
        st.markdown(
            "<p style='font-size:12px;font-weight:600;color:#94a3b8;letter-spacing:.5px;"
            "text-transform:uppercase;margin-bottom:10px;'>Select Your Role</p>",
            unsafe_allow_html=True
        )

        if "reg_role" not in st.session_state:
            st.session_state["reg_role"] = "Citizen"

        role_options = {
            "Citizen": ("👤", "Report local issues to the municipality"),
            "Worker":  ("🔧", "Resolve issues assigned by admin"),
        }

        r1, r2 = st.columns(2)
        for col_obj, (rname, (icon, rdesc)) in zip([r1, r2], role_options.items()):
            with col_obj:
                is_sel = st.session_state["reg_role"] == rname
                border = "#3b82f6" if is_sel else "#334155"
                bg     = "rgba(59,130,246,.13)" if is_sel else "#1e293b"
                check  = "✓ " if is_sel else ""
                st.markdown(
                    f"<div style='border:2px solid {border};border-radius:12px;background:{bg};"
                    f"padding:16px 12px;text-align:center;cursor:pointer;'>"
                    f"<div style='font-size:28px;margin-bottom:6px;'>{icon}</div>"
                    f"<div style='font-size:14px;font-weight:700;color:#f1f5f9;'>{check}{rname}</div>"
                    f"<div style='font-size:11px;color:#64748b;margin-top:3px;'>{rdesc}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
                if st.button(f"Select {rname}", key=f"pick_{rname}", use_container_width=True):
                    st.session_state["reg_role"] = rname
                    st.rerun()

        role = st.session_state["reg_role"].lower()
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # Personal info
        st.markdown("**Personal Information**")
        name  = st.text_input("Full Name *", placeholder="e.g. Amit Kumar Sharma", key="reg_name")

        ec1, ec2 = st.columns(2)
        with ec1:
            email = st.text_input("Email Address *", placeholder="amit@example.com", key="reg_email")
        with ec2:
            phone = st.text_input("Phone Number *", placeholder="9876543210", key="reg_phone")

        # Worker department
        dept = None
        if role == "worker":
            st.markdown("**Work Details**")
            dept = st.selectbox("Department *", DEPARTMENTS, key="reg_dept")
            st.markdown(
                "<div style='background:#1e3a5f;border:1px solid #1d4ed8;border-radius:8px;"
                "padding:10px 14px;font-size:12px;color:#93c5fd;margin-bottom:8px;'>"
                "Worker accounts are visible to Admin who will assign you tasks.</div>",
                unsafe_allow_html=True
            )

        # Password
        st.markdown("**Set a Password**")
        pc1, pc2 = st.columns(2)
        with pc1:
            pw1 = st.text_input("Password *", type="password", placeholder="Min 6 chars", key="reg_pw1")
        with pc2:
            pw2 = st.text_input("Confirm Password *", type="password", placeholder="Re-enter", key="reg_pw2")

        # Strength meter
        if pw1:
            score = 0
            hints = []
            if len(pw1) >= 6:                    score += 1
            else:                                hints.append("6+ chars")
            if len(pw1) >= 10:                   score += 1
            if re.search(r"[A-Z]", pw1):         score += 1
            else:                                hints.append("uppercase")
            if re.search(r"\d", pw1):            score += 1
            else:                                hints.append("number")
            if re.search(r"[^A-Za-z0-9]", pw1): score += 1
            else:                                hints.append("symbol")

            colours = ["#ef4444", "#f59e0b", "#f59e0b", "#22c55e", "#22c55e"]
            labels  = ["Weak", "Fair", "Good", "Strong", "Very strong"]
            idx     = min(score, 4)
            pct     = int((score / 5) * 100)
            hint_str = (f" &nbsp;· Add: <span style='color:#64748b;'>{', '.join(hints)}</span>" if hints else "")
            st.markdown(
                f"<div class='strength-wrap'>"
                f"<div class='strength-bar' style='width:{pct}%;background:{colours[idx]};'></div>"
                f"</div>"
                f"<span class='strength-text' style='color:{colours[idx]};font-size:12px;'>{labels[idx]}</span>"
                + hint_str,
                unsafe_allow_html=True
            )

        if pw2 and pw1 != pw2:
            st.markdown("<p style='color:#ef4444;font-size:12px;margin-top:4px;'>Passwords do not match.</p>",
                        unsafe_allow_html=True)

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        agreed = st.checkbox(
            "I confirm that the information provided is accurate and will be used "
            "for municipality services only.",
            key="reg_agree"
        )

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("Create Account", use_container_width=True, type="primary", key="reg_submit"):
            errors = []
            if not name.strip():            errors.append("Full name is required.")
            if not _valid_email(email):     errors.append("Enter a valid email address.")
            if not _valid_phone(phone):     errors.append("Enter a valid phone number (7–15 digits).")
            if len(pw1) < 6:               errors.append("Password must be at least 6 characters.")
            if pw1 != pw2:                 errors.append("Passwords do not match.")
            if not agreed:                 errors.append("Please accept the terms to continue.")
            if role == "worker" and not dept:
                errors.append("Please select your department.")

            if errors:
                for e in errors:
                    st.error(e)
                return

            ok, result = register_user(
                name=name, email=email, password=pw1,
                role=role, phone=phone, dept=dept
            )

            if ok:
                st.success(f"Account created! Welcome, **{result['name']}**. You are now logged in.")
                st.balloons()
                st.session_state["user"] = result
                st.rerun()
            else:
                st.error(f"Registration failed: {result}")

        st.markdown(
            "<p style='text-align:center;font-size:13px;color:#64748b;margin-top:16px;'>"
            "Already have an account? Switch to the <b>Login</b> tab above.</p>",
            unsafe_allow_html=True
        )


# ── Public entry point ────────────────────────────────────────────────────────

def login_page():
    _page_header()
    _, col, _ = st.columns([1, 5, 1])
    with col:
        tab_login, tab_register = st.tabs(["  Login  ", "  Register  "])
        with tab_login:
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            _login_tab()
        with tab_register:
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            _register_tab()
