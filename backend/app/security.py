import hashlib
import os
import secrets
import time
from argon2 import PasswordHasher, Type
from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy import delete, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session as DB
from .db import get_db
from .models import Session, User, RateBucket

ORIGIN = os.getenv('FRONTEND_ORIGIN', 'http://localhost:5173').rstrip('/')
SECURE = os.getenv('COOKIE_SECURE', 'false').lower() == 'true'
if ORIGIN.startswith('https://') and not SECURE:
    raise RuntimeError('HTTPS deployments require COOKIE_SECURE=true')
COOKIE = '__Host-ticketdesk' if SECURE else 'ticketdesk_local'
ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2, type=Type.ID)

def digest(value: str): return hashlib.sha256(value.encode()).hexdigest()

def session_for(request: Request, db: DB):
    raw = request.cookies.get(COOKIE, '')
    return db.scalar(select(Session).where(Session.id == digest(raw), Session.expires_at > time.time())) if raw else None

def new_session(response: Response, db: DB, user_id=None):
    raw, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    db.add(Session(id=digest(raw), csrf_hash=digest(csrf), user_id=user_id, expires_at=time.time()+28800))
    db.execute(delete(Session).where(Session.expires_at < time.time()))
    response.set_cookie(COOKIE, raw, httponly=True, secure=SECURE, samesite='lax', max_age=28800, path='/')
    return csrf

def csrf_guard(request: Request, db: DB = Depends(get_db)):
    if request.headers.get('origin') != ORIGIN:
        raise HTTPException(403, 'Request origin not allowed')
    session = session_for(request, db)
    value = request.headers.get('x-csrf-token', '')
    if not session or not value or not secrets.compare_digest(session.csrf_hash, digest(value)):
        raise HTTPException(403, 'Session expired. Refresh and try again.')
    return session

def current_user(request: Request, db: DB = Depends(get_db)):
    session = session_for(request, db)
    user = db.get(User, session.user_id) if session and session.user_id else None
    if not user or not user.active: raise HTTPException(401, 'Please sign in')
    return user

def staff(user: User = Depends(current_user)):
    if user.role not in ('agent', 'admin'): raise HTTPException(403, 'Support access required')
    return user

def admin(user: User = Depends(current_user)):
    if user.role != 'admin': raise HTTPException(403, 'Administrator access required')
    return user

def rate_limit(db: DB, namespace: str, identity: str, limit: int, seconds: int = 60):
    now = time.time()
    window = int(now // seconds)
    key = digest(f'{namespace}:{identity}:{window}')
    insert = sqlite_insert if db.bind.dialect.name == 'sqlite' else pg_insert
    statement = insert(RateBucket).values(key=key, count=1, expires_at=(window+1)*seconds)
    count = db.execute(statement.on_conflict_do_update(index_elements=['key'], set_={'count': RateBucket.count+1}).returning(RateBucket.count)).scalar_one()
    db.execute(delete(RateBucket).where(RateBucket.expires_at < now-seconds))
    db.commit()  # An unsuccessful sign-in still consumes an attempt.
    if count > limit:
        raise HTTPException(429, 'Too many attempts. Please try again shortly.', headers={'Retry-After': str(seconds)})

def public_user(user: User):
    return {'id': user.id, 'name': user.name, 'email': user.email, 'role': user.role, 'active': user.active, 'demo': user.demo}
