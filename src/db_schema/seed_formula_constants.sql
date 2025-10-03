-- Seed default formula constants for cabinet calculations
-- These constants are used by the formula engine to calculate cabinet part dimensions

INSERT OR IGNORE INTO formula_constants (key, value, type, group, description) VALUES
-- Basic thickness values
('plyta_thickness', 18, 'float', 'thickness', 'Standard plywood thickness in mm'),
('hdf_thickness', 3, 'float', 'thickness', 'HDF back thickness in mm'),

-- Default cabinet dimensions by category
('base_height', 720, 'float', 'dimensions', 'Default height for base cabinets (D*)'),
('base_depth', 560, 'float', 'dimensions', 'Default depth for base cabinets (D*)'),
('upper_height', 720, 'float', 'dimensions', 'Default height for upper cabinets (G*)'),
('upper_depth', 300, 'float', 'dimensions', 'Default depth for upper cabinets (G*)'),
('tall_height', 2020, 'float', 'dimensions', 'Default height for tall cabinets (N*, DNZ*)'),
('tall_depth', 560, 'float', 'dimensions', 'Default depth for tall cabinets (N*, DNZ*)'),

-- Front gap settings
('front_gap_top', 2, 'float', 'gaps', 'Gap between front and top edge'),
('front_gap_bottom', 2, 'float', 'gaps', 'Gap between front and bottom edge'),
('front_gap_side', 2, 'float', 'gaps', 'Gap between front and side edges'),

-- Back clearance settings
('back_play_h', 0, 'float', 'clearance', 'Height clearance for back panel'),
('back_play_w', 0, 'float', 'clearance', 'Width clearance for back panel'),
('board_back_play_h', 2, 'float', 'clearance', 'Height clearance for board back panels'),
('board_back_play_w', 2, 'float', 'clearance', 'Width clearance for board back panels'),

-- Shelf and rail settings
('shelf_back_clear', 10, 'float', 'clearance', 'Clearance between shelf and back panel'),
('rail_height', 100, 'float', 'dimensions', 'Standard rail height'),

-- Drawer settings
('drawer_inter_gap', 2, 'float', 'gaps', 'Gap between drawer fronts'),
('s1_drawer_h', 572, 'float', 'drawers', 'Height for single drawer front (S1)'),
('s2_top_h', 141, 'float', 'drawers', 'Height for top drawer in 2-drawer stack (S2)'),
('s2_bottom_h', 572, 'float', 'drawers', 'Height for bottom drawer in 2-drawer stack (S2)'),
('s3_top_h', 140, 'float', 'drawers', 'Height for top drawer in 3-drawer stack (S3)'),
('s3_middle_h', 283, 'float', 'drawers', 'Height for middle drawer in 3-drawer stack (S3)'),
('s3_bottom_h', 572, 'float', 'drawers', 'Height for bottom drawer in 3-drawer stack (S3)'),

-- Validation settings
('min_cut_mm', 10, 'float', 'validation', 'Minimum cut size in mm for validation');
