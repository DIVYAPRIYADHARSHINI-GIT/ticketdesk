import csv
import io
import secrets
import time
import pytest
from sqlalchemy import select, func
from app.models import Ticket, Comment, History, Notification, User, Rating, Category, SavedReply
from app.domain import TRANSITIONS, patch_ticket, sla_state, sla_expression
from app.reports import safe_cell
from app.security import COOKIE


def create(ctx,payload,user=1):
    factory,client=ctx; c=client(user); r=c.post('/api/tickets',json=payload); assert r.status_code==201
    return c,r.json()['id']

@pytest.mark.parametrize('suffix', ['', '/comments','/history','/attachments/1'])
def test_employee_cannot_read_other_ticket(ctx,payload,suffix):
    owner,tid=create(ctx,payload)
    attacker=ctx[1](2)
    assert attacker.get(f'/api/tickets/{tid}{suffix}').status_code==404
    assert attacker.get('/api/tickets').json()['total']==0

@pytest.mark.parametrize('method,suffix,data', [('patch','',{'status':'Closed'}),('post','/comments',{'body':'not allowed'}),('post','/rating',{'stars':5})])
def test_employee_cannot_mutate_other_ticket(ctx,payload,method,suffix,data):
    _,tid=create(ctx,payload)
    assert getattr(ctx[1](2),method)(f'/api/tickets/{tid}{suffix}',json=data).status_code==404

def test_employee_cannot_upload_to_other_ticket(ctx,payload):
    _,tid=create(ctx,payload)
    assert ctx[1](2).post(f'/api/tickets/{tid}/attachments',files={'file':('test.pdf',b'%PDF-1.4','application/pdf')}).status_code==404

@pytest.mark.parametrize('values',[{'priority':'Urgent'},{'assignee_id':3},{'status':'Resolved'},{'status':'In progress'},{'status':'Closed','priority':'Low'}])
def test_employee_control_restrictions(ctx,payload,values):
    c,tid=create(ctx,payload)
    assert c.patch(f'/api/tickets/{tid}',json=values).status_code==403

def test_internal_note_never_leaks(ctx,payload):
    employee,tid=create(ctx,payload)
    agent=ctx[1](3)
    assert agent.post(f'/api/tickets/{tid}/comments',json={'body':'TEST internal confidential marker','internal':True}).status_code==201
    assert employee.get(f'/api/tickets/{tid}/comments').json()==[]
    assert all(h['field']!='internal_note' for h in employee.get(f'/api/tickets/{tid}/history').json())
    assert employee.get('/api/notifications').json()['unread']==0
    assert agent.get(f'/api/tickets/{tid}/comments').json()[0]['internal']
    assert employee.post(f'/api/tickets/{tid}/comments',json={'body':'TEST internal','internal':True}).status_code==403
    assert employee.get(f'/api/tickets/{tid}').json()['first_response_at'] is None

@pytest.mark.parametrize('user',[1,3])
@pytest.mark.parametrize('method,path,data',[
 ('get','/users',None),('patch','/users/2',{'role':'agent'}),('post','/categories',{'name':'New'}),('put','/categories/1',{'name':'Changed'}),
 ('put','/sla-rules/Low',{'response_minutes':5,'resolution_minutes':10}),('post','/saved-replies',{'title':'Hello','body':'Help'}),
 ('put','/saved-replies/1',{'title':'Hello','body':'Help'}),('delete','/saved-replies/1',None),('get','/reports',None),('get','/reports/export.csv',None)])
def test_admin_only_endpoints(ctx,user,method,path,data):
    kwargs={'json':data} if data is not None else {}
    assert getattr(ctx[1](user),method)('/api'+path,**kwargs).status_code==403

@pytest.mark.parametrize('path',['/agents','/saved-replies'])
def test_staff_read_restricted(ctx,path): assert ctx[1](1).get('/api'+path).status_code==403

@pytest.mark.parametrize('user',[3,5])
def test_staff_queue_controls_saved_replies_and_history(ctx,payload,user):
    _,tid=create(ctx,payload); staff=ctx[1](user)
    assert staff.get('/api/tickets').json()['total']==1
    assert staff.get('/api/agents').status_code==200
    assert staff.get('/api/saved-replies').status_code==200
    assert staff.patch(f'/api/tickets/{tid}',json={'assignee_id':4,'priority':'High','status':'In progress'}).status_code==200
    history=staff.get(f'/api/tickets/{tid}/history').json()
    assert {h['field'] for h in history} >= {'created','assignee_id','priority','status'}
    assert all(h['actor'] and h['created_at'] for h in history)
    assert ctx[1](4).get('/api/notifications').json()['unread']==1

def test_admin_management(ctx):
    c=ctx[1](5)
    assert c.get('/api/users').status_code==200
    assert c.patch('/api/users/2',json={'role':'agent','active':True}).status_code==200
    assert c.patch('/api/users/5',json={'role':'employee'}).status_code==409
    r=c.post('/api/categories',json={'name':'TEST category'}); assert r.status_code==201
    assert c.put(f"/api/categories/{r.json()['id']}",json={'name':'TEST archived','active':False}).status_code==200
    assert c.put('/api/sla-rules/Low',json={'response_minutes':30,'resolution_minutes':60}).status_code==200
    r=c.post('/api/saved-replies',json={'title':'TEST reply','body':'TEST assistance'}); assert r.status_code==201
    assert c.put(f"/api/saved-replies/{r.json()['id']}",json={'title':'TEST revised','body':'Updated'}).status_code==200
    assert c.delete(f"/api/saved-replies/{r.json()['id']}").status_code==200

@pytest.mark.parametrize('old',list(TRANSITIONS))
@pytest.mark.parametrize('new',list(TRANSITIONS))
def test_status_graph(ctx,payload,old,new):
    _,tid=create(ctx,payload)
    with ctx[0]() as db:
        ticket=db.get(Ticket,tid); ticket.status=old
        if old in ('Resolved','Closed'): ticket.resolved_at=time.time()-50
        if old=='Waiting for requester': ticket.waiting_since=time.time()-50
        db.commit()
    result=ctx[1](3).patch(f'/api/tickets/{tid}',json={'status':new})
    assert result.status_code==(200 if new==old or new in TRANSITIONS[old] else 409)

def test_sla_pause_response_and_resolution(ctx,payload):
    _,tid=create(ctx,payload)
    with ctx[0]() as db:
        ticket=db.get(Ticket,tid); agent=db.get(User,3)
        ticket.created_at=1000; ticket.response_due=4600; ticket.resolution_due=15400
        patch_ticket(db,ticket,agent,{'status':'Waiting for requester'},now=1600)
        assert sla_state(ticket,10000)=='On track'
        assert db.scalar(select(sla_expression(10000)).where(Ticket.id==tid))=='On track'
        patch_ticket(db,ticket,agent,{'status':'In progress'},now=10600)
        assert ticket.response_due==13600 and ticket.resolution_due==24400
        assert ticket.paused_seconds==9000
        assert sla_state(ticket,13000)=='At risk'
        assert sla_state(ticket,14000)=='Breached'
        patch_ticket(db,ticket,agent,{'status':'Resolved'},now=12000)
        assert ticket.resolution_seconds==2000
        patch_ticket(db,ticket,agent,{'status':'Reopened'},now=22000)
        assert ticket.resolved_at is None and ticket.resolution_due==34400

def test_first_response_is_public_only_and_once(ctx,payload):
    employee,tid=create(ctx,payload); c=ctx[1](3)
    c.post(f'/api/tickets/{tid}/comments',json={'body':'Internal','internal':True})
    assert c.get(f'/api/tickets/{tid}').json()['first_response_at'] is None
    c.post(f'/api/tickets/{tid}/comments',json={'body':'Public response'})
    first=c.get(f'/api/tickets/{tid}').json()['first_response_at']
    c.post(f'/api/tickets/{tid}/comments',json={'body':'Another response'})
    assert c.get(f'/api/tickets/{tid}').json()['first_response_at']==first
    notification=employee.get('/api/notifications').json()
    assert notification['unread']==2
    assert ctx[1](2).post(f"/api/notifications/{notification['items'][0]['id']}/read").status_code==404
    assert employee.post(f"/api/notifications/{notification['items'][0]['id']}/read").status_code==200
    assert employee.get('/api/notifications').json()['unread']==1

def test_employee_close_reopen_rate(ctx,payload):
    c,tid=create(ctx,payload)
    assert c.post(f'/api/tickets/{tid}/rating',json={'stars':5}).status_code==409
    assert c.patch(f'/api/tickets/{tid}',json={'status':'Closed'}).status_code==200
    assert c.patch(f'/api/tickets/{tid}',json={'status':'Reopened'}).status_code==200
    ctx[1](3).patch(f'/api/tickets/{tid}',json={'status':'Resolved'})
    assert ctx[1](3).post(f'/api/tickets/{tid}/rating',json={'stars':5}).status_code==403
    assert c.post(f'/api/tickets/{tid}/rating',json={'stars':5,'comment':'TEST helpful'}).status_code==201
    assert c.post(f'/api/tickets/{tid}/rating',json={'stars':4}).status_code==409

@pytest.mark.parametrize('filename,mime,blob,status',[
 ('ok.png','image/png',b'\x89PNG\r\n\x1a\nbytes',201),('ok.jpg','image/jpeg',b'\xff\xd8\xffbytes',201),
 ('ok.webp','image/webp',b'RIFF0000WEBPbytes',201),('ok.pdf','application/pdf',b'%PDF-1.4',201),
 ('bad.svg','image/svg+xml',b'<svg/>',422),('bad.pdf','image/png',b'%PDF-1.4',422),
 ('bad.png','image/png',b'<script>bad</script>',422),('bad.exe','application/pdf',b'%PDF-1.4',422),
 ('empty.pdf','application/pdf',b'',413),('big.pdf','application/pdf',b'%PDF-'+b'a'*1048572,413)])
def test_attachment_types_and_limits(ctx,payload,filename,mime,blob,status):
    c,tid=create(ctx,payload)
    r=c.post(f'/api/tickets/{tid}/attachments',files={'file':(filename,blob,mime)})
    assert r.status_code==status
    if status==201:
        get=c.get(f"/api/tickets/{tid}/attachments/{r.json()['id']}")
        assert get.content==blob and get.headers['x-content-type-options']=='nosniff'
        assert get.headers['content-disposition'].startswith('attachment;')
        assert 'sandbox' in get.headers['content-security-policy']
        assert c.post(f'/api/tickets/{tid}/attachments',files={'file':(filename,blob,mime)}).status_code==409

def test_bulk_assignment_atomic_and_restricted(ctx,payload):
    c,tid=create(ctx,payload); agent=ctx[1](3)
    assert c.post('/api/tickets/bulk-assign',json={'ticket_ids':[tid],'assignee_id':3}).status_code==403
    assert agent.post('/api/tickets/bulk-assign',json={'ticket_ids':[tid,9999],'assignee_id':3}).status_code==404
    assert agent.get(f'/api/tickets/{tid}').json()['assignee_id'] is None
    assert agent.post('/api/tickets/bulk-assign',json={'ticket_ids':[tid],'assignee_id':1}).status_code==422
    assert agent.post('/api/tickets/bulk-assign',json={'ticket_ids':[tid],'assignee_id':3}).json()=={'updated':1}

def test_queue_search_filters_sort_pagination(ctx,payload):
    c,tid=create(ctx,payload)
    c.post('/api/tickets',json={**payload,'title':'TEST a second request','priority':'Urgent'})
    agent=ctx[1](3)
    assert agent.get('/api/tickets?q=TD-'+str(1000+tid)).json()['total']==1
    assert agent.get('/api/tickets?q=%25').json()['total']==0
    assert agent.get('/api/tickets?priority=Urgent&status=Open&category_id=1&assignee_id=0&sla=On%20track').json()['total']==1
    assert len(agent.get('/api/tickets?page_size=1&page=2&sort=priority').json()['items'])==1
    assert agent.get('/api/tickets?page=0').status_code==422

def test_csrf_cookie_and_auth(ctx,credential):
    c=ctx[1]()
    assert c.get('/api/auth/me').status_code==401
    c.headers.pop('X-CSRF-Token')
    assert c.post('/api/auth/login',json={'email':'test1@example.invalid','password':credential[0]}).status_code==403
    token=c.get('/api/auth/csrf').json()['csrf']; c.headers['X-CSRF-Token']=token
    c.headers['Origin']='https://attacker.invalid'
    assert c.post('/api/auth/login',json={'email':'test1@example.invalid','password':credential[0]}).status_code==403
    c.headers['Origin']='http://localhost:5173'
    r=c.post('/api/auth/login',json={'email':'test1@example.invalid','password':credential[0]})
    assert r.status_code==200
    assert 'HttpOnly' in r.headers['set-cookie'] and 'SameSite=lax' in r.headers['set-cookie']
    assert 'Domain=' not in r.headers['set-cookie']
    c.headers['X-CSRF-Token']=r.json()['csrf']
    assert c.get('/api/auth/me').json()['role']=='employee'
    assert c.post('/api/auth/logout').status_code==200
    assert c.get('/api/auth/me').status_code==401

def test_signup_cannot_choose_role_or_leak_password(ctx):
    c=ctx[1](); password=secrets.token_urlsafe(24)
    data={'email':'test.signup@example.invalid','name':'TEST signup','password':password}
    r=c.post('/api/auth/signup',json={**data,'role':'admin'})
    assert r.status_code==422 and password not in r.text
    r=c.post('/api/auth/signup',json=data)
    assert r.status_code==201 and r.json()['user']['role']=='employee'
    with ctx[0]() as db:
        user=db.scalar(select(User).where(User.email==data['email']))
        assert user.password_hash.startswith('$argon2id$') and user.password_hash!=password

def test_login_rate_limit(ctx):
    c=ctx[1](); data={'email':'unknown@example.invalid','password':secrets.token_urlsafe(24)}
    for _ in range(10): assert c.post('/api/auth/login',json=data).status_code==401
    assert c.post('/api/auth/login',json=data).status_code==429

def test_creation_rate_limit(ctx,payload):
    c=ctx[1](1)
    for _ in range(10): assert c.post('/api/tickets',json=payload).status_code==201
    assert c.post('/api/tickets',json=payload).status_code==429

def test_report_known_aggregates_and_csv(ctx,payload):
    _,tid=create(ctx,payload)
    with ctx[0]() as db:
        t=db.get(Ticket,tid); t.status='Resolved'; t.first_response_at=t.created_at+60; t.first_response_seconds=60; t.resolved_at=t.created_at+120; t.resolution_seconds=120
        db.add(Rating(ticket_id=tid,author_id=1,stars=4,comment='TEST rating'))
        db.get(Category,1).name='=TEST_FORMULA()'; db.commit()
    c=ctx[1](5); result=c.get('/api/reports').json()
    assert result['total']==1 and result['closed']==1 and result['open']==0
    assert result['avg_first_response_seconds']==60 and result['avg_resolution_seconds']==120
    assert result['sla_compliance']==100 and result['satisfaction']==4
    assert sum(r['count'] for r in result['over_time'])==1
    export=c.get('/api/reports/export.csv')
    rows=list(csv.reader(io.StringIO(export.text.lstrip('\ufeff'))))
    assert ['by_category',"'=TEST_FORMULA()",'1'] in rows
    assert export.headers['content-disposition'].endswith('"ticketdesk-report.csv"')
    assert c.get('/api/reports?start=2020-01-01&end=2026-01-01').status_code==422

@pytest.mark.parametrize('value',['=SUM(A1)','+1','-2','@command','\tformula','\rformula','  =x'])
def test_csv_formula_protection(value): assert safe_cell(value).startswith("'")

def test_health_real_db_query(ctx):
    assert ctx[1]().get('/health').json()=={'status':'ok','database':'connected'}

def test_demo_disabled(ctx,monkeypatch):
    monkeypatch.setenv('DEMO_ENABLED','false')
    assert ctx[1]().post('/api/auth/demo',json={'role':'admin'}).status_code==403
