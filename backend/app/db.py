import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

class Base(DeclarativeBase):
    pass

if os.getenv('VERCEL') and not os.getenv('DATABASE_URL'):
    raise RuntimeError('DATABASE_URL is required in hosting; ephemeral SQLite is not supported')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./ticketdesk.db')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql+psycopg://', 1)
elif DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)
engine = create_engine(DATABASE_URL, pool_pre_ping=True, hide_parameters=True, **(
    {'connect_args': {'check_same_thread': False, 'timeout': 30}} if DATABASE_URL.startswith('sqlite')
    else {'pool_size': 2, 'max_overflow': 1, 'pool_timeout': 10, 'connect_args': {'connect_timeout': 10}}))
if DATABASE_URL.startswith('sqlite'):
    @event.listens_for(engine, 'connect')
    def sqlite_constraints(connection, _):
        connection.execute('PRAGMA foreign_keys=ON')
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

def get_db():
    with SessionLocal() as db:
        yield db
