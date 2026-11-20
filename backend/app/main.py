import os
import re
import secrets
import time
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request, Response, UploadFile, File, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from argon2.exceptions import VerificationError, InvalidHashError
from sqlalchemy import select, func, text, delete, case
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session as DB
from .db import get_db
from .models import User, Session, Category, SLARule, Ticket, Comment, Attachment, History, Notification, Rating, SavedReply
from . import schemas as s
from .security import ORIGIN, COOKIE, ph, digest, new_session, session_for, csrf_guard, current_user, staff, admin, rate_limit, public_user
from .domain import get_ticket, ticket_query, ticket_json, patch_ticket, history, notify, effective_pause, sla_expression, TERMINAL
from .middleware import BoundedBody

app = FastAPI(title='TicketDesk API', version='1.0.0', docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=[ORIGIN], allow_credentials=True, allow_methods=['GET','POST','PATCH','PUT','DELETE'], allow_headers=['Content-Type','X-CSRF-Token'])
app.add_middleware(BoundedBody)
api = APIRouter(prefix='/api')
unsafe = [Depends(csrf_guard)]

@app.middleware('http')
async def headers(request, call_next):
    # Reject oversized requests before multipart parsing; stream reader below is bounded too.
    try: length = int(request.headers.get('content-length', '0'))
    except ValueError: return JSONResponse({'detail': 'Invalid content length'}, 400)
    if length > 1100000: return JSONResponse({'detail': 'Maximum attachment size is 1 MB'}, 413)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Referrer-Policy'] = 'no-referrer'
    return response

@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    # Never reflect passwords or rejected ticket bodies through Pydantic's input field.
    return JSONResponse({'detail': 'Please check the supplied fields.', 'fields': ['.'.join(map(str,e['loc'])) for e in exc.errors()]}, 422)

@app.exception_handler(IntegrityError)
async def conflict(request, exc):
    return JSONResponse({'detail': 'This item already exists or conflicts with another change.'}, 409)

@app.exception_handler(SQLAlchemyError)
async def database_unavailable(request, exc):
    # Do not emit SQL parameters, request text or connection details into logs.
    return JSONResponse({'detail': 'The workspace database is temporarily unavailable. Please try again.'}, 503)

@app.get('/health')
@api.get('/health')
def health(db: DB = Depends(get_db)):
    try:
        assert db.execute(text('SELECT 1')).scalar_one() == 1
        return {'status': 'ok', 'database': 'connected'}
    except SQLAlchemyError:
        return JSONResponse({'status': 'unavailable'}, 503)

@api.get('/auth/csrf')
def csrf(request: Request, response: Response, db: DB = Depends(get_db)):
    session = session_for(request, db)
    if session:
        token = secrets.token_urlsafe(32)
        session.csrf_hash = digest(token)
    else: token = new_session(response, db)
    db.commit()
    user = db.get(User, session.user_id) if session and session.user_id else None
    return {'csrf': token, 'user': public_user(user) if user and user.active else None}

def authenticate(response, request, db, user):
    old = session_for(request, db)
    if old: db.delete(old)
    token = new_session(response, db, user.id)
    db.commit()
    return {'user': public_user(user), 'csrf': token}

def auth_rate(request, db, identity):
    rate_limit(db, 'auth-account', identity, 10, 300)
    rate_limit(db, 'auth-address', request.client.host if request.client else 'unknown', 60, 300)

@api.post('/auth/signup', dependencies=unsafe, status_code=201)
def signup(data: s.Signup, request: Request, response: Response, db: DB = Depends(get_db)):
    if os.getenv('SIGNUP_ENABLED', 'true') != 'true': raise HTTPException(403, 'Sign-up is disabled for this workspace')
    auth_rate(request, db, data.email)
    user = User(name=data.name, email=data.email, password_hash=ph.hash(data.password), role='employee')
    db.add(user); db.flush()
    return authenticate(response, request, db, user)

@api.post('/auth/login', dependencies=unsafe)
def login(data: s.Credentials, request: Request, response: Response, db: DB = Depends(get_db)):
    auth_rate(request, db, data.email)
    user = db.scalar(select(User).where(User.email == data.email))
    valid = False
    try:
        # Run the same expensive algorithm for unknown users without storing a plaintext credential.
        if user: valid = ph.verify(user.password_hash, data.password)
        else: ph.hash(data.password)
    except (VerificationError, InvalidHashError): pass
    if not user or not valid or not user.active: raise HTTPException(401, 'Email or password is incorrect')
    return authenticate(response, request, db, user)

@api.post('/auth/demo', dependencies=unsafe)
def demo(data: s.Demo, request: Request, response: Response, db: DB = Depends(get_db)):
    if os.getenv('DEMO_ENABLED', 'false') != 'true': raise HTTPException(403, 'Demo sign-in is disabled')
    auth_rate(request, db, 'demo-'+data.role)
    user = db.scalar(select(User).where(User.role == data.role, User.demo.is_(True), User.active.is_(True)).order_by(User.id))
    if not user: raise HTTPException(503, 'Demo data has not been seeded')
    return authenticate(response, request, db, user)

@api.get('/auth/me')
def me(user: User = Depends(current_user)): return public_user(user)

@api.post('/auth/logout', dependencies=unsafe)
def logout(request: Request, response: Response, db: DB = Depends(get_db), user: User = Depends(current_user)):
    db.delete(session_for(request, db)); db.commit()
    response.delete_cookie(COOKIE, path='/')
    return {'ok': True}

@api.get('/categories')
def categories(user: User = Depends(current_user), db: DB = Depends(get_db)):
    query = select(Category).order_by(Category.id)
    if user.role != 'admin': query = query.where(Category.active.is_(True))
    return [{'id': c.id, 'name': c.name, 'active': c.active} for c in db.scalars(query)]

@api.post('/categories', dependencies=unsafe, status_code=201)
def create_category(data: s.CategoryInput, user: User = Depends(admin), db: DB = Depends(get_db)):
    item = Category(**data.model_dump()); db.add(item); db.commit()
    return {'id': item.id, 'name': item.name, 'active': item.active}

@api.put('/categories/{item_id}', dependencies=unsafe)
def edit_category(item_id: int, data: s.CategoryInput, user: User = Depends(admin), db: DB = Depends(get_db)):
    item = db.get(Category, item_id)
    if not item: raise HTTPException(404, 'Category not found')
    item.name, item.active = data.name, data.active; db.commit()
    return {'ok': True}

@api.get('/agents')
def agents(user: User = Depends(staff), db: DB = Depends(get_db)):
    return [{'id': u.id, 'name': u.name, 'role': u.role} for u in db.scalars(select(User).where(User.role.in_(['agent','admin']), User.active.is_(True)).order_by(User.name))]

@api.get('/users')
def users(user: User = Depends(admin), db: DB = Depends(get_db)):
    return [public_user(u) for u in db.scalars(select(User).order_by(User.id).limit(1000))]

@api.patch('/users/{user_id}', dependencies=unsafe)
def edit_user(user_id: int, data: s.UserPatch, user: User = Depends(admin), db: DB = Depends(get_db)):
    # Lock active admins as a set to prevent concurrent last-admin demotions.
    admins = db.scalars(select(User).where(User.role == 'admin', User.active.is_(True)).with_for_update()).all()
    target = db.get(User, user_id)
    if not target: raise HTTPException(404, 'User not found')
    if target.demo: raise HTTPException(409, 'Demo role identities are protected. Use a normal account for role changes.')
    if target in admins and len(admins) == 1 and (data.role != 'admin' or not data.active): raise HTTPException(409, 'Keep at least one active administrator')
    target.role, target.active = data.role, data.active
    db.execute(delete(Session).where(Session.user_id == target.id)); db.commit()
    return public_user(target)

@api.get('/sla-rules')
def sla_rules(user: User = Depends(current_user), db: DB = Depends(get_db)):
    return [{'priority': r.priority, 'response_minutes': r.response_minutes, 'resolution_minutes': r.resolution_minutes} for r in db.scalars(select(SLARule))]

@api.put('/sla-rules/{priority}', dependencies=unsafe)
def edit_sla(priority: s.Priority, data: s.SLAInput, user: User = Depends(admin), db: DB = Depends(get_db)):
    rule = db.get(SLARule, priority)
    if not rule: raise HTTPException(404, 'Rule not found')
    rule.response_minutes, rule.resolution_minutes = data.response_minutes, data.resolution_minutes
    db.commit(); return {'ok': True}

@api.get('/saved-replies')
def saved_replies(user: User = Depends(staff), db: DB = Depends(get_db)):
    return [{'id': r.id, 'title': r.title, 'body': r.body} for r in db.scalars(select(SavedReply).order_by(SavedReply.id))]

@api.post('/saved-replies', dependencies=unsafe, status_code=201)
def create_reply(data: s.ReplyInput, user: User = Depends(admin), db: DB = Depends(get_db)):
    item = SavedReply(**data.model_dump()); db.add(item); db.commit(); return {'id': item.id}

@api.put('/saved-replies/{item_id}', dependencies=unsafe)
def edit_reply(item_id: int, data: s.ReplyInput, user: User = Depends(admin), db: DB = Depends(get_db)):
    item = db.get(SavedReply, item_id)
    if not item: raise HTTPException(404, 'Reply not found')
    item.title, item.body = data.title, data.body; db.commit(); return {'ok': True}

@api.delete('/saved-replies/{item_id}', dependencies=unsafe)
def remove_reply(item_id: int, user: User = Depends(admin), db: DB = Depends(get_db)):
    item = db.get(SavedReply, item_id)
    if not item: raise HTTPException(404, 'Reply not found')
    db.delete(item); db.commit(); return {'ok': True}

@api.get('/tickets')
def tickets(user: User = Depends(current_user), db: DB = Depends(get_db), q: str = Query('', max_length=160), status: s.Status | None = None, priority: s.Priority | None = None, category_id: int | None = Query(None, gt=0), assignee_id: int | None = Query(None, ge=0), sla: str | None = Query(None, pattern='^(On track|At risk|Breached)$'), sort: str = Query('newest', pattern='^(newest|oldest|priority|due)$'), page: int = Query(1, ge=1), page_size: int = Query(12, ge=1, le=50)):
    query = ticket_query(user)
    if q:
        if re.fullmatch(r'TD-\d+', q.upper()): query = query.where(Ticket.id == int(q[3:])-1000)
        else: query = query.where(Ticket.title.ilike('%'+q.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%', escape='\\'))
    for field, value in [('status',status),('priority',priority),('category_id',category_id)]:
        if value is not None: query = query.where(getattr(Ticket,field) == value)
    if assignee_id is not None: query = query.where(Ticket.assignee_id == (assignee_id or None))
    if sla: query = query.where(sla_expression() == sla)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    ordering = {'newest': Ticket.created_at.desc(), 'oldest': Ticket.created_at.asc(), 'due': Ticket.resolution_due.asc(), 'priority': case((Ticket.priority=='Urgent',0),(Ticket.priority=='High',1),(Ticket.priority=='Medium',2),else_=3)}[sort]
    rows = db.scalars(query.order_by(ordering, Ticket.id.desc()).offset((page-1)*page_size).limit(page_size)).all()
    return {'items': [ticket_json(t,db) for t in rows], 'total': total, 'page': page, 'page_size': page_size}

@api.post('/tickets', dependencies=unsafe, status_code=201)
def create_ticket(data: s.TicketCreate, user: User = Depends(current_user), db: DB = Depends(get_db)):
    rate_limit(db, 'create-ticket', str(user.id), 10, 60)
    category = db.get(Category, data.category_id)
    if not category or not category.active: raise HTTPException(422, 'Choose an active category')
    rule = db.get(SLARule, data.priority)
    if not rule: raise HTTPException(503, 'SLA rules are not configured')
    now = time.time()
    ticket = Ticket(**data.model_dump(), requester_id=user.id, status='Open', created_at=now, updated_at=now, response_target=rule.response_minutes*60, resolution_target=rule.resolution_minutes*60, response_due=now+rule.response_minutes*60, resolution_due=now+rule.resolution_minutes*60)
    db.add(ticket); db.flush(); history(db,ticket,user,'created',new='Open'); db.commit()
    return ticket_json(ticket,db)

@api.post('/tickets/bulk-assign', dependencies=unsafe)
def bulk_assign(data: s.BulkAssign, user: User = Depends(staff), db: DB = Depends(get_db)):
    rows = [get_ticket(db,user,i,True) for i in sorted(data.ticket_ids)]
    for ticket in rows: patch_ticket(db,ticket,user,{'assignee_id':data.assignee_id})
    db.commit(); return {'updated': len(rows)}

@api.get('/tickets/{ticket_id}')
def detail(ticket_id: int, user: User = Depends(current_user), db: DB = Depends(get_db)):
    ticket = get_ticket(db,user,ticket_id)
    metadata = db.execute(select(Attachment.id, Attachment.filename, Attachment.mime, Attachment.size).where(Attachment.ticket_id==ticket_id)).mappings().first()
    rating = db.scalar(select(Rating).where(Rating.ticket_id==ticket_id))
    return {**ticket_json(ticket,db), 'attachment': dict(metadata) if metadata else None, 'rating': {'stars':rating.stars,'comment':rating.comment} if rating else None}

@api.patch('/tickets/{ticket_id}', dependencies=unsafe)
def edit_ticket(ticket_id: int, data: s.TicketPatch, user: User = Depends(current_user), db: DB = Depends(get_db)):
    ticket = get_ticket(db,user,ticket_id,True)
    patch_ticket(db,ticket,user,data.model_dump(exclude_unset=True)); db.commit()
    return ticket_json(ticket,db)

@api.get('/tickets/{ticket_id}/comments')
def comments(ticket_id: int, user: User = Depends(current_user), db: DB = Depends(get_db)):
    get_ticket(db,user,ticket_id)
    query = select(Comment,User.name).join(User,Comment.author_id==User.id).where(Comment.ticket_id==ticket_id)
    if user.role == 'employee': query = query.where(Comment.internal.is_(False))
    return [{'id': c.id,'body':c.body,'internal':c.internal,'author':name,'created_at':c.created_at} for c,name in db.execute(query.order_by(Comment.created_at,Comment.id))]

@api.post('/tickets/{ticket_id}/comments', dependencies=unsafe, status_code=201)
def add_comment(ticket_id: int, data: s.CommentCreate, user: User = Depends(current_user), db: DB = Depends(get_db)):
    ticket = get_ticket(db,user,ticket_id,True)
    if data.internal and user.role == 'employee': raise HTTPException(403, 'Internal notes are for support staff')
    if ticket.status == 'Closed': raise HTTPException(409, 'Reopen this ticket before replying')
    now = time.time()
    item = Comment(ticket_id=ticket_id, author_id=user.id, **data.model_dump(), created_at=now)
    db.add(item)
    if user.role in ('agent','admin') and not data.internal and ticket.first_response_at is None:
        pause = effective_pause(ticket,now)
        ticket.response_due += pause
        ticket.first_response_at = now
        ticket.first_response_seconds = max(0,now-ticket.created_at-ticket.paused_seconds-pause)
        history(db,ticket,user,'first_response',new='Recorded')
    history(db,ticket,user,'internal_note' if data.internal else 'reply',new='Added',internal=data.internal)
    if not data.internal: notify(db,ticket,user,'New reply')
    ticket.updated_at = now
    db.commit(); return {'id': item.id}

@api.get('/tickets/{ticket_id}/history')
def ticket_history(ticket_id: int, user: User = Depends(current_user), db: DB = Depends(get_db)):
    get_ticket(db,user,ticket_id)
    query = select(History,User.name).join(User,History.actor_id==User.id).where(History.ticket_id==ticket_id)
    if user.role == 'employee': query = query.where(History.internal.is_(False))
    return [{'id':h.id,'actor':name,'field':h.field,'old':h.old,'new':h.new,'created_at':h.created_at} for h,name in db.execute(query.order_by(History.created_at,History.id))]

@api.post('/tickets/{ticket_id}/attachments', dependencies=unsafe, status_code=201)
async def upload(ticket_id: int, request: Request, file: UploadFile = File(...), user: User = Depends(current_user), db: DB = Depends(get_db)):
    ticket = get_ticket(db,user,ticket_id,True)
    form = await request.form()
    if len(form.multi_items()) != 1 or form.multi_items()[0][0] != 'file':
        raise HTTPException(422, 'Upload exactly one file and no additional fields')
    if db.scalar(select(Attachment.id).where(Attachment.ticket_id==ticket_id)): raise HTTPException(409, 'One attachment per ticket is allowed')
    blob = await file.read(1048577)
    await file.close()
    if not blob or len(blob)>1048576: raise HTTPException(413, 'Choose one non-empty file of at most 1 MB')
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', (file.filename or 'attachment').replace('\\','/').split('/')[-1])[-120:]
    extension = filename.rsplit('.',1)[-1].lower()
    allowed = {'png':'image/png','jpg':'image/jpeg','jpeg':'image/jpeg','webp':'image/webp','pdf':'application/pdf'}
    signature = (extension=='png' and blob.startswith(b'\x89PNG\r\n\x1a\n')) or (extension in ('jpg','jpeg') and blob.startswith(b'\xff\xd8\xff')) or (extension=='webp' and blob.startswith(b'RIFF') and blob[8:12]==b'WEBP') or (extension=='pdf' and blob.startswith(b'%PDF-'))
    if extension not in allowed or file.content_type != allowed[extension] or not signature:
        raise HTTPException(422, 'Only matching PNG, JPEG, WebP or PDF files are allowed')
    item = Attachment(ticket_id=ticket_id,author_id=user.id,filename=filename,mime=file.content_type,data=blob,size=len(blob))
    db.add(item); history(db,ticket,user,'attachment',new='Added'); ticket.updated_at=time.time(); db.commit()
    return {'id':item.id,'filename':filename}

@api.get('/tickets/{ticket_id}/attachments/{attachment_id}')
def download(ticket_id: int, attachment_id: int, user: User = Depends(current_user), db: DB = Depends(get_db)):
    get_ticket(db,user,ticket_id)
    item = db.scalar(select(Attachment).where(Attachment.id==attachment_id, Attachment.ticket_id==ticket_id))
    if not item: raise HTTPException(404, 'Attachment not found')
    return Response(item.data, media_type=item.mime, headers={'Content-Disposition':f'attachment; filename="{item.filename}"','Content-Security-Policy':"sandbox; default-src 'none'",'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'})

@api.post('/tickets/{ticket_id}/rating', dependencies=unsafe, status_code=201)
def rate_ticket(ticket_id: int, data: s.RatingCreate, user: User = Depends(current_user), db: DB = Depends(get_db)):
    ticket = get_ticket(db,user,ticket_id,True)
    if ticket.requester_id != user.id: raise HTTPException(403, 'Only the requester may rate support')
    if ticket.status not in TERMINAL: raise HTTPException(409, 'Rate support after resolution')
    if db.scalar(select(Rating.id).where(Rating.ticket_id==ticket_id)): raise HTTPException(409, 'This ticket has already been rated')
    db.add(Rating(ticket_id=ticket_id,author_id=user.id,**data.model_dump())); history(db,ticket,user,'rating',new=str(data.stars)); db.commit(); return {'ok':True}

@api.get('/notifications')
def notifications(user: User = Depends(current_user), db: DB = Depends(get_db)):
    rows = db.scalars(select(Notification).where(Notification.user_id==user.id).order_by(Notification.created_at.desc()).limit(50))
    count = db.scalar(select(func.count()).select_from(Notification).where(Notification.user_id==user.id,Notification.read_at.is_(None)))
    return {'unread':count,'items':[{'id':n.id,'ticket_id':n.ticket_id,'number':f'TD-{1000+n.ticket_id}','kind':n.kind,'read':n.read_at is not None,'created_at':n.created_at} for n in rows]}

@api.post('/notifications/{item_id}/read', dependencies=unsafe)
def read_notification(item_id: int, user: User = Depends(current_user), db: DB = Depends(get_db)):
    item = db.scalar(select(Notification).where(Notification.id==item_id,Notification.user_id==user.id))
    if not item: raise HTTPException(404, 'Notification not found')
    item.read_at=time.time(); db.commit(); return {'ok':True}

app.include_router(api)
from .reports import router as reports_router
app.include_router(reports_router)
