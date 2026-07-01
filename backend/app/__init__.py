from flask import Flask
from flask_cors import CORS
from app.routes import api
from app.config import MAX_UPLOAD_MB

def create_app():
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024
    CORS(app)
    app.register_blueprint(api)
    return app
