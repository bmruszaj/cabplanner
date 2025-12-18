from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    Index,
    Float,
    JSON,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


# ---------- User-editable constants for formulas ----------


class FormulaConstant(Base):
    """
    A single named constant used by the formula engine.
    Examples:
      key="defaults.board_mm", value=18, type="float"
      key="defaults.edge_mm", value=2, type="float"
      key="lower.front_gap_mm", value=7, type="float"
      key="upper.front_gap_mm", value=4, type="float"
      key="upper.groove_mm", value=282, type="float"
      key="drawers.comfortbox.runner_offset_mm", value=75, type="float"
    """

    __tablename__ = "formula_constants"

    id = Column(Integer, primary_key=True)
    key = Column(String(120), nullable=False, unique=True)
    value = Column(Float, nullable=False)
    type = Column(
        String(16), nullable=False, default="float"
    )  # "int" | "float" | "bool" | "str"
    group = Column(String(120), nullable=True)
    description = Column(String(255), nullable=True)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ---------- Core domain ----------


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)

    # free-form to allow new kitchen types without schema changes
    kitchen_type = Column(String(60), nullable=False, default="LOFT")

    order_number = Column(String(120), nullable=False)
    client_name = Column(String(255), nullable=True)
    client_address = Column(String(255), nullable=True)
    client_phone = Column(String(120), nullable=True)
    client_email = Column(String(255), nullable=True)

    blaty = Column(Boolean, nullable=False, default=False)
    blaty_note = Column(Text, nullable=True)
    cokoly = Column(Boolean, nullable=False, default=False)
    cokoly_note = Column(Text, nullable=True)
    uwagi = Column(Boolean, nullable=False, default=False)
    uwagi_note = Column(Text, nullable=True)

    flag_notes = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    cabinets = relationship(
        "ProjectCabinet", back_populates="project", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("order_number", name="uq_project_order"),)


class CabinetTemplate(Base):
    """
    Catalog template for a cabinet model (e.g., D60, G60).
    LOWER/UPPER classification is inferred from `name` in code (no DB column).
    """

    __tablename__ = "cabinet_types"

    id = Column(Integer, primary_key=True)
    kitchen_type = Column(String(60), nullable=False, default="LOFT")
    name = Column(String(255), nullable=False)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    project_cabinets = relationship(
        "ProjectCabinet", back_populates="cabinet_type", cascade="all, delete-orphan"
    )
    parts = relationship(
        "CabinetPart", back_populates="cabinet_type", cascade="all, delete-orphan"
    )

    # Drawer stack rows defined at template level (0..N).
    drawer_rows = relationship(
        "CabinetTemplateDrawer",
        back_populates="cabinet_type",
        cascade="all, delete-orphan",
        order_by="CabinetTemplateDrawer.position",
    )

    # Default accessories for this cabinet template
    accessories = relationship(
        "CabinetTemplateAccessory",
        back_populates="cabinet_type",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        # If you want same name in different kitchen types, swap to ("name", "kitchen_type")
        UniqueConstraint("name", name="uq_cabinettype_name"),
        Index("ix_cabinet_types_kitchen_type", "kitchen_type"),
    )


class CabinetPart(Base):
    """
    A cut part belonging to a catalog cabinet template.
    Material/thickness enable reports and grouping by material without guessing from name.
    processing_json can hold structured machining info (e.g., edge=0.8, groove: {pos:282, depth:12, from:'front'}).
    """

    __tablename__ = "cabinet_parts"

    id = Column(Integer, primary_key=True)
    cabinet_type_id = Column(
        Integer, ForeignKey("cabinet_types.id", ondelete="CASCADE"), nullable=False
    )

    part_name = Column(
        String(255), nullable=False
    )  # e.g., 'wieniec dolny', 'boki', 'HDF'
    height_mm = Column(Integer, nullable=False, default=0)
    width_mm = Column(Integer, nullable=False, default=0)
    pieces = Column(Integer, nullable=False, default=1)

    wrapping = Column(String(32), nullable=True)  # e.g., 'D', 'K', 'DDKK'
    comments = Column(Text, nullable=True)

    # new: explicit material info instead of is_hdf
    material = Column(
        String(32), nullable=True
    )  # e.g., 'PLYTA 12', 'PLYTA 16', 'PLYTA 18', 'HDF', 'FRONT', 'INNE'

    # optional: structured machining/processing data
    processing_json = Column(JSON, nullable=True)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    cabinet_type = relationship("CabinetTemplate", back_populates="parts")

    __table_args__ = (
        CheckConstraint("height_mm >= 0 AND width_mm >= 0", name="ck_part_dims_nonneg"),
        CheckConstraint("pieces >= 0", name="ck_part_pieces_nonneg"),
        Index("ix_cabinet_parts_type", "cabinet_type_id"),
    )


class Accessory(Base):
    """
    SKU-based hardware/supplies (handles, runners, gallery rails, etc.)
    Can be linked to a project cabinet or to a drawer template as defaults.
    """

    __tablename__ = "accessories"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    sku = Column(String(120), nullable=False)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    cabinet_links = relationship(
        "ProjectCabinetAccessory",
        back_populates="accessory",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("sku", name="uq_accessory_sku"),
        Index("ix_accessories_sku", "sku"),
    )


class CabinetTemplateAccessory(Base):
    """
    Default accessory lines attached to a CabinetTemplate.
    Helps auto-populate hardware when a cabinet is created in a project.
    """

    __tablename__ = "cabinet_template_accessories"

    cabinet_type_id = Column(
        Integer, ForeignKey("cabinet_types.id", ondelete="CASCADE"), primary_key=True
    )
    accessory_id = Column(
        Integer, ForeignKey("accessories.id", ondelete="RESTRICT"), primary_key=True
    )
    count = Column(Integer, nullable=False, default=1)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    cabinet_type = relationship("CabinetTemplate", back_populates="accessories")
    accessory = relationship("Accessory")


class ProjectCabinetPart(Base):
    """
    Snapshot of cabinet parts for a specific project cabinet instance.
    Works for both standard (from catalog) and custom cabinets.
    This is the materialized/frozen version of parts at the time of cabinet creation.
    """

    __tablename__ = "project_cabinet_parts"

    id = Column(Integer, primary_key=True)
    project_cabinet_id = Column(
        Integer, ForeignKey("project_cabinets.id", ondelete="CASCADE"), nullable=False
    )

    part_name = Column(
        String(255), nullable=False
    )  # e.g., 'wieniec dolny', 'boki', 'HDF'
    height_mm = Column(Integer, nullable=False, default=0)
    width_mm = Column(Integer, nullable=False, default=0)
    pieces = Column(Integer, nullable=False, default=1)

    wrapping = Column(String(32), nullable=True)  # e.g., 'D', 'K', 'DDKK'
    comments = Column(Text, nullable=True)

    # Material info
    material = Column(
        String(32), nullable=True
    )  # e.g., 'PLYTA 12', 'PLYTA 16', 'PLYTA 18', 'HDF', 'FRONT', 'INNE'

    # Optional: structured machining/processing data
    processing_json = Column(JSON, nullable=True)

    # Traceability: where this part came from
    source_template_id = Column(
        Integer, ForeignKey("cabinet_types.id", ondelete="SET NULL"), nullable=True
    )  # NULL for custom cabinets
    source_part_id = Column(
        Integer, ForeignKey("cabinet_parts.id", ondelete="SET NULL"), nullable=True
    )  # NULL for custom cabinets

    # Snapshot of calculation context for custom cabinets
    calc_context_json = Column(JSON, nullable=True)  # W/H/D, constants, variants, etc.

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    project_cabinet = relationship("ProjectCabinet", back_populates="parts")
    source_template = relationship("CabinetTemplate", foreign_keys=[source_template_id])
    source_part = relationship("CabinetPart", foreign_keys=[source_part_id])

    __table_args__ = (
        CheckConstraint(
            "height_mm >= 0 AND width_mm >= 0", name="ck_project_part_dims_nonneg"
        ),
        CheckConstraint("pieces >= 0", name="ck_project_part_pieces_nonneg"),
        Index("ix_project_cabinet_parts_cabinet", "project_cabinet_id"),
        Index("ix_project_cabinet_parts_source_template", "source_template_id"),
        Index("ix_project_cabinet_parts_source_part", "source_part_id"),
    )


class ProjectCabinetAccessorySnapshot(Base):
    """
    Snapshot of accessories for a specific project cabinet instance.
    Similar concept to ProjectCabinetPart but for accessories.
    """

    __tablename__ = "project_cabinet_accessory_snapshots"

    id = Column(Integer, primary_key=True)
    project_cabinet_id = Column(
        Integer, ForeignKey("project_cabinets.id", ondelete="CASCADE"), nullable=False
    )

    name = Column(String(255), nullable=False)
    sku = Column(String(120), nullable=False)
    count = Column(Integer, nullable=False, default=1)

    # Traceability: where this accessory came from
    source_accessory_id = Column(
        Integer, ForeignKey("accessories.id", ondelete="SET NULL"), nullable=True
    )  # NULL if accessory was deleted from catalog

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    project_cabinet = relationship(
        "ProjectCabinet", back_populates="accessory_snapshots"
    )
    source_accessory = relationship("Accessory", foreign_keys=[source_accessory_id])

    __table_args__ = (
        CheckConstraint("count >= 1", name="ck_project_accessory_count_pos"),
        Index("ix_project_cabinet_accessory_snapshots_cabinet", "project_cabinet_id"),
        Index("ix_project_cabinet_accessory_snapshots_source", "source_accessory_id"),
    )


class ProjectCabinet(Base):
    """
    A cabinet instance placed in a specific project.
    Points to a catalog template (type_id). Ad-hoc dimensions and offsets are handled in code, not persisted here.
    """

    __tablename__ = "project_cabinets"

    id = Column(Integer, primary_key=True)
    project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    type_id = Column(
        Integer, ForeignKey("cabinet_types.id", ondelete="RESTRICT"), nullable=True
    )

    sequence_number = Column(Integer, nullable=False)
    body_color = Column(String(120), nullable=False)
    front_color = Column(String(120), nullable=False)
    handle_type = Column(String(120), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    project = relationship("Project", back_populates="cabinets")
    cabinet_type = relationship("CabinetTemplate", back_populates="project_cabinets")

    # Drawer rows applied to this cabinet (overrides template if present).
    drawer_rows = relationship(
        "ProjectCabinetDrawer",
        back_populates="project_cabinet",
        cascade="all, delete-orphan",
        order_by="ProjectCabinetDrawer.position",
    )

    # Snapshot of parts for this cabinet instance (works for both standard and custom)
    parts = relationship(
        "ProjectCabinetPart",
        back_populates="project_cabinet",
        cascade="all, delete-orphan",
    )

    # Snapshot of accessories for this cabinet instance
    accessory_snapshots = relationship(
        "ProjectCabinetAccessorySnapshot",
        back_populates="project_cabinet",
        cascade="all, delete-orphan",
    )

    # Legacy relationship for backwards compatibility (will be removed)
    accessories = relationship(
        "ProjectCabinetAccessory",
        back_populates="project_cabinet",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("project_id", "sequence_number", name="uq_project_sequence"),
        CheckConstraint("quantity >= 1", name="ck_quantity_pos"),
        Index("ix_project_cabinets_project", "project_id"),
        Index("ix_project_cabinets_type", "type_id"),
    )


class ProjectCabinetAccessory(Base):
    """
    Hardware line attached to a project cabinet (SKU + count).
    """

    __tablename__ = "project_cabinet_accessories"

    project_cabinet_id = Column(
        Integer, ForeignKey("project_cabinets.id", ondelete="CASCADE"), primary_key=True
    )
    accessory_id = Column(
        Integer, ForeignKey("accessories.id", ondelete="RESTRICT"), primary_key=True
    )
    count = Column(Integer, nullable=False, default=1)

    project_cabinet = relationship("ProjectCabinet", back_populates="accessories")
    accessory = relationship("Accessory")


class Setting(Base):
    """
    Application settings stored in the DB.
    Keep values as strings + value_type or switch to JSON for structured values.
    """

    __tablename__ = "settings"

    id = Column(Integer, primary_key=True)
    key = Column(String(120), unique=True, nullable=False)
    value = Column(String, nullable=True)
    value_type = Column(
        String(16), nullable=False, default="str"
    )  # str, int, float, bool
    description = Column(String(255), nullable=True)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ---------- Drawers layer (Strings + CheckConstraints) ----------

_FACE_MODES = ("AUTO", "FIXED", "RATIO")
_DRAWER_SYSTEMS = ("WOOD_BOX", "COMFORTBOX")
_HEIGHT_PROFILES = ("LOW", "MED", "HIGH")


class DrawerTemplate(Base):
    """
    Reusable drawer type (system, runner length, optional height profile).
    Can include default accessories. params_json may hold default formula constants.
    """

    __tablename__ = "drawer_templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    system = Column(String(32), nullable=False)  # constrained by check below
    runner_length_mm = Column(Integer, nullable=False)
    height_profile = Column(String(16), nullable=True)  # constrained by check below
    params_json = Column(JSON, nullable=True)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    accessories = relationship(
        "DrawerTemplateAccessory",
        back_populates="drawer_template",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("name", name="uq_drawer_template_name"),
        CheckConstraint(
            f"system IN {_DRAWER_SYSTEMS}", name="ck_drawer_template_system"
        ),
        CheckConstraint(
            f"(height_profile IS NULL) OR (height_profile IN {_HEIGHT_PROFILES})",
            name="ck_drawer_template_height_profile",
        ),
        Index("ix_drawer_template_sys_len", "system", "runner_length_mm"),
    )


class DrawerTemplateAccessory(Base):
    """
    Default accessory lines attached to a DrawerTemplate.
    Helps auto-populate hardware when a drawer is selected.
    """

    __tablename__ = "drawer_template_accessories"

    drawer_template_id = Column(
        Integer, ForeignKey("drawer_templates.id", ondelete="CASCADE"), primary_key=True
    )
    accessory_id = Column(
        Integer, ForeignKey("accessories.id", ondelete="RESTRICT"), primary_key=True
    )
    count = Column(Integer, nullable=False, default=1)

    drawer_template = relationship("DrawerTemplate", back_populates="accessories")
    accessory = relationship("Accessory")


class CabinetTemplateDrawer(Base):
    """
    Drawer row in a cabinet template (stack position, count, sizing mode).
    If drawer_template_id is NULL, the row is 'ad-hoc' and params_json must
    provide enough info for formula generation.
    """

    __tablename__ = "cabinet_template_drawers"

    id = Column(Integer, primary_key=True)

    cabinet_type_id = Column(
        Integer, ForeignKey("cabinet_types.id", ondelete="CASCADE"), nullable=False
    )
    position = Column(Integer, nullable=False)  # 1..N (top to bottom or vice versa)
    count = Column(Integer, nullable=False, default=1)

    drawer_template_id = Column(
        Integer, ForeignKey("drawer_templates.id", ondelete="SET NULL"), nullable=True
    )

    face_mode = Column(
        String(16), nullable=False, default="AUTO"
    )  # constrained by check below
    face_height_mm = Column(Integer, nullable=True)  # used when FIXED
    face_ratio = Column(Integer, nullable=True)  # used when RATIO

    params_json = Column(JSON, nullable=True)  # per-row overrides

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    cabinet_type = relationship("CabinetTemplate", back_populates="drawer_rows")
    drawer_template = relationship("DrawerTemplate")

    __table_args__ = (
        UniqueConstraint(
            "cabinet_type_id", "position", name="uq_template_drawer_stack"
        ),
        CheckConstraint("count >= 1", name="ck_template_drawer_count"),
        CheckConstraint(f"face_mode IN {_FACE_MODES}", name="ck_ct_drawers_face_mode"),
        Index("ix_ct_drawers_cabinet", "cabinet_type_id"),
    )


class ProjectCabinetDrawer(Base):
    """
    Drawer row instance attached to a project cabinet.
    If present, these override the template drawer rows for that cabinet.
    """

    __tablename__ = "project_cabinet_drawers"

    id = Column(Integer, primary_key=True)

    project_cabinet_id = Column(
        Integer, ForeignKey("project_cabinets.id", ondelete="CASCADE"), nullable=False
    )
    position = Column(Integer, nullable=False)  # 1..N
    count = Column(Integer, nullable=False, default=1)

    drawer_template_id = Column(
        Integer, ForeignKey("drawer_templates.id", ondelete="SET NULL"), nullable=True
    )

    face_mode = Column(
        String(16), nullable=False, default="AUTO"
    )  # constrained by check below
    face_height_mm = Column(Integer, nullable=True)
    face_ratio = Column(Integer, nullable=True)

    params_json = Column(JSON, nullable=True)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    project_cabinet = relationship("ProjectCabinet", back_populates="drawer_rows")
    drawer_template = relationship("DrawerTemplate")

    accessories = relationship(
        "ProjectCabinetDrawerAccessory",
        back_populates="project_cabinet_drawer",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "project_cabinet_id", "position", name="uq_pcabinet_drawer_stack"
        ),
        CheckConstraint("count >= 1", name="ck_pcabinet_drawer_count"),
        CheckConstraint(
            f"face_mode IN {_FACE_MODES}", name="ck_pcabinet_drawers_face_mode"
        ),
        Index("ix_pcabinet_drawers_pcabinet", "project_cabinet_id"),
    )


class ProjectCabinetDrawerAccessory(Base):
    """
    Optional: hardware tracked per drawer row (instead of per cabinet).
    Useful if each drawer row has separate SKUs or counts.
    """

    __tablename__ = "project_cabinet_drawer_accessories"

    project_cabinet_drawer_id = Column(
        Integer,
        ForeignKey("project_cabinet_drawers.id", ondelete="CASCADE"),
        primary_key=True,
    )
    accessory_id = Column(
        Integer, ForeignKey("accessories.id", ondelete="RESTRICT"), primary_key=True
    )
    count = Column(Integer, nullable=False, default=1)

    project_cabinet_drawer = relationship(
        "ProjectCabinetDrawer", back_populates="accessories"
    )
    accessory = relationship("Accessory")


# Temporary compatibility alias during refactor
CabinetType = CabinetTemplate
