import streamlit as st
from utils.database import (
    get_issues, get_issue, get_stats, assign_worker,
    get_workers, get_timeline
)
from utils.ui import (
    stat_cards, render_issue_card, render_timeline,
    render_image, status_badge, priority_badge, category_chip,
    fmt_date, gps_box
)

CATEGORIES = ["All", "Roads", "Water", "Electricity", "Sanitation", "Parks", "Buildings", "Drainage"]


def _issue_detail(issue_id):
    issue = get_issue(issue_id)
    if not issue:
        st.error("Issue not found.")
        return

    col_title, col_back = st.columns([4, 1])
    with col_title:
        st.markdown(f"### {issue['title']}")
    with col_back:
        if st.button("← Back", key="admin_back"):
            st.session_state.pop("admin_view_id", None)
            st.rerun()

    st.markdown(
        f"{status_badge(issue['status'])} &nbsp; {priority_badge(issue['priority'])} &nbsp; {category_chip(issue['category'])}",
        unsafe_allow_html=True
    )
    st.markdown(f"<p style='color:#94a3b8;margin-top:8px;font-size:14px;'>{issue['description']}</p>", unsafe_allow_html=True)
    st.markdown("---")

    info_col, gps_col = st.columns(2)
    with info_col:
        st.markdown(f"**📍 Address:** {issue['address']}")
        st.markdown(f"**🗓️ Reported:** {fmt_date(issue['reported_at'])}")
        st.markdown(f"**👤 Citizen:** {issue.get('citizen_name', '—')}")
        if issue.get("worker_name"):
            st.markdown(f"**👷 Assigned Worker:** {issue['worker_name']} ({issue.get('worker_dept','—')})")
        if issue.get("assigned_at"):
            st.markdown(f"**📌 Assigned on:** {fmt_date(issue['assigned_at'])}")
        if issue.get("resolved_at"):
            st.markdown(f"**✅ Resolved on:** {fmt_date(issue['resolved_at'])}")
    with gps_col:
        gps_box(issue["lat"], issue["lng"])
        st.markdown(f"**Category:** {issue['category']}")
        st.markdown(f"**Priority:** {issue['priority'].upper()}")

    st.markdown("#### 📷 Photos")
    img_c1, img_c2 = st.columns(2)
    with img_c1:
        render_image(issue.get("before_image"), "📸 Before (reported)", height=200)
    with img_c2:
        render_image(issue.get("after_image"), "✅ After (resolved)", height=200)

    # Assign worker section
    if issue["status"] == "pending":
        st.markdown("---")
        st.markdown("#### 👷 Assign to Worker")
        workers = get_workers()
        if not workers:
            st.warning("No workers registered yet.")
        else:
            worker_options = {f"{w['name']} — {w['dept']} Dept.": w for w in workers}
            selected_label = st.selectbox("Select Worker", list(worker_options.keys()), key=f"wsel_{issue_id}")
            if st.button("✓ Assign Worker", type="primary", key=f"assign_{issue_id}"):
                w = worker_options[selected_label]
                assign_worker(issue_id, w["id"], w["name"], w["dept"])
                st.success(f"Issue assigned to **{w['name']}** ({w['dept']} Dept.)")
                st.rerun()

    elif issue["status"] == "assigned":
        st.info(f"⏳ Awaiting resolution by **{issue.get('worker_name','worker')}**")
    elif issue["status"] == "resolved":
        st.success("✅ This issue has been resolved.")

    st.markdown("#### 📅 Activity Timeline")
    tl = get_timeline(issue_id)
    render_timeline(tl)


def dashboard():
    if "admin_view_id" in st.session_state:
        _issue_detail(st.session_state["admin_view_id"])
        return

    st.markdown("## 🏠 Admin Dashboard")
    st.markdown("Overview of all municipality issues and workforce.")

    stats = get_stats()
    stat_cards(stats)

    # Recent pending
    st.markdown("#### 🟡 Pending Issues (need assignment)")
    pending = get_issues({"status": "Pending"})[:5]
    if not pending:
        st.success("No pending issues! All caught up.")
    else:
        for iss in pending:
            if render_issue_card(iss, "Assign Worker"):
                st.session_state["admin_view_id"] = iss["id"]
                st.rerun()

    st.markdown("#### 📋 Recent Issues")
    recent = get_issues()[:5]
    for iss in recent:
        if render_issue_card(iss, "View / Manage"):
            st.session_state["admin_view_id"] = iss["id"]
            st.rerun()


def all_issues():
    if "admin_view_id" in st.session_state:
        _issue_detail(st.session_state["admin_view_id"])
        return

    st.markdown("## 📋 All Issues")

    c1, c2, c3 = st.columns(3)
    with c1:
        status_filter = st.selectbox("Status", ["All", "Pending", "Assigned", "Resolved"])
    with c2:
        cat_filter = st.selectbox("Category", CATEGORIES)
    with c3:
        priority_filter = st.selectbox("Priority", ["All", "high", "medium", "low"],
                                        format_func=lambda x: x.upper() if x != "All" else x)

    issues = get_issues({"status": status_filter, "category": cat_filter})
    if priority_filter != "All":
        issues = [i for i in issues if i["priority"] == priority_filter]

    st.markdown(f"<p style='color:#64748b;font-size:13px;margin-bottom:12px;'>Showing {len(issues)} issue(s)</p>",
                unsafe_allow_html=True)

    if not issues:
        st.info("No issues found for selected filters.")
        return

    for iss in issues:
        if render_issue_card(iss, "View / Manage"):
            st.session_state["admin_view_id"] = iss["id"]
            st.rerun()


def workers_page():
    st.markdown("## 👷 Workers")
    st.markdown("Municipality field workers and their assignments.")

    workers = get_workers()
    all_issues_list = get_issues()

    for w in workers:
        w_issues = [i for i in all_issues_list if i["worker_id"] == w["id"]]
        active   = sum(1 for i in w_issues if i["status"] == "assigned")
        resolved = sum(1 for i in w_issues if i["status"] == "resolved")

        st.markdown(f"""
        <div style='background:#1e293b;border:1px solid #334155;border-radius:12px;
                    padding:14px 18px;margin-bottom:10px;'>
            <div style='display:flex;align-items:center;gap:14px;'>
                <div style='width:48px;height:48px;border-radius:50%;background:#1d4ed8;
                            display:flex;align-items:center;justify-content:center;
                            font-size:22px;flex-shrink:0;'>👷</div>
                <div style='flex:1;'>
                    <div style='font-size:16px;font-weight:600;color:#f1f5f9;'>{w["name"]}</div>
                    <div style='font-size:13px;color:#94a3b8;'>{w["dept"]} Dept. &nbsp;·&nbsp; {w["phone"]}</div>
                </div>
                <div style='text-align:right;'>
                    <div style='font-size:14px;color:#f59e0b;font-weight:600;'>{active} active</div>
                    <div style='font-size:12px;color:#22c55e;'>{resolved} resolved</div>
                    <div style='font-size:12px;color:#64748b;'>{len(w_issues)} total</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def analytics():
    st.markdown("## 📊 Analytics")
    st.markdown("Municipality issue statistics and trends.")

    all_iss = get_issues()
    if not all_iss:
        st.info("No data available yet.")
        return

    # Overall stats
    stats = get_stats()
    stat_cards(stats)

    # Category breakdown
    st.markdown("#### Issues by Category")
    from collections import Counter
    cat_counts = Counter(i["category"] for i in all_iss)
    import pandas as pd
    cat_df = pd.DataFrame(cat_counts.most_common(), columns=["Category", "Count"])
    st.bar_chart(cat_df.set_index("Category"))

    # Priority breakdown
    pri_counts = Counter(i["priority"] for i in all_iss)
    pri_df = pd.DataFrame({"Priority": list(pri_counts.keys()), "Count": list(pri_counts.values())})

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Issues by Priority")
        st.bar_chart(pri_df.set_index("Priority"))

    with col2:
        st.markdown("#### Issues by Status")
        status_counts = Counter(i["status"] for i in all_iss)
        st.bar_chart(pd.DataFrame({"Status": list(status_counts.keys()),
                                   "Count": list(status_counts.values())}).set_index("Status"))

    # Resolution rate
    total = len(all_iss)
    resolved = sum(1 for i in all_iss if i["status"] == "resolved")
    rate = round((resolved / total * 100) if total > 0 else 0, 1)
    st.markdown(f"""
    <div style='background:#1e293b;border:1px solid #334155;border-radius:12px;
                padding:20px;margin-top:16px;text-align:center;'>
        <div style='font-size:40px;font-weight:700;color:#22c55e;'>{rate}%</div>
        <div style='font-size:14px;color:#94a3b8;'>Overall Resolution Rate</div>
    </div>
    """, unsafe_allow_html=True)
