import streamlit as st
from utils.database import (
    get_issues, get_issue, get_stats, resolve_issue, get_timeline
)
from utils.ui import (
    stat_cards, render_issue_card, render_timeline,
    render_image, status_badge, priority_badge, category_chip,
    fmt_date, image_to_bytes, gps_box
)


def _task_detail(issue_id):
    user = st.session_state["user"]
    issue = get_issue(issue_id)
    if not issue:
        st.error("Task not found.")
        return

    col_title, col_back = st.columns([4, 1])
    with col_title:
        st.markdown(f"### {issue['title']}")
    with col_back:
        if st.button("← Back", key="worker_back"):
            st.session_state.pop("worker_view_id", None)
            st.session_state.pop("resolve_img", None)
            st.rerun()

    st.markdown(
        f"{status_badge(issue['status'])} &nbsp; {priority_badge(issue['priority'])} &nbsp; {category_chip(issue['category'])}",
        unsafe_allow_html=True
    )
    st.markdown(f"<p style='color:#94a3b8;margin-top:8px;font-size:14px;'>{issue['description']}</p>",
                unsafe_allow_html=True)
    st.markdown("---")

    info_col, gps_col = st.columns(2)
    with info_col:
        st.markdown(f"**📍 Address:** {issue['address']}")
        st.markdown(f"**🗓️ Reported:** {fmt_date(issue['reported_at'])}")
        st.markdown(f"**📌 Assigned:** {fmt_date(issue.get('assigned_at'))}")
        if issue.get("resolved_at"):
            st.markdown(f"**✅ Resolved:** {fmt_date(issue['resolved_at'])}")
    with gps_col:
        gps_box(issue["lat"], issue["lng"])

    st.markdown("#### 📷 Photos")
    img_c1, img_c2 = st.columns(2)
    with img_c1:
        render_image(issue.get("before_image"), "📸 Before (reported)", height=200)
    with img_c2:
        if issue.get("after_image"):
            render_image(issue["after_image"], "✅ After (resolved)", height=200)
        else:
            render_image(None, "📷 After photo — not uploaded yet", height=200)

    # Resolve section
    if issue["status"] == "assigned" and issue["worker_id"] == user["id"]:
        st.markdown("---")
        st.markdown("### ✅ Mark Issue as Resolved")
        st.markdown("Upload an after-resolution photo from the same spot and provide current GPS coordinates.")

        with st.form("resolve_form"):
            after_photo = st.file_uploader(
                "📷 Upload After-Resolution Photo *",
                type=["jpg", "jpeg", "png", "webp"],
                help="Take a photo from the same spot showing the issue is resolved"
            )
            if after_photo:
                st.image(after_photo, caption="After-resolution preview", use_container_width=True)

            st.markdown("**📡 Current GPS Coordinates** (from your location at the site)")
            g1, g2 = st.columns(2)
            with g1:
                r_lat = st.number_input("Latitude", value=float(issue["lat"]), format="%.6f", step=0.000001)
            with g2:
                r_lng = st.number_input("Longitude", value=float(issue["lng"]), format="%.6f", step=0.000001)

            st.markdown(f"""
            <div class="gps-box" style="margin:4px 0 8px;">
                📡 Resolution GPS: {r_lat:.6f}, {r_lng:.6f}
            </div>
            """, unsafe_allow_html=True)

            remarks = st.text_area("Remarks (optional)", placeholder="Describe what was done to fix the issue...")

            submitted = st.form_submit_button("✅ Submit Resolution", type="primary", use_container_width=True)

        if submitted:
            if not after_photo:
                st.error("Please upload the after-resolution photo.")
                return
            img_bytes = image_to_bytes(after_photo)
            resolve_issue(issue_id, user["name"], img_bytes)
            st.success("🎉 Issue marked as resolved! Great work!")
            st.balloons()
            st.session_state.pop("worker_view_id", None)
            st.rerun()

    elif issue["status"] == "resolved":
        st.success("✅ You have already resolved this issue.")

    st.markdown("#### 📅 Activity Timeline")
    tl = get_timeline(issue_id)
    render_timeline(tl)


def dashboard():
    user = st.session_state["user"]

    if "worker_view_id" in st.session_state:
        _task_detail(st.session_state["worker_view_id"])
        return

    st.markdown("## 🏠 Worker Dashboard")
    st.markdown(f"Welcome, **{user['name']}** ({user.get('dept', '')} Dept.)")

    stats = get_stats({"worker_id": user["id"]})
    stat_cards(stats)

    # Active tasks first
    active = get_issues({"worker_id": user["id"], "status": "Assigned"})
    if active:
        st.markdown("#### 🔧 Active Tasks (need resolution)")
        for iss in active:
            if render_issue_card(iss, "Resolve Issue"):
                st.session_state["worker_view_id"] = iss["id"]
                st.rerun()
    else:
        st.success("No active tasks right now.")

    st.markdown("#### 📋 Recent Tasks")
    recent = get_issues({"worker_id": user["id"]})[:5]
    for iss in recent:
        if render_issue_card(iss, "View Details"):
            st.session_state["worker_view_id"] = iss["id"]
            st.rerun()


def my_tasks():
    user = st.session_state["user"]

    if "worker_view_id" in st.session_state:
        _task_detail(st.session_state["worker_view_id"])
        return

    st.markdown("## 🔧 My Tasks")

    status_filter = st.selectbox("Filter", ["All", "Assigned", "Resolved"])

    tasks = get_issues({"worker_id": user["id"], "status": status_filter})

    st.markdown(f"<p style='color:#64748b;font-size:13px;margin-bottom:12px;'>Showing {len(tasks)} task(s)</p>",
                unsafe_allow_html=True)

    if not tasks:
        st.info("No tasks found.")
        return

    for iss in tasks:
        label = "Resolve Issue" if iss["status"] == "assigned" else "View Details"
        if render_issue_card(iss, label):
            st.session_state["worker_view_id"] = iss["id"]
            st.rerun()
