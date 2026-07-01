import time
from sqlalchemy import create_engine, text
from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

def init_db():
    for attempt in range(30):
        try:
            with engine.begin() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS submissions (
                        id SERIAL PRIMARY KEY,
                        full_name TEXT,
                        target_role TEXT,
                        original_filename TEXT,
                        job_description TEXT,
                        extracted_resume_text TEXT,
                        ats_score INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
            print("Database initialized successfully")
            return
        except Exception as error:
            print(f"Database not ready yet. Retry {attempt + 1}/30")
            time.sleep(2)

    raise RuntimeError("Database connection failed after retries")

def check_db_connection():
    with engine.begin() as conn:
        result = conn.execute(text("SELECT 1 AS ok")).mappings().first()
        return result["ok"] == 1
