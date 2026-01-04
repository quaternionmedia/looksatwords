"""FastAPI application for conversation thread visualization."""

from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select

from .database import create_db_and_tables, get_session
from .models import (
    Conversation,
    ConversationCreate,
    ConversationListItem,
    ConversationResponse,
)

# Import backend visualizer for analysis
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from frontend.visualizer_backend import ThreadVisualizerBackend

# Mount static files for frontend
FRONTEND_PATH = Path(__file__).parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    create_db_and_tables()
    yield
    # Shutdown (nothing to do)


app = FastAPI(
    title="Conversation Thread Visualizer API",
    description="API for analyzing and visualizing conversation threads",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Conversation Thread Visualizer API is running"}


@app.get("/", response_class=HTMLResponse)
def root():
    """Serve the frontend."""
    index_path = FRONTEND_PATH / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return HTMLResponse("<h1>Conversation Thread Visualizer API</h1><p>Frontend not found. Visit <a href='/docs'>/docs</a> for API documentation.</p>")


@app.post("/api/conversations/analyze", response_model=ConversationResponse)
def analyze_conversation(
    request: ConversationCreate,
    session: Session = Depends(get_session)
):
    """Analyze a conversation and store results."""
    # Use backend visualizer for analysis
    visualizer = ThreadVisualizerBackend()
    visualizer.parseConversation(request.text)
    visualizer.identifyThreads()
    
    # Create title if not provided
    title = request.title or f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    # Prepare thread data for storage
    threads_data = []
    for thread in visualizer.threads:
        threads_data.append({
            "name": thread["name"],
            "color": thread["color"],
            "points": thread["points"],
            "total_intensity": thread["totalIntensity"]
        })
    
    # Prepare tangent data for storage
    tangents_data = []
    for tangent in visualizer.tangents:
        tangents_data.append({
            "start_time": tangent["startTime"],
            "end_time": tangent["endTime"],
            "tangent_type": tangent["type"],
            "topics": tangent["topics"],
            "start_text": tangent["startText"],
            "resolution_text": tangent.get("resolutionText")
        })
    
    # Create conversation record
    conversation = Conversation(
        title=title,
        text=request.text,
        total_duration=visualizer.totalDuration,
        speakers=visualizer.speakers,
        threads=threads_data,
        tangents=tangents_data
    )
    
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    
    return ConversationResponse(
        conversation_id=conversation.id,
        title=conversation.title,
        total_duration=conversation.total_duration,
        speakers=conversation.speakers,
        threads=conversation.threads,
        tangents=conversation.tangents
    )


@app.get("/api/conversations", response_model=List[ConversationListItem])
def list_conversations(session: Session = Depends(get_session)):
    """List all stored conversations."""
    conversations = session.exec(select(Conversation)).all()
    
    return [
        ConversationListItem(
            id=conv.id,
            title=conv.title,
            created_at=conv.created_at,
            total_duration=conv.total_duration,
            speaker_count=len(conv.speakers),
            thread_count=len(conv.threads),
            tangent_count=len(conv.tangents)
        )
        for conv in conversations
    ]


@app.get("/api/conversations/{conversation_id}")
def get_conversation(
    conversation_id: int,
    session: Session = Depends(get_session)
):
    """Get a specific conversation by ID."""
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversation


@app.delete("/api/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    session: Session = Depends(get_session)
):
    """Delete a conversation by ID."""
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    session.delete(conversation)
    session.commit()
    
    return {"status": "ok", "message": f"Conversation {conversation_id} deleted"}


# Mount static files for frontend assets (css/, js/, etc.)
# This must come AFTER API routes so it doesn't override them
if FRONTEND_PATH.exists():
    # Mount subdirectories for CSS and JS
    css_path = FRONTEND_PATH / "css"
    js_path = FRONTEND_PATH / "js"
    if css_path.exists():
        app.mount("/css", StaticFiles(directory=str(css_path)), name="css")
    if js_path.exists():
        app.mount("/js", StaticFiles(directory=str(js_path)), name="js")
    # Mount root-level static files (visualizer.js, visualizer.html, etc.)
    app.mount("/", StaticFiles(directory=str(FRONTEND_PATH), html=True), name="frontend")
