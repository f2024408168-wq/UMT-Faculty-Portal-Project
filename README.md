# UMT Combined Faculty Portal

A unified web portal that combines UMT's attendance and grading systems into one application.
Built for OSSD Y9 Final Semester Project.

**Student:** Ghulam Mohaiudin Butt (F2024408168)
**Instructor:** Abdullah Miraj Butt

## Features

- Faculty registration and login
- Dashboard with stats, alerts, and quick actions
- Course management (add/delete courses)
- Student management (add/edit/delete students per course)
- Mark attendance (Theory 1, Theory 2, Lab) with history
- Attendance report with at-risk alerts (below 75%)
- Course assessments (Quiz, Mid Term, Final Exam, etc.) with weightage
- Enter marks per student per assessment
- Auto grading with distribution chart + manual override
- Combined student profile (attendance + grades)
- Settings page for profile/password update

## Project Structure

```
umt-faculty-portal/
├── main.py              # FastAPI app with all routes
├── database.py          # MongoDB connection
├── requirements.txt     # Python dependencies
├── vercel.json           # Vercel deployment config
├── api/
│   └── index.py          # Vercel entry point
├── templates/            # 16 HTML pages (Jinja2)
└── static/css/style.css  # UMT blue theme styling
```

## Setup (Local)

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://127.0.0.1:8000

## Database

MongoDB Atlas — database name: `umt_faculty_db`

Collections: `faculty`, `courses`, `students`, `attendance`, `assessments`, `marks`

Connection string is stored in `.env` as `MONGO_URL` (not committed to GitHub).

## Deployment

Deployed on Vercel. The `vercel.json` and `api/index.py` files allow FastAPI to run
as a serverless function. Set `MONGO_URL` as an environment variable in the Vercel
project settings.

## Demo Flow

1. Register a faculty account
2. Login
3. Add a course
4. Add students to the course
5. Mark attendance for a lecture
6. Create assessments and enter marks
7. View grading page and submit course result
8. View attendance report (at-risk alerts)
9. View a student's combined profile
