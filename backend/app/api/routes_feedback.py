import sqlite3
import time
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends
from app.config import settings, STORAGE_DIR
from app.services.auth_service import verify_api_key

router = APIRouter(prefix="/feedback", tags=["Feedback Collection"])

DB_PATH = STORAGE_DIR / "feedback.db"

def init_feedback_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            generation_id TEXT NOT NULL,
            rating TEXT CHECK(rating IN ('thumbs_up', 'thumbs_down')),
            feedback_text TEXT,
            corrected_sql TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_feedback_db()

class FeedbackRequest(BaseModel):
    generation_id: str = Field(..., description="Target generation ID")
    rating: str = Field(..., description="'thumbs_up' or 'thumbs_down'")
    feedback_text: Optional[str] = Field(None, description="Optional user comments")
    corrected_sql: Optional[str] = Field(None, description="User provided correct SQL if generated was wrong")

@router.post("", dependencies=[Depends(verify_api_key)])
async def submit_feedback(req: FeedbackRequest):
    """Submits user feedback on generated SQL queries to store for future QLoRA fine-tuning iterations."""
    if req.rating not in ("thumbs_up", "thumbs_down"):
        raise HTTPException(status_code=400, detail="Rating must be 'thumbs_up' or 'thumbs_down'")
        
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.execute(
            "INSERT INTO user_feedback (generation_id, rating, feedback_text, corrected_sql) VALUES (?, ?, ?, ?)",
            (req.generation_id, req.rating, req.feedback_text, req.corrected_sql)
        )
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "message": "Feedback submitted successfully and saved for future fine-tuning dataset generation.",
            "generation_id": req.generation_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/list")
async def list_feedback():
    """Lists submitted feedback entries for inspection."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT id, generation_id, rating, feedback_text, corrected_sql, timestamp FROM user_feedback ORDER BY id DESC LIMIT 50")
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for r in rows:
        result.append({
            "id": r[0],
            "generation_id": r[1],
            "rating": r[2],
            "feedback_text": r[3],
            "corrected_sql": r[4],
            "timestamp": r[5]
        })
    return result
