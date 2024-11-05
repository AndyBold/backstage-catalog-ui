#!/usr/bin/env python3

import shutil
from datetime import datetime
from pathlib import Path
from config import Config


def backup_database():
    """Create a backup of the database file"""
    if not Config.SQLITE_DB_PATH.exists():
        raise FileNotFoundError(f"Database file not found at {Config.SQLITE_DB_PATH}")

    # Create backups directory if it doesn't exist
    backup_dir = Config.DATA_DIR / "backups"
    backup_dir.mkdir(exist_ok=True)

    # Create backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"catalog_{timestamp}.db"

    # Copy database file
    shutil.copy2(Config.SQLITE_DB_PATH, backup_file)

    # Remove old backups (keep last 5)
    backup_files = sorted(backup_dir.glob("catalog_*.db"))
    if len(backup_files) > 5:
        for old_backup in backup_files[:-5]:
            old_backup.unlink()

    return backup_file
