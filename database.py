import motor.motor_asyncio
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://aimenahad05_db_user:e5bgOub3VuqzGIvz@cluster0.7ssh5vk.mongodb.net/?appName=Cluster0")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client["umt_faculty_db"]

faculty_collection     = db["faculty"]
courses_collection     = db["courses"]
students_collection    = db["students"]
attendance_collection  = db["attendance"]
assessments_collection = db["assessments"]
marks_collection       = db["marks"]
