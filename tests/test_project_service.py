import pytest
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db_schema.orm_models import Base, CabinetColor
from src.services.project_service import ProjectService
from src.services.template_service import TemplateService
from src.services.color_palette_service import ColorPaletteService


@pytest.fixture(scope="module")
def engine():
    # In-memory SQLite for fast tests
    return create_engine("sqlite:///:memory:", future=True)


@pytest.fixture(scope="module", autouse=True)
def prepare_db(engine):
    # Create all tables once per test run
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def session(engine):
    Session = sessionmaker(bind=engine, future=True)
    sess = Session()
    try:
        yield sess
    finally:
        sess.rollback()
        sess.close()


@pytest.fixture
def service(session):
    return ProjectService(session)


@pytest.fixture
def template_service(session):
    return TemplateService(session)


def test_create_and_get_project(service):
    # GIVEN a fresh ProjectService
    # WHEN creating a new project
    proj = service.create_project(
        name="Proj A",
        kitchen_type="LOFT",
        order_number="123",
    )
    # THEN the created project should have correct fields
    assert proj.id is not None
    assert proj.name == "Proj A"
    assert proj.kitchen_type == "LOFT"
    assert proj.order_number == "123"
    assert isinstance(proj.created_at, datetime)

    # WHEN fetching the project by its ID
    fetched = service.get_project(proj.id)
    # THEN the fetched project should match the created one
    assert fetched is not None
    assert fetched.id == proj.id
    assert fetched.name == "Proj A"


def test_list_projects_order(service):
    # GIVEN two newly created projects
    p1 = service.create_project(name="P1", kitchen_type="A", order_number="1")
    p2 = service.create_project(name="P2", kitchen_type="A", order_number="2")

    # WHEN listing all projects
    lst = service.list_projects()

    # THEN they should appear in reverse creation order (newest first)
    # When created_at is the same, sort by id DESC (higher id = newer)
    ids = [p.id for p in lst]
    assert ids.index(p2.id) < ids.index(p1.id)


def test_update_project(service):
    # GIVEN an existing project
    proj = service.create_project(name="Up", kitchen_type="B", order_number="999")
    old_updated = proj.updated_at

    # WHEN updating its name and client_name
    updated = service.update_project(proj.id, name="Up2", client_name="Alice")
    # THEN the returned project should reflect the changes
    assert updated is not None
    assert updated.name == "Up2"
    assert updated.client_name == "Alice"
    # AND its updated_at timestamp should move forward
    assert updated.updated_at >= old_updated


def test_delete_project(service):
    # GIVEN a new project
    proj = service.create_project(name="Del", kitchen_type="C", order_number="000")
    pid = proj.id

    # WHEN deleting it
    result_first = service.delete_project(pid)
    # THEN deletion should succeed and project no longer exists
    assert result_first is True
    assert service.get_project(pid) is None

    # WHEN deleting again
    result_second = service.delete_project(pid)
    # THEN deletion should report False
    assert result_second is False


def test_cabinet_sequence_and_crud(service, template_service):
    # GIVEN a project with no cabinets and a cabinet template
    proj = service.create_project(name="CabTest", kitchen_type="X", order_number="42")
    pid = proj.id

    # Create a cabinet template to use
    template = template_service.create_template(kitchen_type="X", name="TestCabinet")
    template_id = template.id

    # WHEN querying next sequence number
    next_seq_initial = service.get_next_cabinet_sequence(pid)
    # THEN it should be 1
    assert next_seq_initial == 1

    # WHEN adding the first cabinet without override
    cab1 = service.add_cabinet(
        pid,
        sequence_number=next_seq_initial,
        type_id=template_id,
        body_color="white",
        front_color="black",
        handle_type="T-Bar",
    )
    # THEN it should get sequence_number 1
    assert cab1.sequence_number == 1
    assert cab1.project_id == pid

    # WHEN querying next sequence again
    next_seq_after = service.get_next_cabinet_sequence(pid)
    # THEN it should be 2
    assert next_seq_after == 2

    # WHEN adding a second cabinet with manual sequence override
    cab2 = service.add_cabinet(
        pid,
        sequence_number=5,
        type_id=template_id,
        body_color="red",
        front_color="blue",
        handle_type="Knob",
    )
    # THEN it should respect the override
    assert cab2.sequence_number == 5

    # WHEN listing cabinets
    ordered = service.list_cabinets(pid)
    # THEN they should be ordered by sequence_number
    seqs = [c.sequence_number for c in ordered]
    assert seqs == [1, 5]

    # WHEN updating the first cabinet
    updated = service.update_cabinet(cab1.id, body_color="gray")
    # THEN the change should persist
    assert updated is not None
    assert updated.body_color == "gray"

    # WHEN deleting the first cabinet
    delete_first = service.delete_cabinet(cab1.id)
    # THEN deletion should succeed and it should no longer exist
    assert delete_first is True
    assert service.get_cabinet(cab1.id) is None

    # WHEN deleting it again
    delete_again = service.delete_cabinet(cab1.id)
    # THEN deletion should report False
    assert delete_again is False


def test_get_cabinet_nonexistent_returns_none(service):
    # GIVEN no cabinet with ID -1
    # WHEN fetching cabinet -1
    result = service.get_cabinet(-1)
    # THEN it should return None
    assert result is None


def test_add_cabinet_marks_color_usage(service, template_service, session):
    """Adding cabinet should increase usage stats for body/front colors."""
    palette = ColorPaletteService(session)
    palette.ensure_seeded()

    proj = service.create_project(
        name="ColorUsageAdd",
        kitchen_type="LOFT",
        order_number="COLOR-USAGE-ADD",
    )
    template = template_service.create_template(
        kitchen_type="LOFT", name="ColorTemplate1"
    )

    before_body = session.query(CabinetColor).filter_by(normalized_name="biały").one()
    before_front = session.query(CabinetColor).filter_by(normalized_name="czarny").one()
    before_body_count = before_body.usage_count
    before_front_count = before_front.usage_count

    service.add_cabinet(
        proj.id,
        sequence_number=1,
        type_id=template.id,
        body_color="Biały",
        front_color="Czarny",
        handle_type="Standardowy",
        quantity=1,
    )

    session.expire_all()
    after_body = session.query(CabinetColor).filter_by(normalized_name="biały").one()
    after_front = session.query(CabinetColor).filter_by(normalized_name="czarny").one()

    assert after_body.usage_count == before_body_count + 1
    assert after_front.usage_count == before_front_count + 1
    assert after_body.last_used_at is not None
    assert after_front.last_used_at is not None


def test_update_cabinet_marks_only_changed_colors(service, template_service, session):
    """Updating cabinet should mark only colors that actually changed."""
    palette = ColorPaletteService(session)
    palette.ensure_seeded()

    proj = service.create_project(
        name="ColorUsageUpdate",
        kitchen_type="LOFT",
        order_number="COLOR-USAGE-UPD",
    )
    template = template_service.create_template(
        kitchen_type="LOFT", name="ColorTemplate2"
    )

    cabinet = service.add_cabinet(
        proj.id,
        sequence_number=1,
        type_id=template.id,
        body_color="Biały",
        front_color="Czarny",
        handle_type="Standardowy",
        quantity=1,
    )

    before_front = session.query(CabinetColor).filter_by(normalized_name="czarny").one()
    before_body_target = (
        session.query(CabinetColor).filter_by(normalized_name="zielony").one()
    )
    before_front_count = before_front.usage_count
    before_body_target_count = before_body_target.usage_count

    service.update_cabinet(cabinet.id, body_color="Zielony", front_color="Czarny")

    session.expire_all()
    after_front = session.query(CabinetColor).filter_by(normalized_name="czarny").one()
    after_body_target = (
        session.query(CabinetColor).filter_by(normalized_name="zielony").one()
    )

    assert after_front.usage_count == before_front_count
    assert after_body_target.usage_count == before_body_target_count + 1


def test_list_cabinets_empty(service):
    # GIVEN a project with zero cabinets
    proj = service.create_project(name="Empty", kitchen_type="Z", order_number="00")
    pid = proj.id

    # WHEN listing cabinets
    cabinets = service.list_cabinets(pid)
    # THEN the result should be an empty list
    assert cabinets == []


@pytest.mark.parametrize("count", [0, 1, 2, 5])
def test_next_sequence_after_manual_insert(service, template_service, count):
    # GIVEN a project with manually inserted cabinets at fixed gaps
    proj = service.create_project(
        name=f"Manual{count}", kitchen_type="M", order_number=f"M{count}"
    )
    pid = proj.id

    # Create a cabinet template to use
    template = template_service.create_template(
        kitchen_type="M", name=f"TestCabinet{count}"
    )
    template_id = template.id

    for i in range(1, count + 1):
        service.add_cabinet(
            pid,
            sequence_number=i * 10,
            type_id=template_id,
            body_color="c",
            front_color="f",
            handle_type="h",
        )

    # WHEN querying next sequence number
    next_seq = service.get_next_cabinet_sequence(pid)
    # THEN it should be max + 1, respecting the manual gaps
    expected = (count * 10) + 1
    assert next_seq == expected


# ==============================================================================
# Edge Cases Tests
# ==============================================================================


class TestProjectEdgeCases:
    """Test edge cases for project operations"""

    def test_project_without_cabinets(self, service):
        """Test that a project with no cabinets works correctly"""
        # GIVEN: A project with no cabinets
        proj = service.create_project(
            name="Empty Project",
            kitchen_type="MODERN",
            order_number="EMPTY-001",
        )

        # THEN: Project should exist and have no cabinets
        assert proj.id is not None
        cabinets = service.list_cabinets(proj.id)
        assert cabinets == []

        # AND: Next sequence should be 1
        next_seq = service.get_next_cabinet_sequence(proj.id)
        assert next_seq == 1

    def test_project_with_many_cabinets(self, service, template_service):
        """Test project with large number of cabinets (100+)"""
        # GIVEN: A project
        proj = service.create_project(
            name="Large Project",
            kitchen_type="LOFT",
            order_number="LARGE-001",
        )

        template = template_service.create_template(
            kitchen_type="LOFT", name="BulkTestCabinet"
        )

        # WHEN: Adding 120 cabinets
        num_cabinets = 120
        for i in range(1, num_cabinets + 1):
            service.add_cabinet(
                proj.id,
                sequence_number=i,
                type_id=template.id,
                body_color="#FFFFFF",
                front_color="#000000",
                handle_type="Standard",
            )

        # THEN: All cabinets should be added
        cabinets = service.list_cabinets(proj.id)
        assert len(cabinets) == num_cabinets

        # AND: Next sequence should be correct
        next_seq = service.get_next_cabinet_sequence(proj.id)
        assert next_seq == num_cabinets + 1

    def test_project_with_unicode_name_polish(self, service):
        """Test project with Polish characters in name"""
        # GIVEN: Polish characters in project name
        polish_name = "Kuchnia Żółć Ąść Ęśćżźł"

        # WHEN: Creating project with Polish name
        proj = service.create_project(
            name=polish_name,
            kitchen_type="MODERN",
            order_number="POLISH-001",
            client_name="Jan Żółciński",
            client_address="ul. Świdnicka 42, Łódź",
        )

        # THEN: All Polish characters should be preserved
        fetched = service.get_project(proj.id)
        assert fetched.name == polish_name
        assert fetched.client_name == "Jan Żółciński"
        assert "Łódź" in fetched.client_address

    def test_project_with_unicode_name_emoji(self, service):
        """Test project with emoji in name"""
        # GIVEN: Emoji in project name
        emoji_name = "Kuchnia 🍳 Nowoczesna ✨"

        # WHEN: Creating project with emoji
        proj = service.create_project(
            name=emoji_name,
            kitchen_type="MODERN",
            order_number="EMOJI-001",
        )

        # THEN: Emoji should be preserved
        fetched = service.get_project(proj.id)
        assert fetched.name == emoji_name
        assert "🍳" in fetched.name
        assert "✨" in fetched.name

    def test_project_with_very_long_notes(self, service):
        """Test project with very long notes/comments"""
        # GIVEN: Very long notes (10000 characters)
        long_note = "A" * 10000

        # WHEN: Creating project with long notes
        proj = service.create_project(
            name="Long Notes Project",
            kitchen_type="MODERN",
            order_number="LONG-001",
            blaty=True,
            blaty_note=long_note,
        )

        # THEN: Notes should be preserved
        fetched = service.get_project(proj.id)
        assert len(fetched.blaty_note) == 10000
