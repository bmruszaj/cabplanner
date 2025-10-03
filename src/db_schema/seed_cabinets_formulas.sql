-- Seed for formula_constants
-- Idempotent inserts (no duplicates on repeated runs)

BEGIN;

-- ===== GLOBAL DEFAULTS =====
INSERT INTO formula_constants (key, value, type, "group", description)
SELECT 'defaults.board_mm', 18, 'float', 'defaults', 'Default board thickness (plyta) in mm'
WHERE NOT EXISTS (SELECT 1 FROM formula_constants WHERE key = 'defaults.board_mm');

INSERT INTO formula_constants (key, value, type, "group", description)
SELECT 'defaults.edge_mm', 2, 'float', 'defaults', 'Front edge band thickness in mm'
WHERE NOT EXISTS (SELECT 1 FROM formula_constants WHERE key = 'defaults.edge_mm');

INSERT INTO formula_constants (key, value, type, "group", description)
SELECT 'defaults.edge_body_mm', 0.8, 'float', 'defaults', 'Body edge band thickness (PCV 0.8) in mm'
WHERE NOT EXISTS (SELECT 1 FROM formula_constants WHERE key = 'defaults.edge_body_mm');

INSERT INTO formula_constants (key, value, type, "group", description)
SELECT 'defaults.hdf_mm', 3, 'float', 'defaults', 'HDF back panel thickness in mm'
WHERE NOT EXISTS (SELECT 1 FROM formula_constants WHERE key = 'defaults.hdf_mm');

-- Clearances used across formulas
INSERT INTO formula_constants (key, value, type, "group", description)
SELECT 'clearance.hdf_mm', 5, 'float', 'clearance', 'General HDF fit clearance in mm'
WHERE NOT EXISTS (SELECT 1 FROM formula_constants WHERE key = 'clearance.hdf_mm');

INSERT INTO formula_constants (key, value, type, "group", description)
SELECT 'clearance.shelf_mm', 10, 'float', 'clearance', 'Shelf depth clearance in mm'
WHERE NOT EXISTS (SELECT 1 FROM formula_constants WHERE key = 'clearance.shelf_mm');

-- ===== LOWER CABINETS =====
INSERT INTO formula_constants (key, value, type, "group", description)
SELECT 'lower.front_gap_mm', 7, 'float', 'lower', 'Front height gap (H - 7) for base cabinets'
WHERE NOT EXISTS (SELECT 1 FROM formula_constants WHERE key = 'lower.front_gap_mm');

-- ===== UPPER CABINETS =====
INSERT INTO formula_constants (key, value, type, "group", description)
SELECT 'upper.front_gap_mm', 4, 'float', 'upper', 'Front height gap (H - 4) for wall cabinets'
WHERE NOT EXISTS (SELECT 1 FROM formula_constants WHERE key = 'upper.front_gap_mm');

INSERT INTO formula_constants (key, value, type, "group", description)
SELECT 'upper.groove_pos_mm', 282, 'float', 'upper', 'Groove position from the front for HDF'
WHERE NOT EXISTS (SELECT 1 FROM formula_constants WHERE key = 'upper.groove_pos_mm');

INSERT INTO formula_constants (key, value, type, "group", description)
SELECT 'upper.groove_depth_mm', 12, 'float', 'upper', 'Groove depth for HDF in side panels'
WHERE NOT EXISTS (SELECT 1 FROM formula_constants WHERE key = 'upper.groove_depth_mm');

-- ===== DRAWERS: COMFORTBOX (from your Excel calculator) =====
INSERT INTO formula_constants (key, value, type, "group", description)
SELECT 'drawers.comfortbox.bottom_width_mm', 495, 'float', 'drawers.comfortbox', 'Drawer bottom nominal width'
WHERE NOT EXISTS (SELECT 1 FROM formula_constants WHERE key = 'drawers.comfortbox.bottom_width_mm');

INSERT INTO formula_constants (key, value, type, "group", description)
SELECT 'drawers.comfortbox.runner_offset_mm', 75, 'float', 'drawers.comfortbox', 'Offset used in inside height calc (W - 36 - 75)'
WHERE NOT EXISTS (SELECT 1 FROM formula_constants WHERE key = 'drawers.comfortbox.runner_offset_mm');

INSERT INTO formula_constants (key, value, type, "group", description)
SELECT 'drawers.comfortbox.back_width_offset_mm', 89, 'float', 'drawers.comfortbox', 'Back panel width offset (W - 89 - 36)'
WHERE NOT EXISTS (SELECT 1 FROM formula_constants WHERE key = 'drawers.comfortbox.back_width_offset_mm');

INSERT INTO formula_constants (key, value, type, "group", description)
SELECT 'drawers.comfortbox.back_height_mm', 70, 'float', 'drawers.comfortbox', 'Back panel height'
WHERE NOT EXISTS (SELECT 1 FROM formula_constants WHERE key = 'drawers.comfortbox.back_height_mm');

-- Front widths for drawers (commonly W - 2*edge)
INSERT INTO formula_constants (key, value, type, "group", description)
SELECT 'drawers.front_side_edge_mm', 2, 'float', 'drawers', 'Edge mm used on drawer fronts (per side)'
WHERE NOT EXISTS (SELECT 1 FROM formula_constants WHERE key = 'drawers.front_side_edge_mm');

-- ===== MATERIAL PRESETS =====
INSERT INTO formula_constants (key, value, type, "group", description)
SELECT 'materials.plyta_mm', 18, 'float', 'materials', 'Default board thickness for body parts'
WHERE NOT EXISTS (SELECT 1 FROM formula_constants WHERE key = 'materials.plyta_mm');

INSERT INTO formula_constants (key, value, type, "group", description)
SELECT 'materials.plyta_alt_mm', 16, 'float', 'materials', 'Alternate board thickness used on some parts'
WHERE NOT EXISTS (SELECT 1 FROM formula_constants WHERE key = 'materials.plyta_alt_mm');

INSERT INTO formula_constants (key, value, type, "group", description)
SELECT 'materials.hdf_mm', 3, 'float', 'materials', 'HDF back panel thickness (duplicate of defaults.hdf_mm for grouping)'
WHERE NOT EXISTS (SELECT 1 FROM formula_constants WHERE key = 'materials.hdf_mm');

COMMIT;
