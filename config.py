#!/usr/bin/env python3

import os
from pathlib import Path


class Config:
    # Get the base directory of the application
    BASE_DIR = Path(__file__).resolve().parent

    # Create a data directory if it doesn't exist
    DATA_DIR = BASE_DIR / "data"
    DATA_DIR.mkdir(exist_ok=True)

    # Database configuration
    SQLITE_DB_PATH = DATA_DIR / "catalog.db"
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{SQLITE_DB_PATH}"

    # SQLAlchemy configuration
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # Flask configuration
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.urandom(24)
