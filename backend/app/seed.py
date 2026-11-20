"""Explicit, idempotent fictional sandbox seed. Never auto-runs on app import."""
import secrets
import time
from sqlalchemy import select, func
from .db import SessionLocal
from .models import User, Category, SLARule, Ticket, Comment, History, Notification, Rating, SavedReply, SeedMarker
from .security import ph

TITLES = [
 ('IT','Laptop disconnects from office Wi-Fi','The wireless connection drops during calls in the east meeting room. Please help check the adapter.'),
 ('HR','Question about learning allowance','I would like to understand the approval steps for a professional development course this quarter.'),
 ('Admin','Visitor access for a project workshop','Please arrange fictional visitor passes for our internal workshop next week. No external personal details are included.'),
 ('Facilities','Meeting room projector needs attention','The display in the Cedar room flickers after a few minutes. The cable has already been checked.'),
 ('IT','Access to the design team shared folder','Please review my access to the sandbox team folder so I can collaborate on the mock onboarding project.'),
 ('HR','Update to the onboarding checklist','The demonstration onboarding checklist still lists an old orientation room. Could the location be updated?'),
 ('Admin','Stationery restock for the studio','We are running low on notebooks and whiteboard markers in the fictional studio supply cabinet.'),
 ('Facilities','Temperature adjustment in the west zone','The afternoon temperature in the west office zone feels unusually warm. Please inspect the thermostat.'),
 ('IT','Headset microphone not detected','My demo workstation recognizes the headphones but not the microphone. Restarting did not resolve it.'),
 ('HR','Clarification on leave policy','Could you explain how a part-day leave request should be recorded in the demonstration policy workflow?'),
 ('Admin','Book a room for a team planning day','Please help reserve the Maple room for the upcoming fictional team planning session.'),
 ('Facilities','Desk lamp replacement requested','The task lamp at a sample workstation no longer turns on. Please arrange a safe replacement.'),
]

def seed(db):
    if db.get(SeedMarker,'fictional-larkspur-demo-v1'): return False
    if db.scalar(select(func.count()).select_from(User)):
        raise RuntimeError('Refusing to mix public demo accounts into an existing organisation')
    definitions = [('Morgan Vale','admin'),('Jordan Reed','agent'),('Casey Rowan','agent'),('Avery Lane','employee'),('Riley Hart','employee'),('Quinn Ellis','employee'),('Robin Wren','employee')]
    users=[]
    for name,role in definitions:
        user=User(name=name,email=name.lower().replace(' ','.')+'@demo.ticketdesk.invalid',role=role,demo=True,password_hash=ph.hash(secrets.token_urlsafe(48)))
        db.add(user); db.flush(); users.append(user)
    cats={}
    for name in ['IT','HR','Admin','Facilities']:
        cat=Category(name=name); db.add(cat); db.flush(); cats[name]=cat.id
    rules={'Low':(480,4320),'Medium':(240,1440),'High':(60,480),'Urgent':(15,120)}
    for p,(r,s) in rules.items(): db.add(SLARule(priority=p,response_minutes=r,resolution_minutes=s))
    for title,body in [('Taking a look','Thanks for the details. I am looking into this and will share the next steps shortly.'),('More information','Could you share what happened just before the issue started? That will help us narrow it down.'),('Resolution check','The requested change is complete. Please check that everything works as expected; you can reopen this ticket if needed.')]: db.add(SavedReply(title=title,body=body))
    now=time.time()
    statuses=['Resolved','Closed','In progress','Open','Waiting for requester','Resolved','Reopened','Closed','Resolved','In progress']
    priorities=list(rules)
    for i in range(60):
        category,title,description=TITLES[i%len(TITLES)]
        priority=priorities[(i//3)%4]; response,resolution=rules[priority]
        created=now-((59-i)//2)*86400-((i%2)*1800+600)
        status=statuses[i%len(statuses)]
        requester=users[3+i%4]; assignee=users[1+i%2]
        response_delay=min(response*60*(1.5 if i%9==0 else .35),max(60,now-created-120))
        closed=status in ('Resolved','Closed')
        resolved=created+min(resolution*60*(1.25 if i%10==0 else .45),now-created-30) if closed else None
        replied=status!='Open'
        ticket=Ticket(title=title,description=description,category_id=cats[category],requester_id=requester.id,assignee_id=None if status=='Open' else assignee.id,priority=priority,status=status,created_at=created,updated_at=resolved or created+response_delay,response_target=response*60,resolution_target=resolution*60,response_due=created+response*60,resolution_due=created+resolution*60,first_response_at=created+response_delay if replied else None,first_response_seconds=response_delay if replied else None,resolved_at=resolved,resolution_seconds=resolved-created if resolved else None,waiting_since=created+response_delay+10 if status=='Waiting for requester' else None,paused_seconds=0)
        db.add(ticket); db.flush()
        db.add(History(ticket_id=ticket.id,actor_id=requester.id,field='created',new='Open',created_at=created))
        if replied:
            db.add(Comment(ticket_id=ticket.id,author_id=assignee.id,body='Thanks for raising this. I have checked the details and am coordinating the next step with the team.',created_at=created+response_delay,internal=False))
            db.add(History(ticket_id=ticket.id,actor_id=assignee.id,field='reply',new='Added',created_at=created+response_delay))
            db.add(History(ticket_id=ticket.id,actor_id=assignee.id,field='status',old='Open',new=status,created_at=resolved or created+response_delay+10))
            if i%4==0:
                db.add(Comment(ticket_id=ticket.id,author_id=assignee.id,body='Demo internal note: coordinate the handover with the second support agent.',internal=True,created_at=created+response_delay+5))
                db.add(History(ticket_id=ticket.id,actor_id=assignee.id,field='internal_note',new='Added',internal=True,created_at=created+response_delay+5))
        if closed and i%3!=0: db.add(Rating(ticket_id=ticket.id,author_id=requester.id,stars=3+i%3,comment='Fictional feedback: clear communication and helpful follow-up.'))
        if i>50 and replied: db.add(Notification(user_id=requester.id,ticket_id=ticket.id,kind='New reply',created_at=ticket.updated_at))
    db.add(SeedMarker(name='fictional-larkspur-demo-v1')); db.commit(); return True

if __name__=='__main__':
    with SessionLocal() as db:
        print('Fictional Larkspur Studio demo created (60 tickets).' if seed(db) else 'Demo already seeded; no changes made.')
