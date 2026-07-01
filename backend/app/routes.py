from flask import Blueprint, jsonify
from app.config import APP_NAME, APP_VERSION
from app.db import check_db_connection

api = Blueprint("api", __name__)

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
