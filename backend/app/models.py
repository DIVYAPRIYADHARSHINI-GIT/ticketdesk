import time
from sqlalchemy import Boolean, CheckConstraint, Float, ForeignKey, Index, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    role: Mapped[str] = mapped_column(String(20), default='employee')
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    demo: Mapped[bool] = mapped_column(Boolean, default=False)
    __table_args__ = (CheckConstraint("role IN ('employee','agent','admin')"),)

class Session(Base):
    __tablename__ = 'sessions'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    csrf_hash: Mapped[str] = mapped_column(String(64))
    user_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'))
    expires_at: Mapped[float] = mapped_column(Float, index=True)

class Category(Base):
    __tablename__ = 'categories'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class SLARule(Base):
    __tablename__ = 'sla_rules'
    priority: Mapped[str] = mapped_column(String(20), primary_key=True)
    response_minutes: Mapped[int] = mapped_column(Integer)
    resolution_minutes: Mapped[int] = mapped_column(Integer)
    __table_args__ = (CheckConstraint('response_minutes > 0 AND resolution_minutes >= response_minutes'),)

class Ticket(Base):
    __tablename__ = 'tickets'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id'), index=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), index=True)
    priority: Mapped[str] = mapped_column(String(20), index=True)
    status: Mapped[str] = mapped_column(String(30), default='Open', index=True)
    created_at: Mapped[float] = mapped_column(Float, default=time.time, index=True)
    updated_at: Mapped[float] = mapped_column(Float, default=time.time)
    first_response_at: Mapped[float | None] = mapped_column(Float)
    resolved_at: Mapped[float | None] = mapped_column(Float)
    response_due: Mapped[float] = mapped_column(Float, index=True)
    resolution_due: Mapped[float] = mapped_column(Float, index=True)
    response_target: Mapped[int] = mapped_column(Integer)
    resolution_target: Mapped[int] = mapped_column(Integer)
    waiting_since: Mapped[float | None] = mapped_column(Float)
    paused_seconds: Mapped[float] = mapped_column(Float, default=0)
    first_response_seconds: Mapped[float | None] = mapped_column(Float)
    resolution_seconds: Mapped[float | None] = mapped_column(Float)
    __table_args__ = (
        Index('ix_ticket_requester_created', 'requester_id', 'created_at'),
        Index('ix_ticket_queue', 'status', 'priority', 'created_at'),
        CheckConstraint("priority IN ('Low','Medium','High','Urgent')"),
        CheckConstraint("status IN ('Open','In progress','Waiting for requester','Resolved','Closed','Reopened')"),
    )

class Comment(Base):
    __tablename__ = 'comments'
    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey('tickets.id'), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    body: Mapped[str] = mapped_column(Text)
    internal: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[float] = mapped_column(Float, default=time.time)

class Attachment(Base):
    __tablename__ = 'attachments'
    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey('tickets.id'), unique=True)
    author_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    filename: Mapped[str] = mapped_column(String(120))
    mime: Mapped[str] = mapped_column(String(40))
    data: Mapped[bytes] = mapped_column(LargeBinary)
    size: Mapped[int] = mapped_column(Integer)
    __table_args__ = (CheckConstraint('size > 0 AND size <= 1048576'),)

class History(Base):
    __tablename__ = 'history'
    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey('tickets.id'), index=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    field: Mapped[str] = mapped_column(String(50))
    old: Mapped[str] = mapped_column(String(200), default='')
    new: Mapped[str] = mapped_column(String(200), default='')
    internal: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[float] = mapped_column(Float, default=time.time)

class Notification(Base):
    __tablename__ = 'notifications'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    ticket_id: Mapped[int] = mapped_column(ForeignKey('tickets.id'))
    kind: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[float] = mapped_column(Float, default=time.time)
    read_at: Mapped[float | None] = mapped_column(Float)
    __table_args__ = (Index('ix_notification_user_read', 'user_id', 'read_at'),)

class Rating(Base):
    __tablename__ = 'ratings'
    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey('tickets.id'), unique=True)
    author_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    stars: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str] = mapped_column(String(1000), default='')
    __table_args__ = (CheckConstraint('stars >= 1 AND stars <= 5'),)

class SavedReply(Base):
    __tablename__ = 'saved_replies'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(80))
    body: Mapped[str] = mapped_column(Text)

class RateBucket(Base):
    __tablename__ = 'rate_buckets'
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    count: Mapped[int] = mapped_column(Integer, default=1)
    expires_at: Mapped[float] = mapped_column(Float, index=True)

class SeedMarker(Base):
    __tablename__ = 'seed_markers'
    name: Mapped[str] = mapped_column(String(80), primary_key=True)
