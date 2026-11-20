import asyncio
import time
from sqlalchemy import select, func
from app.models import Ticket, User, History
from app.domain import patch_ticket, sla_state, sla_expression
from app.middleware import BoundedBody
from app.db import get_db
from app.main import app
from sqlalchemy.exc import OperationalError
from test_api import create


def test_rejects_multiple_files(ctx,payload):
    c,tid=create(ctx,payload)
    files=[('file',('a.pdf',b'%PDF-1','application/pdf')),('file',('b.pdf',b'%PDF-2','application/pdf'))]
    assert c.post(f'/api/tickets/{tid}/attachments',files=files).status_code==422

def test_accepts_exactly_one_mebibyte(ctx,payload):
    c,tid=create(ctx,payload)
    data=b'%PDF-'+b'x'*(1048576-5)
    assert c.post(f'/api/tickets/{tid}/attachments',files={'file':('edge.pdf',data,'application/pdf')}).status_code==201

def test_chunked_limit_before_parser():
    reached=[]; output=[]
    async def endpoint(scope,receive,send): reached.append(True)
    messages=iter([{'type':'http.request','body':b'x'*600000,'more_body':True},{'type':'http.request','body':b'x'*600000,'more_body':False}])
    async def receive(): return next(messages)
    async def send(message): output.append(message)
    asyncio.run(BoundedBody(endpoint)({'type':'http','method':'POST'},receive,send))
    assert not reached and output[0]['status']==413

def test_response_during_pause_does_not_double_shift(ctx,payload):
    _,tid=create(ctx,payload)
    with ctx[0]() as db:
        t=db.get(Ticket,tid); now=time.time(); t.created_at=now-600; t.response_due=now+3000; t.resolution_due=now+13800; t.status='Waiting for requester'; t.waiting_since=now-300; db.commit()
    agent=ctx[1](3)
    assert agent.post(f'/api/tickets/{tid}/comments',json={'body':'TEST public reply while waiting'}).status_code==201
    with ctx[0]() as db:
        t=db.get(Ticket,tid); due=t.response_due; agent_user=db.get(User,3)
        patch_ticket(db,t,agent_user,{'status':'In progress'},now=t.waiting_since+900)
        assert t.response_due==due
        assert 299<t.first_response_seconds<305

def test_sql_and_python_sla_agree(ctx,payload):
    _,tid=create(ctx,payload)
    with ctx[0]() as db:
        t=db.get(Ticket,tid); t.created_at=1000; t.response_due=4600; t.resolution_due=15400
        for stamp in [1100,3900,4500,4601,16000]:
            db.flush()
            assert sla_state(t,stamp)==db.scalar(select(sla_expression(stamp)).where(Ticket.id==tid))

def test_priority_changes_keep_sla_snapshot(ctx,payload):
    c,tid=create(ctx,payload); before=c.get(f'/api/tickets/{tid}').json()
    ctx[1](3).patch(f'/api/tickets/{tid}',json={'priority':'Urgent'})
    after=c.get(f'/api/tickets/{tid}').json()
    assert before['response_due']==after['response_due'] and before['resolution_target']==after['resolution_target']

def test_noop_change_creates_no_false_history(ctx,payload):
    c,tid=create(ctx,payload)
    agent=ctx[1](3); agent.patch(f'/api/tickets/{tid}',json={'status':'Open'})
    assert len(c.get(f'/api/tickets/{tid}/history').json())==1

def test_report_utc_day_does_not_round_at_noon(ctx,payload):
    from datetime import datetime, timezone
    _,tid=create(ctx,payload)
    with ctx[0]() as db:
        db.get(Ticket,tid).created_at=datetime(2026,11,10,23,59,tzinfo=timezone.utc).timestamp()
        db.commit()
    data=ctx[1](5).get('/api/reports?start=2026-11-10&end=2026-11-11').json()
    assert data['over_time']==[{'name':'2026-11-10','count':1}]

def test_health_database_failure_is_503(ctx):
    client=ctx[1]()
    class BrokenDB:
        def execute(self,*args): raise OperationalError('SELECT 1',{},Exception('TEST connection unavailable'))
    def broken(): yield BrokenDB()
    app.dependency_overrides[get_db]=broken
    assert client.get('/health').status_code==503
