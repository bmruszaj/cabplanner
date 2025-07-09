from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Boolean,
    JSON,
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    cabinets = relationship(
        "ProjectCabinet",
        back_populates="project",
        cascade="all, delete-orphan",
    )


class CabinetType(Base):
    __tablename__ = "cabinet_types"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    kitchen_type = Column(String(50), nullable=False)
    base_formula_offset_mm = Column(Integer, default=0)

    project_cabinets = relationship(
        "ProjectCabinet",
        back_populates="cabinet_type",
        cascade="all, delete-orphan",
    )


class Accessory(Base):
    __tablename__ = "accessories"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    unit_price = Column(Integer, nullable=True)

    cabinet_links = relationship(
        "ProjectCabinetAccessory",
        back_populates="accessory",
        cascade="all, delete-orphan",
    )


class ProjectCabinet(Base):
    __tablename__ = "project_cabinets"

    id = Column(Integer, primary_key=True)
    project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    cabinet_type_id = Column(
        Integer,
        ForeignKey("cabinet_types.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quantity = Column(Integer, default=1, nullable=False)
    override_offset_mm = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)

    project = relationship("Project", back_populates="cabinets")
    cabinet_type = relationship("CabinetType", back_populates="project_cabinets")
    accessories = relationship(
        "ProjectCabinetAccessory",
        back_populates="project_cabinet",
        cascade="all, delete-orphan",
    )


class ProjectCabinetAccessory(Base):
    __tablename__ = "project_cabinet_accessories"

    id = Column(Integer, primary_key=True)
    project_cabinet_id = Column(
        Integer,
        ForeignKey("project_cabinets.id", ondelete="CASCADE"),
        nullable=False,
    )
    accessory_id = Column(
        Integer, ForeignKey("accessories.id", ondelete="RESTRICT"), nullable=False
    )
    quantity = Column(Integer, default=1, nullable=False)

    project_cabinet = relationship("ProjectCabinet", back_populates="accessories")
    accessory = relationship("Accessory", back_populates="cabinet_links")


class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True)
    values = Column(JSON, nullable=False, default={})
    current_version = Column(String(20), nullable=False, default="0.1.0")
    autoupdate_enabled = Column(Boolean, default=False, nullable=False)
    autoupdate_interval_days = Column(Integer, default=7, nullable=False)
    formula_script = Column(Text, nullable=True)
    logo_path = Column(String(200), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
