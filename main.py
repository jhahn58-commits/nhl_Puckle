# -*- coding: utf-8 -*-
"""
Created on Wed Jan  7 22:15:13 2026

@author: hahnj
"""

from contextlib import asynccontextmanager 
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

@app.get("/daily-player")
def get_daily_player(db: Session = Depends(get_db)):
    players = db.query(Player).all()
    # For a true Wordle, you'd pick based on the date. For now, it's random.
    target = random.choice(players)
    return {
        "id": target.id,
        "jersey": target.jersey_number,
        "team": target.team_abbr,
        "position": target.position,
        "image": target.headshot_url
    }

@app.get("/search-players")
def search_players(q: str, db: Session = Depends(get_db)):
    # Search for players where the name matches the query string
    # We limit to 10 results to keep the dropdown clean and fast
    results = db.query(Player).filter(
        Player.full_name.ilike(f"%{q}%")
    ).limit(10).all()
    
    return [{"name": p.full_name, "id": p.id} for p in results]

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

