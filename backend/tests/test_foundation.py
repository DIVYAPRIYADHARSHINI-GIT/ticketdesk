from pathlib import Path
import tomllib
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.db import Base
from app.models import User, SLARule, Attachment

@pytest.fixture
def db():
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    with Session(engine) as session: yield session
    engine.dispose()

def test_dependency_manifests_match():
    root = Path(__file__).parents[1]
    project = tomllib.loads((root/'pyproject.toml').read_text())
    assert set(project['project']['dependencies']) == set((root/'requirements.txt').read_text().splitlines())
    assert (root/'.python-version').read_text().strip() == '3.14'

def test_all_tables_and_queue_indexes(db):
    inspector = inspect(db.bind)
    assert len(inspector.get_table_names()) == 13
    indexes = {i['name'] for i in inspector.get_indexes('tickets')}
    assert {'ix_ticket_queue','ix_ticket_requester_created','ix_tickets_assignee_id','ix_tickets_category_id'} <= indexes

@pytest.mark.parametrize('role', ['owner','superadmin',''])
def test_database_rejects_unknown_roles(db, role):
    db.add(User(name='Test Fixture', email='fixture@example.invalid', password_hash='not-a-password', role=role))
    with pytest.raises(IntegrityError): db.flush()

@pytest.mark.parametrize('response,resolution', [(0,10), (10,5), (-1,60)])
def test_sla_constraints(db, response, resolution):
    db.add(SLARule(priority='Low', response_minutes=response, resolution_minutes=resolution))
    with pytest.raises(IntegrityError): db.flush()

def test_attachment_size_constraint(db):
    db.add(Attachment(ticket_id=1, author_id=1, filename='test.pdf', mime='application/pdf', data=b'%PDF-', size=1048577))
    with pytest.raises(IntegrityError): db.flush()
