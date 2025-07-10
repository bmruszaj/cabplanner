from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Float,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    kitchen_type = Column(String, nullable=False)  # 'LOFT', 'PARIS', 'WINO'
    order_number = Column(String, nullable=False)
    client_name = Column(String, nullable=True)
    client_address = Column(String, nullable=True)
    client_phone = Column(String, nullable=True)
    client_email = Column(String, nullable=True)
    blaty = Column(Boolean, nullable=False, default=False)
    cokoly = Column(Boolean, nullable=False, default=False)
    uwagi = Column(Boolean, nullable=False, default=False)
    flag_notes = Column(Text, nullable=True)
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
        "ProjectCabinet", back_populates="project", cascade="all, delete-orphan"
    )


class CabinetType(Base):
    __tablename__ = "cabinet_types"

    id = Column(Integer, primary_key=True)
    kitchen_type = Column(String, nullable=False)  # 'LOFT', 'PARIS', 'WINO'
    nazwa = Column(String, nullable=False)
    hdf_plecy = Column(Boolean, nullable=False, default=False)

    listwa_count = Column(Integer, nullable=False, default=0)
    listwa_w_mm = Column(Float, nullable=True)
    listwa_h_mm = Column(Float, nullable=True)

    wieniec_count = Column(Integer, nullable=False, default=0)
    wieniec_w_mm = Column(Float, nullable=True)
    wieniec_h_mm = Column(Float, nullable=True)

    bok_count = Column(Integer, nullable=False, default=0)
    bok_w_mm = Column(Float, nullable=True)
    bok_h_mm = Column(Float, nullable=True)

    front_count = Column(Integer, nullable=False, default=0)
    front_w_mm = Column(Float, nullable=True)
    front_h_mm = Column(Float, nullable=True)

    polka_count = Column(Integer, nullable=False, default=0)
    polka_w_mm = Column(Float, nullable=True)
    polka_h_mm = Column(Float, nullable=True)

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

    project_cabinets = relationship(
        "ProjectCabinet", back_populates="cabinet_type", cascade="all, delete-orphan"
    )


class Accessory(Base):
    __tablename__ = "accessories"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    sku = Column(String, nullable=False)
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
    type_id = Column(
        Integer, ForeignKey("cabinet_types.id", ondelete="RESTRICT"), nullable=True
    )  # nullable for adhoc
    sequence_number = Column(Integer, nullable=False)
    body_color = Column(String, nullable=False)
    front_color = Column(String, nullable=False)
    handle_type = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)

    adhoc_width_mm = Column(Float, nullable=True)
    adhoc_height_mm = Column(Float, nullable=True)
    adhoc_depth_mm = Column(Float, nullable=True)

    formula_offset_mm = Column(Float, nullable=True)  # overrides Settings.default

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

    project = relationship("Project", back_populates="cabinets")
    cabinet_type = relationship("CabinetType", back_populates="project_cabinets")
    accessories = relationship(
        "ProjectCabinetAccessory",
        back_populates="project_cabinet",
        cascade="all, delete-orphan",
    )


class ProjectCabinetAccessory(Base):
    __tablename__ = "project_cabinet_accessories"

    project_cabinet_id = Column(
        Integer, ForeignKey("project_cabinets.id", ondelete="CASCADE"), primary_key=True
    )
    accessory_id = Column(
        Integer, ForeignKey("accessories.id", ondelete="RESTRICT"), primary_key=True
    )
    count = Column(Integer, nullable=False)

    project_cabinet = relationship("ProjectCabinet", back_populates="accessories")
    accessory = relationship("Accessory", back_populates="cabinet_links")


class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True)
    base_formula_offset_mm = Column(Float, nullable=False, default=-2.0)
    advanced_script = Column(Text, nullable=True)
    theme_accent_rgb = Column(String, nullable=True)
    autoupdate_interval = Column(
        String, nullable=False, default="weekly"
    )  # 'on_start', 'daily', 'weekly'
    current_version = Column(String, nullable=False, default="0.1.0")
