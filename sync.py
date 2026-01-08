# -*- coding: utf-8 -*-
"""
Created on Wed Jan  7 21:54:40 2026

@author: hahnj
"""

from nhlpy import NHLClient # pip install nhl-api-py
from database import SessionLocal, Player

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
