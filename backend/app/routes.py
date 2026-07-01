import uuid
from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename
from sqlalchemy import text

from app.config import APP_NAME, APP_VERSION, UPLOAD_DIR, ALLOWED_EXTENSIONS, MAX_UPLOAD_MB
from app.db import check_db_connection, engine
from app.services.extractor import extract_text
from app.services.ats_analyzer import analyze_resume_against_job

api = Blueprint("api", __name__)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def join_list(items):
    return ", ".join(items or [])

def split_text(value):
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]

@api.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "talyrd-backend"
    })

@api.get("/api/status")
def status():
    db_ok = check_db_connection()

    return jsonify({
        "app": APP_NAME,
        "version": APP_VERSION,
        "backend": "ok",
        "database": "ok" if db_ok else "error"
    })

@api.post("/api/uploads")
def upload_resume():
    if "resume" not in request.files:
        return jsonify({"error": "Resume file is required"}), 400

    resume_file = request.files["resume"]
    full_name = request.form.get("full_name", "").strip()
    target_role = request.form.get("target_role", "").strip()
    job_description = request.form.get("job_description", "").strip()

    if not full_name:
        return jsonify({"error": "Full name is required"}), 400

    if not target_role:
        return jsonify({"error": "Target role is required"}), 400

    if not job_description:
        return jsonify({"error": "Job description is required"}), 400

    if not resume_file.filename:
        return jsonify({"error": "Resume filename is missing"}), 400

    if not allowed_file(resume_file.filename):
        return jsonify({"error": "Allowed file types are PDF, DOCX, TXT, and TEX"}), 400

    resume_file.seek(0, 2)
    file_size_mb = resume_file.tell() / (1024 * 1024)
    resume_file.seek(0)

    if file_size_mb > MAX_UPLOAD_MB:
        return jsonify({"error": f"File is too large. Max file size is {MAX_UPLOAD_MB} MB"}), 400

    original_filename = secure_filename(resume_file.filename)
    stored_filename = f"{uuid.uuid4()}_{original_filename}"
    upload_path = UPLOAD_DIR / stored_filename

    resume_file.save(upload_path)

    try:
        extracted_text = extract_text(upload_path)
    except Exception as error:
        return jsonify({
            "error": f"File uploaded, but text extraction failed: {str(error)}"
        }), 400

    analysis = analyze_resume_against_job(extracted_text, job_description)
    extracted_char_count = len(extracted_text)

    with engine.begin() as conn:
        row = conn.execute(
            text("""
                INSERT INTO submissions (
                    full_name,
                    target_role,
                    original_filename,
                    stored_filename,
                    upload_path,
                    job_description,
                    extracted_resume_text,
                    extracted_char_count,
                    extraction_status,
                    ats_score,
                    job_keywords,
                    resume_keywords,
                    matched_keywords,
                    missing_keywords,
                    recommendations
                )
                VALUES (
                    :full_name,
                    :target_role,
                    :original_filename,
                    :stored_filename,
                    :upload_path,
                    :job_description,
                    :extracted_resume_text,
                    :extracted_char_count,
                    :extraction_status,
                    :ats_score,
                    :job_keywords,
                    :resume_keywords,
                    :matched_keywords,
                    :missing_keywords,
                    :recommendations
                )
                RETURNING id, created_at
            """),
            {
                "full_name": full_name,
                "target_role": target_role,
                "original_filename": original_filename,
                "stored_filename": stored_filename,
                "upload_path": str(upload_path),
                "job_description": job_description,
                "extracted_resume_text": extracted_text,
                "extracted_char_count": extracted_char_count,
                "extraction_status": "completed",
                "ats_score": analysis["ats_score"],
                "job_keywords": join_list(analysis["job_keywords"]),
                "resume_keywords": join_list(analysis["resume_keywords"]),
                "matched_keywords": join_list(analysis["matched_keywords"]),
                "missing_keywords": join_list(analysis["missing_keywords"]),
                "recommendations": "\n".join(analysis["recommendations"])
            }
        ).mappings().first()

    return jsonify({
        "message": "Resume uploaded, text extracted, and ATS analysis completed",
        "submission_id": row["id"],
        "original_filename": original_filename,
        "stored_filename": stored_filename,
        "full_name": full_name,
        "target_role": target_role,
        "extraction_status": "completed",
        "extracted_char_count": extracted_char_count,
        "extracted_preview": extracted_text[:1200],
        "ats_score": analysis["ats_score"],
        "job_keywords": analysis["job_keywords"],
        "resume_keywords": analysis["resume_keywords"],
        "matched_keywords": analysis["matched_keywords"],
        "missing_keywords": analysis["missing_keywords"],
        "recommendations": analysis["recommendations"],
        "created_at": str(row["created_at"])
    }), 201

@api.get("/api/submissions")
def list_submissions():
    with engine.begin() as conn:
        rows = conn.execute(
            text("""
                SELECT
                    id,
                    full_name,
                    target_role,
                    original_filename,
                    extracted_char_count,
                    extraction_status,
                    ats_score,
                    created_at::text AS created_at
                FROM submissions
                ORDER BY created_at DESC
            """)
        ).mappings().all()

    return jsonify([dict(row) for row in rows])

@api.get("/api/submissions/<int:submission_id>")
def get_submission(submission_id):
    with engine.begin() as conn:
        row = conn.execute(
            text("""
                SELECT
                    id,
                    full_name,
                    target_role,
                    original_filename,
                    job_description,
                    extracted_resume_text,
                    extracted_char_count,
                    extraction_status,
                    ats_score,
                    job_keywords,
                    resume_keywords,
                    matched_keywords,
                    missing_keywords,
                    recommendations,
                    created_at::text AS created_at
                FROM submissions
                WHERE id = :submission_id
            """),
            {"submission_id": submission_id}
        ).mappings().first()

    if not row:
        return jsonify({"error": "Submission not found"}), 404

    item = dict(row)
    item["extracted_preview"] = item["extracted_resume_text"][:2000]
    item["job_keywords"] = split_text(item["job_keywords"])
    item["resume_keywords"] = split_text(item["resume_keywords"])
    item["matched_keywords"] = split_text(item["matched_keywords"])
    item["missing_keywords"] = split_text(item["missing_keywords"])
    item["recommendations"] = item["recommendations"].splitlines() if item["recommendations"] else []

    return jsonify(item)
