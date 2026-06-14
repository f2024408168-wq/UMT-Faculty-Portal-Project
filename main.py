from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from bson import ObjectId
from datetime import datetime
import uvicorn

from database import (
    faculty_collection, courses_collection, students_collection,
    attendance_collection, assessments_collection, marks_collection
)

app = FastAPI(title="UMT Combined Faculty Portal")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def fix_id(doc):
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

def get_faculty(request: Request):
    fid = request.cookies.get("faculty_id")
    fname = request.cookies.get("faculty_name")
    if not fid:
        return None
    return {"_id": fid, "name": fname}

# ── PUBLIC ────────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse(request, "landing.html", {})

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse(request, "about.html", {})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {})

@app.post("/login")
async def login(request: Request, employee_code: str = Form(...), password: str = Form(...)):
    f = await faculty_collection.find_one({"employee_code": employee_code})
    if not f or f["password"] != password:
        return templates.TemplateResponse(request, "login.html", {"error": "Wrong employee code or password."})
    r = RedirectResponse(url="/dashboard", status_code=302)
    r.set_cookie("faculty_id", str(f["_id"]), max_age=86400)
    r.set_cookie("faculty_name", f["name"], max_age=86400)
    return r

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html", {})

@app.post("/register")
async def register(request: Request, name: str = Form(...), employee_code: str = Form(...),
                   email: str = Form(...), department: str = Form(...), password: str = Form(...)):
    if await faculty_collection.find_one({"employee_code": employee_code}):
        return templates.TemplateResponse(request, "register.html", {"error": "Employee code already registered."})
    result = await faculty_collection.insert_one({
        "name": name, "employee_code": employee_code, "email": email,
        "department": department, "password": password, "created_at": datetime.now()
    })
    r = RedirectResponse(url="/dashboard", status_code=302)
    r.set_cookie("faculty_id", str(result.inserted_id), max_age=86400)
    r.set_cookie("faculty_name", name, max_age=86400)
    return r

@app.get("/logout")
async def logout():
    r = RedirectResponse(url="/login", status_code=302)
    r.delete_cookie("faculty_id")
    r.delete_cookie("faculty_name")
    return r

# ── DASHBOARD ─────────────────────────────────────────────────────────────────
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    faculty = get_faculty(request)
    if not faculty: return RedirectResponse(url="/login", status_code=302)
    courses = await courses_collection.find({"faculty_id": faculty["_id"]}).to_list(100)
    course_ids = [str(c["_id"]) for c in courses]
    total_students = await students_collection.count_documents({"course_id": {"$in": course_ids}})
    att_records = await attendance_collection.find({"course_id": {"$in": course_ids}}).to_list(1000)
    total_present = sum(sum(1 for r in rec.get("records",[]) if r.get("present")) for rec in att_records)
    total_possible = sum(len(rec.get("records",[])) for rec in att_records)
    att_pct = round(total_present/total_possible*100) if total_possible else 0
    pending = sum(1 for c in courses if c.get("status") != "Submit")
    at_risk = []
    for cid in course_ids:
        sts = await students_collection.find({"course_id": cid}).to_list(100)
        lecs = await attendance_collection.find({"course_id": cid}).to_list(100)
        tl = len(lecs)
        for s in sts:
            if not tl: continue
            p = sum(1 for l in lecs for r in l.get("records",[]) if str(r.get("student_id"))==str(s["_id"]) and r.get("present"))
            pct = round(p/tl*100)
            if pct < 75: at_risk.append({"name": s["name"], "roll": s["roll_no"], "pct": pct})
    return templates.TemplateResponse(request, "dashboard.html", {
        "faculty": faculty, "courses": [fix_id(c) for c in courses],
        "total_students": total_students, "att_pct": att_pct,
        "pending": pending, "at_risk": at_risk[:5]
    })

# ── COURSES ───────────────────────────────────────────────────────────────────
@app.get("/courses", response_class=HTMLResponse)
async def courses_page(request: Request):
    faculty = get_faculty(request)
    if not faculty: return RedirectResponse(url="/login", status_code=302)
    courses = [fix_id(c) for c in await courses_collection.find({"faculty_id": faculty["_id"]}).to_list(100)]
    return templates.TemplateResponse(request, "courses.html", {"faculty": faculty, "courses": courses})

@app.post("/courses/add")
async def add_course(request: Request, course_id: str = Form(...), title: str = Form(...),
                     section: str = Form(...), semester: str = Form(...)):
    faculty = get_faculty(request)
    if not faculty: return RedirectResponse(url="/login", status_code=302)
    await courses_collection.insert_one({"course_id": course_id, "title": title, "section": section,
        "semester": semester, "faculty_id": faculty["_id"], "status": "In Progress", "created_at": datetime.now()})
    return RedirectResponse(url="/courses", status_code=302)

@app.post("/courses/delete/{oid}")
async def delete_course(request: Request, oid: str):
    faculty = get_faculty(request)
    if not faculty: return RedirectResponse(url="/login", status_code=302)
    await courses_collection.delete_one({"_id": ObjectId(oid)})
    return RedirectResponse(url="/courses", status_code=302)

# ── STUDENTS ──────────────────────────────────────────────────────────────────
@app.get("/students/{coid}", response_class=HTMLResponse)
async def students_page(request: Request, coid: str):
    faculty = get_faculty(request)
    if not faculty: return RedirectResponse(url="/login", status_code=302)
    course = fix_id(await courses_collection.find_one({"_id": ObjectId(coid)}))
    students = [fix_id(s) for s in await students_collection.find({"course_id": coid}).to_list(200)]
    return templates.TemplateResponse(request, "students.html", {"faculty": faculty, "course": course, "students": students})

@app.post("/students/add")
async def add_student(request: Request, course_oid: str = Form(...), roll_no: str = Form(...),
                      name: str = Form(...), program: str = Form(...), section: str = Form(...), email: str = Form(...)):
    faculty = get_faculty(request)
    if not faculty: return RedirectResponse(url="/login", status_code=302)
    await students_collection.insert_one({"roll_no": roll_no, "name": name, "program": program,
        "section": section, "email": email, "course_id": course_oid, "created_at": datetime.now()})
    return RedirectResponse(url=f"/students/{course_oid}", status_code=302)

@app.post("/students/delete/{soid}")
async def delete_student(request: Request, soid: str, course_oid: str = Form(...)):
    faculty = get_faculty(request)
    if not faculty: return RedirectResponse(url="/login", status_code=302)
    await students_collection.delete_one({"_id": ObjectId(soid)})
    return RedirectResponse(url=f"/students/{course_oid}", status_code=302)

# ── ATTENDANCE ────────────────────────────────────────────────────────────────
@app.get("/attendance/{coid}", response_class=HTMLResponse)
async def attendance_page(request: Request, coid: str):
    faculty = get_faculty(request)
    if not faculty: return RedirectResponse(url="/login", status_code=302)
    course = fix_id(await courses_collection.find_one({"_id": ObjectId(coid)}))
    students = [fix_id(s) for s in await students_collection.find({"course_id": coid}).to_list(200)]
    lectures = [fix_id(l) for l in await attendance_collection.find({"course_id": coid}).to_list(100)]
    return templates.TemplateResponse(request, "attendance.html", {"faculty": faculty, "course": course, "students": students, "lectures": lectures})

@app.post("/attendance/save")
async def save_attendance(request: Request):
    faculty = get_faculty(request)
    if not faculty: return RedirectResponse(url="/login", status_code=302)
    form = await request.form()
    coid = form.get("course_oid")
    students = await students_collection.find({"course_id": coid}).to_list(200)
    records = [{"student_id": str(s["_id"]), "present": form.get(f"present_{str(s['_id'])}") == "on"} for s in students]
    await attendance_collection.insert_one({"course_id": coid, "lecture_type": form.get("lecture_type"),
        "classroom": form.get("classroom"), "date": form.get("date"), "records": records, "created_at": datetime.now()})
    return RedirectResponse(url=f"/attendance/{coid}", status_code=302)

@app.get("/attendance/report/{coid}", response_class=HTMLResponse)
async def attendance_report(request: Request, coid: str):
    faculty = get_faculty(request)
    if not faculty: return RedirectResponse(url="/login", status_code=302)
    course = fix_id(await courses_collection.find_one({"_id": ObjectId(coid)}))
    students = await students_collection.find({"course_id": coid}).to_list(200)
    lectures = await attendance_collection.find({"course_id": coid}).to_list(100)
    tl = len(lectures)
    report = []
    for s in students:
        sid = str(s["_id"])
        p = sum(1 for l in lectures for r in l.get("records",[]) if str(r.get("student_id"))==sid and r.get("present"))
        pct = round(p/tl*100) if tl else 0
        status = "Good" if pct >= 75 else ("Warning" if pct >= 60 else "At Risk")
        report.append({"_id": sid, "name": s["name"], "roll_no": s["roll_no"], "present": p, "total": tl, "pct": pct, "status": status})
    at_risk_count = sum(1 for r in report if r["pct"] < 75)
    avg = round(sum(r["pct"] for r in report)/len(report)) if report else 0
    perfect = sum(1 for r in report if r["pct"] == 100)
    return templates.TemplateResponse(request, "attendance_report.html", {"faculty": faculty, "course": course,
        "report": report, "total_lecs": tl, "at_risk_count": at_risk_count, "avg": avg, "perfect": perfect})

# ── ASSESSMENTS ───────────────────────────────────────────────────────────────
@app.get("/assessments/{coid}", response_class=HTMLResponse)
async def assessments_page(request: Request, coid: str):
    faculty = get_faculty(request)
    if not faculty: return RedirectResponse(url="/login", status_code=302)
    course = fix_id(await courses_collection.find_one({"_id": ObjectId(coid)}))
    assessments = [fix_id(a) for a in await assessments_collection.find({"course_id": coid}).to_list(50)]
    total_w = sum(a.get("weightage", 0) for a in assessments)
    return templates.TemplateResponse(request, "assessments.html", {"faculty": faculty, "course": course, "assessments": assessments, "total_w": total_w})

@app.post("/assessments/add")
async def add_assessment(request: Request, course_oid: str = Form(...), assessment_type: str = Form(...),
                         calc_method: str = Form(...), total_marks: int = Form(0), weightage: int = Form(...)):
    faculty = get_faculty(request)
    if not faculty: return RedirectResponse(url="/login", status_code=302)
    await assessments_collection.insert_one({"course_id": course_oid, "type": assessment_type,
        "calc_method": calc_method, "total_marks": total_marks, "weightage": weightage, "created_at": datetime.now()})
    return RedirectResponse(url=f"/assessments/{course_oid}", status_code=302)

@app.post("/assessments/delete/{aoid}")
async def delete_assessment(request: Request, aoid: str, course_oid: str = Form(...)):
    faculty = get_faculty(request)
    if not faculty: return RedirectResponse(url="/login", status_code=302)
    await assessments_collection.delete_one({"_id": ObjectId(aoid)})
    return RedirectResponse(url=f"/assessments/{course_oid}", status_code=302)

# ── MARKS ─────────────────────────────────────────────────────────────────────
@app.get("/marks/{coid}", response_class=HTMLResponse)
async def marks_page(request: Request, coid: str):
    faculty = get_faculty(request)
    if not faculty: return RedirectResponse(url="/login", status_code=302)
    course = fix_id(await courses_collection.find_one({"_id": ObjectId(coid)}))
    students = [fix_id(s) for s in await students_collection.find({"course_id": coid}).to_list(200)]
    assessments = [fix_id(a) for a in await assessments_collection.find({"course_id": coid}).to_list(50)]
    all_marks = await marks_collection.find({"course_id": coid}).to_list(1000)
    marks_map = {f"{m['student_id']}_{m['assessment_id']}": m.get("obtained_marks", 0) for m in all_marks}
    return templates.TemplateResponse(request, "marks.html", {"faculty": faculty, "course": course, "students": students, "assessments": assessments, "marks_map": marks_map})

@app.post("/marks/save")
async def save_marks(request: Request):
    faculty = get_faculty(request)
    if not faculty: return RedirectResponse(url="/login", status_code=302)
    form = await request.form()
    coid = form.get("course_oid")
    students = await students_collection.find({"course_id": coid}).to_list(200)
    assessments = await assessments_collection.find({"course_id": coid}).to_list(50)
    for s in students:
        sid = str(s["_id"])
        for a in assessments:
            aid = str(a["_id"])
            val = form.get(f"mark_{sid}_{aid}")
            if val and val != "":
                await marks_collection.update_one({"student_id": sid, "assessment_id": aid, "course_id": coid},
                    {"$set": {"obtained_marks": float(val), "course_id": coid, "saved_at": datetime.now()}}, upsert=True)
    return RedirectResponse(url=f"/marks/{coid}", status_code=302)

# ── GRADING ───────────────────────────────────────────────────────────────────
@app.get("/grading/{coid}", response_class=HTMLResponse)
async def grading_page(request: Request, coid: str):
    faculty = get_faculty(request)
    if not faculty: return RedirectResponse(url="/login", status_code=302)
    course = fix_id(await courses_collection.find_one({"_id": ObjectId(coid)}))
    students = [fix_id(s) for s in await students_collection.find({"course_id": coid}).to_list(200)]
    assessments = [fix_id(a) for a in await assessments_collection.find({"course_id": coid}).to_list(50)]
    all_marks = await marks_collection.find({"course_id": coid}).to_list(1000)
    marks_map = {f"{m['student_id']}_{m['assessment_id']}": m.get("obtained_marks", 0) for m in all_marks}
    grade_data = []
    for s in students:
        sid = s["_id"]
        total = sum((marks_map.get(f"{sid}_{a['_id']}",0) / (a.get("total_marks",1) or 1)) * a.get("weightage",0) for a in assessments)
        total = round(total, 2)
        grade = "A" if total>=85 else "A-" if total>=80 else "B+" if total>=75 else "B" if total>=70 else "B-" if total>=65 else "C+" if total>=60 else "C" if total>=55 else "C-" if total>=50 else "F"
        grade_data.append({"_id": sid, "name": s["name"], "roll_no": s["roll_no"], "total": total, "grade": grade, "saved_grade": s.get("final_grade","")})
    scores = [g["total"] for g in grade_data]
    avg = round(sum(scores)/len(scores),2) if scores else 0
    grade_dist = {}
    for g in grade_data: grade_dist[g["grade"]] = grade_dist.get(g["grade"],0) + 1
    return templates.TemplateResponse(request, "grading.html", {"faculty": faculty, "course": course,
        "grade_data": grade_data, "avg": avg, "high": max(scores) if scores else 0,
        "low": min(scores) if scores else 0, "grade_dist": grade_dist})

@app.post("/grading/save/{coid}")
async def save_grades(request: Request, coid: str):
    faculty = get_faculty(request)
    if not faculty: return RedirectResponse(url="/login", status_code=302)
    form = await request.form()
    students = await students_collection.find({"course_id": coid}).to_list(200)
    for s in students:
        grade = form.get(f"grade_{str(s['_id'])}")
        if grade:
            await students_collection.update_one({"_id": s["_id"]}, {"$set": {"final_grade": grade}})
    await courses_collection.update_one({"_id": ObjectId(coid)}, {"$set": {"status": "Submit"}})
    return RedirectResponse(url=f"/grading/{coid}", status_code=302)

# ── STUDENT PROFILE ───────────────────────────────────────────────────────────
@app.get("/student-profile/{soid}", response_class=HTMLResponse)
async def student_profile(request: Request, soid: str):
    faculty = get_faculty(request)
    if not faculty: return RedirectResponse(url="/login", status_code=302)
    student = fix_id(await students_collection.find_one({"_id": ObjectId(soid)}))
    course = fix_id(await courses_collection.find_one({"_id": ObjectId(student["course_id"])}))
    lectures = await attendance_collection.find({"course_id": student["course_id"]}).to_list(100)
    tl = len(lectures)
    p = sum(1 for l in lectures for r in l.get("records",[]) if str(r.get("student_id"))==soid and r.get("present"))
    att_pct = round(p/tl*100) if tl else 0
    assessments = await assessments_collection.find({"course_id": student["course_id"]}).to_list(50)
    all_marks = await marks_collection.find({"student_id": soid}).to_list(100)
    marks_map = {m["assessment_id"]: m.get("obtained_marks",0) for m in all_marks}
    breakdown = [{"type": a["type"], "obtained": marks_map.get(str(a["_id"]),0), "total": a.get("total_marks",0), "weightage": a.get("weightage",0)} for a in assessments]
    return templates.TemplateResponse(request, "student_profile.html", {"faculty": faculty, "student": student,
        "course": course, "att_pct": att_pct, "present_count": p, "total_lecs": tl,
        "breakdown": breakdown, "final_grade": student.get("final_grade","N/A")})

# ── SETTINGS ──────────────────────────────────────────────────────────────────
@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    faculty = get_faculty(request)
    if not faculty: return RedirectResponse(url="/login", status_code=302)
    fd = fix_id(await faculty_collection.find_one({"_id": ObjectId(faculty["_id"])}))
    return templates.TemplateResponse(request, "settings.html", {"faculty": faculty, "faculty_data": fd})

@app.post("/settings/update")
async def update_settings(request: Request, name: str = Form(...), email: str = Form(...),
                          department: str = Form(...), new_password: str = Form("")):
    faculty = get_faculty(request)
    if not faculty: return RedirectResponse(url="/login", status_code=302)
    upd = {"name": name, "email": email, "department": department}
    if new_password: upd["password"] = new_password
    await faculty_collection.update_one({"_id": ObjectId(faculty["_id"])}, {"$set": upd})
    r = RedirectResponse(url="/settings", status_code=302)
    r.set_cookie("faculty_name", name, max_age=86400)
    return r

# ── JSON APIS ─────────────────────────────────────────────────────────────────
@app.get("/api/dashboard/stats")
async def api_stats(request: Request):
    faculty = get_faculty(request)
    if not faculty: raise HTTPException(401, "Not authenticated")
    courses = await courses_collection.find({"faculty_id": faculty["_id"]}).to_list(100)
    cids = [str(c["_id"]) for c in courses]
    return {"total_courses": len(courses), "total_students": await students_collection.count_documents({"course_id": {"$in": cids}}), "pending": sum(1 for c in courses if c.get("status")!="Submit")}

@app.get("/api/courses")
async def api_courses(request: Request):
    faculty = get_faculty(request)
    if not faculty: raise HTTPException(401)
    return [fix_id(c) for c in await courses_collection.find({"faculty_id": faculty["_id"]}).to_list(100)]

@app.get("/api/students/{coid}")
async def api_students(coid: str):
    return [fix_id(s) for s in await students_collection.find({"course_id": coid}).to_list(200)]

@app.get("/api/attendance/report/{coid}")
async def api_report(coid: str):
    students = await students_collection.find({"course_id": coid}).to_list(200)
    lectures = await attendance_collection.find({"course_id": coid}).to_list(100)
    tl = len(lectures)
    return [{"name": s["name"], "roll_no": s["roll_no"], "pct": round(sum(1 for l in lectures for r in l.get("records",[]) if str(r.get("student_id"))==str(s["_id"]) and r.get("present"))/tl*100) if tl else 0} for s in students]

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
