# Persistence Helpers & Platform Print

This module provides UI state persistence and cross-platform file operations for the project details interface.

## UiState Class

A convenience wrapper around `QSettings("Cabplanner","Cabplanner")` for managing UI state persistence.

### Features

- **Splitter State**: Save/restore QSplitter positions
- **Column Widths**: Save/restore QTableView column widths  
- **View Modes**: Persist user's preferred view mode (cards/table)
- **Selected Tabs**: Future-proof tab selection persistence
- **Automatic Prefixing**: All keys stored under `project_details/*`

### Usage

```python
from models import UiState

ui_state = UiState()

# Splitter persistence
ui_state.save_splitter("main_splitter", splitter_widget)
ui_state.restore_splitter("main_splitter", splitter_widget)

# Table column persistence  
ui_state.save_column_widths("cabinet_table", table_widget)
ui_state.restore_column_widths("cabinet_table", table_widget)

# View mode persistence
ui_state.set_view_mode("table")
mode = ui_state.get_view_mode(default="cards")

# Tab selection persistence
ui_state.set_selected_tab(2)
tab = ui_state.get_selected_tab()
```

## open_or_print Function

Cross-platform file opening and printing with Windows-specific print support.

### Features

- **Cross-Platform Open**: Works on all platforms via `QDesktopServices`
- **Windows Print**: Uses `os.startfile(path, "print")` on Windows
- **Fallback Print**: Uses `QDesktopServices.openUrl()` on non-Windows
- **Error Handling**: Graceful handling of missing files

### Usage

```python
from models import open_or_print

# Open file in default application
success = open_or_print("document.pdf", "open")

# Print file (Windows: shows print dialog, others: opens file)
success = open_or_print("document.pdf", "print")
```

### Platform Behavior

| Platform | Action="open" | Action="print" |
|----------|---------------|----------------|
| Windows | `os.startfile(path)` | `os.startfile(path, "print")` |
| Others | `QDesktopServices.openUrl()` | `QDesktopServices.openUrl()` |

## Testing

Both components have been thoroughly tested:

✅ **UiState**:
- Settings organization/application verification
- Splitter save/restore with actual QSplitter widgets
- Table column save/restore with QTableView widgets  
- View mode and tab persistence
- Settings key prefixing under `project_details/*`

✅ **open_or_print**:
- Cross-platform compatibility testing
- Windows-specific print verb verification
- Error handling for missing files
- Mocked OS calls to avoid disrupting test environment
