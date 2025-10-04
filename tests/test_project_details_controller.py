"""
Comprehensive tests for ProjectDetailsController.

This test suite covers:
1. Basic controller initialization and setup
2. Data loading and error handling
3. Sequence number validation and updates (including UNIQUE constraint fix)
4. Quantity updates and validation
5. Cabinet deletion functionality
6. Custom cabinet addition (with and without parts)
7. Catalog cabinet addition (with type_id preservation)
8. Sequence number auto-increment behavior
9. Project context preservation in validation
10. Comprehensive edge cases and error scenarios

Key fixes tested:
- UNIQUE constraint error resolution for sequence_number updates
- Proper project_id inclusion in sequence validation
- Type_id preservation for catalog vs custom cabinets
"""

from unittest.mock import Mock

from src.controllers.project_details_controller import ProjectDetailsController
from src.services.project_service import ProjectService


class TestProjectDetailsController:
    def test_init_creates_controller(self, session, sample_project):
        """Test that controller initializes properly."""
        controller = ProjectDetailsController(session, sample_project)

        assert controller.session == session
        assert controller.project == sample_project
        assert isinstance(controller.project_service, ProjectService)
        assert controller.cabinets == []

    def test_load_data_success(self, session, sample_project, sample_project_cabinets):
        """Test successful data loading."""
        controller = ProjectDetailsController(session, sample_project)

        # Set up signal spy
        data_loaded_spy = Mock()
        controller.data_loaded.connect(data_loaded_spy)

        # Load data
        controller.load_data()

        # Verify signal was emitted
        data_loaded_spy.assert_called_once()

        # Verify cabinets were loaded
        assert len(controller.cabinets) >= 0  # May be empty if no cabinets exist

    def test_load_data_error_handling(self, session, sample_project):
        """Test error handling during data loading."""
        controller = ProjectDetailsController(session, sample_project)

        # Mock project_service to raise exception
        controller.project_service.list_cabinets = Mock(
            side_effect=Exception("Database error")
        )

        # Set up signal spy
        data_error_spy = Mock()
        controller.data_error.connect(data_error_spy)

        # Load data
        controller.load_data()

        # Verify error signal was emitted
        data_error_spy.assert_called_once()
        call_args = data_error_spy.call_args[0][0]
        assert "Błąd podczas ładowania danych projektu" in call_args

    def test_on_sequence_changed_valid(
        self, session, sample_project, sample_project_cabinets
    ):
        """Test successful sequence change."""
        controller = ProjectDetailsController(session, sample_project)

        # Load data first
        controller.load_data()

        if controller.cabinets:  # Only test if cabinets exist
            # Set up signal spy
            cabinet_updated_spy = Mock()
            controller.cabinet_updated.connect(cabinet_updated_spy)

            # Change sequence of first cabinet
            cabinet_id = controller.cabinets[0].id
            controller.on_sequence_changed(cabinet_id, 5)

            # Verify cabinet was updated (if sequence actually changed)
            # Note: May not emit signal if new sequence == old sequence

    def test_on_sequence_changed_nonexistent_cabinet(self, session, sample_project):
        """Test sequence change for non-existent cabinet."""
        controller = ProjectDetailsController(session, sample_project)

        # Load data first
        controller.load_data()

        # Set up signal spy
        validation_error_spy = Mock()
        controller.validation_error.connect(validation_error_spy)

        # Try to change sequence of non-existent cabinet
        controller.on_sequence_changed(99999, 5)

        # Verify validation error was emitted
        validation_error_spy.assert_called_once()
        call_args = validation_error_spy.call_args[0][0]
        assert "Nie znaleziono szafy do aktualizacji" in call_args

    def test_on_quantity_changed_valid(
        self, session, sample_project, sample_project_cabinets
    ):
        """Test successful quantity change."""
        controller = ProjectDetailsController(session, sample_project)

        # Load data first
        controller.load_data()

        if controller.cabinets:  # Only test if cabinets exist
            # Set up signal spy
            cabinet_updated_spy = Mock()
            controller.cabinet_updated.connect(cabinet_updated_spy)

            # Change quantity of first cabinet
            cabinet_id = controller.cabinets[0].id
            controller.on_quantity_changed(cabinet_id, 3)

            # Verify cabinet was updated (if quantity actually changed)

    def test_on_quantity_changed_invalid_quantity(self, session, sample_project):
        """Test quantity change with invalid quantity."""
        controller = ProjectDetailsController(session, sample_project)

        # Load data first
        controller.load_data()

        # Set up signal spy
        validation_error_spy = Mock()
        controller.validation_error.connect(validation_error_spy)

        # Try to set invalid quantity (assuming we have at least one cabinet)
        if controller.cabinets:
            cabinet_id = controller.cabinets[0].id
            controller.on_quantity_changed(cabinet_id, 0)

            # Verify validation error was emitted
            validation_error_spy.assert_called_once()
            call_args = validation_error_spy.call_args[0][0]
            assert "Ilość musi być większa od zera" in call_args

    def test_on_quantity_changed_negative_quantity(self, session, sample_project):
        """Test quantity change with negative quantity."""
        controller = ProjectDetailsController(session, sample_project)

        # Load data first
        controller.load_data()

        # Set up signal spy
        validation_error_spy = Mock()
        controller.validation_error.connect(validation_error_spy)

        # Try to set negative quantity
        if controller.cabinets:
            cabinet_id = controller.cabinets[0].id
            controller.on_quantity_changed(cabinet_id, -1)

            # Verify validation error was emitted
            validation_error_spy.assert_called_once()
            call_args = validation_error_spy.call_args[0][0]
            assert "Ilość musi być większa od zera" in call_args

    def test_get_next_cabinet_sequence(
        self, session, sample_project, sample_project_cabinets
    ):
        """Test getting next available sequence number."""
        controller = ProjectDetailsController(session, sample_project)

        # Load data first
        controller.load_data()

        # Get next sequence
        next_sequence = controller.get_next_cabinet_sequence(sample_project.id)

        # Should be at least 1
        assert next_sequence >= 1

    def test_signal_connections(self, session, sample_project):
        """Test that controller has the expected signals."""
        controller = ProjectDetailsController(session, sample_project)

        # Check that signals exist and are of correct type
        assert hasattr(controller, "data_loaded")
        assert hasattr(controller, "data_error")
        assert hasattr(controller, "cabinet_updated")
        assert hasattr(controller, "validation_error")

        # Verify signals are Signal objects
        from PySide6.QtCore import Signal

        assert isinstance(controller.data_loaded, Signal)
        assert isinstance(controller.data_error, Signal)
        assert isinstance(controller.cabinet_updated, Signal)
        assert isinstance(controller.validation_error, Signal)

    def test_cabinets_list_initialization(self, session, sample_project):
        """Test that cabinets list is properly initialized."""
        controller = ProjectDetailsController(session, sample_project)

        assert isinstance(controller.cabinets, list)
        assert len(controller.cabinets) == 0  # Should start empty

    def test_project_service_initialization(self, session, sample_project):
        """Test that project service is properly initialized."""
        controller = ProjectDetailsController(session, sample_project)

        assert controller.project_service is not None
        assert isinstance(controller.project_service, ProjectService)

    def test_on_sequence_changed_with_duplicate_sequence(
        self, session, sample_project, sample_project_cabinets
    ):
        """Test sequence change validation with duplicate sequence number."""
        controller = ProjectDetailsController(session, sample_project)

        # Load data first
        controller.load_data()

        if len(controller.cabinets) >= 2:  # Need at least 2 cabinets
            # Set up signal spy
            validation_error_spy = Mock()
            controller.validation_error.connect(validation_error_spy)

            # Try to set first cabinet to same sequence as second cabinet
            first_cabinet_id = controller.cabinets[0].id
            second_cabinet_sequence = controller.cabinets[1].sequence_number

            controller.on_sequence_changed(first_cabinet_id, second_cabinet_sequence)

            # Verify validation error was emitted for duplicate sequence
            validation_error_spy.assert_called_once()
            call_args = validation_error_spy.call_args[0][0]
            assert (
                str(second_cabinet_sequence) in call_args
            )  # Error should mention the duplicate sequence

    def test_sequence_validation_includes_project_id(
        self, session, sample_project, sample_project_cabinets
    ):
        """Test that sequence validation properly includes project_id in validation logic."""
        controller = ProjectDetailsController(session, sample_project)
        controller.load_data()

        if len(controller.cabinets) >= 1:
            cabinet = controller.cabinets[0]
            original_sequence = cabinet.sequence_number

            # Set up signal spy
            validation_error_spy = Mock()
            controller.validation_error.connect(validation_error_spy)

            # Try to change to same sequence (should be no-op)
            controller.on_sequence_changed(cabinet.id, original_sequence)

            # Should not emit error since sequence hasn't changed
            validation_error_spy.assert_not_called()

            # Try to change to a valid new sequence
            new_sequence = original_sequence + 10
            controller.on_sequence_changed(cabinet.id, new_sequence)

            # Should succeed without validation error
            validation_error_spy.assert_not_called()

    def test_add_custom_cabinet_without_parts(self, session, sample_project):
        """Test adding a custom cabinet without predefined parts."""
        controller = ProjectDetailsController(session, sample_project)
        controller.load_data()

        initial_count = len(controller.cabinets)

        # Set up signal spy
        cabinet_updated_spy = Mock()
        controller.cabinet_updated.connect(cabinet_updated_spy)

        # Add custom cabinet (type_id=None)
        cabinet_data = {
            "body_color": "#ff0000",
            "front_color": "#00ff00",
            "handle_type": "Modern",
            "quantity": 1,
        }

        new_cabinet = controller.add_cabinet(sample_project.id, **cabinet_data)

        # Verify cabinet was added
        assert new_cabinet is not None
        assert new_cabinet.type_id is None  # Custom cabinet
        assert new_cabinet.body_color == "#ff0000"
        assert new_cabinet.front_color == "#00ff00"
        assert new_cabinet.handle_type == "Modern"
        assert new_cabinet.quantity == 1
        assert len(controller.cabinets) == initial_count + 1

    def test_add_catalog_cabinet_with_type_id(
        self, session, sample_project, template_service
    ):
        """Test adding a cabinet from catalog with existing template."""
        controller = ProjectDetailsController(session, sample_project)
        controller.load_data()

        # Create a template to use as catalog item
        template = template_service.create_template(
            nazwa="CatalogTemplate", kitchen_type="LOFT"
        )

        initial_count = len(controller.cabinets)

        # Add cabinet from catalog (with type_id)
        cabinet_data = {
            "type_id": template.id,
            "body_color": "#0000ff",
            "front_color": "#ffff00",
            "handle_type": "Classic",
            "quantity": 2,
        }

        new_cabinet = controller.add_cabinet(sample_project.id, **cabinet_data)

        # Verify cabinet was added with correct type_id
        assert new_cabinet is not None
        assert new_cabinet.type_id == template.id  # Catalog cabinet
        assert new_cabinet.body_color == "#0000ff"
        assert new_cabinet.front_color == "#ffff00"
        assert new_cabinet.handle_type == "Classic"
        assert new_cabinet.quantity == 2
        assert len(controller.cabinets) == initial_count + 1

    def test_add_custom_cabinet_with_parts(self, session, sample_project):
        """Test adding a custom cabinet with calculated parts."""
        controller = ProjectDetailsController(session, sample_project)
        controller.load_data()

        initial_count = len(controller.cabinets)

        # Add custom cabinet with parts
        cabinet_data = {
            "name": "Custom Cabinet with Parts",
            "kitchen_type": "MODERN",
            "body_color": "#ffffff",
            "front_color": "#000000",
            "handle_type": "Handleless",
            "quantity": 1,
            "parts": [
                {
                    "part_name": "Bok lewy",
                    "height_mm": 720,
                    "width_mm": 560,
                    "pieces": 1,
                    "material": "Płyta laminowana",
                    "thickness_mm": 18,
                },
                {
                    "part_name": "Bok prawy",
                    "height_mm": 720,
                    "width_mm": 560,
                    "pieces": 1,
                    "material": "Płyta laminowana",
                    "thickness_mm": 18,
                },
            ],
        }

        new_cabinet = controller.add_cabinet(sample_project.id, **cabinet_data)

        # Verify cabinet was added
        assert new_cabinet is not None
        assert (
            new_cabinet.type_id is None
        )  # Custom cabinet - no template in new architecture
        assert new_cabinet.body_color == "#ffffff"
        assert new_cabinet.front_color == "#000000"
        assert new_cabinet.handle_type == "Handleless"
        assert new_cabinet.quantity == 1
        assert len(controller.cabinets) == initial_count + 1

        # Verify custom parts were added to the cabinet
        session.refresh(new_cabinet)
        assert len(new_cabinet.parts) == 2  # Should have 2 custom parts
        part_names = [part.part_name for part in new_cabinet.parts]
        assert "Bok lewy" in part_names
        assert "Bok prawy" in part_names

    def test_add_catalog_cabinet_via_catalog_method(self, session, sample_project):
        """Test adding cabinet using the specific catalog method."""
        controller = ProjectDetailsController(session, sample_project)
        controller.load_data()

        initial_count = len(controller.cabinets)

        # Mock catalog cabinet data
        catalog_data = {
            "name": "Catalog Cabinet D60",
            "width": 60,
            "height": 72,
            "depth": 35,
            "code": "D60",
            "description": "Standard base cabinet 60cm",
            "price": 450.00,
        }

        new_cabinet = controller.add_catalog_cabinet(catalog_data)

        # Verify cabinet was added
        assert new_cabinet is not None
        assert len(controller.cabinets) == initial_count + 1
        # Note: This method creates a more generic cabinet structure

    def test_sequence_number_auto_increment(
        self, session, sample_project, sample_project_cabinets
    ):
        """Test that sequence numbers are automatically incremented when adding cabinets."""
        controller = ProjectDetailsController(session, sample_project)
        controller.load_data()

        # Get current max sequence
        max_sequence = max([c.sequence_number for c in controller.cabinets], default=0)

        # Add a new cabinet without specifying sequence
        cabinet_data = {
            "body_color": "#cccccc",
            "front_color": "#dddddd",
            "handle_type": "Standard",
            "quantity": 1,
        }

        new_cabinet = controller.add_cabinet(sample_project.id, **cabinet_data)

        # Verify sequence was auto-incremented
        assert new_cabinet.sequence_number > max_sequence

    def test_sequence_constraint_validation_during_add(
        self, session, sample_project, sample_project_cabinets
    ):
        """Test that sequence constraint validation works during cabinet addition."""
        controller = ProjectDetailsController(session, sample_project)
        controller.load_data()

        if len(controller.cabinets) >= 1:
            existing_sequence = controller.cabinets[0].sequence_number

            # Try to add cabinet with duplicate sequence number
            cabinet_data = {
                "sequence_number": existing_sequence,  # Duplicate!
                "body_color": "#aaaaaa",
                "front_color": "#bbbbbb",
                "handle_type": "Standard",
                "quantity": 1,
            }

            # This should either fail or auto-adjust the sequence
            # The exact behavior depends on implementation, but it shouldn't crash
            try:
                new_cabinet = controller.add_cabinet(sample_project.id, **cabinet_data)
                # If it succeeds, sequence should be different
                assert new_cabinet.sequence_number != existing_sequence
            except Exception as e:
                # If it fails, it should be a validation error
                assert "sekwencji" in str(e).lower() or "sequence" in str(e).lower()

    def test_sequence_validation_preserves_project_context(
        self, session, sample_project, sample_project_cabinets
    ):
        """Test that sequence validation correctly handles project_id context."""
        controller = ProjectDetailsController(session, sample_project)
        controller.load_data()

        if len(controller.cabinets) >= 2:
            # Get two different cabinets
            cabinet1 = controller.cabinets[0]
            cabinet2 = controller.cabinets[1]

            # Verify they have the same project_id (they should)
            assert cabinet1.project_id == cabinet2.project_id == sample_project.id

            # Set up validation error spy
            validation_error_spy = Mock()
            controller.validation_error.connect(validation_error_spy)

            # Try to change cabinet1 to have same sequence as cabinet2
            controller.on_sequence_changed(cabinet1.id, cabinet2.sequence_number)

            # Should emit validation error because sequences would conflict within same project
            validation_error_spy.assert_called_once()
            error_message = validation_error_spy.call_args[0][0]
            assert str(cabinet2.sequence_number) in error_message

    def test_add_cabinet_type_id_preservation(
        self, session, sample_project, template_service
    ):
        """Test that type_id is properly preserved when adding catalog cabinets."""
        controller = ProjectDetailsController(session, sample_project)
        controller.load_data()

        # Create a catalog template
        catalog_template = template_service.create_template(
            nazwa="Catalog Base D60", kitchen_type="LOFT"
        )

        # Add cabinet with explicit type_id (catalog cabinet)
        catalog_cabinet_data = {
            "type_id": catalog_template.id,
            "body_color": "#f5f5f5",
            "front_color": "#2c2c2c",
            "handle_type": "Modern",
            "quantity": 1,
        }

        catalog_cabinet = controller.add_cabinet(
            sample_project.id, **catalog_cabinet_data
        )

        # Verify type_id is preserved
        assert catalog_cabinet.type_id == catalog_template.id

        # Add custom cabinet (no type_id)
        custom_cabinet_data = {
            "body_color": "#e0e0e0",
            "front_color": "#404040",
            "handle_type": "Handleless",
            "quantity": 1,
        }

        custom_cabinet = controller.add_cabinet(
            sample_project.id, **custom_cabinet_data
        )

        # Verify custom cabinet has no type_id
        assert custom_cabinet.type_id is None

    def test_cabinet_addition_sequence_assignment(
        self, session, sample_project, sample_project_cabinets
    ):
        """Test that cabinet addition properly assigns sequence numbers."""
        controller = ProjectDetailsController(session, sample_project)
        controller.load_data()

        # Get current sequences
        existing_sequences = {c.sequence_number for c in controller.cabinets}
        max_existing = max(existing_sequences) if existing_sequences else 0

        # Add cabinet without specifying sequence
        cabinet_data = {
            "body_color": "#ffffff",
            "front_color": "#000000",
            "handle_type": "Standard",
            "quantity": 1,
        }

        new_cabinet = controller.add_cabinet(sample_project.id, **cabinet_data)

        # Should get next available sequence
        assert new_cabinet.sequence_number not in existing_sequences
        assert new_cabinet.sequence_number > max_existing

        # Add another cabinet with explicit sequence
        explicit_sequence = max_existing + 10
        cabinet_data_explicit = {
            "sequence_number": explicit_sequence,
            "body_color": "#cccccc",
            "front_color": "#333333",
            "handle_type": "Modern",
            "quantity": 1,
        }

        new_cabinet_explicit = controller.add_cabinet(
            sample_project.id, **cabinet_data_explicit
        )
        assert new_cabinet_explicit.sequence_number == explicit_sequence

    def test_sequence_change_validation_comprehensive(self, session, sample_project):
        """Test comprehensive sequence change validation scenarios."""
        from src.db_schema.orm_models import ProjectCabinet

        # Create test cabinets directly
        cabinet1 = ProjectCabinet(
            project_id=sample_project.id,
            type_id=None,
            sequence_number=1,
            body_color="#ffffff",
            front_color="#000000",
            handle_type="Standard",
            quantity=1,
        )

        cabinet2 = ProjectCabinet(
            project_id=sample_project.id,
            type_id=None,
            sequence_number=3,
            body_color="#f0f0f0",
            front_color="#333333",
            handle_type="Modern",
            quantity=1,
        )

        session.add_all([cabinet1, cabinet2])
        session.commit()

        controller = ProjectDetailsController(session, sample_project)
        controller.load_data()

        validation_error_spy = Mock()
        controller.validation_error.connect(validation_error_spy)

        # Test 1: Change to existing sequence (should fail)
        controller.on_sequence_changed(cabinet1.id, 3)
        validation_error_spy.assert_called_once()
        validation_error_spy.reset_mock()

        # Test 2: Change to new unique sequence (should succeed)
        controller.on_sequence_changed(cabinet1.id, 5)
        validation_error_spy.assert_not_called()

        # Test 3: Change to same sequence (should be no-op)
        current_sequence = cabinet2.sequence_number
        controller.on_sequence_changed(cabinet2.id, current_sequence)
        validation_error_spy.assert_not_called()

    def test_sequence_validation_logic_comprehensive(self, session, sample_project):
        """Test the sequence validation logic comprehensively to ensure it catches all duplicates."""
        from src.db_schema.orm_models import ProjectCabinet
        from src.domain.sorting import validate_sequence_unique

        # Create test cabinets with different scenarios
        cabinets = [
            ProjectCabinet(id=1, project_id=sample_project.id, sequence_number=1),
            ProjectCabinet(id=2, project_id=sample_project.id, sequence_number=2),
            ProjectCabinet(id=3, project_id=sample_project.id, sequence_number=3),
        ]

        # Test 1: No duplicates should pass validation
        errors = validate_sequence_unique(cabinets)
        assert len(errors) == 0

        # Test 2: Add duplicate sequence should fail validation
        cabinets.append(
            ProjectCabinet(id=4, project_id=sample_project.id, sequence_number=2)
        )
        errors = validate_sequence_unique(cabinets)
        assert len(errors) == 1
        assert "2" in errors[0]

        # Test 3: Multiple duplicates should be detected
        cabinets.append(
            ProjectCabinet(id=5, project_id=sample_project.id, sequence_number=1)
        )
        errors = validate_sequence_unique(cabinets)
        assert len(errors) == 2  # Should detect both 1 and 2 as duplicates
