# ProjectDetailsController

The main controller for orchestrating business logic and wiring the project details interface.

## Overview

The `ProjectDetailsController` serves as the central orchestrator for all project details functionality, managing data operations, coordinating UI components, and handling user interactions while maintaining strict separation of concerns.

## Architecture

### Responsibilities

- **Data Management**: Loading and persistence via `ProjectService`
- **Signal Orchestration**: Wiring all view signals to appropriate handlers
- **Dialog Integration**: Connecting to existing `AddCabinetDialog` and `AdhocCabinetDialog`
- **UI State Persistence**: Saving/restoring view state via `UiState`
- **Error Management**: Graceful error handling with user-friendly banners

### Design Principles

- **No UI Code**: Controller only uses view's public API methods
- **Service Layer**: All persistence flows through services with proper error handling
- **Immediate Persistence**: Quantity changes, reordering, and client saves persist immediately
- **Comprehensive Error Handling**: All operations wrapped in try/except with banner feedback

## Usage

### Basic Setup

```python
from controllers import ProjectDetailsController
from view import ProjectDetailsView

# Create controller
controller = ProjectDetailsController(session, project, modal=True)

# Create and attach view
view = ProjectDetailsView(modal=True)
controller.attach(view)

# Show dialog
controller.open()
```

### Constructor Parameters

```python
ProjectDetailsController(
    session: Session,      # Database session for operations
    project: Project,      # Project to manage
    modal: bool = False    # Whether dialog should be modal
)
```

## Signal Handling

The controller automatically wires all view signals during `attach()`:

### Header Signals
- `sig_export` → Generate and open project report
- `sig_print` → Generate and print project report

### Toolbar Signals  
- `sig_add_from_catalog` → Open `AddCabinetDialog`
- `sig_add_custom` → Open `AdhocCabinetDialog`
- `sig_search_changed` → Apply search filter to cabinet proxy
- `sig_view_mode_changed` → Save view mode preference

### Cabinet Signals
- `sig_cabinet_qty_changed` → Persist quantity change immediately
- `sig_cabinet_edit` → Edit cabinet (custom cabinets only currently)
- `sig_cabinet_duplicate` → Duplicate cabinet with new sequence
- `sig_cabinet_delete` → Delete cabinet with confirmation
- `sig_cabinet_selected` → Handle cabinet selection

### Client Signals
- `sig_client_save` → Save client information immediately

## Data Operations

### Loading
- Project metadata (name, order number, status)
- Cabinet list with full details
- Client information

### Persistence
- **Immediate**: Quantity changes, client saves, cabinet operations
- **Automatic**: Reordering with sequence number updates
- **Confirmation**: Delete operations require user confirmation

### Error Handling
```python
try:
    # Operation
    result = self.project_service.update_cabinet(cabinet_id, quantity=new_qty)
    if result:
        self.view.show_success_banner("Quantity updated")
    else:
        self.view.show_error_banner("Failed to update quantity")
except Exception as e:
    logger.error(f"Error: {e}")
    self.view.show_error_banner(f"Error updating quantity: {e}")
```

## Integration Features

### Table Model Integration
- Creates `CabinetTableModel` for table view
- Sets up `make_proxy()` for filtering/sorting
- Registers `ColorChipDelegate` for color columns
- Handles model signals for data changes

### UI State Persistence
- Splitter positions
- Table column widths  
- View mode preferences (cards/table)
- Selected tab state (future-proof)

### Dialog Integration
- **Add from Catalog**: Uses existing `AddCabinetDialog`
- **Add Custom**: Uses existing `AdhocCabinetDialog`
- **Edit Custom**: Reuses `AdhocCabinetDialog` in edit mode

## Modal vs Modeless

The controller supports both modal and modeless operation:

```python
# Modal (blocks parent)
controller = ProjectDetailsController(session, project, modal=True)
controller.open()  # Calls view.exec()

# Modeless (non-blocking)
controller = ProjectDetailsController(session, project, modal=False)
controller.open()  # Calls view.show()
```

## Testing

The controller includes comprehensive error handling and has been tested with:

- ✅ Signal wiring and emission
- ✅ Error handling with mock services
- ✅ Modal/modeless behavior
- ✅ View API integration
- ✅ Service layer integration
- ✅ UI state persistence

## Dependencies

- `ProjectService`: Data persistence operations
- `ReportGenerator`: Export and print functionality
- `UiState`: UI state persistence
- `CabinetTableModel`, `make_proxy`: Table view support
- `AddCabinetDialog`, `AdhocCabinetDialog`: Existing dialog integration

## Future Enhancements

- Edit support for catalog cabinets
- Advanced cabinet filtering options
- Bulk operations (multi-select)
- Undo/redo functionality
- Real-time collaboration features
