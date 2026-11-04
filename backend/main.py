from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import shutil
import os

app = FastAPI(title="University Security Backend", version="2.0.0")

# Enable CORS for Flutter web / cross-platform clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded media files publicly
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# In-Memory Database Mock (Replace with PostgreSQL or MongoDB in production if needed)
USERS_DB = {
    "CSO-MASTER-01": {
        "badgeNumber": "CSO-MASTER-01",
        "name": "Chief Security Officer",
        "email": "cso@meru.ac.ke",
        "role": "chiefSecurity",
        "passphrase": "ChiefSecure2026!",
        "assignedZone": "All Zones",
        "bio": "Commanding Officer for Campus Operations & Forensics Enclave.",
        "photoUrl": ""
    },
    "SEC-001": {
        "badgeNumber": "SEC-001",
        "name": "Officer Brian Kipkurui",
        "email": "brian@meru.ac.ke",
        "role": "guard",
        "passphrase": "password123",
        "assignedZone": "Gate A & Administration",
        "bio": "Mobile application developer & security detail.",
        "photoUrl": ""
    }
}

MESSAGES_DB = []
SYSTEM_ALERTS = [
    {
        "id": "alert-1",
        "title": "System Initialized",
        "message": "Python FastAPI backend connected successfully to Render cloud enclave.",
        "timestamp": datetime.utcnow().isoformat()
    }
]

# Active WebSocket connections manager for real-time broadcasting
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

class LoginRequest(BaseModel):
    badgeNumber: str
    passphrase: str

@app.post("/api/auth/login")
def login(data: LoginRequest):
    user = USERS_DB.get(data.badgeNumber)
    if user and user["passphrase"] == data.passphrase:
        return {"success": True, "user": user}
    raise HTTPException(status_code=401, detail="Invalid badge number or passphrase")

@app.get("/api/guards")
def get_guards():
    return list(USERS_DB.values())

@app.get("/api/messages/{user1}/{user2}")
def get_messages(user1: str, user2: str):
    chat_msgs = [
        m for m in MESSAGES_DB 
        if (m["senderBadge"] == user1 and m["receiverBadge"] == user2) or 
           (m["senderBadge"] == user2 and m["receiverBadge"] == user1)
    ]
    return sorted(chat_msgs, key=lambda x: x["timestamp"], reverse=True)

@app.post("/api/messages")
async def send_message(
    senderBadge: str = Form(...),
    receiverBadge: str = Form(...),
    text: str = Form(""),
    file: Optional[UploadFile] = File(None)
):
    media_url = None
    media_type = "text"

    if file:
        file_filename = f"{int(datetime.utcnow().timestamp())}_{file.filename}"
        file_path = os.path.join("uploads", file_filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Public URL for the uploaded file
        media_url = f"https://university-security-backend.onrender.com/uploads/{file_filename}"
        media_type = "image"

    msg_data = {
        "senderBadge": senderBadge,
        "receiverBadge": receiverBadge,
        "text": text,
        "mediaPath": media_url,
        "mediaType": media_type,
        "isEdited": False,
        "timestamp": datetime.utcnow().isoformat()
    }
    MESSAGES_DB.append(msg_data)

    # Broadcast via WebSocket to connected Flutter clients
    await manager.broadcast({"type": "chat_message", "data": msg_data})
    return {"success": True, "message": msg_data}

@app.get("/api/alerts")
def get_alerts():
    return SYSTEM_ALERTS

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
