# 🏛️ MuniTrack — Municipality Issue Management System

A full-stack municipality issue tracking app built with **Streamlit + SQLite**.  
Citizens report issues with photos & GPS. Admins assign work. Workers upload resolution photos.

---

## 🚀 Deploy to Streamlit Community Cloud (Free)

### Step 1 — Push to GitHub

1. Create a new repository on GitHub (e.g. `munitrack`)
2. Upload all these files maintaining the folder structure:

```
munitrack/
├── app.py
├── requirements.txt
├── .streamlit/
│   └── config.toml
├── utils/
│   ├── __init__.py
│   ├── database.py
│   ├── auth.py
│   └── ui.py
└── pages/
    ├── __init__.py
    ├── citizen.py
    ├── admin.py
    └── worker.py
```

### Step 2 — Deploy on Streamlit

1. Go to **https://share.streamlit.io**
2. Sign in with GitHub
3. Click **"New app"**
4. Select your repository, branch (`main`), and set **Main file path** to `app.py`
5. Click **"Deploy!"**

Your app will be live at:  
`https://your-username-munitrack-app-xxxx.streamlit.app`

---

## 🔑 Demo Accounts (password: `123`)

| Role     | Email                  | Access |
|----------|------------------------|--------|
| Citizen  | citizen@muni.gov       | Report issues, track status |
| Admin    | admin@muni.gov         | Assign workers, view all, analytics |
| Worker 1 | worker1@muni.gov       | Roads department tasks |
| Worker 2 | worker2@muni.gov       | Water department tasks |
| Worker 3 | worker3@muni.gov       | Sanitation department tasks |

---

## ✨ Features

### 👤 Citizen
- Report issues with **photo upload** (camera on mobile)
- **GPS coordinate** input with map reference
- Track status of all submitted reports in real-time
- View before/after photos and activity timeline

### 🔑 Admin
- Dashboard with live statistics
- View and filter all issues (status, category, priority)
- **Assign issues to workers** with one click
- Workers overview with active task counts
- Analytics charts (by category, priority, status)

### 🔧 Worker
- See only tasks assigned to them
- Upload **after-resolution photo** from the same spot
- Input **current GPS coordinates** at resolution
- Auto-marks issue as resolved with timestamp

---

## 🗄️ Database

Uses **SQLite** (`munitrack.db`) — automatically created on first run.

Tables:
- `users` — citizens, admins, workers
- `issues` — all reported issues with photos (stored as BLOB)
- `timeline` — activity log per issue

> **Note:** On Streamlit Community Cloud, the SQLite file resets on each redeploy.  
> For production persistence, replace with **PostgreSQL** via `st.connection` or **Supabase**.

---

## 🛠️ Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501

---

## 📦 Production Upgrade Tips

- **Database:** Replace SQLite with PostgreSQL using `st.secrets` for credentials
- **Image storage:** Use AWS S3 or Cloudinary for photo storage instead of BLOB
- **Auth:** Add JWT-based auth or use Streamlit Authenticator package
- **SMS alerts:** Integrate Twilio to notify citizens on status changes
- **Maps:** Add Folium or Pydeck for interactive GPS map view
