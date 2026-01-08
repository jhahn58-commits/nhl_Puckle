import os
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database

# 1. DATABASE URL LOGIC
# On Render/Railway, they provide a DATABASE_URL environment variable.
# Locally, it will default to your postgres setup.
local_url = "postgresql://postgres:yourpassword@localhost:5432/nhl_trivia"
DATABASE_URL = os.environ.get("DATABASE_URL", local_url)

# Fix for Render/Heroku: they often use 'postgres://' but SQLAlchemy requires 'postgresql://'
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 2. SETUP ENGINE AND SESSION
# 'check_same_thread' is only needed for SQLite, but doesn't hurt for Postgres
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 3. PLAYER MODEL
class Player(Base):
    __tablename__ = 'players'
    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    jersey_number = Column(Integer)
    position = Column(String)
    team_abbr = Column(String)
    headshot_url = Column(String)

# 4. INITIALIZATION LOGIC
def init_db():
    """
    Creates the database if it doesn't exist (Postgres only)
    and creates all tables defined in the models.
    """
    try:
        # Only try to create the database if we are using Postgres
        if DATABASE_URL.startswith("postgresql"):
            if not database_exists(engine.url):
                create_database(engine.url)
                print("--- Created new database: nhl_trivia ---")
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        print("--- Database tables initialized successfully ---")
    except Exception as e:
        print(f"Error initializing database: {e}")

if __name__ == "__main__":
    # Running this file directly will initialize the DB
    init_db()
