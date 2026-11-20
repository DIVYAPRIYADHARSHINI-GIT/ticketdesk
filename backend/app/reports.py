import csv
import io
import time
from datetime import datetime, timezone, timedelta, date
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select, func, case, Integer, and_
from sqlalchemy.orm import Session
from .db import get_db
from .models import Ticket, Category, User, Rating
from .security import admin
from .domain import TERMINAL

router = APIRouter(prefix='/api/reports')

def bounds(start: date | None, end: date | None):
    today = datetime.now(timezone.utc).date()
    start, end = start or today-timedelta(days=29), end or today
    if start > end or (end-start).days > 366: raise HTTPException(422, 'Choose a date range of up to 367 days')
    return datetime.combine(start,datetime.min.time(),timezone.utc).timestamp(), datetime.combine(end+timedelta(days=1),datetime.min.time(),timezone.utc).timestamp()

def aggregate(db, start, end):
    lo, hi = bounds(start,end)
    where = (Ticket.created_at>=lo, Ticket.created_at<hi)
    completed = Ticket.resolved_at.is_not(None)
    compliant = and_(completed, Ticket.resolved_at<=Ticket.resolution_due, case((Ticket.first_response_at.is_not(None), Ticket.first_response_at),else_=Ticket.resolved_at)<=Ticket.response_due)
    summary = db.execute(select(func.count(Ticket.id).label('total'),
        func.sum(case((Ticket.status.not_in(TERMINAL),1),else_=0)).label('open'),
        func.sum(case((Ticket.status.in_(TERMINAL),1),else_=0)).label('closed'),
        func.avg(Ticket.first_response_seconds).label('avg_first_response_seconds'),
        func.avg(Ticket.resolution_seconds).label('avg_resolution_seconds'),
        func.sum(case((completed,1),else_=0)).label('completed'),
        func.sum(case((compliant,1),else_=0)).label('compliant')).where(*where)).mappings().one()
    result = dict(summary)
    for key in ('total','open','closed','completed','compliant'): result[key] = result[key] or 0
    result['sla_compliance'] = round(100*result['compliant']/result['completed'],1) if result['completed'] else None
    def grouped(column, join=None):
        q = select(column.label('name'),func.count(Ticket.id).label('count')).select_from(Ticket)
        if join is not None: q = q.join(join)
        return [dict(r) for r in db.execute(q.where(*where).group_by(column).order_by(column)).mappings()]
    result['by_status'] = grouped(Ticket.status)
    result['by_priority'] = grouped(Ticket.priority)
    result['by_category'] = grouped(Category.name,Category)
    # Day number is portable between PostgreSQL and SQLite; only aggregate rows leave SQL.
    day = func.floor(Ticket.created_at/86400).cast(Integer)
    result['over_time'] = [{'name':datetime.fromtimestamp(d*86400,timezone.utc).date().isoformat(),'count':count} for d,count in db.execute(select(day,func.count(Ticket.id)).where(*where).group_by(day).order_by(day))]
    workload = select(User.name.label('name'),func.count(Ticket.id).label('count')).select_from(User).outerjoin(Ticket,and_(Ticket.assignee_id==User.id,Ticket.status.not_in(TERMINAL),*where)).where(User.role.in_(['agent','admin']),User.active.is_(True)).group_by(User.id,User.name).order_by(User.name)
    result['workload'] = [dict(r) for r in db.execute(workload).mappings()]
    result['satisfaction'] = db.scalar(select(func.avg(Rating.stars)).join(Ticket,Rating.ticket_id==Ticket.id).where(*where))
    result['rating_count'] = db.scalar(select(func.count(Rating.id)).join(Ticket,Rating.ticket_id==Ticket.id).where(*where))
    result['from'] = datetime.fromtimestamp(lo,timezone.utc).date().isoformat()
    result['to'] = datetime.fromtimestamp(hi-1,timezone.utc).date().isoformat()
    return result

@router.get('')
def reports(start: date | None = None, end: date | None = None, user: User = Depends(admin), db: Session = Depends(get_db)):
    return aggregate(db,start,end)

def safe_cell(value):
    text = '' if value is None else str(value)
    # Includes leading whitespace/control characters that spreadsheet software can discard.
    if text.lstrip().startswith(('=','+','-','@')) or text.startswith(('\t','\r','\n')): return "'"+text
    return text

@router.get('/export.csv')
def export(start: date | None = None, end: date | None = None, user: User = Depends(admin), db: Session = Depends(get_db)):
    data = aggregate(db,start,end)
    output = io.StringIO(newline='')
    writer = csv.writer(output)
    writer.writerow(['Section','Metric','Value'])
    for key,value in data.items():
        if isinstance(value,list):
            for row in value: writer.writerow([safe_cell(key),safe_cell(row['name']),safe_cell(row['count'])])
        else: writer.writerow(['Summary',safe_cell(key),safe_cell(value)])
    return Response('\ufeff'+output.getvalue(),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename="ticketdesk-report.csv"','X-Content-Type-Options':'nosniff'})
