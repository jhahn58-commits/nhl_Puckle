import os
import random
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

# Import our local database logic and the Sync script
from database import SessionLocal, init_db, Player
from sync import sync_nhl_data

# 1. LIFESPAN: This runs when Render starts your app
@asynccontextmanager
async def lifespan(app: FastAPI):
    # This creates the 'players' table if it doesn't exist
    init_db()
    
    # Check if we have players. If not, trigger the sync.
    db = SessionLocal()
    try:
        player_count = db.query(Player).count()
        if player_count == 0:
            print("--- Database empty! Running initial NHL sync ---")
            sync_nhl_data()
        else:
            print(f"--- Database ready with {player_count} players ---")
    finally:
        db.close()
    
    yield
    # Cleanup logic (if any) would go here on shutdown

# 2. INITIALIZE APP
app = FastAPI(lifespan=lifespan)

# Dependency to get a DB session for our routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 3. ROUTES

# Serve the actual game page
@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

# Endpoint to pick a random player for the daily challenge
@app.get("/daily-player")
def get_daily_player(db: Session = Depends(get_db)):
    count = db.query(Player).count()
    if count == 0:
        raise HTTPException(status_code=404, detail="No players found")
    
    # Pick a random player
    random_index = random.randint(0, count - 1)
    player = db.query(Player).offset(random_index).first()
    
    return {
        "id": player.id,
        "team": player.team_abbr,
        "jersey": player.jersey_number,
        "position": player.position,
        "image": player.headshot_url,
        "name": player.full_name # Frontend will hide this until revealed
    }

# Endpoint for the search bar autocomplete
@app.get("/search-players")
def search_players(q: str, db: Session = Depends(get_db)):
    # Search for names containing the string (case-insensitive)
    results = db.query(Player).filter(Player.full_name.ilike(f"%{q}%")).limit(10).all()
    return [{"id": p.id, "name": p.full_name} for p in results]

# 4. MOUNT STATIC FILES
# This must come AFTER your specific routes so it doesn't "swallow" the /daily-player path
app.mount("/static", StaticFiles(directory="static"), name="static")
