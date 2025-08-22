# Cabinet Table Model

This module provides a complete table model implementation for displaying cabinet data in table views.

## Features

### CabinetTableModel
- **Columns**: `["Lp.", "Typ", "Kolor korpusu", "Kolor frontu", "Rodzaj uchwytu", "Ilość", "Niestandardowy"]`
- **Editing**: Quantity column is editable inline
- **Drag-Reorder**: Full `moveRows()` support with automatic sequence number updates
- **Data Management**: `set_rows()` and `get_row()` methods for easy data manipulation
- **Zero Service Calls**: Pure UI model, no database dependencies

### Proxy Model Support
- **make_proxy()**: Helper function for case-insensitive, all-columns filtering
- **CabinetProxyModel**: Advanced filtering by search text, type (standard/custom), and colors
- **Sorting**: Full column sorting support with case-insensitive text handling

### Color Display
- **ColorChipDelegate**: Custom delegate for displaying colors in table cells
- **setup_color_chip_delegate()**: Helper to register delegate on color columns
- **Visual Integration**: Consistent with ColorChip widget from card view

## Usage

```python
from models.cabinet_table import CabinetTableModel, make_proxy, setup_color_chip_delegate

# Create model with cabinet data
model = CabinetTableModel(cabinet_list)

# Create filtered/sorted proxy
proxy = make_proxy(model)
proxy.set_search_filter("szafka")

# Setup table view
table_view.setModel(proxy)
setup_color_chip_delegate(table_view, model)

# Handle drag-reorder
# moveRows() automatically updates sequence numbers
```

## Signals

- `cabinet_data_changed(cabinet_id, column_name, new_value)`: Emitted when cabinet data changes
- `dataChanged`: Standard Qt signal emitted when LP sequence numbers update after reordering

## Testing

All functionality verified with dummy data:
- ✅ Required columns present and correct
- ✅ Drag-reorder with sequence number updates  
- ✅ Case-insensitive filtering across all columns
- ✅ Sorting and filtering through proxy model
- ✅ Color delegate registration helper
- ✅ Zero service calls (UI-only)
