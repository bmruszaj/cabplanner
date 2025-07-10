import pytest
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db_schema.orm_models import Base
from src.services.accessory_service import AccessoryService


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
    return AccessoryService(session)


def test_list_accessories_empty(service):
    # GIVEN no accessories in DB
    # WHEN listing accessories
    accessories = service.list_accessories()
    # THEN returns empty list
    assert accessories == []


def test_create_and_get_accessory(service):
    # GIVEN a fresh AccessoryService
    # WHEN creating a new accessory
    acc = service.create_accessory(name="Handle", sku="HNDL-001")
    # THEN the created accessory should have correct fields
    assert acc.id is not None
    assert acc.name == "Handle"
    assert acc.sku == "HNDL-001"
    assert isinstance(acc.created_at, datetime)
    assert isinstance(acc.updated_at, datetime)

    # WHEN fetching by ID
    fetched = service.get_accessory(acc.id)
    # THEN fetched matches the created accessory
    assert fetched is not None
    assert fetched.id == acc.id
    assert fetched.name == "Handle"


def test_find_by_sku(service):
    # GIVEN an accessory exists
    acc = service.create_accessory(name="Knob", sku="KNOB-001")

    # WHEN finding by existing SKU
    found = service.find_by_sku("KNOB-001")
    # THEN it should return that accessory
    assert found is not None
    assert found.id == acc.id

    # WHEN finding by non-existent SKU
    missing = service.find_by_sku("UNKNOWN")
    # THEN returns None
    assert missing is None


def test_update_accessory(service):
    # GIVEN an existing accessory
    acc = service.create_accessory(name="Panel", sku="PNL-001")
    acc_id = acc.id

    # WHEN updating name and sku
    updated = service.update_accessory(acc_id, name="PanelX", sku="PNL-001X")
    # THEN it should reflect the new values
    assert updated is not None
    assert updated.id == acc_id
    assert updated.name == "PanelX"
    assert updated.sku == "PNL-001X"


def test_update_nonexistent_accessory(service):
    # GIVEN no accessory with ID -1
    # WHEN attempting to update non-existent accessory
    result = service.update_accessory(-1, name="Nope")
    # THEN returns None
    assert result is None


def test_delete_accessory(service):
    # GIVEN an accessory to delete
    acc = service.create_accessory(name="Trim", sku="TRM-001")
    acc_id = acc.id

    # WHEN deleting first time
    first = service.delete_accessory(acc_id)
    # THEN deletion succeeds and it no longer exists
    assert first is True
    assert service.get_accessory(acc_id) is None

    # WHEN deleting second time
    second = service.delete_accessory(acc_id)
    # THEN deletion returns False
    assert second is False


def test_get_or_create_existing(service):
    # GIVEN existing accessory
    acc = service.create_accessory(name="Seal", sku="SLC-001")

    # WHEN calling get_or_create with same SKU
    got = service.get_or_create(name="Seal-New", sku="SLC-001")
    # THEN returns the existing accessory
    assert got.id == acc.id
    assert got.name == acc.name


def test_get_or_create_new(service):
    # GIVEN no accessory with SKU NEW-001
    # WHEN calling get_or_create
    new = service.get_or_create(name="NewAcc", sku="NEW-001")
    # THEN creates and returns new accessory
    assert new.id is not None
    assert new.name == "NewAcc"
    assert new.sku == "NEW-001"
