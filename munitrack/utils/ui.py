import streamlit as st
import base64
from datetime import datetime


def fmt_date(iso_str):
    if not iso_str:
        return "—"
    try:
        dt = datetime.strptime(iso_str[:19], "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%-d %b %Y, %I:%M %p")
    except Exception:
        return iso_str


def status_badge(status):
    labels = {
        "pending":  ("🟡", "Pending",     "#fef3c7", "#92400e"),
        "assigned": ("🔵", "In Progress", "#dbeafe", "#1e40af"),
        "resolved": ("🟢", "Resolved",    "#dcfce7", "#166534"),
        "rejected": ("🔴", "Rejected",    "#fee2e2", "#991b1b"),
    }
    emoji, label, bg, color = labels.get(status, ("⚪", status.title(), "#f1f5f9", "#374151"))
    return f'<span style="background:{bg};color:{color};padding:3px 12px;border-radius:20px;font-size:12px;font-weight:600;">{emoji} {label}</span>'


def priority_badge(priority):
    cfg = {
        "high":   ("#fee2e2", "#991b1b", "▲ HIGH"),
        "medium": ("#fef3c7", "#92400e", "● MEDIUM"),
        "low":    ("#dcfce7", "#166534", "▼ LOW"),
    }
    bg, color, label = cfg.get(priority, ("#f1f5f9", "#374151", priority.upper()))
    return f'<span style="background:{bg};color:{color};padding:2px 10px;border-radius:5px;font-size:11px;font-weight:700;">{label}</span>'


def category_chip(cat):
    icons = {
        "Roads": "🛣️", "Water": "💧", "Electricity": "⚡",
        "Sanitation": "🗑️", "Parks": "🌳", "Buildings": "🏗️", "Drainage": "🌊",
    }
    icon = icons.get(cat, "🏷️")
    return f'<span style="background:#1e3a5f;color:#93c5fd;padding:2px 10px;border-radius:6px;font-size:12px;">{icon} {cat}</span>'


def stat_cards(stats):
    items = [
        ("Total Issues",  stats["total"],    "#3b82f6"),
        ("Pending",       stats["pending"],  "#f59e0b"),
        ("In Progress",   stats["assigned"], "#60a5fa"),
        ("Resolved",      stats["resolved"], "#22c55e"),
    ]
    cols = st.columns(4)
    for col, (label, value, color) in zip(cols, items):
        with col:
            st.markdown(f"""
            <div class="stat-card">
                <p class="stat-number" style="color:{color}">{value}</p>
                <p class="stat-label">{label}</p>
            </div>
            """, unsafe_allow_html=True)
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)


def image_to_bytes(uploaded_file):
    if uploaded_file is None:
        return None
    return uploaded_file.read()


def bytes_to_b64(img_bytes):
    if not img_bytes:
        return None
    return base64.b64encode(img_bytes).decode()


def render_image(img_bytes, caption="", height=200):
    if img_bytes:
        b64 = bytes_to_b64(img_bytes)
        st.markdown(f"""
        <div style='border-radius:10px;overflow:hidden;border:1px solid #334155;'>
            <img src="data:image/jpeg;base64,{b64}"
                 style="width:100%;height:{height}px;object-fit:cover;display:block;">
            {"<div style='background:#1e293b;padding:6px 10px;font-size:12px;color:#94a3b8;'>" + caption + "</div>" if caption else ""}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style='height:{height}px;background:#1e293b;border:1px solid #334155;
             border-radius:10px;display:flex;align-items:center;justify-content:center;
             flex-direction:column;color:#475569;font-size:13px;'>
            <div style='font-size:28px;margin-bottom:8px'>🖼️</div>
            <div>{caption or "No photo uploaded"}</div>
        </div>
        """, unsafe_allow_html=True)


def render_timeline(events):
    if not events:
        return
    st.markdown("<div style='margin-top:12px;'>", unsafe_allow_html=True)
    for ev in events:
        color = ev.get("color", "#3b82f6")
        st.markdown(f"""
        <div style='border-left:2px solid {color};padding:0 0 14px 16px;
                    margin-left:8px;position:relative;'>
            <div style='width:10px;height:10px;border-radius:50%;background:{color};
                        position:absolute;left:-6px;top:2px;'></div>
            <div style='font-size:11px;color:#64748b;margin-bottom:3px;'>{fmt_date(ev.get("created_at",""))}</div>
            <div style='font-size:13px;color:#cbd5e1;'>{ev.get("text","")}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_issue_card(issue, on_click_label="View Details"):
    """Renders a single issue summary card. Returns True if button clicked."""
    st.markdown(f"""
    <div style='background:#1e293b;border:1px solid #334155;border-radius:12px;
                padding:14px 18px;margin-bottom:10px;'>
        <div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;flex-wrap:wrap;gap:6px;'>
            <div style='display:flex;align-items:center;gap:8px;flex-wrap:wrap;'>
                <span style='font-family:monospace;font-size:11px;color:#64748b;'>{issue["id"]}</span>
                {priority_badge(issue["priority"])}
                {category_chip(issue["category"])}
            </div>
            {status_badge(issue["status"])}
        </div>
        <div style='font-size:15px;font-weight:600;color:#f1f5f9;margin-bottom:4px;'>{issue["title"]}</div>
        <div style='font-size:13px;color:#94a3b8;line-height:1.5;margin-bottom:10px;'>
            {issue["description"][:100]}{"..." if len(issue.get("description","")) > 100 else ""}
        </div>
        <div style='display:flex;gap:16px;flex-wrap:wrap;font-size:12px;color:#64748b;'>
            <span>📍 {issue["address"]}</span>
            <span>🗓️ {fmt_date(issue["reported_at"])}</span>
            {"<span>👷 " + issue["worker_name"] + "</span>" if issue.get("worker_name") else ""}
        </div>
    </div>
    """, unsafe_allow_html=True)

    return st.button(on_click_label, key=f"view_{issue['id']}_{on_click_label}")


def gps_box(lat, lng):
    st.markdown(f"""
    <div class="gps-box">
        📡 GPS Coordinates: {lat:.6f}, {lng:.6f}
    </div>
    """, unsafe_allow_html=True)
