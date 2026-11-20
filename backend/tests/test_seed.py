from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session
from app.db import Base
from app.models import User, Ticket, Comment, Rating
from app.seed import seed

def test_demo_seed_idempotent_and_fictional():
    engine=create_engine('sqlite://'); Base.metadata.create_all(engine)
    with Session(engine) as db:
        assert seed(db) is True
        assert seed(db) is False
        assert db.scalar(select(func.count()).select_from(Ticket))==60
        assert db.scalar(select(func.count()).select_from(User))==7
        assert db.scalar(select(func.count()).select_from(Comment))>40
        assert db.scalar(select(func.count()).select_from(Rating))>0
        assert all(u.demo and u.email.endswith('.invalid') and u.password_hash.startswith('$argon2id$') for u in db.scalars(select(User)))
    engine.dispose()
