"""
File: main.py
Author: Saumya Ranadive
Task: Implement FastAPI backend logic, handle routes for chatbot
"""

import datetime
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime
import re

# --- FASTAPI SETUP ---
app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATABASE FIELD CONSTANTS ---
FIELD_NAME = "name"
FIELD_MESSAGES = "messages"
FIELD_FROM = "from"
FIELD_TEXT = "text"
FIELD_TIME = "time"
ROLE_USER = "user"
ROLE_BOT = "bot"
'''
--- MONGO DB SETUP ---
 Author: Nishant Patil
 Task: MongoDB integration - store and retrieve student chat history
 Date: 11-10-2025
'''

try:
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
    db = client["university_bot"]
    chats = db["chats"]
   
    client.admin.command('ping')
    print("Successfully connected to MongoDB.")
except Exception as e:
    print(f"Could not connect to MongoDB: {e}")
   



class ChatRequest(BaseModel):
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

    "1": " Courses: We offer B.Tech, M.Tech, B.Sc, and M.Sc programs.",
    "courses": " Courses: We offer B.Tech, M.Tech, B.Sc, and M.Sc programs.",
    "2": " Hostels: Separate hostels for boys and girls with WiFi & security.",
    "hostels": " Hostels: Separate hostels for boys and girls with WiFi & security.",
    "3": " Sports: Football, cricket, basketball & cultural clubs available.",
    "sports": " Sports: Football, cricket, basketball & cultural clubs available.",
    "4": " Scholarships: Merit-based & need-based scholarships available.",
    "scholarships": " Scholarships: Merit-based & need-based scholarships available.",
    "5": " Fee Structure: Fee details available on the ERP portal.",
    "fee": " Fee Structure: Fee details available on the ERP portal.",
    "6": " Admission: Apply online through the official website.",
    "admission": " Admission: Apply online through the official website.",
    "7": " Library: Open 8 AM – 8 PM. Digital & physical resources.",
    "library": " Library: Open 8 AM – 8 PM. Digital & physical resources.",
    "8": " Placements: Top recruiters include Infosys, TCS, and Wipro.",
    "placements": " Placements: Top recruiters include Infosys, TCS, and Wipro.",
    "9": " Exams: Semester-wise exams conducted as per schedule.",
    "exams": " Exams: Semester-wise exams conducted as per schedule.",
    "10": " Contact Info: Reach us at university@gmail.com",
    "contact": " Contact Info: Reach us at university@gmail.com",
}


FALLBACK_REPLY = " Sorry, I didn't understand that. For further details, please contact: university@gmail.com"
WELCOME_FORMAT = " Welcome {user_name}! {MENU}"




@app.post("/chat")
def chat(request: ChatRequest) -> Dict[str, str]:
    user_name = request.name.strip()
    user_text = request.text.strip()

  
    if not user_name or not user_text:
        raise HTTPException(status_code=400, detail="Name and text cannot be empty.")
    
  
    normalized_text = user_text.lower()
    bot_reply = FALLBACK_REPLY
    is_new_user = False
    

    try:
        update_result = chats.update_one(
            {FIELD_NAME: user_name},
            {"$setOnInsert": {
                FIELD_MESSAGES: [],
                "created_at": datetime.now()
            }},
            upsert=True
        )
  
        if update_result.upserted_id:
            is_new_user = True
        
    except Exception as e:
        print(f"Database error during user check/creation for {user_name}: {e}")
     
        raise HTTPException(status_code=500, detail="A server error occurred while connecting to the database.")

 
    if is_new_user:
        bot_reply = WELCOME_FORMAT.format(user_name=user_name, MENU=MENU)
    
  
    elif normalized_text in RESPONSES:
        bot_reply = RESPONSES[normalized_text]
        
   
    elif re.search(r'\b(1|2|3|4|5|6|7|8|9|10)\b', normalized_text):
        match = re.search(r'\b(1|2|3|4|5|6|7|8|9|10)\b', normalized_text)
        option = match.group(1)
        bot_reply = RESPONSES.get(option, FALLBACK_REPLY)
    
 
    elif any(keyword in normalized_text for keyword in ["courses", "hostels", "sports", "scholarships", "fee", "admission", "library", "placements", "exams", "contact"]):
        if "courses" in normalized_text:
            bot_reply = RESPONSES["courses"]
        elif "hostels" in normalized_text:
            bot_reply = RESPONSES["hostels"]
        elif "sports" in normalized_text:
            bot_reply = RESPONSES["sports"]
        elif "scholarships" in normalized_text:
            bot_reply = RESPONSES["scholarships"]
        elif "fee" in normalized_text or "structure" in normalized_text:
            bot_reply = RESPONSES["fee"]
        elif "admission" in normalized_text or "apply" in normalized_text:
            bot_reply = RESPONSES["admission"]
        elif "library" in normalized_text:
            bot_reply = RESPONSES["library"]
        elif "placements" in normalized_text:
            bot_reply = RESPONSES["placements"]
        elif "exams" in normalized_text:
            bot_reply = RESPONSES["exams"]
        elif "contact" in normalized_text or "info" in normalized_text:
            bot_reply = RESPONSES["contact"]


    try:
        user_msg_doc = {FIELD_FROM: ROLE_USER, FIELD_TEXT: user_text, FIELD_TIME: datetime.now()}
        bot_msg_doc = {FIELD_FROM: ROLE_BOT, FIELD_TEXT: bot_reply, FIELD_TIME: datetime.now()}
        
      
        chats.update_one(
            {FIELD_NAME: user_name},
            {"$push": {FIELD_MESSAGES: {"$each": [user_msg_doc, bot_msg_doc]}}}
        )

    except Exception as e:
        print(f"Database error during message logging for {user_name}: {e}")
        
        pass 

    return {"reply": bot_reply}




@app.get("/users")
def get_users():
    try:
     
        users = chats.find({}, {FIELD_NAME: 1, "_id": 0})
        return list(users)
    except Exception as e:
        print(f"Error fetching users: {e}")
        raise HTTPException(status_code=500, detail="Database error fetching users.")


@app.get("/chat-history/{name}")
def get_chat_history(name: str):
    try:
 
        user_doc = chats.find_one({FIELD_NAME: name}, {"_id": 0})
        if not user_doc:
            raise HTTPException(status_code=404, detail=f"User '{name}' not found.")
        return user_doc
    except HTTPException:
 
        raise
    except Exception as e:
        print(f"Error fetching chat history for {name}: {e}")
        raise HTTPException(status_code=500, detail="Database error fetching chat history.")


@app.get("/stats")
def get_stats():
    try:
        users_count = chats.count_documents({})

    
        pipeline = [
            {"$unwind": f"${FIELD_MESSAGES}"},
            {"$match": {f"{FIELD_MESSAGES}.{FIELD_FROM}": ROLE_USER}},
            {"$group": {"_id": f"${FIELD_MESSAGES}.{FIELD_TEXT}", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        top_questions = list(chats.aggregate(pipeline))
        return {"total_users": users_count, "top_questions": top_questions}
    except Exception as e:
        print(f"Error generating statistics: {e}")
        raise HTTPException(status_code=500, detail="Database error generating statistics.")
