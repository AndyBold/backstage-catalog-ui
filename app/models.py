#!/usr/bin/env python3

from datetime import datetime
from typing import Optional
from dataclasses import field
from slugify import slugify
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Text, String, DateTime, Index
from app.database import db


class CatalogEntity(db.Model):
    """Catalog entity model using SQLAlchemy 3.0 features"""

    __tablename__ = "catalog_entities"

    # Primary key with identity generation
    id: Mapped[int] = mapped_column(init=False, primary_key=True, autoincrement=True)

    # Required fields with constraints
    kind: Mapped[str] = mapped_column(
        String(50), nullable=False, info={"description": "Type of the catalog entity"}
    )

    name: Mapped[str] = mapped_column(
        String(100), nullable=False, info={"description": "Name of the entity"}
    )

    namespace: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        info={"description": "Namespace the entity belongs to"},
    )

    # Required fields for catalog metadata
    owner: Mapped[str] = mapped_column(
        String(100), nullable=False, info={"description": "Entity owner"}
    )

    system: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        info={"description": "System the entity belongs to"},
    )

    lifecycle: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        info={"description": "Lifecycle stage of the entity"},
    )

    # Full entity data storage
    entity_data: Mapped[str] = mapped_column(
        Text, nullable=False, info={"description": "Complete YAML representation"}
    )

    # Optional fields
    title: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        default=None,
        info={"description": "Display title of the entity"},
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        default=None,
        info={"description": "Detailed description of the entity"},
    )

    # Timestamps with server defaults
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=datetime.utcnow,
        nullable=False,
        init=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        init=False,
    )

    # Indexes for common queries
    __table_args__ = (
        Index("idx_kind_name", "kind", "name"),
        Index("idx_namespace", "namespace"),
        Index("idx_owner", "owner"),
        Index("idx_created_at", "created_at"),
    )

    @property
    def unique_name(self) -> str:
        """Generate a unique name for the entity based on kind and name"""
        return f"{self.kind.lower()}-{slugify(self.name)}"

    def to_dict(self) -> dict:
        """Convert entity to dictionary representation"""
        return {
            "id": self.id,
            "kind": self.kind,
            "name": self.name,
            "namespace": self.namespace,
            "title": self.title,
            "description": self.description,
            "owner": self.owner,
            "system": self.system,
            "lifecycle": self.lifecycle,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
