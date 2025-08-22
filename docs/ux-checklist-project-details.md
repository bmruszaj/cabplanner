# UX Checklist: Project Details Dialog

## Overview

This document provides a comprehensive QA checklist for the Project Details dialog functionality. Use this checklist to validate the user experience without needing to examine the code implementation.

**Test Environment Requirements:**
- Windows 10/11 (for print testing)
- Sample project with at least 3-5 cabinets
- Valid printer configured (for print verification)

---

## Core Flows Testing

### 1. Open Project Details

**Test Steps:**
1. From main window, select a project
2. Click "Open Details" or double-click project row
3. Dialog should open in modal mode

**Expected Behavior:**
- ✅ Dialog opens within 2 seconds
- ✅ Project name and order number displayed in header
- ✅ Client information loaded in right sidebar
- ✅ Cabinet cards displayed in grid (default view)
- ✅ Toolbar shows correct buttons: "Dodaj z listy", "Szafka niestandardowa", search, view toggles, export, print

### 2. Search Functionality

**Test Steps:**
1. Click search field or press `Ctrl+F`
2. Type partial cabinet name or type
3. Try search with no results
4. Clear search

**Expected Behavior:**
- ✅ `Ctrl+F` focuses search field
- ✅ Search filters results in real-time
- ✅ Card grid shows filtered results
- ✅ Table view respects search filter
- ✅ No results shows contextual empty state: "Brak wyników dla '[term]'"
- ✅ Clear search shows all cabinets again

### 3. View Mode Switching

**Test Steps:**
1. Press `Ctrl+1` or click cards view button
2. Press `Ctrl+2` or click table view button
3. Switch between views multiple times
4. Perform search in each view

**Expected Behavior:**
- ✅ `Ctrl+1` switches to cards view
- ✅ `Ctrl+2` switches to table view
- ✅ View mode persists when switching
- ✅ Search works in both views
- ✅ Selection state maintained across view switches
- ✅ View mode saved and restored on dialog reopen

### 4. Add Cabinet from Catalog

**Test Steps:**
1. Click "Dodaj z listy" button
2. Select cabinet type from catalog
3. Configure options (colors, handles, quantity)
4. Confirm addition

**Expected Behavior:**
- ✅ Catalog dialog opens
- ✅ Cabinet selection interface functional
- ✅ Options configurable
- ✅ Success banner appears: "Szafka została dodana z katalogu"
- ✅ New cabinet appears in grid/table
- ✅ Auto-hide banner after 2.5 seconds

### 5. Add Custom Cabinet

**Test Steps:**
1. Click "Szafka niestandardowa" button
2. Fill in custom cabinet details
3. Set dimensions, colors, handles
4. Save custom cabinet

**Expected Behavior:**
- ✅ Custom cabinet dialog opens
- ✅ All fields editable
- ✅ Validation works for required fields
- ✅ Success banner appears: "Niestandardowa szafka została dodana"
- ✅ Custom cabinet shows with "Szafka niestandardowa" type
- ✅ Auto-hide banner after 2.5 seconds

### 6. Edit Cabinet

**Test Steps:**
1. Right-click cabinet card or table row
2. Select "Edit" or press `F2`
3. Modify cabinet properties
4. Save changes

**Expected Behavior:**
- ✅ `F2` key opens edit dialog
- ✅ Context menu shows edit option
- ✅ Edit dialog pre-populated with current values
- ✅ Changes saved successfully
- ✅ Success banner appears: "Szafka została zaktualizowana"
- ✅ Updated data reflected immediately

### 7. Duplicate Cabinet

**Test Steps:**
1. Right-click cabinet card or table row
2. Select "Duplicate"
3. Confirm duplication

**Expected Behavior:**
- ✅ Duplicate action available in context menu
- ✅ New cabinet created with same properties
- ✅ Sequence number auto-incremented
- ✅ Success banner appears: "Szafka została zduplikowana"
- ✅ Duplicate appears in list immediately

### 8. Delete Cabinet

**Test Steps:**
1. Right-click cabinet card or table row
2. Select "Delete" or press `Delete` key
3. Confirm deletion in dialog

**Expected Behavior:**
- ✅ `Delete` key triggers delete action
- ✅ Confirmation dialog appears
- ✅ "Cancel" preserves cabinet
- ✅ "Delete" removes cabinet permanently
- ✅ Success banner appears: "Szafka została usunięta"
- ✅ Cabinet removed from view immediately

### 9. Quantity Changes

**Test Steps:**
1. In cards view, use +/- buttons on cabinet card
2. In table view, edit quantity cell directly
3. Test invalid quantities (0, negative, text)

**Expected Behavior:**
- ✅ +/- buttons increment/decrement by 1
- ✅ Minimum quantity is 1 (cannot go below)
- ✅ Table cell editing accepts valid numbers
- ✅ Invalid entries revert to previous value
- ✅ Success banner appears: "Ilość została zaktualizowana na [X]"
- ✅ Changes persist across view switches

### 10. Export Functionality

**Test Steps:**
1. Click "Export" button in toolbar
2. Choose export location
3. Verify file generation

**Expected Behavior:**
- ✅ Export dialog opens
- ✅ Default filename includes project name and date
- ✅ File saves to chosen location
- ✅ Success banner appears: "Raport został wygenerowany i otwarty"
- ✅ File opens automatically (if system configured)
- ✅ Error banner if export fails

### 11. Windows Print

**Test Steps:**
1. Click "Print" button in toolbar
2. Select printer in Windows print dialog
3. Confirm print job

**Expected Behavior:**
- ✅ Windows print dialog opens
- ✅ Project details formatted for printing
- ✅ Print preview shows correct content
- ✅ Print job sent to selected printer
- ✅ Success banner appears: "Raport został wysłany do drukarki"
- ✅ Error banner if print fails

### 12. Client Information Save

**Test Steps:**
1. Edit client name in right sidebar
2. Modify address, phone, email fields
3. Tab between fields or click elsewhere
4. Verify auto-save behavior

**Expected Behavior:**
- ✅ Fields editable inline
- ✅ Auto-save on field blur/tab
- ✅ Success banner appears: "Dane klienta zostały zapisane"
- ✅ Phone validation (7+ digits, basic format)
- ✅ Email format validation
- ✅ Changes persist immediately

---

## Keyboard Shortcuts Verification

### Global Shortcuts
- ✅ `Ctrl+F` - Focus search field
- ✅ `Ctrl+1` - Switch to cards view
- ✅ `Ctrl+2` - Switch to table view
- ✅ `Esc` - Clear search or close dialog

### Table View Shortcuts
- ✅ `Delete` - Delete selected cabinet
- ✅ `F2` - Edit selected cabinet
- ✅ `Enter` - Edit selected cabinet
- ✅ `Up/Down arrows` - Navigate selection
- ✅ `Tab` - Move between table cells

### Cards View Shortcuts
- ✅ `Delete` - Delete focused cabinet
- ✅ `Enter` - Edit focused cabinet
- ✅ `Tab` - Navigate between cards
- ✅ `Space` - Select/deselect card

---

## Empty States Testing

### 1. No Cabinets in Project

**Setup:** Empty project or delete all cabinets

**Expected State:**
- ✅ Large centered message: "Brak szafek w projekcie"
- ✅ Subtitle: "Dodaj szafki używając przycisku 'Dodaj z listy' lub 'Szafka niestandardowa'"
- ✅ Action button: "Dodaj z listy"
- ✅ Button click opens catalog dialog

### 2. No Search Results

**Setup:** Search for non-existent cabinet type

**Expected State:**
- ✅ Message: "Brak wyników dla '[search term]'"
- ✅ Subtitle: "Spróbuj zmienić kryteria wyszukiwania"
- ✅ No action button (clear search to return)

### 3. Empty Table View

**Setup:** Switch to table view with no cabinets

**Expected State:**
- ✅ Message: "Brak danych do wyświetlenia"
- ✅ Subtitle: "Dodaj szafki, aby zobaczyć je w widoku tabeli"
- ✅ Action button: "Dodaj szafkę"

---

## Banner System Testing

### Success Banners (Auto-hide after 2.5s)
- ✅ Cabinet added: "Szafka została dodana z katalogu"
- ✅ Custom cabinet added: "Niestandardowa szafka została dodana"
- ✅ Cabinet edited: "Szafka została zaktualizowana"
- ✅ Cabinet duplicated: "Szafka została zduplikowana"
- ✅ Cabinet deleted: "Szafka została usunięta"
- ✅ Quantity updated: "Ilość została zaktualizowana na [X]"
- ✅ Client saved: "Dane klienta zostały zapisane"
- ✅ Export success: "Raport został wygenerowany i otwarty"
- ✅ Print success: "Raport został wysłany do drukarki"

### Warning Banners (Auto-hide after 3.5s)
- ✅ Validation warnings appear for invalid input
- ✅ Data conflicts or formatting issues

### Error Banners (Manual dismiss only)
- ✅ Database connection errors
- ✅ File system errors (export/print failures)
- ✅ Validation errors for required fields
- ✅ Network timeouts or service failures

### Banner Behavior
- ✅ Multiple different banners stack vertically
- ✅ Duplicate banners renew timer instead of creating new banner
- ✅ Close button (×) works on all banners
- ✅ Auto-hide timing correct for each type

---

## State Persistence Testing

### 1. View Mode Persistence

**Test Steps:**
1. Switch to table view
2. Close dialog
3. Reopen same project

**Expected Behavior:**
- ✅ Table view restored (not cards view)
- ✅ Setting persists across application sessions

### 2. Splitter Position

**Test Steps:**
1. Resize splitter between main content and sidebar
2. Close and reopen dialog

**Expected Behavior:**
- ✅ Splitter position restored exactly
- ✅ Proportions maintained on different screen sizes

### 3. Table Column Widths

**Test Steps:**
1. Switch to table view
2. Resize columns (sequence, type, quantity, etc.)
3. Close and reopen dialog

**Expected Behavior:**
- ✅ Column widths restored precisely
- ✅ Column order maintained if changed
- ✅ Sort state preserved

### 4. Search State

**Test Steps:**
1. Enter search term
2. Close dialog (without clearing search)
3. Reopen dialog

**Expected Behavior:**
- ✅ Search field cleared on reopen (expected)
- ✅ Full cabinet list shown
- ✅ No stale filter state

### 5. Dialog Geometry

**Test Steps:**
1. Resize dialog window
2. Move dialog to different screen position
3. Close and reopen

**Expected Behavior:**
- ✅ Window size restored
- ✅ Window position restored
- ✅ Maximized state preserved if applicable

---

## Error Resilience Testing

### 1. Missing Cabinet Type Data

**Setup:** Database with orphaned cabinets (missing cabinet_type references)

**Expected Behavior:**
- ✅ Dialog opens without crashing
- ✅ Missing type shows as "Szafka katalogowa" or "Szafka niestandardowa"
- ✅ Other cabinet data displays correctly
- ✅ Operations (edit, delete) work normally

### 2. Invalid Data Values

**Setup:** Corrupt data (null quantities, invalid colors, etc.)

**Expected Behavior:**
- ✅ Safe fallbacks applied automatically
- ✅ Quantity defaults to 1 if invalid
- ✅ Colors default to standard values if invalid
- ✅ Handle type defaults to "Standardowy" if missing

### 3. Network/Database Errors

**Setup:** Simulate database connection issues

**Expected Behavior:**
- ✅ Error banners show user-friendly Polish messages
- ✅ Application doesn't crash
- ✅ Partial data loads when possible
- ✅ Retry mechanisms work for transient errors

---

## Performance Verification

### Large Dataset Testing

**Setup:** Project with 50+ cabinets

**Expected Performance:**
- ✅ Dialog opens within 3 seconds
- ✅ Search results appear within 500ms
- ✅ View switching within 1 second
- ✅ Smooth scrolling in both views
- ✅ No UI freezing during operations

### Memory Usage

**Test Steps:**
1. Open/close dialog repeatedly
2. Switch between projects
3. Perform bulk operations

**Expected Behavior:**
- ✅ No memory leaks on dialog close
- ✅ Stable memory usage over time
- ✅ Responsive UI throughout testing

---

## Cross-Platform Considerations

### Windows-Specific Features
- ✅ Print dialog uses Windows print spooler
- ✅ File dialogs use Windows native style
- ✅ Keyboard shortcuts follow Windows conventions
- ✅ High DPI scaling support

### Accessibility
- ✅ Tab navigation works throughout dialog
- ✅ Focus indicators visible
- ✅ Screen reader compatible labels
- ✅ Keyboard-only operation possible

---

## Future Work

### High Priority Enhancements

#### 1. Cards Drag-Reorder with Persistence
**Scope:** Enable drag-and-drop reordering in cards view with automatic sequence number updates
- Visual drag preview during operation
- Automatic sequence number recalculation
- Database persistence of new order
- Undo/redo support for reordering operations

#### 2. Category Group Headers
**Scope:** Organize cabinets by category (Base/Upper/Tall) with collapsible groups
- Automatic grouping based on cabinet type category
- Collapsible group headers with counts
- "Expand All" / "Collapse All" functionality
- Group-level operations (hide/show category)

#### 3. Accessories Management
**Scope:** Complete accessories functionality with add/edit dialogs
- Accessories tab in main dialog
- Add accessories dialog with catalog browsing
- Edit accessories with quantity and specification changes
- Accessories summary and costing integration
- Accessories included in reports and exports

#### 4. Bulk Operations with Multi-Select
**Scope:** Multi-select in table view with bulk operations toolbar
- Checkbox column for multi-selection
- Bulk delete with confirmation
- Bulk quantity changes
- Bulk color/handle changes
- Bulk export of selected items

### Medium Priority Enhancements

#### 5. Advanced Search and Filtering
- Filter by cabinet category (Base/Upper/Tall)
- Filter by color combinations
- Filter by handle type
- Saved search presets
- Advanced search dialog with multiple criteria

#### 6. Cabinet Visualization
- Thumbnail images for cabinet types
- 3D preview integration
- Kitchen layout view with cabinet positioning
- Print layouts with visual cabinet representations

#### 7. Data Import/Export
- Import cabinets from CSV/Excel
- Export to various formats (CSV, Excel, PDF)
- Template-based exports
- Custom report layouts

### Low Priority Enhancements

#### 8. Collaboration Features
- Comments and notes on individual cabinets
- Change tracking and audit log
- Project sharing with read-only access
- Approval workflows for cabinet changes

#### 9. Integration Enhancements
- ERP system integration for pricing
- Supplier catalog synchronization
- Real-time inventory checking
- Automated ordering workflows

#### 10. Mobile Companion
- Mobile app for field verification
- Barcode scanning for cabinet tracking
- Photo capture and attachment
- Offline mode with sync capabilities

---

## QA Sign-off

**Reviewer:** _________________ **Date:** _________________

**Test Environment:**
- OS Version: _________________
- Application Version: _________________
- Test Data: _________________

**Test Results:**
- [ ] All core flows working
- [ ] Keyboard shortcuts functional
- [ ] Empty states display correctly
- [ ] Banner system working
- [ ] State persistence confirmed
- [ ] Error resilience validated
- [ ] Performance acceptable

**Critical Issues Found:** _________________

**Approved for Release:** [ ] Yes [ ] No

**Notes:** _________________________________________________

---

*This document should be updated as features are added or modified. Last updated: August 22, 2025*
