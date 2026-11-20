import time
from fastapi import HTTPException
from sqlalchemy import and_, case, or_, select
from .models import Ticket, History, Notification, User

TERMINAL = ('Resolved', 'Closed')
TRANSITIONS = {
    'Open': {'In progress', 'Waiting for requester', 'Resolved', 'Closed'},
    'In progress': {'Waiting for requester', 'Resolved', 'Closed'},
    'Waiting for requester': {'In progress', 'Resolved', 'Closed'},
    'Resolved': {'Closed', 'Reopened'}, 'Closed': {'Reopened'},
    'Reopened': {'In progress', 'Waiting for requester', 'Resolved', 'Closed'},
}

def ticket_query(user):
    query = select(Ticket)
    return query.where(Ticket.requester_id == user.id) if user.role == 'employee' else query

def get_ticket(db, user, ticket_id, lock=False):
    query = ticket_query(user).where(Ticket.id == ticket_id)
    if lock: query = query.with_for_update()
    ticket = db.scalar(query)
    if not ticket: raise HTTPException(404, 'Ticket not found')
    return ticket

def history(db, ticket, actor, field, old='', new='', internal=False, now=None):
    db.add(History(ticket_id=ticket.id, actor_id=actor.id, field=field, old=str(old or '')[:200], new=str(new or '')[:200], internal=internal, created_at=now or time.time()))

def notify(db, ticket, actor, kind, recipients=None):
    for recipient in set(recipients if recipients is not None else [ticket.requester_id, ticket.assignee_id]):
        if recipient and recipient != actor.id:
            db.add(Notification(user_id=recipient, ticket_id=ticket.id, kind=kind))

def effective_pause(ticket, now):
    return max(0, now-ticket.waiting_since) if ticket.waiting_since is not None else 0

def sla_state(ticket, now=None):
    now = time.time() if now is None else now
    pause = effective_pause(ticket, now)
    r_end = ticket.first_response_at if ticket.first_response_at is not None else (ticket.resolved_at or now)
    s_end = ticket.resolved_at or now
    r_due = ticket.response_due + (pause if ticket.first_response_at is None else 0)
    s_due = ticket.resolution_due + (pause if ticket.resolved_at is None else 0)
    if r_end > r_due or s_end > s_due: return 'Breached'
    if (ticket.first_response_at is None and ticket.resolved_at is None and now >= r_due-ticket.response_target*.2) or (ticket.resolved_at is None and now >= s_due-ticket.resolution_target*.2):
        return 'At risk'
    return 'On track'

def sla_expression(now=None):
    now = time.time() if now is None else now
    pause = case((Ticket.waiting_since.is_not(None), now-Ticket.waiting_since), else_=0)
    r_due = Ticket.response_due + case((Ticket.first_response_at.is_(None), pause), else_=0)
    s_due = Ticket.resolution_due + case((Ticket.resolved_at.is_(None), pause), else_=0)
    r_end = case((Ticket.first_response_at.is_not(None), Ticket.first_response_at), (Ticket.resolved_at.is_not(None), Ticket.resolved_at), else_=now)
    s_end = case((Ticket.resolved_at.is_not(None), Ticket.resolved_at), else_=now)
    return case((or_(r_end > r_due, s_end > s_due), 'Breached'), (or_(and_(Ticket.first_response_at.is_(None), Ticket.resolved_at.is_(None), now >= r_due-Ticket.response_target*.2), and_(Ticket.resolved_at.is_(None), now >= s_due-Ticket.resolution_target*.2)), 'At risk'), else_='On track')

def validate_assignee(db, assignee):
    if assignee is None: return
    user = db.get(User, assignee)
    if not user or not user.active or user.role not in ('agent', 'admin'):
        raise HTTPException(422, 'Choose an active agent or administrator')

def patch_ticket(db, ticket, actor, values, now=None):
    now = time.time() if now is None else now
    if actor.role == 'employee':
        if set(values) != {'status'} or values['status'] not in ('Closed', 'Reopened'):
            raise HTTPException(403, 'Employees may only close or reopen their own ticket')
    if 'assignee_id' in values: validate_assignee(db, values['assignee_id'])
    status = values.get('status')
    if status and status != ticket.status and status not in TRANSITIONS[ticket.status]:
        raise HTTPException(409, 'This status transition is not allowed')
    for field, value in values.items():
        old = getattr(ticket, field)
        if value == old: continue
        if field == 'status':
            if ticket.waiting_since is not None:
                pause = max(0, now-ticket.waiting_since)
                ticket.paused_seconds += pause
                if ticket.first_response_at is None: ticket.response_due += pause
                ticket.resolution_due += pause
                ticket.waiting_since = None
            if old in TERMINAL and value == 'Reopened':
                frozen = max(0, now-(ticket.resolved_at or now))
                ticket.paused_seconds += frozen
                ticket.resolution_due += frozen
                if ticket.first_response_at is None: ticket.response_due += frozen
                ticket.resolved_at = None
                ticket.resolution_seconds = None
            if value == 'Waiting for requester': ticket.waiting_since = now
            if value in TERMINAL and old not in TERMINAL:
                ticket.resolved_at = now
                ticket.resolution_seconds = max(0, now-ticket.created_at-ticket.paused_seconds)
            notify(db, ticket, actor, 'Status changed')
        setattr(ticket, field, value)
        history(db, ticket, actor, field, old, value, now=now)
        if field == 'assignee_id': notify(db, ticket, actor, 'Assigned to you', [value])
    ticket.updated_at = now

def ticket_json(ticket, db):
    from .models import Category
    requester = db.get(User, ticket.requester_id)
    assignee = db.get(User, ticket.assignee_id) if ticket.assignee_id else None
    category = db.get(Category, ticket.category_id)
    pause = effective_pause(ticket, time.time())
    return {**{field: getattr(ticket, field) for field in ('id','title','description','category_id','requester_id','assignee_id','priority','status','created_at','updated_at','first_response_at','resolved_at','waiting_since','paused_seconds','response_target','resolution_target')},
        'number': f'TD-{1000+ticket.id}', 'requester': requester.name, 'assignee': assignee.name if assignee else None,
        'category': category.name, 'sla': sla_state(ticket),
        'response_due': ticket.response_due+(pause if ticket.first_response_at is None else 0),
        'resolution_due': ticket.resolution_due+(pause if ticket.resolved_at is None else 0)}
