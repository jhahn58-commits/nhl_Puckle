# -*- coding: utf-8 -*-
"""
Created on Wed Jan  7 21:52:18 2026

@author: hahnj
"""

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Player(Base):
    __tablename__ = 'players'
    id = Column(Integer, primary_key=True)
    full_name = Column(String)
    jersey_number = Column(Integer)
    position = Column(String)
    team_abbr = Column(String)
    headshot_url = Column(String)

# Connect to your local Postgres or SQLite
engine = create_engine('postgresql://postgres:antProj891@localhost/nhl_trivia')
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)

def init_db():
    # This command looks at all your classes (like Player) 
    # and creates the actual tables in Postgres.
    Base.metadata.create_all(bind=engine)
    
    
    
    
from nhlpy import NHLClient # pip install nhl-api-py

def sync_nhl_data():
    client = NHLClient()
    db = SessionLocal()
    
    # Get all teams first
    teams = client.teams.teams()
    
    for team in teams:
        abbr = team['abbr']
        # Fetch current roster for the 20252026 season
        roster = client.teams.team_roster(team_abbr=abbr, season="20252026")
        
        # Add Forwards, Defensemen, and Goalies to your DB
        for player_data in roster['forwards'] + roster['defensemen'] + roster['goalies']:
            player = Player(
                id=player_data['id'],
                full_name=player_data['firstName']['default'] + " " + player_data['lastName']['default'],
                jersey_number=player_data.get('sweaterNumber', 0),
                position=player_data['positionCode'],
                team_abbr=abbr,
                headshot_url=player_data['headshot']
            )
            db.merge(player) # merge avoids duplicates
    db.commit()
    db.close()