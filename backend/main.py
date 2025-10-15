"""
File: main.py
Author: Saumya Ranadive
Task: Implement FastAPI backend logic, handle routes for chatbot
Date: 1-10-2025
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup
"""
Author: Nishant Patil
Task: MongoDB integration - store and retrieve student chat history
Date: 11-10-2025
"""

client = MongoClient("mongodb://localhost:27017/")
db = client["university_chatbot"]
chats_collection = db["chats"]

client = MongoClient("mongodb://localhost:27017/")
db = client["university_bot"]
chats = db["chats"]

# Request model
class Message(BaseModel):
    name: str
    text: str

MENU = """
Please choose from the following options:
1) Courses
2) Hostels
3) Sports & Extra Curriculars
4) Scholarships
5) Fee Structure
6) Admission Process
7) Library
8) Placements
9) Exams
10) Contact Info
"""

RESPONSES = {
    "1": "📘 Courses: We offer B.Tech, M.Tech, B.Sc, and M.Sc programs.",
    "2": "🏠 Hostels: Separate hostels for boys and girls with WiFi & security.",
    "3": "⚽ Sports: Football, cricket, basketball & cultural clubs available.",
    "4": "🎓 Scholarships: Merit-based & need-based scholarships available.",
    "5": "💰 Fee Structure: Fee details available on the ERP portal.",
    "6": "📝 Admission: Apply online through the official website.",
    "7": "📚 Library: Open 8 AM – 8 PM. Digital & physical resources.",
    "8": "💼 Placements: Top recruiters include Infosys, TCS, and Wipro.",
    "9": "📝 Exams: Semester-wise exams conducted as per schedule.",
    "10": "📞 Contact Info: Reach us at university@gmail.com",
}


@app.post("/chat")
def chat(message: Message):
    user_name = message.name.strip()
    user_text = message.text.strip()

    # Check if user exists
    user_doc = chats.find_one({"name": user_name})
    if not user_doc:
        chats.insert_one({
            "name": user_name,
            "messages": [],
            "created_at": datetime.now()
        })
        bot_reply = f"👋 Welcome {user_name}! {MENU}"
    else:
        # Determine bot reply
        if user_text in RESPONSES:
            bot_reply = RESPONSES[user_text]
        else:
            bot_reply = "😅 Sorry, I didn't understand that. For further details, please contact: university@gmail.com"

    # Save user message
    chats.update_one(
        {"name": user_name},
        {"$push": {"messages": {"from": "user", "text": user_text, "time": datetime.now()}}}
    )

    # Save bot reply
    chats.update_one(
        {"name": user_name},
        {"$push": {"messages": {"from": "bot", "text": bot_reply, "time": datetime.now()}}}
    )

    return {"reply": bot_reply}


# Admin endpoints
@app.get("/users")
def get_users():
    users = chats.find({}, {"name": 1, "_id": 0})
    return list(users)


@app.get("/chat-history/{name}")
def get_chat_history(name: str):
    user_doc = chats.find_one({"name": name}, {"_id": 0})
    if not user_doc:
        return {"messages": []}
    return user_doc


@app.get("/stats")
def get_stats():
    users_count = chats.count_documents({})
    # Top 5 most asked options
    pipeline = [
        {"$unwind": "$messages"},
        {"$match": {"messages.from": "user"}},
        {"$group": {"_id": "$messages.text", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    top_questions = list(chats.aggregate(pipeline))
    return {"total_users": users_count, "top_questions": top_questions}
