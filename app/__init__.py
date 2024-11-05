#!/usr/bin/env python3


from flask import Flask
from app.database import db
from config import Config
import logging
from logging.handlers import RotatingFileHandler


def create_app(config_class=Config):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Set up logging
    if not app.debug:
        # Create logs directory if it doesn't exist
        log_dir = Config.DATA_DIR / "logs"
        log_dir.mkdir(exist_ok=True)

        # Set up file handler
        file_handler = RotatingFileHandler(
            log_dir / "catalog_manager.log", maxBytes=10240000, backupCount=10  # 10MB
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s " "[in %(pathname)s:%(lineno)d]"
            )
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info("Catalog Manager startup")

    # Initialize database
    db.init_app(app)

    # Register blueprints
    from app.routes import bp

    app.register_blueprint(bp)

    # Ensure the database exists
    with app.app_context():
        app.logger.info(f"Database path: {Config.SQLITE_DB_PATH}")
        try:
            db.create_all()
            app.logger.info("Database tables created successfully")
        except Exception as e:
            app.logger.error(f"Error creating database tables: {str(e)}")
            raise

    return app
