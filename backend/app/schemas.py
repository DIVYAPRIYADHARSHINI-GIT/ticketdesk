from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Role = Literal['employee', 'agent', 'admin']
Priority = Literal['Low', 'Medium', 'High', 'Urgent']
Status = Literal['Open', 'In progress', 'Waiting for requester', 'Resolved', 'Closed', 'Reopened']

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, strict=True)

class Credentials(Strict):
    email: str = Field(min_length=5, max_length=254, pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    password: str = Field(min_length=12, max_length=128)
    @field_validator('email')
    @classmethod
    def lower_email(cls, value): return value.lower()

class Signup(Credentials):
    name: str = Field(min_length=2, max_length=80)

class Demo(Strict):
    role: Role

class TicketCreate(Strict):
    title: str = Field(min_length=5, max_length=160)
    description: str = Field(min_length=10, max_length=10000)
    category_id: int = Field(gt=0)
    priority: Priority = 'Medium'

class TicketPatch(Strict):
    status: Status | None = None
    priority: Priority | None = None
    assignee_id: int | None = Field(default=None, gt=0)
    @model_validator(mode='after')
    def not_empty(self):
        if not self.model_fields_set: raise ValueError('No changes supplied')
        if 'status' in self.model_fields_set and self.status is None: raise ValueError('Status required')
        if 'priority' in self.model_fields_set and self.priority is None: raise ValueError('Priority required')
        return self

class CommentCreate(Strict):
    body: str = Field(min_length=1, max_length=5000)
    internal: bool = False

class RatingCreate(Strict):
    stars: int = Field(ge=1, le=5)
    comment: str = Field(default='', max_length=1000)

class BulkAssign(Strict):
    ticket_ids: list[int] = Field(min_length=1, max_length=50)
    assignee_id: int = Field(gt=0)
    @field_validator('ticket_ids')
    @classmethod
    def ids(cls, value):
        if any(v < 1 for v in value) or len(set(value)) != len(value): raise ValueError('Unique positive IDs required')
        return value

class UserPatch(Strict):
    role: Role
    active: bool = True

class CategoryInput(Strict):
    name: str = Field(min_length=2, max_length=50)
    active: bool = True

class SLAInput(Strict):
    response_minutes: int = Field(ge=1, le=43200)
    resolution_minutes: int = Field(ge=1, le=129600)
    @model_validator(mode='after')
    def ordered(self):
        if self.resolution_minutes < self.response_minutes: raise ValueError('Resolution must not precede response')
        return self

class ReplyInput(Strict):
    title: str = Field(min_length=2, max_length=80)
    body: str = Field(min_length=1, max_length=5000)
