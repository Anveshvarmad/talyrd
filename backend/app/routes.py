import uuid
from pathlib import Path
from flask import Blueprint, jsonify, request, send_file
from werkzeug.utils import secure_filename
from sqlalchemy import text

from app.config import (
    APP_NAME,
    APP_VERSION,
    UPLOAD_DIR,
    OUTPUT_DIR,
    ALLOWED_EXTENSIONS,
    MAX_UPLOAD_MB,
    OPENAI_MODEL,
    OPENAI_API_KEY
)
from app.db import check_db_connection, engine
from app.services.extractor import extract_text
from app.services.ats_analyzer import analyze_resume_against_job
from app.services.openai_tailor import tailor_resume_with_openai
from app.services.pdf_service import compile_pdf

api = Blueprint("api", __name__)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def join_list(items):
    return ", ".join(items or [])

def split_text(value):
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]

def build_file_url(relative_path):
    if not relative_path:
        return None
    return f"/api/files/{relative_path}"

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
        "database": "ok" if db_ok else "error",
        "openai": "configured" if OPENAI_API_KEY else "missing",
        "openai_model": OPENAI_MODEL,
        "pdf_generation": "enabled"
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

    pre_analysis = analyze_resume_against_job(extracted_text, job_description)
    extracted_char_count = len(extracted_text)

    try:
        ai_output = tailor_resume_with_openai(
            full_name=full_name,
            target_role=target_role,
            resume_text=extracted_text,
            job_description=job_description,
            ats_analysis=pre_analysis
        )
        tailoring_status = "completed"
    except Exception as error:
        return jsonify({
            "error": f"OpenAI tailoring failed: {str(error)}"
        }), 500

    post_analysis = analyze_resume_against_job(
        ai_output["tailored_resume_text"],
        job_description
    )

    try:
        resume_pdf_path = compile_pdf(
            template_name="resume.tex.j2",
            data={
                "full_name": full_name,
                "target_role": target_role,
                "tailored_resume_text": ai_output["tailored_resume_text"]
            },
            output_prefix="talyrd_resume"
        )

        cover_letter_pdf_path = compile_pdf(
            template_name="cover_letter.tex.j2",
            data={
                "full_name": full_name,
                "target_role": target_role,
                "cover_letter_text": ai_output["cover_letter_text"]
            },
            output_prefix="talyrd_cover_letter"
        )

        pdf_status = "completed"
    except Exception as error:
        return jsonify({
            "error": f"PDF generation failed: {str(error)}"
        }), 500

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
                    pre_ats_score,
                    post_ats_score,
                    job_keywords,
                    resume_keywords,
                    matched_keywords,
                    missing_keywords,
                    recommendations,
                    tailoring_status,
                    tailored_resume_text,
                    cover_letter_text,
                    improvement_summary,
                    pdf_status,
                    resume_pdf_path,
                    cover_letter_pdf_path
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
                    :pre_ats_score,
                    :post_ats_score,
                    :job_keywords,
                    :resume_keywords,
                    :matched_keywords,
                    :missing_keywords,
                    :recommendations,
                    :tailoring_status,
                    :tailored_resume_text,
                    :cover_letter_text,
                    :improvement_summary,
                    :pdf_status,
                    :resume_pdf_path,
                    :cover_letter_pdf_path
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
                "ats_score": post_analysis["ats_score"],
                "pre_ats_score": pre_analysis["ats_score"],
                "post_ats_score": post_analysis["ats_score"],
                "job_keywords": join_list(post_analysis["job_keywords"]),
                "resume_keywords": join_list(post_analysis["resume_keywords"]),
                "matched_keywords": join_list(post_analysis["matched_keywords"]),
                "missing_keywords": join_list(post_analysis["missing_keywords"]),
                "recommendations": "\n".join(post_analysis["recommendations"]),
                "tailoring_status": tailoring_status,
                "tailored_resume_text": ai_output["tailored_resume_text"],
                "cover_letter_text": ai_output["cover_letter_text"],
                "improvement_summary": ai_output["improvement_summary"],
                "pdf_status": pdf_status,
                "resume_pdf_path": resume_pdf_path,
                "cover_letter_pdf_path": cover_letter_pdf_path
            }
        ).mappings().first()

    return jsonify({
        "message": "Resume tailored and PDFs generated successfully",
        "submission_id": row["id"],
        "original_filename": original_filename,
        "full_name": full_name,
        "target_role": target_role,
        "extraction_status": "completed",
        "tailoring_status": tailoring_status,
        "pdf_status": pdf_status,
        "extracted_char_count": extracted_char_count,
        "extracted_preview": extracted_text[:1200],
        "pre_ats_score": pre_analysis["ats_score"],
        "post_ats_score": post_analysis["ats_score"],
        "ats_score": post_analysis["ats_score"],
        "matched_keywords": post_analysis["matched_keywords"],
        "missing_keywords": post_analysis["missing_keywords"],
        "recommendations": post_analysis["recommendations"],
        "tailored_resume_text": ai_output["tailored_resume_text"],
        "cover_letter_text": ai_output["cover_letter_text"],
        "improvement_summary": ai_output["improvement_summary"],
        "resume_pdf_url": build_file_url(resume_pdf_path),
        "cover_letter_pdf_url": build_file_url(cover_letter_pdf_path),
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
                    tailoring_status,
                    pdf_status,
                    ats_score,
                    pre_ats_score,
                    post_ats_score,
                    resume_pdf_path,
                    cover_letter_pdf_path,
                    created_at::text AS created_at
                FROM submissions
                ORDER BY created_at DESC
            """)
        ).mappings().all()

    items = []

    for row in rows:
        item = dict(row)
        item["resume_pdf_url"] = build_file_url(item.get("resume_pdf_path"))
        item["cover_letter_pdf_url"] = build_file_url(item.get("cover_letter_pdf_path"))
        items.append(item)

    return jsonify(items)

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
                    tailoring_status,
                    pdf_status,
                    ats_score,
                    pre_ats_score,
                    post_ats_score,
                    job_keywords,
                    resume_keywords,
                    matched_keywords,
                    missing_keywords,
                    recommendations,
                    tailored_resume_text,
                    cover_letter_text,
                    improvement_summary,
                    resume_pdf_path,
                    cover_letter_pdf_path,
                    created_at::text AS created_at
                FROM submissions
                WHERE id = :submission_id
            """),
            {"submission_id": submission_id}
        ).mappings().first()

    if not row:
        return jsonify({"error": "Submission not found"}), 404

    item = dict(row)
    item["extracted_preview"] = item["extracted_resume_text"][:2000] if item["extracted_resume_text"] else ""
    item["job_keywords"] = split_text(item["job_keywords"])
    item["resume_keywords"] = split_text(item["resume_keywords"])
    item["matched_keywords"] = split_text(item["matched_keywords"])
    item["missing_keywords"] = split_text(item["missing_keywords"])
    item["recommendations"] = item["recommendations"].splitlines() if item["recommendations"] else []
    item["resume_pdf_url"] = build_file_url(item.get("resume_pdf_path"))
    item["cover_letter_pdf_url"] = build_file_url(item.get("cover_letter_pdf_path"))

    return jsonify(item)

@api.get("/api/files/<path:relative_path>")
def get_file(relative_path):
    output_root = OUTPUT_DIR.resolve()
    file_path = (OUTPUT_DIR / relative_path).resolve()

    if output_root not in file_path.parents:
        return jsonify({"error": "Invalid file path"}), 400

    if not file_path.exists():
        return jsonify({"error": "File not found"}), 404

    return send_file(file_path, mimetype="application/pdf", as_attachment=False)
