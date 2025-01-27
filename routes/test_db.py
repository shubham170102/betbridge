from sqlalchemy import create_engine

DATABASE_URL = "postgresql://postgres:password@localhost:5432/sports_db"
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as connection:
        print("Database connection successful!")
except Exception as e:
    print(f"Database connection failed: {e}")
