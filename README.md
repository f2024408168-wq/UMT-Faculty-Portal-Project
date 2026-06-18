# UMT Combined Faculty Portal

A full-stack web application for managing faculty operations at the University of Management and Technology (UMT). Built with FastAPI, MongoDB Atlas, Jinja2, and deployed on Vercel.

**Student:** Aiman | **Roll No:** F2024408168 | **Instructor:** Abdullah Miraj Butt (OSSD Y9)

---

## Live Links

| Service | URL |
|--------|-----|
| **Frontend (Vercel)** | `https://<your-vercel-app>.vercel.app` |
| **Backend API (FastAPI Docs)** | `https://<your-backend-url>/docs` |
| **GitHub Repository** | `https://github.com/f2024408168-wq/<repo-name>` |

> Replace placeholder URLs with your actual deployed links.

---

## Features

- **Attendance Management** — Mark, view, and update student attendance per session
- **Grading System** — Enter and manage student grades across courses
- **At-Risk Student Alerts** — Automatic flagging of students with low attendance or grades
- **PDF Export** — Generate downloadable attendance and grade reports
- **Combined Faculty View** — Unified dashboard across multiple departments

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend Framework | FastAPI (Python) |
| Database | MongoDB Atlas (via Motor async driver) |
| Templating | Jinja2 |
| Deployment | Vercel |
| Version Control | GitHub |

---

## Project Structure

```
project-root/
├── main.py                  # FastAPI app entry point
├── database.py              # MongoDB Atlas connection (Motor)
├── models/                  # Pydantic data models
│   ├── student.py
│   ├── attendance.py
│   └── grade.py
├── routes/                  # API route handlers
│   ├── attendance.py
│   ├── grades.py
│   └── alerts.py
├── templates/               # Jinja2 HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── attendance.html
│   └── grades.html
├── static/                  # CSS, JS, images
│   ├── css/
│   └── js/
├── vercel.json              # Vercel deployment config
├── requirements.txt         # Python dependencies
└── README.md
```

---

## Setup Instructions

### Prerequisites

- Python 3.10+
- MongoDB Atlas account (free tier works)
- Vercel account
- Git

---

### 1. Clone the Repository

```bash
git clone https://github.com/f2024408168-wq/<repo-name>.git
cd <repo-name>
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory:

```env
MONGO_URI=mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/<dbname>?retryWrites=true&w=majority
DB_NAME=umt_faculty_portal
SECRET_KEY=your-secret-key-here
```

> Get your `MONGO_URI` from MongoDB Atlas → Clusters → Connect → Python driver.

### 5. Run Locally

```bash
uvicorn main:app --reload
```

App will be available at: `http://localhost:8000`  
API docs at: `http://localhost:8000/docs`

---

## MongoDB Atlas Configuration

1. Go to [cloud.mongodb.com](https://cloud.mongodb.com)
2. Create a free M0 cluster
3. Under **Database Access** → Add a database user
4. Under **Network Access** → Allow access from `0.0.0.0/0` (for Vercel deployment)
5. Copy the connection string into your `.env` as `MONGO_URI`

**Collections used:**
- `students`
- `courses`
- `attendance`
- `grades`
- `faculty`

---

## Vercel Deployment

### Step 1: Add `vercel.json`

```json
{
  "builds": [
    { "src": "main.py", "use": "@vercel/python" }
  ],
  "routes": [
    { "src": "/(.*)", "dest": "main.py" }
  ]
}
```

### Step 2: Deploy

```bash
# Install Vercel CLI
npm install -g vercel

# Login and deploy
vercel login
vercel --prod
```

### Step 3: Set Environment Variables on Vercel

Go to Vercel Dashboard → Your Project → Settings → Environment Variables and add:
- `MONGO_URI`
- `DB_NAME`
- `SECRET_KEY`

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Dashboard home |
| GET | `/attendance` | View attendance records |
| POST | `/attendance/mark` | Mark attendance |
| GET | `/grades` | View all grades |
| POST | `/grades/update` | Update student grade |
| GET | `/alerts` | Get at-risk student list |
| GET | `/export/pdf` | Download PDF report |
| GET | `/docs` | Swagger UI (auto-generated) |

---

## Screenshots

> See `/screenshots` folder in the repository for:
> - Dashboard view
> - Attendance management page
> - Grades entry page
> - At-risk alerts panel
> - PDF export output
> - MongoDB Atlas collection view

---

## Phase 1 Documentation

The full project proposal and Phase 1 documentation PDF is included in the `/docs` folder of this repository.

---

## License

This project was developed for academic purposes at the University of Management and Technology (UMT), Lahore.  
Course: Open Source Software Development (OSSD Y9) | Instructor: Abdullah Miraj Butt
