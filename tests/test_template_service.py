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
        nazwa="Wall Unit",
    )
    # THEN the created CabinetTemplate should have correct fields
    assert ctype.id is not None
    assert ctype.kitchen_type == "LOFT"
    assert ctype.nazwa == "Wall Unit"
    assert isinstance(ctype.created_at, datetime)
    assert isinstance(ctype.updated_at, datetime)

    # WHEN fetching the CabinetTemplate by its ID
    fetched = service.get_template(ctype.id)
    # THEN the fetched CabinetTemplate should match the created one
    assert fetched is not None
    assert fetched.id == ctype.id
    assert fetched.nazwa == "Wall Unit"


def test_list_cabinet_types_no_filter(service):
    # GIVEN multiple CabinetTemplate entries with various kitchen_types
    a = service.create_template(kitchen_type="PARIS", nazwa="Base Unit")
    b = service.create_template(kitchen_type="WINO", nazwa="Tall Unit")

    # WHEN listing all cabinet templates without a filter
    all_types = service.list_templates()
    # THEN the result should include the newly created entries
    ids = {ct.id for ct in all_types}
    assert a.id in ids
    assert b.id in ids


def test_list_cabinet_types_with_filter(service):
    # GIVEN CabinetTemplate entries with kitchen_type "FILTER" and others
    x1 = service.create_template(kitchen_type="FILTER", nazwa="X1")
    x2 = service.create_template(kitchen_type="FILTER", nazwa="X2")
    service.create_template(kitchen_type="OTHER", nazwa="O1")

    # WHEN listing cabinet templates filtered by kitchen_type="FILTER"
    filtered = service.list_templates(kitchen_type="FILTER")
    # THEN only entries with kitchen_type "FILTER" should be returned
    assert all(ct.kitchen_type == "FILTER" for ct in filtered)
    filtered_ids = {ct.id for ct in filtered}
    assert x1.id in filtered_ids and x2.id in filtered_ids


def test_update_cabinet_type(service):
    # GIVEN an existing CabinetTemplate
    ct = service.create_template(kitchen_type="UPD", nazwa="Orig")
    ct_id = ct.id
    old_name = ct.nazwa

    # WHEN updating its nazwa
    updated = service.update_template(ct_id, nazwa="NewName")
    # THEN the CabinetTemplate should reflect the new values
    assert updated is not None
    assert updated.id == ct_id
    assert updated.nazwa == "NewName"
    assert updated.nazwa != old_name


def test_update_nonexistent_returns_none(service):
    # GIVEN no CabinetTemplate with ID -1
    # WHEN attempting to update a non-existent entry
    result = service.update_template(-1, nazwa="Nope")
    # THEN the result should be None
    assert result is None


def test_delete_cabinet_type(service):
    # GIVEN a CabinetTemplate to delete
    ct = service.create_template(kitchen_type="DEL", nazwa="ToDelete")
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
