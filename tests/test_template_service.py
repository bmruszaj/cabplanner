import pytest
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db_schema.orm_models import Base
from src.services.template_service import TemplateService


@pytest.fixture(scope="module")
def engine():
    return create_engine("sqlite:///:memory:", future=True)


@pytest.fixture(scope="module", autouse=True)
def prepare_db(engine):
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
    return TemplateService(session)


def test_create_and_get_cabinet_type(service):
    # GIVEN a fresh TemplateService
    # WHEN creating a new CabinetTemplate
    ctype = service.create_template(
        kitchen_type="LOFT",
        name="Wall Unit",
    )
    # THEN the created CabinetTemplate should have correct fields
    assert ctype.id is not None
    assert ctype.kitchen_type == "LOFT"
    assert ctype.name == "Wall Unit"
    assert isinstance(ctype.created_at, datetime)
    assert isinstance(ctype.updated_at, datetime)

    # WHEN fetching the CabinetTemplate by its ID
    fetched = service.get_template(ctype.id)
    # THEN the fetched CabinetTemplate should match the created one
    assert fetched is not None
    assert fetched.id == ctype.id
    assert fetched.name == "Wall Unit"


def test_list_cabinet_types_no_filter(service):
    # GIVEN multiple CabinetTemplate entries with various kitchen_types
    a = service.create_template(kitchen_type="PARIS", name="Base Unit")
    b = service.create_template(kitchen_type="WINO", name="Tall Unit")

    # WHEN listing all cabinet templates without a filter
    all_types = service.list_templates()
    # THEN the result should include the newly created entries
    ids = {ct.id for ct in all_types}
    assert a.id in ids
    assert b.id in ids


def test_list_cabinet_types_with_filter(service):
    # GIVEN CabinetTemplate entries with kitchen_type "FILTER" and others
    x1 = service.create_template(kitchen_type="FILTER", name="X1")
    x2 = service.create_template(kitchen_type="FILTER", name="X2")
    service.create_template(kitchen_type="OTHER", name="O1")

    # WHEN listing cabinet templates filtered by kitchen_type="FILTER"
    filtered = service.list_templates(kitchen_type="FILTER")
    # THEN only entries with kitchen_type "FILTER" should be returned
    assert all(ct.kitchen_type == "FILTER" for ct in filtered)
    filtered_ids = {ct.id for ct in filtered}
    assert x1.id in filtered_ids and x2.id in filtered_ids


def test_update_cabinet_type(service):
    # GIVEN an existing CabinetTemplate
    ct = service.create_template(kitchen_type="UPD", name="Orig")
    ct_id = ct.id
    old_name = ct.name

    # WHEN updating its nazwa
    updated = service.update_template(ct_id, name="NewName")
    # THEN the CabinetTemplate should reflect the new values
    assert updated is not None
    assert updated.id == ct_id
    assert updated.name == "NewName"
    assert updated.name != old_name


def test_update_nonexistent_returns_none(service):
    # GIVEN no CabinetTemplate with ID -1
    # WHEN attempting to update a non-existent entry
    result = service.update_template(-1, name="Nope")
    # THEN the result should be None
    assert result is None


def test_delete_cabinet_type(service):
    # GIVEN a CabinetTemplate to delete
    ct = service.create_template(kitchen_type="DEL", name="ToDelete")
    ct_id = ct.id

    # WHEN deleting it the first time
    first_delete = service.delete_template(ct_id)
    # THEN deletion should succeed and the entry should no longer exist
    assert first_delete is True
    assert service.get_template(ct_id) is None

    # WHEN deleting it a second time
    second_delete = service.delete_template(ct_id)
    # THEN deletion should return False
    assert second_delete is False


def test_get_nonexistent_returns_none(service):
    # GIVEN no CabinetTemplate with ID -999
    # WHEN fetching a non-existent entry
    result = service.get_template(-999)
    # THEN the result should be None
    assert result is None


# -- Accessory tests --


def test_add_accessory_by_name_creates_accessory(service):
    # GIVEN a cabinet template
    ct = service.create_template(kitchen_type="LOFT", name="AccTestCabinet1")

    # WHEN adding an accessory by name that doesn't exist yet
    link = service.add_accessory_by_name(
        cabinet_type_id=ct.id,
        name="Uchwyt ZĹ‚oty",
        count=2,
    )

    # THEN the link should be created with correct values
    assert link is not None
    assert link.cabinet_type_id == ct.id
    assert link.count == 2

    # AND the accessory should have been created
    assert link.accessory.name == "Uchwyt ZĹ‚oty"


def test_add_accessory_by_name_uses_existing_accessory(service):
    # GIVEN a cabinet template and an existing accessory
    ct = service.create_template(kitchen_type="LOFT", name="AccTestCabinet2")

    # First create an accessory
    first_link = service.add_accessory_by_name(
        cabinet_type_id=ct.id,
        name="Handle A",
        count=1,
    )
    first_accessory_id = first_link.accessory.id

    # Create another cabinet template
    ct2 = service.create_template(kitchen_type="LOFT", name="AccTestCabinet3")

    # WHEN adding an accessory with the same name to another cabinet
    second_link = service.add_accessory_by_name(
        cabinet_type_id=ct2.id,
        name="Handle A",  # Same name
        count=3,
    )

    # THEN the same accessory should be reused
    assert second_link.accessory.id == first_accessory_id
    assert second_link.count == 3


def test_list_accessories_for_cabinet_template(service):
    # GIVEN a cabinet template with some accessories
    ct = service.create_template(kitchen_type="WINO", name="AccTestCabinet4")

    service.add_accessory_by_name(cabinet_type_id=ct.id, name="Prowadnica", count=4)
    service.add_accessory_by_name(cabinet_type_id=ct.id, name="Zawias", count=2)

    # WHEN listing accessories
    accessories = service.list_accessories(ct.id)

    # THEN we should have both accessories
    assert len(accessories) == 2
    names = {a.accessory.name for a in accessories}
    assert names == {"Prowadnica", "Zawias"}


def test_delete_accessory_from_cabinet_template(service):
    # GIVEN a cabinet template with an accessory
    ct = service.create_template(kitchen_type="PARIS", name="AccTestCabinet5")
    link = service.add_accessory_by_name(cabinet_type_id=ct.id, name="Uchwyt", count=1)
    accessory_id = link.accessory.id

    # WHEN deleting the accessory link
    result = service.delete_accessory(ct.id, accessory_id)

    # THEN deletion should succeed
    assert result is True

    # AND the link should no longer exist
    accessories = service.list_accessories(ct.id)
    assert len(accessories) == 0


def test_update_accessory_count(service):
    # GIVEN a cabinet template with an accessory
    ct = service.create_template(kitchen_type="LOFT", name="AccTestCabinet6")
    service.add_accessory_by_name(cabinet_type_id=ct.id, name="RÄ…czka", count=1)

    # WHEN adding the same accessory again with a different count
    updated_link = service.add_accessory_by_name(
        cabinet_type_id=ct.id, name="RÄ…czka", count=5
    )

    # THEN the count should be updated
    assert updated_link.count == 5

    # AND there should still be only one link
    accessories = service.list_accessories(ct.id)
    assert len(accessories) == 1
