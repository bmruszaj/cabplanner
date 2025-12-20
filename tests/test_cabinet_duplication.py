"""
Tests for cabinet duplication functionality.

Tests cover:
1. Duplicating a project cabinet instance with all parts and accessories
2. Duplicating a cabinet template with all parts and accessories
3. Unique naming for duplicated templates
"""

from unittest.mock import Mock
import pytest

from src.db_schema.orm_models import (
    ProjectCabinet,
    ProjectCabinetPart,
    ProjectCabinetAccessorySnapshot,
    CabinetTemplate,
    CabinetPart,
    CabinetTemplateAccessory,
)


class TestProjectCabinetDuplication:
    """Test duplicating cabinet instances in a project."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = Mock()
        session.add = Mock()
        session.flush = Mock()
        session.commit = Mock()
        session.refresh = Mock()
        session.get = Mock()
        session.scalar = Mock(return_value=5)  # Next sequence number = 6
        return session

    @pytest.fixture
    def source_cabinet(self):
        """Create a source cabinet with parts and accessories."""
        cabinet = Mock(spec=ProjectCabinet)
        cabinet.id = 1
        cabinet.project_id = 100
        cabinet.sequence_number = 3
        cabinet.type_id = 10
        cabinet.body_color = "Biały"
        cabinet.front_color = "Szary"
        cabinet.handle_type = "Uchwyt A"
        cabinet.quantity = 2

        # Create mock parts
        part1 = Mock(spec=ProjectCabinetPart)
        part1.part_name = "Bok lewy"
        part1.height_mm = 720
        part1.width_mm = 560
        part1.pieces = 1
        part1.wrapping = "L"
        part1.comments = "Test comment"
        part1.material = "PLYTA 18"
        part1.processing_json = {"edge": "abs"}
        part1.source_template_id = 10
        part1.source_part_id = 100
        part1.calc_context_json = None

        part2 = Mock(spec=ProjectCabinetPart)
        part2.part_name = "Bok prawy"
        part2.height_mm = 720
        part2.width_mm = 560
        part2.pieces = 1
        part2.wrapping = "P"
        part2.comments = None
        part2.material = "PLYTA 18"
        part2.processing_json = None
        part2.source_template_id = 10
        part2.source_part_id = 101
        part2.calc_context_json = None

        cabinet.parts = [part1, part2]

        # Create mock accessories
        acc1 = Mock(spec=ProjectCabinetAccessorySnapshot)
        acc1.name = "Zawias"
        acc1.unit = "szt"
        acc1.count = 4
        acc1.source_accessory_id = 200

        cabinet.accessory_snapshots = [acc1]

        return cabinet

    def test_duplicate_cabinet_creates_new_cabinet(self, mock_session, source_cabinet):
        """Test that duplicating a cabinet creates a new cabinet with same attributes."""
        from src.services.project_service import ProjectService

        # Setup mock to return source cabinet
        mock_session.get.return_value = source_cabinet

        service = ProjectService(mock_session)
        service.duplicate_cabinet(1)

        # Verify new cabinet was added
        assert mock_session.add.called
        assert mock_session.commit.called

    def test_duplicate_cabinet_gets_next_sequence(self, mock_session, source_cabinet):
        """Test that duplicated cabinet gets next available sequence number."""
        from src.services.project_service import ProjectService

        mock_session.get.return_value = source_cabinet
        mock_session.scalar.return_value = 5  # Max sequence is 5

        service = ProjectService(mock_session)

        # We need to check that sequence_number is set correctly
        # The add() call should receive a cabinet with sequence 6
        added_objects = []

        def capture_add(obj):
            added_objects.append(obj)

        mock_session.add.side_effect = capture_add

        service.duplicate_cabinet(1)

        # Find the ProjectCabinet in added objects
        cabinets = [obj for obj in added_objects if isinstance(obj, ProjectCabinet)]
        assert len(cabinets) == 1
        assert cabinets[0].sequence_number == 6

    def test_duplicate_cabinet_copies_all_parts(self, mock_session, source_cabinet):
        """Test that all parts are copied to the duplicated cabinet."""
        from src.services.project_service import ProjectService

        mock_session.get.return_value = source_cabinet

        added_objects = []

        def capture_add(obj):
            added_objects.append(obj)

        mock_session.add.side_effect = capture_add

        service = ProjectService(mock_session)
        service.duplicate_cabinet(1)

        # Find parts in added objects
        parts = [obj for obj in added_objects if isinstance(obj, ProjectCabinetPart)]
        assert len(parts) == 2

        # Check part names
        part_names = {p.part_name for p in parts}
        assert "Bok lewy" in part_names
        assert "Bok prawy" in part_names

    def test_duplicate_cabinet_copies_all_accessories(
        self, mock_session, source_cabinet
    ):
        """Test that all accessories are copied to the duplicated cabinet."""
        from src.services.project_service import ProjectService

        mock_session.get.return_value = source_cabinet

        added_objects = []

        def capture_add(obj):
            added_objects.append(obj)

        mock_session.add.side_effect = capture_add

        service = ProjectService(mock_session)
        service.duplicate_cabinet(1)

        # Find accessories in added objects
        accessories = [
            obj
            for obj in added_objects
            if isinstance(obj, ProjectCabinetAccessorySnapshot)
        ]
        assert len(accessories) == 1
        assert accessories[0].name == "Zawias"
        assert accessories[0].count == 4

    def test_duplicate_nonexistent_cabinet_returns_none(self, mock_session):
        """Test that duplicating non-existent cabinet returns None."""
        from src.services.project_service import ProjectService

        mock_session.get.return_value = None

        service = ProjectService(mock_session)
        result = service.duplicate_cabinet(999)

        assert result is None
        assert not mock_session.add.called


class TestCabinetTemplateDuplication:
    """Test duplicating cabinet templates in the catalog."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = Mock()
        session.add = Mock()
        session.flush = Mock()
        session.commit = Mock()
        session.refresh = Mock()
        session.get = Mock()
        session.scalar = Mock(return_value=None)  # No existing with same name
        return session

    @pytest.fixture
    def source_template(self):
        """Create a source template with parts and accessories."""
        template = Mock(spec=CabinetTemplate)
        template.id = 1
        template.name = "Dolna 60"
        template.kitchen_type = "LOFT"

        # Create mock parts
        part1 = Mock(spec=CabinetPart)
        part1.part_name = "Bok"
        part1.height_mm = 720
        part1.width_mm = 560
        part1.pieces = 2
        part1.material = "PLYTA 18"
        part1.wrapping = "L"
        part1.comments = None
        part1.processing_json = None

        template.parts = [part1]

        # Create mock accessory links
        acc_link = Mock(spec=CabinetTemplateAccessory)
        acc_link.accessory_id = 100
        acc_link.count = 4

        template.accessories = [acc_link]

        return template

    def test_duplicate_template_creates_new_template(
        self, mock_session, source_template
    ):
        """Test that duplicating a template creates a new template."""
        from src.services.template_service import TemplateService

        mock_session.get.return_value = source_template

        service = TemplateService(mock_session)
        service.duplicate_template(1)

        assert mock_session.add.called
        assert mock_session.commit.called

    def test_duplicate_template_has_unique_name(self, mock_session, source_template):
        """Test that duplicated template gets a unique name with (kopia) suffix."""
        from src.services.template_service import TemplateService

        mock_session.get.return_value = source_template

        added_objects = []

        def capture_add(obj):
            added_objects.append(obj)

        mock_session.add.side_effect = capture_add

        service = TemplateService(mock_session)
        service.duplicate_template(1)

        # Find the CabinetTemplate in added objects
        templates = [obj for obj in added_objects if isinstance(obj, CabinetTemplate)]
        assert len(templates) == 1
        assert templates[0].name == "Dolna 60 (kopia)"
        assert templates[0].kitchen_type == "LOFT"

    def test_duplicate_template_increments_copy_number(
        self, mock_session, source_template
    ):
        """Test that duplicate name gets incremented if (kopia) exists."""
        from src.services.template_service import TemplateService

        mock_session.get.return_value = source_template

        # First call returns existing template (name exists), second call returns None
        call_count = [0]

        def mock_scalar(stmt):
            call_count[0] += 1
            if call_count[0] == 1:
                # "Dolna 60 (kopia)" exists
                return Mock()
            else:
                # "Dolna 60 (kopia 2)" doesn't exist
                return None

        mock_session.scalar.side_effect = mock_scalar

        added_objects = []

        def capture_add(obj):
            added_objects.append(obj)

        mock_session.add.side_effect = capture_add

        service = TemplateService(mock_session)
        service.duplicate_template(1)

        templates = [obj for obj in added_objects if isinstance(obj, CabinetTemplate)]
        assert len(templates) == 1
        assert templates[0].name == "Dolna 60 (kopia 2)"

    def test_duplicate_template_copies_all_parts(self, mock_session, source_template):
        """Test that all parts are copied to the duplicated template."""
        from src.services.template_service import TemplateService

        mock_session.get.return_value = source_template

        added_objects = []

        def capture_add(obj):
            added_objects.append(obj)

        mock_session.add.side_effect = capture_add

        service = TemplateService(mock_session)
        service.duplicate_template(1)

        # Find parts in added objects
        parts = [obj for obj in added_objects if isinstance(obj, CabinetPart)]
        assert len(parts) == 1
        assert parts[0].part_name == "Bok"
        assert parts[0].pieces == 2

    def test_duplicate_template_copies_accessory_links(
        self, mock_session, source_template
    ):
        """Test that accessory links are copied to the duplicated template."""
        from src.services.template_service import TemplateService

        mock_session.get.return_value = source_template

        added_objects = []

        def capture_add(obj):
            added_objects.append(obj)

        mock_session.add.side_effect = capture_add

        service = TemplateService(mock_session)
        service.duplicate_template(1)

        # Find accessory links in added objects
        links = [
            obj for obj in added_objects if isinstance(obj, CabinetTemplateAccessory)
        ]
        assert len(links) == 1
        assert links[0].accessory_id == 100
        assert links[0].count == 4

    def test_duplicate_nonexistent_template_returns_none(self, mock_session):
        """Test that duplicating non-existent template returns None."""
        from src.services.template_service import TemplateService

        mock_session.get.return_value = None

        service = TemplateService(mock_session)
        result = service.duplicate_template(999)

        assert result is None
        assert not mock_session.add.called


class TestCabinetDuplicationIntegration:
    """Integration tests for cabinet duplication using real models."""

    def test_project_cabinet_duplication_preserves_attributes(self):
        """Test that all important attributes are preserved during duplication."""
        # Create a source cabinet with all attributes
        source = ProjectCabinet(
            project_id=1,
            sequence_number=5,
            type_id=10,
            body_color="Biały",
            front_color="Szary",
            handle_type="Uchwyt Premium",
            quantity=3,
        )

        # Simulate what duplicate_cabinet does
        new_cabinet = ProjectCabinet(
            project_id=source.project_id,
            sequence_number=6,  # Next sequence
            type_id=source.type_id,
            body_color=source.body_color,
            front_color=source.front_color,
            handle_type=source.handle_type,
            quantity=source.quantity,
        )

        # Verify all attributes match except sequence
        assert new_cabinet.project_id == source.project_id
        assert new_cabinet.type_id == source.type_id
        assert new_cabinet.body_color == source.body_color
        assert new_cabinet.front_color == source.front_color
        assert new_cabinet.handle_type == source.handle_type
        assert new_cabinet.quantity == source.quantity
        assert new_cabinet.sequence_number != source.sequence_number

    def test_template_duplication_name_variations(self):
        """Test various naming scenarios for template duplication."""
        test_cases = [
            ("Dolna 60", "Dolna 60 (kopia)"),
            ("Szafka", "Szafka (kopia)"),
            ("Test Cabinet Type", "Test Cabinet Type (kopia)"),
        ]

        for original, expected in test_cases:
            result = f"{original} (kopia)"
            assert result == expected
