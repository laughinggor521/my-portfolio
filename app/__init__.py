import os
from pathlib import Path
import click
from flask import Flask, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect, generate_csrf
from werkzeug.middleware.proxy_fix import ProxyFix

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__, static_folder=None)
    app.config.from_object("app.config.Config")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    from . import models
    from .routes import api
    app.register_blueprint(api, url_prefix="/api")

    @login_manager.user_loader
    def load_user(user_id):
        from .models import Admin
        try:
            return db.session.get(Admin, int(user_id))
        except (TypeError, ValueError):
            return None

    @app.get("/")
    def index():
        return send_from_directory(str(Path(app.root_path).parent / "site"), "index.html")

    @app.get("/uploads/<path:filename>")
    def uploaded_file(filename):
        upload_dir = Path(app.config["UPLOAD_DIR"]).resolve()
        candidate = (upload_dir / filename).resolve()
        if not str(candidate).startswith(str(upload_dir) + os.sep) or not candidate.is_file():
            return jsonify(error="Not found"), 404
        mime = {".jpg":"image/jpeg", ".jpeg":"image/jpeg", ".png":"image/png", ".webp":"image/webp", ".gif":"image/gif"}.get(candidate.suffix.lower(), "application/octet-stream")
        return app.response_class(open(candidate, "rb"), mimetype=mime,
            headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "public, max-age=86400"})

    @app.get("/healthz")
    def healthz():
        return jsonify(status="ok")

    @app.get("/api/csrf")
    def csrf_token():
        response = jsonify(csrf_token=generate_csrf())
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/<path:path>")
    def static_files(path):
        site = (Path(app.root_path).parent / "site").resolve()
        candidate = (site / path).resolve()
        if not str(candidate).startswith(str(site) + os.sep):
            return jsonify(error="Not found"), 404
        if candidate.is_file():
            return send_from_directory(str(site), path)
        return send_from_directory(str(site), "index.html")

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Content-Security-Policy", "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'")
        return response

    @app.cli.command("create-admin")
    @click.option("--if-not-exists", is_flag=True, default=False)
    def create_admin(if_not_exists):
        from .models import Admin
        username = os.environ.get("ADMIN_USERNAME", "").strip()
        password = os.environ.get("ADMIN_PASSWORD", "")
        if not username or not password:
            raise click.ClickException("Set ADMIN_USERNAME and ADMIN_PASSWORD.")
        if len(password) < 14:
            raise click.ClickException("ADMIN_PASSWORD must be at least 14 characters.")
        old = Admin.query.filter_by(username=username).first()
        if old:
            if if_not_exists:
                click.echo("Admin already exists; password unchanged.")
                return
            raise click.ClickException("Admin already exists.")
        admin = Admin(username=username)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        click.echo("Admin created.")
    return app
