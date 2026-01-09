# -*- coding: utf-8 -*-
"""
Created on Wed Jan  7 22:15:13 2026

@author: hahnj
"""

from contextlib import asynccontextmanager  # <--- Add this line
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database import SessionLocal, Player
import random

from database import SessionLocal, Player, init_db
from sync import sync_nhl_data # Import your sync function

app = FastAPI()

# Enable CORS so your frontend can talk to your backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Updated random player route with team filtering
@app.get("/daily-player")
def get_daily_player(team: str = None, db: Session = Depends(get_db)):
    query = db.query(Player)
    
    # Apply filter if team is provided (e.g., "TOR", "BOS")
    if team and team != "ALL":
        query = query.filter(Player.team_abbr == team)
        
    count = query.count()
    if count == 0:
        raise HTTPException(status_code=404, detail="No players found for this team")
    
    random_index = random.randint(0, count - 1)
    player = query.offset(random_index).first()
    
    return {
        "id": player.id,
        "team": player.team_abbr,
        "jersey": player.jersey_number,
        "position": player.position,
        "image": player.headshot_url,
        "name": player.full_name
    }

# Updated search route to prioritize or limit to the chosen team
@app.get("/search-players")
def search_players(q: str, team: str = None, db: Session = Depends(get_db)):
    query = db.query(Player).filter(Player.full_name.ilike(f"%{q}%"))
    
    # Filter search results if a team is selected
    if team and team != "ALL":
        query = query.filter(Player.team_abbr == team)
        
    results = query.limit(10).all()
    return [{"id": p.id, "name": p.full_name} for p in results]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Create tables
    init_db()
    
    # 2. Check if we have players. If not, sync!
    db = SessionLocal()
    player_count = db.query(Player).count()
    if player_count == 0:
        print("Database empty! Running initial NHL sync...")
        sync_nhl_data()
    db.close()
    
    yield

# This serves your HTML file from a folder named "static"
app.mount("/", StaticFiles(directory="static", html=True), name="static")
