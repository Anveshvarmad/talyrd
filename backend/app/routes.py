import uuid
from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename
from sqlalchemy import text

from app.config import APP_NAME, APP_VERSION, UPLOAD_DIR, ALLOWED_EXTENSIONS, MAX_UPLOAD_MB
from app.db import check_db_connection, engine

api = Blueprint("api", __name__)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

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
                    ats_score
                )
                VALUES (
                    :full_name,
                    :target_role,
                    :original_filename,
                    :stored_filename,
                    :upload_path,
                    :job_description,
                    :extracted_resume_text,
                    :ats_score
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
                "extracted_resume_text": "",
                "ats_score": 0
            }
        ).mappings().first()

    return jsonify({
        "message": "Resume uploaded successfully",
        "submission_id": row["id"],
        "original_filename": original_filename,
        "stored_filename": stored_filename,
        "full_name": full_name,
        "target_role": target_role,
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
                    ats_score,
                    created_at::text AS created_at
                FROM submissions
                ORDER BY created_at DESC
            """)
        ).mappings().all()

    return jsonify([dict(row) for row in rows])
