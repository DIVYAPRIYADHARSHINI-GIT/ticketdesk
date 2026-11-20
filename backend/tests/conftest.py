import secrets
import pytest
from fastapi import Response
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db import Base, get_db
from app.main import app
from app.models import User, Category, SLARule
from app.security import ph, new_session, COOKIE, ORIGIN

@pytest.fixture(scope='session')
def credential():
    password=secrets.token_urlsafe(24)
    return password,ph.hash(password)

@pytest.fixture
def ctx(credential):
    engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory=sessionmaker(bind=engine,expire_on_commit=False)
    with factory() as db:
        for i,role in enumerate(['employee','employee','agent','agent','admin'],1):
            db.add(User(id=i,name=f'TEST {role} {i}',email=f'test{i}@example.invalid',role=role,password_hash=credential[1]))
        db.add(Category(id=1,name='IT'))
        for priority in ['Low','Medium','High','Urgent']: db.add(SLARule(priority=priority,response_minutes=60,resolution_minutes=240))
        db.commit()
    def override():
        with factory() as db: yield db
    app.dependency_overrides[get_db]=override
    clients=[]
    def client(user_id=None):
        c=TestClient(app,raise_server_exceptions=True)
        if user_id:
            with factory() as db:
                response=Response(); token=new_session(response,db,user_id); db.commit()
                raw=response.headers['set-cookie'].split(';')[0].split('=',1)[1]
            c.cookies.set(COOKIE,raw)
        else: token=c.get('/api/auth/csrf').json()['csrf']
        c.headers.update({'Origin':ORIGIN,'X-CSRF-Token':token})
        clients.append(c); return c
    yield factory,client
    for c in clients: c.close()
    app.dependency_overrides.clear(); engine.dispose()

@pytest.fixture
def payload(): return {'title':'TEST office network request','description':'TEST fixture: network support needed.','category_id':1,'priority':'Medium'}
