import streamlit as st
from utils.database import (
    get_issues, get_issue, get_stats, create_issue, get_timeline
)
from utils.ui import (
    stat_cards, render_issue_card, render_timeline,
    render_image, status_badge, priority_badge, category_chip,
    fmt_date, image_to_bytes, gps_box
)

CATEGORIES = ["Roads", "Water", "Electricity", "Sanitation", "Parks", "Buildings", "Drainage"]


def _issue_detail_modal(issue_id):
    issue = get_issue(issue_id)
    if not issue:
        st.error("Issue not found.")
        return

    st.markdown(f"### {issue['title']}")
    cols = st.columns([3, 1])
    with cols[0]:
        st.markdown(
            f"{status_badge(issue['status'])} &nbsp; {priority_badge(issue['priority'])} &nbsp; {category_chip(issue['category'])}",
            unsafe_allow_html=True
        )
    with cols[1]:
        if st.button("← Back", key="back_detail"):
            st.session_state.pop("view_issue_id", None)
            st.rerun()

    st.markdown(f"<p style='color:#94a3b8;font-size:14px;margin-top:8px'>{issue['description']}</p>", unsafe_allow_html=True)

    st.markdown("---")
    info_cols = st.columns(2)
    with info_cols[0]:
        st.markdown(f"**📍 Address:** {issue['address']}")
        st.markdown(f"**🗓️ Reported:** {fmt_date(issue['reported_at'])}")
        if issue.get("assigned_at"):
            st.markdown(f"**👷 Assigned:** {fmt_date(issue['assigned_at'])}")
        if issue.get("resolved_at"):
            st.markdown(f"**✅ Resolved:** {fmt_date(issue['resolved_at'])}")
    with info_cols[1]:
        gps_box(issue["lat"], issue["lng"])
        if issue.get("worker_name"):
            st.markdown(f"**Worker:** {issue['worker_name']}")

    # Photos
    st.markdown("#### 📷 Photos")
    img_cols = st.columns(2)
    with img_cols[0]:
        render_image(issue.get("before_image"), "📸 Before (reported)", height=200)
    with img_cols[1]:
        render_image(issue.get("after_image"), "✅ After (resolved)", height=200)

    # Timeline
    st.markdown("#### 📅 Activity Timeline")
    tl = get_timeline(issue_id)
    render_timeline(tl)


def dashboard():
    user = st.session_state["user"]

    if "view_issue_id" in st.session_state:
        _issue_detail_modal(st.session_state["view_issue_id"])
        return

    st.markdown("## 🏠 Dashboard")
    st.markdown(f"Welcome back, **{user['name']}**! Here are your reported issues.")

    stats = get_stats({"citizen_id": user["id"]})
    stat_cards(stats)

    st.markdown("#### 📋 Recent Reports")
    issues = get_issues({"citizen_id": user["id"]})[:5]
    if not issues:
        st.info("You haven't reported any issues yet. Use **Report Issue** to get started.")
        return

    for issue in issues:
        if render_issue_card(issue, "View Details"):
            st.session_state["view_issue_id"] = issue["id"]
            st.rerun()


def my_reports():
    user = st.session_state["user"]

    if "view_issue_id" in st.session_state:
        _issue_detail_modal(st.session_state["view_issue_id"])
        return

    st.markdown("## 📋 My Reports")

    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Filter by Status", ["All", "Pending", "Assigned", "Resolved"])
    with col2:
        cat_filter = st.selectbox("Filter by Category", ["All"] + CATEGORIES)

    issues = get_issues({
        "citizen_id": user["id"],
        "status": status_filter,
        "category": cat_filter
    })

    st.markdown(f"<p style='color:#64748b;font-size:13px;margin-bottom:12px;'>Showing {len(issues)} issue(s)</p>", unsafe_allow_html=True)

    if not issues:
        st.info("No issues found for the selected filters.")
        return

    for issue in issues:
        if render_issue_card(issue, "View Details"):
            st.session_state["view_issue_id"] = issue["id"]
            st.rerun()


def report_issue():
    user = st.session_state["user"]
    st.markdown("## 📍 Report a New Issue")
    st.markdown("Document a problem in your area with a photo and GPS location.")

    with st.form("report_form", clear_on_submit=True):
        st.markdown("#### 📝 Issue Details")
        title = st.text_input("Issue Title *", placeholder="e.g. Pothole on MG Road near Station")
        description = st.text_area("Description *", placeholder="Describe the problem in detail...", height=100)

        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox("Category *", CATEGORIES)
        with col2:
            priority = st.selectbox("Priority *", ["high", "medium", "low"],
                                    format_func=lambda x: x.upper())

        address = st.text_input("Address / Landmark *", placeholder="e.g. Near Patna Junction, MG Road")

        st.markdown("#### 📷 Photo")
        photo = st.file_uploader(
            "Upload photo of the issue (required)",
            type=["jpg", "jpeg", "png", "webp"],
            help="Take a photo using your phone camera or upload from gallery"
        )
        if photo:
            st.image(photo, caption="Issue photo preview", use_container_width=True)

        st.markdown("#### 📡 GPS Location")
        st.info("Enter GPS coordinates from your phone's Maps app, or use approximate coordinates.")
        gps_col1, gps_col2 = st.columns(2)
        with gps_col1:
            lat = st.number_input("Latitude", value=25.5941, format="%.6f", step=0.000001)
        with gps_col2:
            lng = st.number_input("Longitude", value=85.1376, format="%.6f", step=0.000001)

        submitted = st.form_submit_button("🚀 Submit Report", use_container_width=True, type="primary")

    if submitted:
        if not title.strip() or not description.strip() or not address.strip():
            st.error("Please fill in all required fields (Title, Description, Address).")
            return
        if not photo:
            st.warning("A photo is strongly recommended. Submitting without photo.")

        img_bytes = image_to_bytes(photo) if photo else None
        issue_id = create_issue(
            title=title.strip(),
            description=description.strip(),
            category=category,
            priority=priority,
            citizen_id=user["id"],
            lat=lat, lng=lng,
            address=address.strip(),
            before_image_bytes=img_bytes
        )
        st.success(f"✅ Issue reported successfully! Your Issue ID: **{issue_id}**")
        st.balloons()
        st.markdown(f"Track your issue under **My Reports**.")
