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
                        stored_filename TEXT,
                        upload_path TEXT,
                        job_description TEXT,
                        extracted_resume_text TEXT,
                        extracted_char_count INTEGER DEFAULT 0,
                        extraction_status TEXT DEFAULT 'pending',
                        ats_score INTEGER DEFAULT 0,
                        pre_ats_score INTEGER DEFAULT 0,
                        post_ats_score INTEGER DEFAULT 0,
                        job_keywords TEXT,
                        resume_keywords TEXT,
                        matched_keywords TEXT,
                        missing_keywords TEXT,
                        recommendations TEXT,
                        tailoring_status TEXT DEFAULT 'pending',
                        tailored_resume_text TEXT,
                        cover_letter_text TEXT,
                        improvement_summary TEXT,
                        pdf_status TEXT DEFAULT 'pending',
                        resume_pdf_path TEXT,
                        cover_letter_pdf_path TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))

                columns = [
                    "stored_filename TEXT",
                    "upload_path TEXT",
                    "extracted_char_count INTEGER DEFAULT 0",
                    "extraction_status TEXT DEFAULT 'pending'",
                    "job_keywords TEXT",
                    "resume_keywords TEXT",
                    "matched_keywords TEXT",
                    "missing_keywords TEXT",
                    "recommendations TEXT",
                    "pre_ats_score INTEGER DEFAULT 0",
                    "post_ats_score INTEGER DEFAULT 0",
                    "tailoring_status TEXT DEFAULT 'pending'",
                    "tailored_resume_text TEXT",
                    "cover_letter_text TEXT",
                    "improvement_summary TEXT",
                    "pdf_status TEXT DEFAULT 'pending'",
                    "resume_pdf_path TEXT",
                    "cover_letter_pdf_path TEXT"
                ]

                for column in columns:
                    conn.execute(text(f"""
                        ALTER TABLE submissions
                        ADD COLUMN IF NOT EXISTS {column}
                    """))

            print("Database initialized successfully")
            return
        except Exception:
            print(f"Database not ready yet. Retry {attempt + 1}/30")
            time.sleep(2)

    raise RuntimeError("Database connection failed after retries")

def check_db_connection():
    with engine.begin() as conn:
        result = conn.execute(text("SELECT 1 AS ok")).mappings().first()
        return result["ok"] == 1
